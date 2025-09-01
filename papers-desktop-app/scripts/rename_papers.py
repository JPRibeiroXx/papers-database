#!/usr/bin/env python3
"""
Paper renaming and migration script.

This script can:
1. Preview different naming schemes on existing data
2. Update all unique_name fields in the database with a new scheme
3. Optionally rename PDF files to match the new unique names
4. Create a backup before making changes
"""

import argparse
import os
import sys
import sqlite3
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.unique import (
    unique_name_from_row, preview_naming_schemes, NamingScheme, 
    get_scheme_description, suggest_best_scheme
)
from app.db import get_record, update_record, read_all


def preview_schemes_for_database(db_path: str, limit: int = 5) -> None:
    """
    Preview how different naming schemes would look for existing records.
    
    Args:
        db_path: Path to SQLite database
        limit: Number of records to preview
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute(f"SELECT * FROM papers ORDER BY id LIMIT {limit}")
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not records:
            print("No records found in database.")
            return
        
        print(f"Previewing naming schemes for {len(records)} records:")
        print("=" * 100)
        
        # Show current vs proposed schemes
        for i, record in enumerate(records, 1):
            print(f"\nRecord {record['id']}: {record['title'][:50]}...")
            print(f"Current unique_name: {record.get('unique_name', 'None')}")
            print(f"Relates to: {record.get('relates_to')} | Project: {record.get('project_id')} | Year: {record.get('year')}")
            print()
            
            schemes = preview_naming_schemes(record, i)
            for scheme_name, unique_name in schemes.items():
                if unique_name:  # Only show valid names
                    print(f"  {scheme_name.upper():12}: {unique_name}")
            print("-" * 80)
        
        # Suggest best scheme
        suggestion = suggest_best_scheme(records)
        print(f"\nRecommended scheme: {suggestion.value.upper()}")
        print(f"Reason: {get_scheme_description(suggestion)}")
        
    except Exception as e:
        print(f"Error previewing schemes: {e}")


def backup_database(db_path: str) -> str:
    """
    Create a backup of the database.
    
    Args:
        db_path: Path to original database
        
    Returns:
        Path to backup file
    """
    backup_path = f"{db_path}.backup"
    shutil.copy2(db_path, backup_path)
    print(f"Database backed up to: {backup_path}")
    return backup_path


def update_unique_names(db_path: str, scheme: NamingScheme, dry_run: bool = True) -> Dict[str, Any]:
    """
    Update unique names in the database using the specified scheme.
    
    Args:
        db_path: Path to SQLite database
        scheme: Naming scheme to use
        dry_run: If True, only show what would be changed without making changes
        
    Returns:
        Dictionary with update statistics
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Get all records
        cursor = conn.execute("SELECT * FROM papers ORDER BY id")
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not records:
            return {"error": "No records found"}
        
        updates = []
        errors = []
        
        print(f"\n{'DRY RUN - ' if dry_run else ''}Updating unique names with scheme: {scheme.value.upper()}")
        print("=" * 100)
        
        for i, record in enumerate(records, 1):
            try:
                old_name = record.get('unique_name', '')
                new_name = unique_name_from_row(record, i, scheme)
                
                if new_name and new_name != old_name:
                    updates.append({
                        'id': record['id'],
                        'old_name': old_name,
                        'new_name': new_name,
                        'title': record['title'][:50] + '...' if len(record['title']) > 50 else record['title']
                    })
                    
                    print(f"Record {record['id']:3}: {old_name:30} → {new_name}")
                    
                    # Actually update if not dry run
                    if not dry_run:
                        update_record(db_path, record['id'], {'unique_name': new_name})
                        
                elif not new_name:
                    errors.append({
                        'id': record['id'],
                        'error': 'Could not generate unique name',
                        'title': record['title'][:50] + '...' if len(record['title']) > 50 else record['title']
                    })
                    
            except Exception as e:
                errors.append({
                    'id': record['id'],
                    'error': str(e),
                    'title': record.get('title', 'Unknown')[:50]
                })
        
        stats = {
            'total_records': len(records),
            'updates': len(updates),
            'errors': len(errors),
            'unchanged': len(records) - len(updates) - len(errors)
        }
        
        print(f"\nSummary:")
        print(f"  Total records: {stats['total_records']}")
        print(f"  Updates needed: {stats['updates']}")
        print(f"  Errors: {stats['errors']}")
        print(f"  Unchanged: {stats['unchanged']}")
        
        if errors:
            print(f"\nErrors:")
            for error in errors:
                print(f"  Record {error['id']}: {error['error']} - {error['title']}")
        
        return {
            'stats': stats,
            'updates': updates,
            'errors': errors
        }
        
    except Exception as e:
        return {"error": f"Database error: {e}"}


def find_pdf_files(pdf_root: str, old_names: List[str]) -> Dict[str, str]:
    """
    Find PDF files that match the old unique names.
    
    Args:
        pdf_root: Root directory to search for PDFs
        old_names: List of old unique names to look for
        
    Returns:
        Dictionary mapping old names to found file paths
    """
    if not os.path.exists(pdf_root):
        return {}
    
    found_files = {}
    
    # Search for PDF files
    for root, dirs, files in os.walk(pdf_root):
        for file in files:
            if file.lower().endswith('.pdf'):
                file_path = os.path.join(root, file)
                file_name = os.path.splitext(file)[0]
                
                # Check if filename matches any old unique name
                for old_name in old_names:
                    if old_name and (file_name == old_name or old_name in file_name):
                        found_files[old_name] = file_path
                        break
    
    return found_files


def rename_pdf_files(pdf_mappings: Dict[str, str], name_updates: List[Dict], dry_run: bool = True) -> Dict[str, Any]:
    """
    Rename PDF files to match new unique names.
    
    Args:
        pdf_mappings: Dictionary mapping old names to PDF file paths
        name_updates: List of name update dictionaries
        dry_run: If True, only show what would be renamed
        
    Returns:
        Dictionary with rename statistics
    """
    renames = []
    errors = []
    
    print(f"\n{'DRY RUN - ' if dry_run else ''}PDF File Renaming:")
    print("=" * 100)
    
    for update in name_updates:
        old_name = update['old_name']
        new_name = update['new_name']
        
        if old_name in pdf_mappings:
            old_path = pdf_mappings[old_name]
            directory = os.path.dirname(old_path)
            extension = os.path.splitext(old_path)[1]
            new_path = os.path.join(directory, new_name + extension)
            
            try:
                print(f"  {os.path.basename(old_path)} → {os.path.basename(new_path)}")
                
                if not dry_run:
                    if os.path.exists(new_path):
                        errors.append(f"Target file already exists: {new_path}")
                    else:
                        os.rename(old_path, new_path)
                        renames.append({'old': old_path, 'new': new_path})
                        
            except Exception as e:
                errors.append(f"Error renaming {old_path}: {e}")
    
    stats = {
        'total_pdfs_found': len(pdf_mappings),
        'renames': len(renames),
        'errors': len(errors)
    }
    
    print(f"\nPDF Rename Summary:")
    print(f"  PDFs found: {stats['total_pdfs_found']}")
    print(f"  Renames needed: {len([u for u in name_updates if u['old_name'] in pdf_mappings])}")
    print(f"  Successful renames: {stats['renames']}")
    print(f"  Errors: {stats['errors']}")
    
    if errors:
        print(f"\nPDF Rename Errors:")
        for error in errors:
            print(f"  {error}")
    
    return {'stats': stats, 'renames': renames, 'errors': errors}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Rename papers with new unique ID scheme",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview naming schemes
  python rename_papers.py --db papers.db --preview
  
  # Update database with hierarchical scheme (dry run)
  python rename_papers.py --db papers.db --scheme hierarchical --dry-run
  
  # Actually update database and rename PDFs
  python rename_papers.py --db papers.db --scheme hierarchical --pdf-root /path/to/pdfs --execute
        """
    )
    
    parser.add_argument('--db', required=True, help='Path to SQLite database file')
    parser.add_argument('--preview', action='store_true', help='Preview different naming schemes')
    parser.add_argument('--scheme', choices=[s.value for s in NamingScheme], help='Naming scheme to use')
    parser.add_argument('--pdf-root', help='Root directory containing PDF files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    parser.add_argument('--execute', action='store_true', help='Actually perform the changes')
    parser.add_argument('--backup', action='store_true', help='Create database backup before changes')
    parser.add_argument('--limit', type=int, default=5, help='Number of records to preview (default: 5)')
    
    args = parser.parse_args()
    
    # Validate database
    if not os.path.exists(args.db):
        print(f"Error: Database file not found: {args.db}")
        sys.exit(1)
    
    # Preview mode
    if args.preview:
        preview_schemes_for_database(args.db, args.limit)
        return
    
    # Require scheme for updates
    if not args.scheme:
        print("Error: --scheme is required for updates. Use --preview to see options.")
        sys.exit(1)
    
    scheme = NamingScheme(args.scheme)
    dry_run = not args.execute
    
    if dry_run:
        print("DRY RUN MODE - No changes will be made")
        print("Use --execute to actually perform changes")
    
    # Create backup if requested
    if args.backup and not dry_run:
        backup_database(args.db)
    
    # Update unique names
    result = update_unique_names(args.db, scheme, dry_run)
    
    if 'error' in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    
    # Rename PDFs if requested
    if args.pdf_root and result['updates']:
        old_names = [update['old_name'] for update in result['updates']]
        pdf_mappings = find_pdf_files(args.pdf_root, old_names)
        
        if pdf_mappings:
            rename_pdf_files(pdf_mappings, result['updates'], dry_run)
        else:
            print(f"\nNo PDF files found in {args.pdf_root}")
    
    if dry_run:
        print(f"\nTo execute these changes, run with --execute")
    else:
        print(f"\nChanges completed successfully!")


if __name__ == "__main__":
    main()

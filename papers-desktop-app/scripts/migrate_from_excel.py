#!/usr/bin/env python3
"""
Excel to SQLite migration script for papers database.

This script imports data from Excel files into the SQLite database,
following the requirements:
- Select sheet with most rows
- Ignore columns starting with 'Unnamed'
- Normalize column headers
- Generate unique_name for each record
"""

import argparse
import os
import sys
import pandas as pd
import re
from typing import List, Dict, Any

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db import init_schema, create_record, DatabaseError
from app.unique import unique_name_from_row


def normalize_column_name(name: str) -> str:
    """
    Normalize column name according to requirements.
    
    Args:
        name: Raw column name from Excel
        
    Returns:
        Normalized column name
    """
    if not name or pd.isna(name):
        return ""
    
    # Convert to string and strip whitespace
    name = str(name).strip()
    
    # Convert to lowercase
    name = name.lower()
    
    # Replace problematic characters with single space
    name = re.sub(r'[\s\n\r/\(\)\[\]\-.]+', ' ', name)
    
    # Join with underscores
    name = '_'.join(name.split())
    
    return name


def should_ignore_column(col_name: str) -> bool:
    """
    Check if column should be ignored based on name.
    
    Args:
        col_name: Column name to check
        
    Returns:
        True if column should be ignored
    """
    if not col_name:
        return True
    
    # Ignore columns starting with 'Unnamed'
    return str(col_name).startswith('Unnamed')


def get_best_sheet(excel_path: str) -> str:
    """
    Get the sheet name with the most rows.
    
    Args:
        excel_path: Path to Excel file
        
    Returns:
        Name of sheet with most rows
    """
    try:
        # Get all sheet names and their row counts
        excel_file = pd.ExcelFile(excel_path)
        sheet_info = []
        
        for sheet_name in excel_file.sheet_names:
            try:
                # Read just to get shape
                df = pd.read_excel(excel_path, sheet_name=sheet_name, header=1)
                sheet_info.append((sheet_name, len(df)))
            except Exception as e:
                print(f"Warning: Could not read sheet '{sheet_name}': {e}")
                continue
        
        if not sheet_info:
            raise ValueError("No readable sheets found in Excel file")
        
        # Return sheet with most rows
        best_sheet = max(sheet_info, key=lambda x: x[1])
        print(f"Selected sheet '{best_sheet[0]}' with {best_sheet[1]} rows")
        return best_sheet[0]
        
    except Exception as e:
        raise ValueError(f"Failed to analyze Excel file: {e}")


def read_excel_data(excel_path: str, sheet_name: str = None) -> pd.DataFrame:
    """
    Read Excel data with proper header handling.
    
    Args:
        excel_path: Path to Excel file
        sheet_name: Sheet name (if None, auto-select best sheet)
        
    Returns:
        DataFrame with normalized columns
    """
    try:
        if sheet_name is None:
            sheet_name = get_best_sheet(excel_path)
        
        # Read with header=1 (row 1 contains headers)
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=1)
        
        print(f"Read {len(df)} rows from sheet '{sheet_name}'")
        print(f"Original columns: {list(df.columns)}")
        
        # Filter out columns to ignore
        columns_to_keep = []
        column_mapping = {}
        
        for col in df.columns:
            if not should_ignore_column(col):
                normalized = normalize_column_name(col)
                if normalized:
                    columns_to_keep.append(col)
                    column_mapping[col] = normalized
        
        # Keep only desired columns
        df = df[columns_to_keep]
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        print(f"Kept columns: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        raise ValueError(f"Failed to read Excel data: {e}")


def map_excel_columns_to_unique_name(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map Excel columns to the fields needed for unique_name generation.
    
    Based on the Excel analysis, we need to map:
    - title (column 2: 'Title')
    - authors (column 8: 'Relates to') 
    - journal (column 9: 'Project ID')
    - doi (column 6: 'DOI')
    - year (column 3: 'Year')
    """
    # Create a copy to avoid modifying original
    df_mapped = df.copy()
    
    # Map columns based on the Excel structure we analyzed
    column_mappings = {
        # These should already be normalized
        'title': 'title',
        'year': 'year', 
        'published_in': 'journal',  # 'Published In' -> 'journal'
        'doi': 'doi',
        'relates_to': 'authors',    # 'Relates to' -> 'authors'
    }
    
    # Apply mappings where source columns exist
    for source_col, target_col in column_mappings.items():
        if source_col in df_mapped.columns:
            if target_col not in df_mapped.columns or df_mapped[target_col].isna().all():
                df_mapped[target_col] = df_mapped[source_col]
    
    # Ensure we have the required fields for unique_name generation
    if 'journal' not in df_mapped.columns or df_mapped['journal'].isna().all():
        # Use 'published_in' or 'project_id' as journal
        if 'published_in' in df_mapped.columns:
            df_mapped['journal'] = df_mapped['published_in']
        elif 'project_id' in df_mapped.columns:
            df_mapped['journal'] = df_mapped['project_id']
    
    if 'authors' not in df_mapped.columns or df_mapped['authors'].isna().all():
        # Use 'relates_to' as authors
        if 'relates_to' in df_mapped.columns:
            df_mapped['authors'] = df_mapped['relates_to']
    
    return df_mapped


def clean_data_for_database(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare data for database insertion.
    
    Args:
        df: Raw DataFrame
        
    Returns:
        Cleaned DataFrame
    """
    df_clean = df.copy()
    
    # Convert year to integer where possible
    if 'year' in df_clean.columns:
        df_clean['year'] = pd.to_numeric(df_clean['year'], errors='coerce')
        df_clean['year'] = df_clean['year'].astype('Int64')  # Nullable integer
    
    # Handle datetime columns - convert to string
    datetime_columns = df_clean.select_dtypes(include=['datetime64', 'datetime']).columns
    for col in datetime_columns:
        df_clean[col] = df_clean[col].astype(str).replace('NaT', '')
    
    # Handle Timestamp columns
    for col in df_clean.columns:
        if df_clean[col].dtype.name == 'object':
            # Check if column contains pandas Timestamps
            sample_val = df_clean[col].dropna().iloc[0] if not df_clean[col].dropna().empty else None
            if sample_val is not None and hasattr(sample_val, 'strftime'):
                # Convert Timestamp to string
                df_clean[col] = df_clean[col].astype(str).replace('NaT', '')
    
    # Clean string fields
    string_columns = df_clean.select_dtypes(include=['object']).columns
    for col in string_columns:
        # Replace NaN with empty string
        df_clean[col] = df_clean[col].fillna('')
        # Strip whitespace
        df_clean[col] = df_clean[col].astype(str).str.strip()
        # Replace 'nan' string with empty
        df_clean[col] = df_clean[col].replace('nan', '')
    
    return df_clean


def build_db(excel_path: str, db_path: str, sheet_name: str = None) -> None:
    """
    Build SQLite database from Excel file.
    
    Args:
        excel_path: Path to Excel file
        db_path: Path to output SQLite database
        sheet_name: Sheet name (if None, auto-select best sheet)
    """
    try:
        print(f"Starting migration from {excel_path} to {db_path}")
        
        # Read Excel data
        df = read_excel_data(excel_path, sheet_name)
        
        if len(df) == 0:
            print("Warning: No data found in Excel file")
            return
        
        # Map columns for unique_name generation
        df = map_excel_columns_to_unique_name(df)
        
        # Ensure common fields exist AFTER mapping
        common_fields = ['title', 'authors', 'year', 'journal', 'doi', 'url', 
                        'abstract', 'keywords', 'tags', 'notes', 'status', 'pdf']
        
        for field in common_fields:
            if field not in df.columns:
                df[field] = ''
                print(f"Added missing field: {field}")
        
        # Clean data
        df = clean_data_for_database(df)
        
        # Initialize database schema
        columns = [col for col in df.columns if col not in ['id', 'unique_name', 'created_at', 'updated_at']]
        print(f"Initializing database with columns: {columns}")
        
        init_schema(db_path, columns)
        
        # Insert records
        success_count = 0
        error_count = 0
        
        print(f"Inserting {len(df)} records...")
        
        for index, row in df.iterrows():
            try:
                # Convert row to dictionary
                record_data = row.to_dict()
                
                # Create record
                create_record(db_path, record_data)
                success_count += 1
                
                if success_count % 10 == 0:
                    print(f"  Inserted {success_count} records...")
                    
            except DatabaseError as e:
                print(f"  Error inserting row {index}: {e}")
                error_count += 1
                continue
        
        print(f"Migration complete!")
        print(f"  Successfully inserted: {success_count} records")
        if error_count > 0:
            print(f"  Errors: {error_count} records")
        
        # Show some statistics
        from app.db import get_stats
        stats = get_stats(db_path)
        print(f"  Total records in database: {stats['total_records']}")
        print(f"  FTS5 enabled: {stats['has_fts']}")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        raise


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate papers data from Excel to SQLite database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate_from_excel.py --excel papers.xlsx --out papers.db
  python migrate_from_excel.py --excel papers.xlsx --out papers.db --sheet "Sheet2"
        """
    )
    
    parser.add_argument(
        '--excel', 
        required=True,
        help='Path to Excel file to import'
    )
    
    parser.add_argument(
        '--out', 
        required=True,
        help='Path to output SQLite database file'
    )
    
    parser.add_argument(
        '--sheet',
        help='Sheet name to import (if not specified, uses sheet with most rows)'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing database file'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.excel):
        print(f"Error: Excel file not found: {args.excel}")
        sys.exit(1)
    
    if os.path.exists(args.out) and not args.overwrite:
        print(f"Error: Database file already exists: {args.out}")
        print("Use --overwrite to replace existing database")
        sys.exit(1)
    
    try:
        # Remove existing database if overwriting
        if args.overwrite and os.path.exists(args.out):
            os.remove(args.out)
            print(f"Removed existing database: {args.out}")
        
        # Run migration
        build_db(args.excel, args.out, args.sheet)
        
        print(f"\nDatabase created successfully: {args.out}")
        
    except Exception as e:
        print(f"\nMigration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

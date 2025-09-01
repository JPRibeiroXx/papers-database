"""
Database layer for papers database.

This module handles all SQLite database operations including:
- Schema initialization with FTS5 support
- CRUD operations
- Search functionality with FTS5 fallback to LIKE
- CSV export
"""

import sqlite3
import csv
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import os

from .unique import unique_name_from_row

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


def init_schema(db_path: str, columns: List[str]) -> None:
    """
    Initialize database schema with the given columns.
    
    Args:
        db_path: Path to SQLite database file
        columns: List of column names from Excel (excluding id, unique_name, timestamps)
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Create main table
        column_defs = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
        
        # Add user columns (from Excel)
        for col in columns:
            if col.lower() == 'year':
                column_defs.append(f"{col} INTEGER")
            else:
                column_defs.append(f"{col} TEXT")
        
        # Add derived and system columns
        column_defs.extend([
            "unique_name TEXT",
            "created_at TEXT DEFAULT (datetime('now'))",
            "updated_at TEXT DEFAULT (datetime('now'))"
        ])
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS papers (
            {', '.join(column_defs)}
        )
        """
        
        conn.execute(create_table_sql)
        
        # Try to create FTS5 virtual table
        fts_columns = _get_fts_columns(columns)
        try:
            fts_sql = f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
                {', '.join(fts_columns)},
                content='papers',
                content_rowid='id'
            )
            """
            conn.execute(fts_sql)
            
            # Create triggers to keep FTS in sync
            _create_fts_triggers(conn, fts_columns)
            
            logger.info("FTS5 virtual table created successfully")
            
        except sqlite3.OperationalError as e:
            logger.warning(f"FTS5 not available: {e}. Will use LIKE fallback for search.")
        
        # Create indexes for common queries
        conn.execute("CREATE INDEX IF NOT EXISTS idx_year ON papers(year)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_journal ON papers(journal)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_unique_name ON papers(unique_name)")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database schema initialized at {db_path}")
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to initialize schema: {e}")


def _get_fts_columns(columns: List[str]) -> List[str]:
    """Get columns that should be included in FTS index."""
    fts_candidates = ['title', 'authors', 'journal', 'abstract', 'keywords', 'tags', 'notes']
    return [col for col in columns if col.lower() in fts_candidates]


def _create_fts_triggers(conn: sqlite3.Connection, fts_columns: List[str]) -> None:
    """Create triggers to keep FTS table in sync with main table."""
    
    # Insert trigger
    insert_sql = f"""
    CREATE TRIGGER IF NOT EXISTS papers_fts_insert AFTER INSERT ON papers BEGIN
        INSERT INTO papers_fts(rowid, {', '.join(fts_columns)})
        VALUES (new.id, {', '.join(f'new.{col}' for col in fts_columns)});
    END
    """
    conn.execute(insert_sql)
    
    # Update trigger
    update_sql = f"""
    CREATE TRIGGER IF NOT EXISTS papers_fts_update AFTER UPDATE ON papers BEGIN
        UPDATE papers_fts SET {', '.join(f'{col} = new.{col}' for col in fts_columns)}
        WHERE rowid = new.id;
    END
    """
    conn.execute(update_sql)
    
    # Delete trigger
    delete_sql = """
    CREATE TRIGGER IF NOT EXISTS papers_fts_delete AFTER DELETE ON papers BEGIN
        DELETE FROM papers_fts WHERE rowid = old.id;
    END
    """
    conn.execute(delete_sql)


def list_columns(db_path: str) -> List[str]:
    """
    Get list of columns in the papers table.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        List of column names
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("PRAGMA table_info(papers)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        return columns
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to list columns: {e}")


def has_fts_support(db_path: str) -> bool:
    """Check if database has FTS5 support enabled."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='papers_fts'")
        result = cursor.fetchone() is not None
        conn.close()
        return result
    except sqlite3.Error:
        return False


def read_all(db_path: str, search: Optional[str] = None, filters: Optional[Dict[str, Any]] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Read records from database with optional search and filters.
    
    Args:
        db_path: Path to SQLite database file
        search: Search term for FTS or LIKE search
        filters: Dictionary of column filters (e.g., {'year': 2023, 'journal': 'Nature'})
        limit: Maximum number of records to return
        
    Returns:
        List of record dictionaries
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Build query
        if search and has_fts_support(db_path):
            # Use FTS5 search
            query = """
            SELECT papers.* FROM papers
            JOIN papers_fts ON papers.id = papers_fts.rowid
            WHERE papers_fts MATCH ?
            """
            params = [search]
        elif search:
            # Fallback to LIKE search
            search_columns = ['title', 'authors', 'journal', 'abstract', 'keywords', 'tags', 'notes', 'doi', 'url']
            like_conditions = []
            params = []
            
            for col in search_columns:
                like_conditions.append(f"{col} LIKE ?")
                params.append(f"%{search}%")
            
            query = f"SELECT * FROM papers WHERE ({' OR '.join(like_conditions)})"
        else:
            query = "SELECT * FROM papers"
            params = []
        
        # Add filters
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if value:  # Skip empty filters
                    if isinstance(value, str):
                        filter_conditions.append(f"{key} LIKE ?")
                        params.append(f"%{value}%")
                    else:
                        filter_conditions.append(f"{key} = ?")
                        params.append(value)
            
            if filter_conditions:
                connector = " AND " if search else " WHERE "
                query += connector + " AND ".join(filter_conditions)
        
        # Add ordering and limit
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionaries
        result = [dict(row) for row in rows]
        
        conn.close()
        return result
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to read records: {e}")


def create_record(db_path: str, data: Dict[str, Any]) -> int:
    """
    Create a new record in the database.
    
    Args:
        db_path: Path to SQLite database file
        data: Dictionary of column values
        
    Returns:
        ID of the created record
    """
    try:
        # Generate unique_name (skip for now, will be handled separately)
        # data['unique_name'] = unique_name_from_row(data)
        data['created_at'] = datetime.now().isoformat()
        data['updated_at'] = datetime.now().isoformat()
        
        conn = sqlite3.connect(db_path)
        
        # Get column names (excluding id which is auto-increment)
        columns = list_columns(db_path)
        columns = [col for col in columns if col != 'id']
        
        # Filter data to only include existing columns
        filtered_data = {k: v for k, v in data.items() if k in columns}
        
        # Build insert query
        placeholders = ', '.join(['?' for _ in filtered_data])
        column_names = ', '.join(filtered_data.keys())
        
        query = f"INSERT INTO papers ({column_names}) VALUES ({placeholders})"
        values = list(filtered_data.values())
        
        cursor = conn.execute(query, values)
        record_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created record with ID {record_id}")
        return record_id
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to create record: {e}")


def update_record(db_path: str, rec_id: int, data: Dict[str, Any]) -> None:
    """
    Update an existing record in the database.
    
    Args:
        db_path: Path to SQLite database file
        rec_id: ID of record to update
        data: Dictionary of column values to update
    """
    try:
        # Generate unique_name (skip for now, will be handled separately)
        # data['unique_name'] = unique_name_from_row(data)
        data['updated_at'] = datetime.now().isoformat()
        
        conn = sqlite3.connect(db_path)
        
        # Get column names (excluding id)
        columns = list_columns(db_path)
        columns = [col for col in columns if col != 'id']
        
        # Filter data to only include existing columns
        filtered_data = {k: v for k, v in data.items() if k in columns}
        
        # Build update query
        set_clauses = [f"{col} = ?" for col in filtered_data.keys()]
        query = f"UPDATE papers SET {', '.join(set_clauses)} WHERE id = ?"
        values = list(filtered_data.values()) + [rec_id]
        
        cursor = conn.execute(query, values)
        
        if cursor.rowcount == 0:
            raise DatabaseError(f"No record found with ID {rec_id}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated record with ID {rec_id}")
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to update record: {e}")


def delete_record(db_path: str, rec_id: int) -> None:
    """
    Delete a record from the database.
    
    Args:
        db_path: Path to SQLite database file
        rec_id: ID of record to delete
    """
    try:
        conn = sqlite3.connect(db_path)
        
        cursor = conn.execute("DELETE FROM papers WHERE id = ?", (rec_id,))
        
        if cursor.rowcount == 0:
            raise DatabaseError(f"No record found with ID {rec_id}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted record with ID {rec_id}")
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to delete record: {e}")


def get_record(db_path: str, rec_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a single record by ID.
    
    Args:
        db_path: Path to SQLite database file
        rec_id: ID of record to retrieve
        
    Returns:
        Record dictionary or None if not found
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("SELECT * FROM papers WHERE id = ?", (rec_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        return dict(row) if row else None
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to get record: {e}")


def export_csv(db_path: str, out_path: str) -> None:
    """
    Export all records to CSV file.
    
    Args:
        db_path: Path to SQLite database file
        out_path: Path to output CSV file
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("SELECT * FROM papers ORDER BY id")
        rows = cursor.fetchall()
        
        if not rows:
            raise DatabaseError("No records to export")
        
        # Write CSV
        with open(out_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = rows[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
        
        conn.close()
        
        logger.info(f"Exported {len(rows)} records to {out_path}")
        
    except (sqlite3.Error, IOError) as e:
        raise DatabaseError(f"Failed to export CSV: {e}")


def get_unique_values(db_path: str, column: str) -> List[str]:
    """
    Get unique values for a column (useful for filters/dropdowns).
    
    Args:
        db_path: Path to SQLite database file
        column: Column name
        
    Returns:
        List of unique values
    """
    try:
        conn = sqlite3.connect(db_path)
        
        cursor = conn.execute(f"SELECT DISTINCT {column} FROM papers WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}")
        values = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return values
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to get unique values: {e}")


def get_stats(db_path: str) -> Dict[str, Any]:
    """
    Get database statistics.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        Dictionary with statistics
    """
    try:
        conn = sqlite3.connect(db_path)
        
        # Total records
        cursor = conn.execute("SELECT COUNT(*) FROM papers")
        total_records = cursor.fetchone()[0]
        
        # Records by year
        cursor = conn.execute("SELECT year, COUNT(*) FROM papers WHERE year IS NOT NULL GROUP BY year ORDER BY year DESC LIMIT 10")
        by_year = dict(cursor.fetchall())
        
        # Recent additions
        cursor = conn.execute("SELECT COUNT(*) FROM papers WHERE date(created_at) >= date('now', '-7 days')")
        recent_additions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_records': total_records,
            'by_year': by_year,
            'recent_additions': recent_additions,
            'has_fts': has_fts_support(db_path)
        }
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to get statistics: {e}")


# Database validation and maintenance
def validate_database(db_path: str) -> List[str]:
    """
    Validate database integrity and return list of issues.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        List of validation issues (empty if all good)
    """
    issues = []
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Check if main table exists
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='papers'")
        if not cursor.fetchone():
            issues.append("Main 'papers' table does not exist")
            return issues
        
        # Check for records with missing unique_name
        cursor = conn.execute("SELECT COUNT(*) FROM papers WHERE unique_name IS NULL OR unique_name = ''")
        missing_unique = cursor.fetchone()[0]
        if missing_unique > 0:
            issues.append(f"{missing_unique} records have missing unique_name")
        
        # Check for duplicate unique_names
        cursor = conn.execute("SELECT unique_name, COUNT(*) FROM papers WHERE unique_name != '' GROUP BY unique_name HAVING COUNT(*) > 1")
        duplicates = cursor.fetchall()
        if duplicates:
            issues.append(f"{len(duplicates)} duplicate unique_name values found")
        
        conn.close()
        
    except sqlite3.Error as e:
        issues.append(f"Database error: {e}")
    
    return issues


if __name__ == "__main__":
    # Simple test
    test_db = "test_papers.db"
    
    # Initialize with test columns
    test_columns = ['title', 'authors', 'year', 'journal', 'doi', 'abstract']
    init_schema(test_db, test_columns)
    
    # Create test record
    test_data = {
        'title': 'Test Paper',
        'authors': 'Smith, J.',
        'year': 2024,
        'journal': 'Test Journal',
        'doi': '10.1234/test',
        'abstract': 'This is a test abstract.'
    }
    
    rec_id = create_record(test_db, test_data)
    print(f"Created record: {rec_id}")
    
    # Read back
    records = read_all(test_db)
    print(f"Found {len(records)} records")
    
    # Clean up
    os.remove(test_db)

"""
Lookup table management for papers database.

This module manages the reference tables for relates_to and project_id fields,
allowing users to maintain the categories and projects that papers can belong to.
"""

import sqlite3
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def init_lookup_tables(db_path: str) -> None:
    """
    Initialize lookup tables for relates_to and project_id.
    
    Args:
        db_path: Path to SQLite database file
    """
    try:
        conn = sqlite3.connect(db_path)
        
        # Create relates_to lookup table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS relates_to_lookup (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # Create project_id lookup table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project_id_lookup (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # Populate with existing values from papers table if empty
        cursor = conn.execute("SELECT COUNT(*) FROM relates_to_lookup")
        if cursor.fetchone()[0] == 0:
            _populate_relates_to_defaults(conn)
        
        cursor = conn.execute("SELECT COUNT(*) FROM project_id_lookup")
        if cursor.fetchone()[0] == 0:
            _populate_project_id_defaults(conn)
        
        conn.commit()
        conn.close()
        
        logger.info("Lookup tables initialized successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize lookup tables: {e}")


def _populate_relates_to_defaults(conn: sqlite3.Connection) -> None:
    """Populate relates_to lookup with default values."""
    defaults = [
        ('BRNG', 'Braining', 'Brain-related research and studies'),
        ('FE35', 'Fellowship i3S', 'Fellowship research at i3S institute'),
        ('PHHD', 'PhD', 'PhD thesis research'),
        ('OTER', 'Other', 'Other types of research')
    ]
    
    for code, name, desc in defaults:
        conn.execute(
            "INSERT OR IGNORE INTO relates_to_lookup (id, name, description) VALUES (?, ?, ?)",
            (code, name, desc)
        )


def _populate_project_id_defaults(conn: sqlite3.Connection) -> None:
    """Populate project_id lookup with default values."""
    defaults = [
        ('SYEL', 'Systematic Review + ML Model', 'Rationale for model development (inputs, outputs and architecture)'),
        ('IBON', 'Ibidi Perfusion', 'Figure out flow and seeding conditions for microfluidics 3D perfusion'),
        ('CANG', 'Cardiac Bioprinting', 'Figure out best bioprinting practices for cardiac tissue'),
        ('AING', 'AI in Bioprinting', 'Use of AI in bioprinting to scale it'),
        ('SCNG', 'Scaling Bioprinting', 'Approaches to scale bioprinted constructs'),
        ('CALS', 'Cardiac Models', 'Study and develop cardiac 3D models'),
        ('CAGY', 'Cardiomyocyte Biology', "How CM's biology lets us achieve upscaled models"),
        ('AITS', 'AI Agents', 'AI Agents research'),
        ('AGLS', 'Ageing Cardiac Models', 'How we can study and mimic ageing in cardiac models'),
        ('JOLN', 'Journal Club - MERLN', 'Journal Club Meetings @ MERLN')
    ]
    
    for code, name, desc in defaults:
        conn.execute(
            "INSERT OR IGNORE INTO project_id_lookup (id, name, description) VALUES (?, ?, ?)",
            (code, name, desc)
        )


def get_relates_to_options(db_path: str) -> List[Dict[str, str]]:
    """
    Get all relates_to options.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        List of dictionaries with id, name, description
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("SELECT id, name, description FROM relates_to_lookup ORDER BY name")
        result = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return result
        
    except sqlite3.Error as e:
        logger.error(f"Failed to get relates_to options: {e}")
        return []


def get_project_id_options(db_path: str) -> List[Dict[str, str]]:
    """
    Get all project_id options.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        List of dictionaries with id, name, description
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("SELECT id, name, description FROM project_id_lookup ORDER BY name")
        result = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return result
        
    except sqlite3.Error as e:
        logger.error(f"Failed to get project_id options: {e}")
        return []


def add_relates_to_option(db_path: str, code: str, name: str, description: str = "") -> bool:
    """
    Add a new relates_to option.
    
    Args:
        db_path: Path to SQLite database file
        code: Short code (e.g., 'BRNG')
        name: Full name (e.g., 'Braining')
        description: Optional description
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO relates_to_lookup (id, name, description) VALUES (?, ?, ?)",
            (code.upper(), name, description)
        )
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Failed to add relates_to option: {e}")
        return False


def add_project_id_option(db_path: str, code: str, name: str, description: str = "") -> bool:
    """
    Add a new project_id option.
    
    Args:
        db_path: Path to SQLite database file
        code: Short code (e.g., 'SYEL')
        name: Full name (e.g., 'Systematic Review + ML Model')
        description: Optional description
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO project_id_lookup (id, name, description) VALUES (?, ?, ?)",
            (code.upper(), name, description)
        )
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Failed to add project_id option: {e}")
        return False


def update_relates_to_option(db_path: str, code: str, name: str, description: str = "") -> bool:
    """Update an existing relates_to option."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "UPDATE relates_to_lookup SET name = ?, description = ? WHERE id = ?",
            (name, description, code.upper())
        )
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
        
    except sqlite3.Error as e:
        logger.error(f"Failed to update relates_to option: {e}")
        return False


def update_project_id_option(db_path: str, code: str, name: str, description: str = "") -> bool:
    """Update an existing project_id option."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "UPDATE project_id_lookup SET name = ?, description = ? WHERE id = ?",
            (name, description, code.upper())
        )
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
        
    except sqlite3.Error as e:
        logger.error(f"Failed to update project_id option: {e}")
        return False


def delete_relates_to_option(db_path: str, code: str) -> bool:
    """Delete a relates_to option (only if not used in papers)."""
    try:
        conn = sqlite3.connect(db_path)
        
        # Check if used in papers
        cursor = conn.execute("SELECT COUNT(*) FROM papers WHERE relates_to = ?", (code.upper(),))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False  # Cannot delete if used
        
        # Delete from lookup
        cursor = conn.execute("DELETE FROM relates_to_lookup WHERE id = ?", (code.upper(),))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return success
        
    except sqlite3.Error as e:
        logger.error(f"Failed to delete relates_to option: {e}")
        return False


def delete_project_id_option(db_path: str, code: str) -> bool:
    """Delete a project_id option (only if not used in papers)."""
    try:
        conn = sqlite3.connect(db_path)
        
        # Check if used in papers
        cursor = conn.execute("SELECT COUNT(*) FROM papers WHERE project_id = ?", (code.upper(),))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False  # Cannot delete if used
        
        # Delete from lookup
        cursor = conn.execute("DELETE FROM project_id_lookup WHERE id = ?", (code.upper(),))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return success
        
    except sqlite3.Error as e:
        logger.error(f"Failed to delete project_id option: {e}")
        return False

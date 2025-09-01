"""
Settings management using QSettings.

This module provides a wrapper around QSettings to manage application preferences
including database path and PDF root directory.
"""

import os
from typing import Optional
from PyQt6.QtCore import QSettings


class AppSettings:
    """Wrapper around QSettings for application preferences."""
    
    def __init__(self):
        """Initialize settings with organization and application name."""
        self.settings = QSettings("PapersDB", "Desktop App")
    
    @property
    def db_path(self) -> Optional[str]:
        """Get the database file path."""
        path = self.settings.value("database/path", None)
        return path if path else None
    
    @db_path.setter
    def db_path(self, path: str) -> None:
        """Set the database file path."""
        self.settings.setValue("database/path", path)
        self.settings.sync()
    
    @property
    def pdf_root(self) -> Optional[str]:
        """Get the PDF root directory path."""
        path = self.settings.value("pdf/root", None)
        return path if path else None
    
    @pdf_root.setter
    def pdf_root(self, path: str) -> None:
        """Set the PDF root directory path."""
        self.settings.setValue("pdf/root", path)
        self.settings.sync()
    
    @property
    def window_geometry(self) -> Optional[bytes]:
        """Get the main window geometry."""
        return self.settings.value("window/geometry", None)
    
    @window_geometry.setter
    def window_geometry(self, geometry: bytes) -> None:
        """Set the main window geometry."""
        self.settings.setValue("window/geometry", geometry)
        self.settings.sync()
    
    @property
    def window_state(self) -> Optional[bytes]:
        """Get the main window state."""
        return self.settings.value("window/state", None)
    
    @window_state.setter
    def window_state(self, state: bytes) -> None:
        """Set the main window state."""
        self.settings.setValue("window/state", state)
        self.settings.sync()
    
    @property
    def last_import_dir(self) -> Optional[str]:
        """Get the last directory used for importing files."""
        path = self.settings.value("import/last_dir", None)
        return path if path else None
    
    @last_import_dir.setter
    def last_import_dir(self, path: str) -> None:
        """Set the last directory used for importing files."""
        self.settings.setValue("import/last_dir", path)
        self.settings.sync()
    
    @property
    def last_export_dir(self) -> Optional[str]:
        """Get the last directory used for exporting files."""
        path = self.settings.value("export/last_dir", None)
        return path if path else None
    
    @last_export_dir.setter
    def last_export_dir(self, path: str) -> None:
        """Set the last directory used for exporting files."""
        self.settings.setValue("export/last_dir", path)
        self.settings.sync()
    
    @property
    def search_limit(self) -> int:
        """Get the search result limit."""
        return self.settings.value("search/limit", 1000, type=int)
    
    @search_limit.setter
    def search_limit(self, limit: int) -> None:
        """Set the search result limit."""
        self.settings.setValue("search/limit", limit)
        self.settings.sync()
    
    @property
    def table_column_widths(self) -> dict:
        """Get saved table column widths."""
        widths = {}
        self.settings.beginGroup("table/columns")
        for key in self.settings.childKeys():
            widths[key] = self.settings.value(key, type=int)
        self.settings.endGroup()
        return widths
    
    def set_table_column_width(self, column: str, width: int) -> None:
        """Set table column width."""
        self.settings.setValue(f"table/columns/{column}", width)
        self.settings.sync()
    
    def get_default_db_path(self) -> str:
        """Get default database path in user's documents folder."""
        documents_dir = os.path.expanduser("~/Documents")
        return os.path.join(documents_dir, "papers.db")
    
    def get_default_pdf_root(self) -> str:
        """Get default PDF root directory."""
        documents_dir = os.path.expanduser("~/Documents")
        return os.path.join(documents_dir, "PDFs")
    
    def is_configured(self) -> bool:
        """Check if basic settings are configured."""
        return self.db_path is not None
    
    def reset_all(self) -> None:
        """Reset all settings to defaults."""
        self.settings.clear()
        self.settings.sync()
    
    def export_settings(self, file_path: str) -> bool:
        """
        Export settings to a file.
        
        Args:
            file_path: Path to export file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a temporary settings object for export
            export_settings = QSettings(file_path, QSettings.Format.IniFormat)
            
            # Copy all settings
            for key in self.settings.allKeys():
                value = self.settings.value(key)
                export_settings.setValue(key, value)
            
            export_settings.sync()
            return export_settings.status() == QSettings.Status.NoError
            
        except Exception:
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """
        Import settings from a file.
        
        Args:
            file_path: Path to import file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            # Create a temporary settings object for import
            import_settings = QSettings(file_path, QSettings.Format.IniFormat)
            
            # Copy all settings
            for key in import_settings.allKeys():
                value = import_settings.value(key)
                self.settings.setValue(key, value)
            
            self.settings.sync()
            return self.settings.status() == QSettings.Status.NoError
            
        except Exception:
            return False
    
    def get_recent_databases(self) -> list:
        """Get list of recently opened databases."""
        recent = []
        self.settings.beginGroup("recent/databases")
        for key in sorted(self.settings.childKeys()):
            path = self.settings.value(key)
            if path and os.path.exists(path):
                recent.append(path)
        self.settings.endGroup()
        return recent
    
    def add_recent_database(self, db_path: str) -> None:
        """Add database to recent list."""
        if not db_path or not os.path.exists(db_path):
            return
        
        recent = self.get_recent_databases()
        
        # Remove if already in list
        if db_path in recent:
            recent.remove(db_path)
        
        # Add to front
        recent.insert(0, db_path)
        
        # Keep only last 10
        recent = recent[:10]
        
        # Save back
        self.settings.beginGroup("recent/databases")
        self.settings.remove("")  # Clear existing
        for i, path in enumerate(recent):
            self.settings.setValue(str(i), path)
        self.settings.endGroup()
        self.settings.sync()
    
    def clear_recent_databases(self) -> None:
        """Clear recent databases list."""
        self.settings.beginGroup("recent/databases")
        self.settings.remove("")
        self.settings.endGroup()
        self.settings.sync()


# Global settings instance
_settings_instance = None


def get_settings() -> AppSettings:
    """Get the global settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = AppSettings()
    return _settings_instance


def configure_logging_from_settings():
    """Configure logging based on settings (for future use)."""
    import logging
    
    # For now, just set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


if __name__ == "__main__":
    # Simple test
    settings = AppSettings()
    
    print("Current settings:")
    print(f"  DB Path: {settings.db_path}")
    print(f"  PDF Root: {settings.pdf_root}")
    print(f"  Is Configured: {settings.is_configured()}")
    
    # Test setting values
    settings.db_path = "/tmp/test.db"
    settings.pdf_root = "/tmp/pdfs"
    
    print("\nAfter setting:")
    print(f"  DB Path: {settings.db_path}")
    print(f"  PDF Root: {settings.pdf_root}")
    print(f"  Is Configured: {settings.is_configured()}")
    
    # Test recent databases
    settings.add_recent_database("/tmp/test1.db")
    settings.add_recent_database("/tmp/test2.db")
    print(f"\nRecent databases: {settings.get_recent_databases()}")

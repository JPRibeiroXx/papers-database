# Papers Desktop Database

A cross-platform desktop CRUD application for managing a scientific papers database. Built with PyQt6 and SQLite, featuring full-text search, Excel import, and PDF integration.

## Features

- **Cross-platform desktop UI** using PyQt6
- **SQLite database** with auto-increment IDs and FTS5 full-text search
- **Excel import** with automatic column normalization and data cleaning
- **Fast search** using SQLite FTS5 (with LIKE fallback if unavailable)
- **PDF integration** - open papers in system viewer from database
- **Full CRUD operations** - Create, Read, Update, Delete records
- **Advanced filtering** by year, journal, and search terms
- **CSV export** for data portability
- **Unique name generation** following specified formula
- **Settings persistence** using QSettings (database path, PDF root)
- **Data validation** and database integrity checks

## Installation & Setup

### Requirements

- Python 3.10 or higher
- PyQt6, pandas, openpyxl (see requirements.txt)

### Install and Run

```bash
# Clone or download the repository
cd papers-desktop-app

# Create virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m app.main
```

## Quick Start

### First Time Setup

1. **Launch the application** - you'll see a welcome dialog
2. **Configure settings** (File → Settings or toolbar button):
   - Set **Database Path** (where to store your SQLite database)
   - Set **PDF Root Directory** (where your PDF files are located)
3. **Import your Excel data** (File → Import Excel):
   - Select your Excel file
   - The app will automatically choose the sheet with the most rows
   - Columns starting with "Unnamed" will be ignored
   - Column headers will be normalized (lowercased, spaces to underscores)

### Using the Application

- **Search**: Enter terms in the search box and click Search
- **Filter**: Use Year and Journal filters to narrow results
- **Add Record**: Click "Add Record" to create new entries
- **Edit Record**: Double-click a row or select and click "Edit Record"
- **Delete Record**: Select a row and click "Delete Record"
- **Open PDF**: Select a record and click "Open PDF" (uses pdf field)
- **Export**: Use File → Export CSV to save all data

## Excel Import Details

The import process follows these rules:

- **Sheet Selection**: Automatically selects the sheet with the most rows
- **Header Row**: Uses row 2 as headers (row 1 is skipped)
- **Column Filtering**: Ignores any columns whose headers start with "Unnamed"
- **Column Normalization**:
  - Converts to lowercase
  - Replaces whitespace, newlines, and punctuation with underscores
  - Example: "Published In" → "published_in"
- **Required Fields**: Ensures these fields exist (creates empty if missing):
  - `title`, `authors`, `year`, `journal`, `doi`, `url`, `abstract`, `keywords`, `tags`, `notes`, `status`, `pdf`
- **Data Cleaning**:
  - Converts year to integer where possible
  - Replaces null/NaN values with empty strings
  - Strips whitespace from text fields

## Unique Name Generation

Each record gets a `unique_name` field generated using this formula:

```
YYYY-TIxx-AUTHORS-JOURNAL-DOI
```

Where:

- **YYYY**: 4-digit year
- **TI**: First 2 letters of title + last 2 letters of title (uppercase)
- **AUTHORS**: Authors field (cleaned)
- **JOURNAL**: Journal/publication field (cleaned)
- **DOI**: DOI field (cleaned)

If any required field is missing, `unique_name` will be empty.

Example: `2023-PRNG-SMITH-NATURE-12345`

## Database Schema

The SQLite database contains a `papers` table with:

- `id` - Auto-increment primary key
- All columns from your Excel file (with normalized names)
- `unique_name` - Generated identifier
- `created_at` - Record creation timestamp
- `updated_at` - Last modification timestamp

### Full-Text Search

If SQLite supports FTS5, a `papers_fts` virtual table is created for fast searching across:

- title, authors, journal, abstract, keywords, tags, notes

If FTS5 is unavailable, search falls back to LIKE queries across the same fields.

## PDF Integration

The application can open PDF files associated with records:

1. **PDF Field**: Each record can have a `pdf` field containing a file path
2. **Path Resolution**:
   - Absolute paths are used as-is
   - Relative paths are resolved against the configured PDF Root directory
3. **Opening**: Uses system default application:
   - Windows: `os.startfile()`
   - macOS: `open` command
   - Linux: `xdg-open` command

## Command Line Migration

You can migrate Excel data to SQLite without the GUI:

```bash
python scripts/migrate_from_excel.py --excel /path/to/PapersDB.xlsx --out papers.db

# Options:
# --sheet "SheetName"  # Specify sheet (otherwise auto-selects)
# --overwrite          # Replace existing database
```

## Settings

Application settings are stored using QSettings and include:

- **Database Path**: Location of SQLite database file
- **PDF Root**: Base directory for relative PDF paths
- **Search Limit**: Maximum search results (default: 1000)
- **Window State**: Size, position, column widths
- **Recent Databases**: Recently opened database files

Settings are automatically saved and restored between sessions.

## Data Validation

The application includes validation features:

- **Database Integrity**: Check for missing unique_names, duplicates
- **Statistics**: View record counts, recent additions, year distribution
- **FTS Status**: Shows whether full-text search is enabled

Access via Tools menu: "Validate Database" and "Database Statistics"

## Troubleshooting

### Import Issues

- **"No readable sheets"**: Check that your Excel file has data starting in row 2
- **"Missing columns"**: Ensure your Excel has headers in row 1 (actual data starts row 2)
- **"Import failed"**: Check file permissions and that Excel file isn't open elsewhere

### Search Issues

- **No results**: Try clearing filters and searching again
- **Slow search**: If you have many records, consider using more specific search terms

### PDF Issues

- **"File not found"**: Check that PDF Root is set correctly in settings
- **"Failed to open"**: Ensure you have a PDF viewer installed

### Database Issues

- **"Database error"**: Run Tools → Validate Database to check for issues
- **Performance**: For large databases (>10k records), consider using more specific filters

## Future Enhancements

Potential improvements for future versions:

- **Packaging**: PyInstaller executable for easy distribution
- **Backup/Sync**: Cloud storage integration
- **Advanced Search**: Boolean operators, field-specific search
- **Batch Operations**: Bulk edit/delete capabilities
- **Import Formats**: Support for other formats (BibTeX, EndNote, etc.)
- **Themes**: Dark mode and custom themes

## Technical Details

### Architecture

- **app/main.py**: PyQt6 UI and main application logic
- **app/db.py**: SQLite database operations and FTS5 integration
- **app/unique.py**: Unique name generation logic
- **app/settings.py**: QSettings wrapper for preferences
- **scripts/migrate_from_excel.py**: Command-line Excel import tool

### Dependencies

- **PyQt6**: Cross-platform GUI framework
- **pandas**: Excel reading and data manipulation
- **openpyxl**: Excel file format support
- **sqlite3**: Built into Python, no additional install needed

### Database Features

- **FTS5**: Full-text search with automatic triggers
- **Indexes**: Performance indexes on year, journal, unique_name
- **Transactions**: Atomic operations for data integrity
- **Validation**: Built-in data consistency checks

## License

This project is provided as-is for educational and research purposes.

## Support

For issues or questions:

1. Check this README for common solutions
2. Use Tools → Validate Database to check for data issues
3. Check the application logs for error details
4. Ensure all dependencies are properly installed

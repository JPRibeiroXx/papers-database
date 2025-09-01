# Papers Database - Scientific Literature Management System

A powerful, cross-platform desktop application for managing scientific papers, research articles, and academic literature. Built with PyQt6 and SQLite, this application provides comprehensive tools for researchers, academics, and students to organize, search, and maintain their scientific literature collections.

_Papers Database - Making scientific literature management simple and efficient._

## Features

### Core Functionality

- **Complete CRUD Operations**: Create, read, update, and delete paper records with intuitive interfaces
- **Advanced Search**: Full-text search across titles, abstracts, and content with FTS5 indexing
- **Excel Import**: Bulk import from Excel files with automatic column mapping and data normalization
- **PDF Management**: Automatic PDF linking, renaming, and organization
- **Unique Naming System**: Intelligent paper identification with multiple naming schemes

### Data Management

- **Flexible Schema**: Dynamic database structure that adapts to your data
- **Category Management**: Organize papers by research areas and project categories
- **Automatic Code Generation**: Intelligent 4-letter codes for categories and projects
- **Data Export**: Export to CSV format and Zotero-compatible databases
- **Multi-Selection Support**: Select multiple papers for batch operations

### User Interface

- **Modern Design**: Clean, professional interface built with PyQt6
- **Responsive Layout**: Adaptive table design with proper text wrapping
- **Read-Only Tables**: Prevents accidental data modification
- **Interactive Elements**: Clickable checkboxes for read status and PDF opening
- **Cross-Platform**: Consistent experience across Windows, macOS, and Linux

### Search and Organization

- **Full-Text Search**: Search across all text fields with relevance ranking
- **Filtering Options**: Filter by categories, projects, read status, and more
- **Sorting Capabilities**: Sort by date added, ID, or other criteria
- **Keyword Integration**: Search within abstracts and titles for comprehensive results

## Getting Started

### Prerequisites

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- 500MB available disk space
- PDF viewer application

### Installation

#### Option 1: Automated Installation (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd PaperDB

# Run the installation script
chmod +x install.sh
./install.sh
```

#### Option 2: Manual Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir PDFs logs
```

### Configuration

#### First Launch Setup

1. **Create PDFs Directory**: The application requires a dedicated folder for PDF storage

   - Create a `PDFs` folder in your desired location
   - This folder will store all paper PDFs with organized naming

2. **Database Initialization**: The application automatically creates `papers.db` on first launch

   - Database file is created in the application directory
   - No manual database setup required

3. **Settings Configuration**: Application settings are stored in `user_settings.ini`
   - PDF root directory path
   - Database location
   - User preferences

### First Launch

```bash
# Navigate to the application directory
cd papers-desktop-app

# Launch the application
python -m app.main
```

## Project Structure

```
PaperDB/
├── papers-desktop-app/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Main application window
│   │   ├── db.py                # Database operations
│   │   ├── lookups.py           # Category and project management
│   │   ├── unique.py            # Unique naming algorithms
│   │   └── settings.py          # Application configuration
│   ├── requirements.txt          # Python dependencies
│   ├── setup.py                 # Package configuration
│   └── install.sh               # Installation script
├── PDFs/                        # PDF storage directory
├── logs/                        # Application logs
├── README.md                    # This file
├── LICENSE                      # License information
└── .gitignore                  # Git ignore patterns
```

## Configuration

### Environment Variables

- `PDF_ROOT`: Path to PDF storage directory
- `DB_PATH`: Custom database file location
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

### Application Settings

- **PDF Management**: Configure PDF storage location and naming conventions
- **Database Options**: Set database path and backup preferences
- **Interface Preferences**: Customize table columns and display options
- **Search Settings**: Configure search algorithms and result limits

## Usage Guide

### Adding Papers

1. **Manual Entry**: Use the "Add Record" button for individual papers
2. **PDF Upload**: Attach PDFs during record creation for automatic organization
3. **Excel Import**: Bulk import from existing Excel databases
4. **Data Validation**: Automatic validation of required fields

### Managing Categories

1. **Access Management**: Tools > Manage Categories
2. **Add Categories**: Create new research area classifications
3. **Auto-Code Generation**: 4-letter codes automatically generated from names
4. **Edit/Delete**: Modify existing categories as needed

### Search Operations

1. **Quick Search**: Use the search bar for immediate results
2. **Advanced Filters**: Combine multiple search criteria
3. **Full-Text Search**: Search within paper content and abstracts
4. **Result Management**: Sort, filter, and export search results

### Data Export

1. **CSV Export**: Export selected papers to CSV format
2. **Zotero Integration**: Export to Zotero-compatible database
3. **PDF Inclusion**: Include associated PDFs in exports
4. **Batch Operations**: Export multiple papers simultaneously

## Advanced Features

### Unique Naming System

The application supports multiple naming schemes for paper identification:

- **Hierarchical**: `YYYY-TIx-AUTHORS-JOURNAL-DOI`
- **Sequential**: `PAPER-001`, `PAPER-002`
- **Year-Based**: `2024-001`, `2024-002`
- **Project-First**: `PROJECT-YYYY-001`
- **Simple**: `PAPER-001`

### Database Management

- **Automatic Backups**: Regular database backup creation
- **Schema Evolution**: Dynamic column addition and modification
- **Data Integrity**: Foreign key constraints and validation
- **Performance Optimization**: Indexed fields for fast queries

### PDF Organization

- **Automatic Renaming**: PDFs renamed according to unique naming scheme
- **File Linking**: Database records linked to physical PDF files
- **Storage Optimization**: Efficient file organization and retrieval
- **Cross-Platform Compatibility**: Works across different operating systems

## Important Notes

### Data Privacy

- **Local Storage**: All data stored locally on your machine
- **No Cloud Sync**: No automatic data transmission to external servers
- **User Control**: Complete control over data location and access
- **Backup Responsibility**: Users responsible for backing up their data

### File Management

- **PDF Organization**: PDFs automatically organized in designated folder
- **Naming Convention**: Consistent naming scheme for easy identification
- **File Integrity**: Automatic validation of PDF file associations
- **Storage Efficiency**: Optimized file organization and retrieval

### Performance

- **Database Optimization**: SQLite with FTS5 for fast text search
- **Memory Management**: Efficient memory usage for large paper collections
- **Search Speed**: Indexed fields for rapid query execution
- **File Access**: Optimized PDF file access and management

## Troubleshooting

### Common Issues

#### Application Won't Start

- Verify Python 3.8+ installation
- Check virtual environment activation
- Ensure all dependencies are installed
- Review error logs in `logs/` directory

#### PDF Upload Issues

- Verify PDF file integrity
- Check file permissions in PDFs directory
- Ensure sufficient disk space
- Validate PDF file format compatibility

#### Search Problems

- Rebuild search index if needed
- Check database file permissions
- Verify text encoding in imported data
- Clear and regenerate search cache

#### Performance Issues

- Optimize database with VACUUM command
- Check available system memory
- Review log files for errors
- Consider database optimization

### Error Resolution

- **Database Errors**: Check file permissions and disk space
- **PDF Issues**: Verify file integrity and storage location
- **Import Problems**: Validate Excel file format and data structure
- **Search Issues**: Rebuild full-text search index

## License

This software is licensed under a custom license that permits personal and educational use. See the `LICENSE` file for complete terms and conditions.

**Key Restrictions:**

- Personal use only
- No redistribution
- No modification
- No commercial use without permission

## Contributing

This is a personal research tool. Contributions are not currently accepted for public distribution.

## Support

For technical support or questions:

- Review this documentation thoroughly
- Check the troubleshooting section
- Examine application logs for error details
- Ensure proper system requirements

## Future Enhancements

### Planned Features

- **Cloud Synchronization**: Optional cloud backup and sync
- **Advanced Analytics**: Citation analysis and research metrics
- **Collaborative Features**: Shared libraries and annotations
- **Mobile Application**: Companion mobile app for field research
- **API Integration**: Connect with academic databases and repositories

### Development Roadmap

- **Version 2.0**: Enhanced search and filtering capabilities
- **Version 2.1**: Advanced PDF processing and text extraction
- **Version 2.2**: Integration with academic databases
- **Version 3.0**: Cloud-based collaboration features

---

**Papers Database** - Empowering researchers with efficient literature management tools.

_Last updated: January 2025_

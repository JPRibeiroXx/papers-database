# Papers Database - Scientific Literature Management System

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Custom-red.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![SQLite](https://img.shields.io/badge/database-SQLite-blue.svg)](https://sqlite.org/)

**A powerful, cross-platform desktop application for managing scientific papers, research articles, and academic literature.**

Built with PyQt6 and SQLite, this application provides comprehensive tools for researchers, academics, and students to organize, search, and maintain their scientific literature collections with professional-grade features and intuitive user experience.

[🚀 Quick Start](#getting-started) • [📚 Documentation](#usage-guide) • [⚙️ Configuration](#configuration) • [📄 License](#license)

## Features

Papers Database delivers a comprehensive suite of literature management capabilities designed for modern research workflows.

### Core Functionality

| Feature               | Description                                                                   | Technology              |
| --------------------- | ----------------------------------------------------------------------------- | ----------------------- |
| **CRUD Operations**   | Complete Create, Read, Update, Delete operations with intuitive interfaces    | PyQt6 Forms             |
| **Advanced Search**   | Full-text search across titles, abstracts, and content with relevance ranking | SQLite FTS5             |
| **Excel Integration** | Bulk import from Excel files with automatic column mapping and normalization  | pandas, openpyxl        |
| **PDF Management**    | Automatic PDF linking, renaming, and organization with filesystem integration | Cross-platform file ops |
| **Unique Naming**     | Intelligent paper identification with multiple configurable naming schemes    | Custom algorithms       |

### Data Management

- **Flexible Schema**: Dynamic database structure that adapts to your research data
- **Category Management**: Organize papers by research areas and project categories
- **Auto Code Generation**: Intelligent 4-letter codes automatically generated for categories
- **Export Capabilities**: Export to CSV format and Zotero-compatible databases
- **Multi-Selection**: Select multiple papers for efficient batch operations
- **Data Integrity**: Foreign key constraints and comprehensive validation

### User Interface

- **Modern Design**: Clean, professional interface built with PyQt6 framework
- **Responsive Layout**: Adaptive table design with proper text wrapping and resizing
- **Read-Only Tables**: Prevents accidental data modification with controlled editing
- **Interactive Elements**: Clickable checkboxes for read status and direct PDF opening
- **Cross-Platform**: Consistent user experience across Windows, macOS, and Linux
- **Performance**: Optimized for large literature collections

### Search and Organization

- **Full-Text Search**: Search across all text fields with intelligent relevance ranking
- **Advanced Filtering**: Filter by categories, projects, read status, and custom criteria
- **Smart Sorting**: Sort by date added, ID, relevance, or any custom field
- **Keyword Integration**: Deep search within abstracts and titles for comprehensive results

## Getting Started

### Prerequisites

Before installing Papers Database, ensure your system meets these requirements:

| Requirement | Minimum                               | Recommended     |
| ----------- | ------------------------------------- | --------------- |
| **Python**  | 3.8+                                  | 3.9+            |
| **RAM**     | 4GB                                   | 8GB             |
| **Storage** | 500MB                                 | 2GB             |
| **OS**      | Windows 10, macOS 10.14, Ubuntu 18.04 | Latest versions |

**Additional Requirements:**

- PDF viewer application (system default or Adobe Reader)
- Git for repository cloning
- Administrative privileges for installation

### Installation

Choose your preferred installation method:

#### Option 1: Automated Installation (Recommended)

The automated installation script handles all dependencies and configuration:

```bash
# Clone the repository
git clone https://github.com/JPRibeiroXx/papers-database.git
cd papers-database

# Make installation script executable
chmod +x install.sh

# Run automated installation
./install.sh
```

The script will:

- ✅ Check Python version compatibility
- ✅ Create and configure virtual environment
- ✅ Install all required dependencies
- ✅ Set up directory structure
- ✅ Configure initial settings

#### Option 2: Manual Installation

For advanced users who prefer manual control:

```bash
# Clone the repository
git clone https://github.com/JPRibeiroXx/papers-database.git
cd papers-database

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p PDFs logs
```

### Configuration

#### Initial Setup and First Launch

Follow these steps to configure Papers Database for optimal performance:

##### 1. PDF Storage Configuration

**Critical First Step:** Configure your PDF storage directory before first launch.

```bash
# Create your PDF storage directory
mkdir ~/Documents/PaperDB_PDFs  # Recommended location
# or choose your preferred location
```

**Important Notes:**

- ⚠️ Choose a location with sufficient storage space (minimum 2GB recommended)
- ✅ Ensure write permissions to the selected directory
- 📝 Remember this path for application configuration

##### 2. Database Initialization

Papers Database automatically handles database setup:

- **Automatic Creation**: `papers.db` is created on first launch
- **Location**: Application directory (configurable)
- **Schema**: Dynamic schema adapts to your research needs
- **Indexing**: FTS5 search indexes created automatically

##### 3. Application Launch

```bash
# Navigate to application directory
cd papers-database/papers-desktop-app

# Activate virtual environment (if not already active)
source ../venv/bin/activate  # Linux/macOS
# or
..\venv\Scripts\activate     # Windows

# Launch Papers Database
python -m app.main
```

**On first launch, you'll be prompted to:**

1. Select your PDF storage directory
2. Configure basic preferences
3. Import existing data (optional)

## Project Structure

Papers Database follows a modular architecture designed for maintainability and extensibility:

```
papers-database/
├── papers-desktop-app/              # Main application directory
│   ├── app/                         # Core application modules
│   │   ├── __init__.py              # Package initialization
│   │   ├── main.py                  # Main application window & UI logic
│   │   ├── db.py                    # Database operations & schema management
│   │   ├── lookups.py               # Category and project management
│   │   ├── unique.py                # Unique naming algorithms
│   │   └── settings.py              # Configuration management
│   ├── requirements.txt             # Python dependencies specification
│   ├── setup.py                     # Package configuration for distribution
│   └── install.sh                   # Automated installation script
├── PDFs/                            # PDF storage directory (created by user)
├── logs/                            # Application logs and debug information
├── README.md                        # This documentation file
├── LICENSE                          # License terms and conditions
└── .gitignore                       # Git ignore patterns for data privacy
```

### Architecture Overview

| Component           | Purpose                            | Technology Stack           |
| ------------------- | ---------------------------------- | -------------------------- |
| **Frontend**        | User interface and interaction     | PyQt6, Qt Designer         |
| **Backend**         | Data processing and business logic | Python 3.8+, SQLite        |
| **Database**        | Data storage and search            | SQLite with FTS5 extension |
| **File Management** | PDF organization and linking       | Python os, shutil modules  |

## Advanced Configuration

### Environment Variables

Configure Papers Database behavior using environment variables:

| Variable          | Description                        | Default       | Example                     |
| ----------------- | ---------------------------------- | ------------- | --------------------------- |
| `PDF_ROOT`        | Path to PDF storage directory      | `./PDFs/`     | `/home/user/research/pdfs/` |
| `DB_PATH`         | Custom database file location      | `./papers.db` | `/data/research.db`         |
| `LOG_LEVEL`       | Logging verbosity level            | `INFO`        | `DEBUG`, `WARNING`, `ERROR` |
| `BACKUP_INTERVAL` | Automatic backup frequency (hours) | `24`          | `12`, `6`                   |

### Application Settings

Fine-tune your Papers Database experience:

#### PDF Management

- **Storage Location**: Configure PDF directory path and organization
- **Naming Conventions**: Choose from multiple unique naming schemes
- **File Validation**: Enable automatic PDF integrity checking
- **Backup Strategy**: Configure automatic PDF backup policies

#### Database Options

- **Location**: Set custom database file path
- **Backup Settings**: Configure automatic backup frequency and retention
- **Performance**: Adjust cache sizes and query optimization
- **Indexing**: Configure full-text search indexing behavior

#### Interface Preferences

- **Table Layout**: Customize visible columns and display order
- **Search Settings**: Configure search result limits and ranking
- **Theme Options**: Adjust color schemes and font preferences
- **Workflow**: Customize default behaviors and shortcuts

## Usage Guide

Master Papers Database with these comprehensive workflow guides designed for researchers at all levels.

### Adding Papers

Papers Database supports multiple methods for adding research papers to your collection:

#### Method 1: Manual Entry

```
1. Click "Add Record" button in the main toolbar
2. Fill in paper details (title, authors, abstract, etc.)
3. Optionally upload PDF file for automatic organization
4. Click "Save" to add paper to your database
```

**Features:**

- ✅ Real-time validation of required fields
- 🎯 Auto-suggestion for existing categories
- 📄 PDF upload with automatic renaming
- 🏷️ Unique identifier generation

#### Method 2: Excel Bulk Import

```
1. Navigate to File > Import > Excel
2. Select your Excel file containing paper data
3. Map columns to database fields
4. Preview and validate import data
5. Execute bulk import operation
```

**Supported Excel Features:**

- 📊 Automatic column detection and mapping
- 🔄 Data normalization and cleanup
- ⚠️ Error detection and reporting
- 📈 Progress tracking for large imports

#### Method 3: PDF with Metadata Extraction

```
1. Drag and drop PDF files into the application
2. Automatic metadata extraction where possible
3. Manual verification and completion of fields
4. Automatic file organization and linking
```

### Managing Categories and Projects

Organize your research with intelligent categorization:

#### Category Management

```
Access: Tools > Manage Categories
```

**Operations Available:**

- ➕ **Add New Categories**: Create research area classifications
- 🏷️ **Auto-Code Generation**: 4-letter codes automatically generated from category names
- ✏️ **Edit Categories**: Modify existing category names and codes
- 🗑️ **Delete Categories**: Remove unused categories (with safety checks)

**Example Category Generation:**

- "Machine Learning" → **MALE**
- "Biomedical Engineering" → **BIEG**
- "Quantum Computing" → **QUNG**

#### Project Organization

```
Access: Tools > Manage Projects
```

- Link papers to specific research projects
- Cross-reference related work
- Generate project-based reports
- Filter by project assignments

### Advanced Search Operations

Papers Database provides powerful search capabilities for efficient literature discovery:

#### Quick Search

```
Location: Main search bar (top of interface)
Scope: Titles, authors, keywords, abstracts
```

#### Advanced Search Builder

```
Access: Search > Advanced Search
```

**Available Filters:**

- 📅 **Date Range**: Filter by publication or addition date
- 👥 **Authors**: Search by specific author names
- 📖 **Categories**: Filter by research area classifications
- 🏷️ **Projects**: Show papers from specific projects
- ✅ **Read Status**: Filter by read/unread status
- 📄 **Has PDF**: Show only papers with attached PDFs

#### Full-Text Search

```
Technology: SQLite FTS5 with relevance ranking
Searchable Content: All text fields, PDF content (if extracted)
```

**Search Tips:**

- Use quotes for exact phrases: `"machine learning"`
- Combine terms with AND/OR: `neural AND networks`
- Use wildcards for partial matches: `bio*`

### Data Export and Integration

#### CSV Export

```
1. Select papers in main table (Ctrl+Click for multiple)
2. Navigate to File > Export > CSV
3. Choose export fields and format options
4. Select destination file
5. Execute export operation
```

#### Zotero Integration

```
1. Select papers for export
2. Choose File > Export > Zotero Database
3. Select export location
4. Choose to include PDFs (optional)
5. Generate Zotero-compatible database
```

**Export Features:**

- 🎯 **Selective Export**: Choose specific papers or collections
- 📄 **PDF Inclusion**: Optionally include PDF files in export
- 🔧 **Format Options**: Multiple export formats supported
- ✅ **Validation**: Export validation and error checking

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

## License

This software is distributed under a **Custom License** designed to support educational and research use while protecting intellectual property.

### License Summary

| Permission              | Status     | Description                                           |
| ----------------------- | ---------- | ----------------------------------------------------- |
| ✅ **Personal Use**     | Allowed    | Use for individual research and academic work         |
| ✅ **Educational Use**  | Allowed    | Use in academic institutions and educational settings |
| ❌ **Commercial Use**   | Restricted | Requires explicit written permission                  |
| ❌ **Redistribution**   | Prohibited | Cannot share or distribute copies                     |
| ❌ **Modification**     | Restricted | Code modifications not permitted                      |
| ❌ **Derivative Works** | Prohibited | Cannot create derived software                        |

📜 **Full License Terms**: See [`LICENSE`](LICENSE) file for complete terms and conditions.

### Important Notes

- **As-Is Provision**: Software provided without warranty or guarantee
- **Educational Priority**: Designed specifically for academic and research environments
- **Contact Required**: Commercial use requires prior written authorization
- **Liability Limitation**: Authors not liable for any damages or data loss

## Contributing

Papers Database is currently maintained as a **personal research tool** with focused development goals.

### Current Status

- 🔒 **Closed Source**: Not accepting public contributions at this time
- 🎯 **Focused Development**: Maintaining specific research workflow optimization
- 📧 **Feedback Welcome**: Bug reports and feature suggestions appreciated

### Future Plans

- 📈 **Community Version**: Considering open-source release for future versions
- 🤝 **Collaboration**: Potential academic partnerships under evaluation
- 🔧 **Plugin System**: Planned extensibility for custom integrations

**Contact**: For collaboration inquiries or feature requests, please refer to the support section below.

## Support

For technical support or questions:

- **Documentation**: Review this README thoroughly for comprehensive guidance
- **Email**: Contact information available in LICENSE file
- **Response Time**: Academic/educational users prioritized
- **Issue Types**: Bug reports, feature requests, compatibility questions
- **LinkedIn**: Connect with the developer at [@joaosribeiro99](https://www.linkedin.com/in/joaosribeiro99/)



---

<div align="center">

## Papers Database

**Empowering researchers with intelligent literature management**

[![Made with Python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Built with PyQt6](https://img.shields.io/badge/Built%20with-PyQt6-41CD52.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Powered by SQLite](https://img.shields.io/badge/Powered%20by-SQLite-003B57.svg)](https://sqlite.org/)

_Advancing scientific research through efficient literature management_

**Last Updated**: September 2025 | **Version**: 1.0.0 | **License**: Custom Academic License

</div>

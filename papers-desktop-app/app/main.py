#!/usr/bin/env python3
"""
Main PyQt6 application for Papers Desktop Database.

This module implements the main UI with:
- Main window with table view
- Search and filter functionality  
- CRUD dialogs
- PDF opening functionality
- Settings management
- Excel import and CSV export
"""

import sys
import os
import platform
import subprocess
import traceback
from typing import Optional, List, Dict, Any
import logging

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QToolBar, QStatusBar, QMessageBox, QDialog, QDialogButtonBox,
    QFormLayout, QTextEdit, QSpinBox, QFileDialog, QProgressDialog,
    QHeaderView, QAbstractItemView, QComboBox, QGroupBox, QCheckBox,
    QSplitter, QTabWidget, QPlainTextEdit, QListWidget, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QIcon

from .settings import get_settings, configure_logging_from_settings
from .db import (
    init_schema, read_all, create_record, update_record, delete_record,
    get_record, export_csv, list_columns, get_unique_values, get_stats,
    validate_database, DatabaseError
)
from .lookups import (
    init_lookup_tables, get_relates_to_options, get_project_id_options,
    add_relates_to_option, add_project_id_option, update_relates_to_option,
    update_project_id_option, delete_relates_to_option, delete_project_id_option
)

# Configure logging
configure_logging_from_settings()
logger = logging.getLogger(__name__)


class ImportWorker(QThread):
    """Background worker for Excel import operations."""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, excel_path: str, db_path: str):
        super().__init__()
        self.excel_path = excel_path
        self.db_path = db_path
    
    def run(self):
        try:
            # Import the migration function
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from scripts.migrate_from_excel import build_db
            
            self.progress.emit("Starting Excel import...")
            build_db(self.excel_path, self.db_path)
            self.finished.emit(True, "Import completed successfully")
            
        except Exception as e:
            error_msg = f"Import failed: {str(e)}"
            logger.error(f"Import error: {e}\n{traceback.format_exc()}")
            self.finished.emit(False, error_msg)


class RecordDialog(QDialog):
    """Dialog for creating/editing records."""
    
    def __init__(self, parent=None, record_data: Optional[Dict[str, Any]] = None, db_path: str = None):
        super().__init__(parent)
        self.record_data = record_data or {}
        self.db_path = db_path
        self.is_edit = record_data is not None
        
        self.setWindowTitle("Edit Record" if self.is_edit else "Add Record")
        self.setModal(True)
        self.resize(600, 400)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Main form
        form_layout = QFormLayout()
        self.fields = {}
        
        # Title
        self.title_edit = QLineEdit()
        self.title_edit.setText(self.record_data.get('title', ''))
        form_layout.addRow("Title:", self.title_edit)
        self.fields['title'] = self.title_edit
        
        # Year
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1900, 2050)
        self.year_spin.setValue(self.record_data.get('year', 2024) or 2024)
        form_layout.addRow("Year:", self.year_spin)
        self.fields['year'] = self.year_spin
        
        # Published In
        self.published_edit = QLineEdit()
        self.published_edit.setText(self.record_data.get('published_in', ''))
        form_layout.addRow("Published In:", self.published_edit)
        self.fields['published_in'] = self.published_edit
        
        # Type
        self.type_combo = QComboBox()
        self.type_combo.setEditable(True)
        self.type_combo.addItems(['Original', 'Review', 'Meta-analysis', 'Case Study', 'Editorial', 'Letter'])
        current_type = self.record_data.get('type', 'Original')
        self.type_combo.setCurrentText(current_type)
        form_layout.addRow("Type:", self.type_combo)
        self.fields['type'] = self.type_combo
        
        # DOI (clickable)
        doi_layout = QHBoxLayout()
        self.doi_edit = QLineEdit()
        self.doi_edit.setText(self.record_data.get('doi', ''))
        self.doi_button = QPushButton("Open DOI")
        self.doi_button.clicked.connect(self.open_doi)
        self.doi_button.setEnabled(bool(self.doi_edit.text()))
        self.doi_edit.textChanged.connect(lambda text: self.doi_button.setEnabled(bool(text)))
        doi_layout.addWidget(self.doi_edit)
        doi_layout.addWidget(self.doi_button)
        form_layout.addRow("DOI:", doi_layout)
        self.fields['doi'] = self.doi_edit
        
        # Relates To (dropdown)
        self.relates_combo = QComboBox()
        self.relates_combo.setEditable(True)
        if self.db_path:
            relates_options = get_relates_to_options(self.db_path)
            for option in relates_options:
                self.relates_combo.addItem(f"{option['id']} - {option['name']}", option['id'])
        current_relates = self.record_data.get('relates_to', '')
        if current_relates:
            index = self.relates_combo.findData(current_relates)
            if index >= 0:
                self.relates_combo.setCurrentIndex(index)
            else:
                self.relates_combo.setCurrentText(current_relates)
        form_layout.addRow("Relates To:", self.relates_combo)
        self.fields['relates_to'] = self.relates_combo
        
        # Project ID (dropdown)
        self.project_combo = QComboBox()
        self.project_combo.setEditable(True)
        if self.db_path:
            project_options = get_project_id_options(self.db_path)
            for option in project_options:
                self.project_combo.addItem(f"{option['id']} - {option['name']}", option['id'])
        current_project = self.record_data.get('project_id', '')
        if current_project:
            index = self.project_combo.findData(current_project)
            if index >= 0:
                self.project_combo.setCurrentIndex(index)
            else:
                self.project_combo.setCurrentText(current_project)
        form_layout.addRow("Project:", self.project_combo)
        self.fields['project_id'] = self.project_combo
        
        # Read checkbox
        self.read_checkbox = QCheckBox()
        read_value = self.record_data.get('read', '')
        self.read_checkbox.setChecked(bool(read_value and read_value.lower() in ['yes', 'true', '1', 'checked']))
        form_layout.addRow("Read:", self.read_checkbox)
        self.fields['read'] = self.read_checkbox
        
        # Abstract (larger text area)
        self.abstract_edit = QTextEdit()
        self.abstract_edit.setMaximumHeight(120)
        self.abstract_edit.setPlainText(self.record_data.get('abstract', ''))
        form_layout.addRow("Abstract:", self.abstract_edit)
        self.fields['abstract'] = self.abstract_edit
        
        # PDF file section
        if not self.is_edit:  # Only show for new records
            pdf_layout = QHBoxLayout()
            self.pdf_path_edit = QLineEdit()
            self.pdf_browse_btn = QPushButton("Browse PDF...")
            self.pdf_browse_btn.clicked.connect(self.browse_pdf)
            pdf_layout.addWidget(self.pdf_path_edit)
            pdf_layout.addWidget(self.pdf_browse_btn)
            form_layout.addRow("PDF File:", pdf_layout)
            self.fields['pdf_upload'] = self.pdf_path_edit
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def open_doi(self):
        """Open DOI in web browser."""
        doi = self.doi_edit.text().strip()
        if doi:
            if not doi.startswith('http'):
                if doi.startswith('10.'):
                    doi = f"https://doi.org/{doi}"
                else:
                    doi = f"https://doi.org/{doi}"
            
            if platform.system() == "Windows":
                os.startfile(doi)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", doi])
            else:  # Linux
                subprocess.run(["xdg-open", doi])
    
    def browse_pdf(self):
        """Browse for PDF file to upload."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF File", "",
            "PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            self.pdf_path_edit.setText(file_path)
    
    def get_data(self) -> Dict[str, Any]:
        """Get form data as dictionary."""
        data = {}
        
        # Handle different widget types
        data['title'] = self.title_edit.text().strip()
        data['year'] = self.year_spin.value()
        data['published_in'] = self.published_edit.text().strip()
        data['type'] = self.type_combo.currentText().strip()
        data['doi'] = self.doi_edit.text().strip()
        data['abstract'] = self.abstract_edit.toPlainText().strip()
        
        # Handle dropdowns
        relates_data = self.relates_combo.currentData()
        if relates_data:
            data['relates_to'] = relates_data
        else:
            data['relates_to'] = self.relates_combo.currentText().strip().split(' - ')[0]
        
        project_data = self.project_combo.currentData()
        if project_data:
            data['project_id'] = project_data
        else:
            data['project_id'] = self.project_combo.currentText().strip().split(' - ')[0]
        
        # Handle checkbox
        data['read'] = 'Yes' if self.read_checkbox.isChecked() else 'No'
        
        # Handle PDF upload for new records
        if not self.is_edit and hasattr(self, 'pdf_path_edit'):
            pdf_path = self.pdf_path_edit.text().strip()
            if pdf_path:
                data['pdf_upload'] = pdf_path
        
        return data


class CategoriesDialog(QDialog):
    """Dialog for managing categories (relates_to and project_id)."""
    
    def __init__(self, parent=None, db_path: str = None):
        super().__init__(parent)
        self.db_path = db_path
        
        self.setWindowTitle("Manage Categories")
        self.setModal(True)
        self.resize(700, 500)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tabs for the two types of categories
        tabs = QTabWidget()
        
        # Relates To tab
        relates_tab = QWidget()
        relates_layout = QVBoxLayout(relates_tab)
        
        relates_layout.addWidget(QLabel("Research Categories (Relates To):"))
        
        # Relates To table
        self.relates_table = QTableWidget()
        self.relates_table.setColumnCount(3)
        self.relates_table.setHorizontalHeaderLabels(["Code", "Name", "Description"])
        relates_layout.addWidget(self.relates_table)
        
        # Relates To buttons
        relates_buttons = QHBoxLayout()
        self.add_relates_btn = QPushButton("Add Category")
        self.edit_relates_btn = QPushButton("Edit Category")
        self.delete_relates_btn = QPushButton("Delete Category")
        
        self.add_relates_btn.clicked.connect(self.add_relates_category)
        self.edit_relates_btn.clicked.connect(self.edit_relates_category)
        self.delete_relates_btn.clicked.connect(self.delete_relates_category)
        
        relates_buttons.addWidget(self.add_relates_btn)
        relates_buttons.addWidget(self.edit_relates_btn)
        relates_buttons.addWidget(self.delete_relates_btn)
        relates_buttons.addStretch()
        
        relates_layout.addLayout(relates_buttons)
        tabs.addTab(relates_tab, "Research Categories")
        
        # Project ID tab
        project_tab = QWidget()
        project_layout = QVBoxLayout(project_tab)
        
        project_layout.addWidget(QLabel("Projects (Project ID):"))
        
        # Project ID table
        self.project_table = QTableWidget()
        self.project_table.setColumnCount(3)
        self.project_table.setHorizontalHeaderLabels(["Code", "Name", "Description"])
        project_layout.addWidget(self.project_table)
        
        # Project ID buttons
        project_buttons = QHBoxLayout()
        self.add_project_btn = QPushButton("Add Project")
        self.edit_project_btn = QPushButton("Edit Project")
        self.delete_project_btn = QPushButton("Delete Project")
        
        self.add_project_btn.clicked.connect(self.add_project)
        self.edit_project_btn.clicked.connect(self.edit_project)
        self.delete_project_btn.clicked.connect(self.delete_project)
        
        project_buttons.addWidget(self.add_project_btn)
        project_buttons.addWidget(self.edit_project_btn)
        project_buttons.addWidget(self.delete_project_btn)
        project_buttons.addStretch()
        
        project_layout.addLayout(project_buttons)
        tabs.addTab(project_tab, "Projects")
        
        layout.addWidget(tabs)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)
    
    def load_data(self):
        """Load category data into tables."""
        if not self.db_path:
            return
        
        # Load relates_to options
        relates_options = get_relates_to_options(self.db_path)
        self.relates_table.setRowCount(len(relates_options))
        
        for row, option in enumerate(relates_options):
            self.relates_table.setItem(row, 0, QTableWidgetItem(option['id']))
            self.relates_table.setItem(row, 1, QTableWidgetItem(option['name']))
            self.relates_table.setItem(row, 2, QTableWidgetItem(option['description'] or ''))
        
        # Load project_id options
        project_options = get_project_id_options(self.db_path)
        self.project_table.setRowCount(len(project_options))
        
        for row, option in enumerate(project_options):
            self.project_table.setItem(row, 0, QTableWidgetItem(option['id']))
            self.project_table.setItem(row, 1, QTableWidgetItem(option['name']))
            self.project_table.setItem(row, 2, QTableWidgetItem(option['description'] or ''))
    
    def add_relates_category(self):
        """Add new relates_to category."""
        dialog = CategoryEditDialog(self, "Add Research Category")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            code, name, description = dialog.get_data()
            if add_relates_to_option(self.db_path, code, name, description):
                self.load_data()
                QMessageBox.information(self, "Success", "Category added successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to add category")
    
    def edit_relates_category(self):
        """Edit selected relates_to category."""
        current_row = self.relates_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a category to edit")
            return
        
        code = self.relates_table.item(current_row, 0).text()
        name = self.relates_table.item(current_row, 1).text()
        description = self.relates_table.item(current_row, 2).text()
        
        dialog = CategoryEditDialog(self, "Edit Research Category", code, name, description)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_code, new_name, new_description = dialog.get_data()
            if update_relates_to_option(self.db_path, new_code, new_name, new_description):
                self.load_data()
                QMessageBox.information(self, "Success", "Category updated successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to update category")
    
    def delete_relates_category(self):
        """Delete selected relates_to category."""
        current_row = self.relates_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a category to delete")
            return
        
        code = self.relates_table.item(current_row, 0).text()
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    f"Delete category '{code}'?\nThis is only possible if no papers use this category.")
        
        if reply == QMessageBox.StandardButton.Yes:
            if delete_relates_to_option(self.db_path, code):
                self.load_data()
                QMessageBox.information(self, "Success", "Category deleted successfully")
            else:
                QMessageBox.warning(self, "Error", "Cannot delete category - it may be used by existing papers")
    
    def add_project(self):
        """Add new project."""
        dialog = CategoryEditDialog(self, "Add Project")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            code, name, description = dialog.get_data()
            if add_project_id_option(self.db_path, code, name, description):
                self.load_data()
                QMessageBox.information(self, "Success", "Project added successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to add project")
    
    def edit_project(self):
        """Edit selected project."""
        current_row = self.project_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a project to edit")
            return
        
        code = self.project_table.item(current_row, 0).text()
        name = self.project_table.item(current_row, 1).text()
        description = self.project_table.item(current_row, 2).text()
        
        dialog = CategoryEditDialog(self, "Edit Project", code, name, description)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_code, new_name, new_description = dialog.get_data()
            if update_project_id_option(self.db_path, new_code, new_name, new_description):
                self.load_data()
                QMessageBox.information(self, "Success", "Project updated successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to update project")
    
    def delete_project(self):
        """Delete selected project."""
        current_row = self.project_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a project to delete")
            return
        
        code = self.project_table.item(current_row, 0).text()
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    f"Delete project '{code}'?\nThis is only possible if no papers use this project.")
        
        if reply == QMessageBox.StandardButton.Yes:
            if delete_project_id_option(self.db_path, code):
                self.load_data()
                QMessageBox.information(self, "Success", "Project deleted successfully")
            else:
                QMessageBox.warning(self, "Error", "Cannot delete project - it may be used by existing papers")


class CategoryEditDialog(QDialog):
    """Dialog for editing a single category or project."""
    
    def __init__(self, parent=None, title="Edit Category", code="", name="", description=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(400, 250)
        
        layout = QFormLayout(self)
        
        # Code field - read-only and auto-generated
        self.code_edit = QLineEdit(code)
        self.code_edit.setMaxLength(10)
        self.code_edit.setReadOnly(True)
        self.code_edit.setStyleSheet("QLineEdit { background-color: #f0f0f0; color: #666; }")
        layout.addRow("Code (auto-generated):", self.code_edit)
        
        self.name_edit = QLineEdit(name)
        # Always connect name changes to auto-generate code
        self.name_edit.textChanged.connect(self.auto_generate_code)
        layout.addRow("Name:", self.name_edit)
        
        # Generate initial code if this is a new entry and name is provided
        if name and not code:
            self.auto_generate_code()
        
        self.description_edit = QTextEdit(description)
        self.description_edit.setMaximumHeight(80)
        layout.addRow("Description:", self.description_edit)
        
        # Add explanation label
        explanation = QLabel("Code is automatically generated from first 2 + last 2 letters of name\n"
                           "Example: 'Cardiac bioprinting' → 'CANG'")
        explanation.setStyleSheet("color: gray; font-size: 10px;")
        explanation.setWordWrap(True)
        layout.addRow("", explanation)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def auto_generate_code(self):
        """Generate a 4-letter code from the name using first 2 + last 2 letters."""
        name = self.name_edit.text().strip()
        if not name:
            self.code_edit.setText("")
            return
        
        # Remove spaces and convert to uppercase
        clean_name = ''.join(name.split()).upper()
        
        # Remove non-alphabetic characters
        clean_name = ''.join(c for c in clean_name if c.isalpha())
        
        if len(clean_name) < 2:
            # If name is too short, pad with 'X'
            code = (clean_name + 'XXXX')[:4]
        elif len(clean_name) == 2:
            # If exactly 2 letters, repeat them
            code = clean_name + clean_name
        elif len(clean_name) == 3:
            # If 3 letters, use first 2 and last 1, then repeat last
            code = clean_name[:2] + clean_name[-1] + clean_name[-1]
        else:
            # Standard case: first 2 + last 2 letters
            code = clean_name[:2] + clean_name[-2:]
        
        self.code_edit.setText(code)
    
    def get_data(self):
        """Return the entered data."""
        return (
            self.code_edit.text().strip().upper(),
            self.name_edit.text().strip(),
            self.description_edit.toPlainText().strip()
        )


class ZoteroExportDialog(QDialog):
    """Dialog for exporting papers to Zotero format."""
    
    def __init__(self, parent=None, records=None, pdf_root=None):
        super().__init__(parent)
        self.records = records or []
        self.pdf_root = pdf_root
        
        self.setWindowTitle("Export to Zotero")
        self.setModal(True)
        self.resize(600, 400)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header info
        info_label = QLabel(f"Exporting {len(self.records)} papers to Zotero format")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(info_label)
        
        # Options
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)
        
        self.include_pdfs_cb = QCheckBox("Include PDF files (copies PDFs to export folder)")
        self.include_pdfs_cb.setChecked(True)
        options_layout.addWidget(self.include_pdfs_cb)
        
        self.create_bibtex_cb = QCheckBox("Create BibTeX file (.bib)")
        self.create_bibtex_cb.setChecked(True)
        options_layout.addWidget(self.create_bibtex_cb)
        
        self.create_csv_cb = QCheckBox("Create CSV metadata file")
        self.create_csv_cb.setChecked(True)
        options_layout.addWidget(self.create_csv_cb)
        
        layout.addWidget(options_group)
        
        # Export location
        location_group = QGroupBox("Export Location")
        location_layout = QFormLayout(location_group)
        
        self.export_path_edit = QLineEdit()
        export_browse_btn = QPushButton("Browse...")
        export_browse_btn.clicked.connect(self.browse_export_path)
        
        export_layout = QHBoxLayout()
        export_layout.addWidget(self.export_path_edit)
        export_layout.addWidget(export_browse_btn)
        
        location_layout.addRow("Export to folder:", export_layout)
        layout.addWidget(location_group)
        
        # Preview
        preview_group = QGroupBox("Papers to Export")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_list = QListWidget()
        self.preview_list.setMaximumHeight(150)
        for record in self.records:
            title = record.get('title', 'Untitled')
            year = record.get('year', '')
            year_str = f" ({year})" if year else ""
            self.preview_list.addItem(f"{title}{year_str}")
        
        preview_layout.addWidget(self.preview_list)
        layout.addWidget(preview_group)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_box = QDialogButtonBox()
        self.export_btn = QPushButton("Export")
        self.cancel_btn = QPushButton("Cancel")
        
        self.export_btn.clicked.connect(self.start_export)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_box.addButton(self.export_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(self.cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)
        
        layout.addWidget(button_box)
    
    def browse_export_path(self):
        """Browse for export directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Export Directory",
            os.path.expanduser("~/Desktop/Zotero_Export")
        )
        if dir_path:
            self.export_path_edit.setText(dir_path)
    
    def start_export(self):
        """Start the export process."""
        export_path = self.export_path_edit.text().strip()
        if not export_path:
            QMessageBox.warning(self, "No Path", "Please select an export directory.")
            return
        
        # Create export directory if it doesn't exist
        try:
            os.makedirs(export_path, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Failed to create export directory: {e}")
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.records))
        self.progress_bar.setValue(0)
        self.export_btn.setEnabled(False)
        
        try:
            self.perform_export(export_path)
            QMessageBox.information(self, "Export Complete", 
                                  f"Successfully exported {len(self.records)} papers to:\n{export_path}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export papers: {e}")
        finally:
            self.export_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def perform_export(self, export_path):
        """Perform the actual export."""
        import shutil
        from datetime import datetime
        
        # Create subdirectories
        if self.include_pdfs_cb.isChecked():
            pdf_dir = os.path.join(export_path, "PDFs")
            os.makedirs(pdf_dir, exist_ok=True)
        
        # Prepare data for BibTeX and CSV
        bibtex_entries = []
        csv_data = []
        
        for i, record in enumerate(self.records):
            self.status_label.setText(f"Processing: {record.get('title', 'Untitled')[:50]}...")
            self.progress_bar.setValue(i)
            QApplication.processEvents()  # Keep UI responsive
            
            # Copy PDF if requested and available
            if self.include_pdfs_cb.isChecked() and self.pdf_root:
                unique_name = record.get('unique_name', '')
                if unique_name:
                    pdf_filename = f"{unique_name}.pdf"
                    source_pdf = os.path.join(self.pdf_root, pdf_filename)
                    if os.path.exists(source_pdf):
                        dest_pdf = os.path.join(pdf_dir, pdf_filename)
                        shutil.copy2(source_pdf, dest_pdf)
            
            # Prepare BibTeX entry
            if self.create_bibtex_cb.isChecked():
                bibtex_entry = self.create_bibtex_entry(record)
                bibtex_entries.append(bibtex_entry)
            
            # Prepare CSV data
            if self.create_csv_cb.isChecked():
                csv_data.append(record)
        
        # Write BibTeX file
        if self.create_bibtex_cb.isChecked() and bibtex_entries:
            bibtex_path = os.path.join(export_path, "papers.bib")
            with open(bibtex_path, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(bibtex_entries))
        
        # Write CSV file
        if self.create_csv_cb.isChecked() and csv_data:
            import csv
            csv_path = os.path.join(export_path, "papers_metadata.csv")
            if csv_data:
                fieldnames = csv_data[0].keys()
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)
        
        # Create README
        readme_path = os.path.join(export_path, "README.txt")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"Papers Database Export\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Number of papers: {len(self.records)}\n\n")
            f.write("Files included:\n")
            if self.create_bibtex_cb.isChecked():
                f.write("- papers.bib: BibTeX format for import into Zotero or other reference managers\n")
            if self.create_csv_cb.isChecked():
                f.write("- papers_metadata.csv: Complete metadata in CSV format\n")
            if self.include_pdfs_cb.isChecked():
                f.write("- PDFs/: Folder containing PDF files of the papers\n")
            f.write("\nTo import into Zotero:\n")
            f.write("1. Open Zotero\n")
            f.write("2. Go to File > Import\n")
            f.write("3. Select the papers.bib file\n")
            f.write("4. Manually attach PDFs from the PDFs folder to each reference\n")
        
        self.progress_bar.setValue(len(self.records))
        self.status_label.setText("Export complete!")
    
    def create_bibtex_entry(self, record):
        """Create a BibTeX entry for a record."""
        # Generate a BibTeX key
        title = record.get('title', 'untitled')
        year = record.get('year', '')
        author_field = record.get('relates_to', '')  # This might be the author info
        
        # Clean title for key
        title_clean = ''.join(c for c in title if c.isalnum())[:20]
        key = f"{author_field}{year}{title_clean}".replace(' ', '')
        
        # Build BibTeX entry
        entry_type = "article"  # Default to article
        record_type = record.get('type', '').lower()
        if 'book' in record_type:
            entry_type = "book"
        elif 'conference' in record_type or 'proceeding' in record_type:
            entry_type = "inproceedings"
        
        lines = [f"@{entry_type}{{{key},"]
        
        # Required/common fields
        if record.get('title'):
            lines.append(f'  title = {{{record["title"]}}},')
        
        if record.get('relates_to'):  # Using as author field
            lines.append(f'  author = {{{record["relates_to"]}}},')
        
        if record.get('year'):
            lines.append(f'  year = {{{record["year"]}}},')
        
        if record.get('published_in'):
            lines.append(f'  journal = {{{record["published_in"]}}},')
        
        if record.get('doi'):
            lines.append(f'  doi = {{{record["doi"]}}},')
        
        if record.get('abstract'):
            # Clean abstract for BibTeX
            abstract_clean = record['abstract'].replace('\n', ' ').replace('\r', ' ')
            lines.append(f'  abstract = {{{abstract_clean}}},')
        
        if record.get('type'):
            lines.append(f'  note = {{Type: {record["type"]}}},')
        
        # Remove trailing comma from last line
        if lines[-1].endswith(','):
            lines[-1] = lines[-1][:-1]
        
        lines.append("}")
        
        return '\n'.join(lines)


class SettingsDialog(QDialog):
    """Dialog for application settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = get_settings()
        
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 300)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Paths group
        paths_group = QGroupBox("File Paths")
        paths_layout = QFormLayout(paths_group)
        
        # Database path
        db_layout = QHBoxLayout()
        self.db_path_edit = QLineEdit()
        db_browse_btn = QPushButton("Browse...")
        db_browse_btn.clicked.connect(self.browse_db_path)
        db_layout.addWidget(self.db_path_edit)
        db_layout.addWidget(db_browse_btn)
        paths_layout.addRow("Database File:", db_layout)
        
        # PDF root path
        pdf_layout = QHBoxLayout()
        self.pdf_root_edit = QLineEdit()
        pdf_browse_btn = QPushButton("Browse...")
        pdf_browse_btn.clicked.connect(self.browse_pdf_root)
        pdf_layout.addWidget(self.pdf_root_edit)
        pdf_layout.addWidget(pdf_browse_btn)
        paths_layout.addRow("PDF Root Directory:", pdf_layout)
        
        layout.addWidget(paths_group)
        
        # Search settings
        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout(search_group)
        
        self.search_limit_spin = QSpinBox()
        self.search_limit_spin.setRange(100, 10000)
        self.search_limit_spin.setSingleStep(100)
        self.search_limit_spin.setToolTip("Maximum number of search results to display at once\n(Higher values may be slower but show more results)")
        
        # Add explanation label
        limit_layout = QVBoxLayout()
        limit_widget = QWidget()
        limit_widget.setLayout(limit_layout)
        limit_layout.addWidget(self.search_limit_spin)
        
        explanation_label = QLabel("Maximum number of records to display in search results.\nHigher values show more results but may be slower.")
        explanation_label.setStyleSheet("color: gray; font-size: 11px;")
        limit_layout.addWidget(explanation_label)
        
        search_layout.addRow("Search Result Limit:", limit_widget)
        
        layout.addWidget(search_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_settings(self):
        """Load current settings into form."""
        self.db_path_edit.setText(self.settings.db_path or '')
        self.pdf_root_edit.setText(self.settings.pdf_root or '')
        self.search_limit_spin.setValue(self.settings.search_limit)
    
    def browse_db_path(self):
        """Browse for database file."""
        # Try to open existing file first
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Existing Database File", 
            self.db_path_edit.text() or self.settings.get_default_db_path(),
            "SQLite Database (*.db *.sqlite *.sqlite3);;All Files (*)"
        )
        
        # If no existing file selected, offer to create new one
        if not file_path:
            reply = QMessageBox.question(
                self, "Create New Database?",
                "No existing database selected. Would you like to create a new database file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Create New Database File", 
                    self.settings.get_default_db_path(),
                    "SQLite Database (*.db *.sqlite *.sqlite3);;All Files (*)"
                )
        
        if file_path:
            self.db_path_edit.setText(file_path)
    
    def browse_pdf_root(self):
        """Browse for PDF root directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select PDF Root Directory",
            self.pdf_root_edit.text() or self.settings.get_default_pdf_root()
        )
        if dir_path:
            self.pdf_root_edit.setText(dir_path)
    
    def save_and_accept(self):
        """Save settings and accept dialog."""
        try:
            # Validate paths
            db_path = self.db_path_edit.text().strip()
            pdf_root = self.pdf_root_edit.text().strip()
            
            if not db_path:
                QMessageBox.warning(self, "Invalid Settings", "Database path is required.")
                return
            
            # Save settings
            self.settings.db_path = db_path
            if pdf_root:
                self.settings.pdf_root = pdf_root
            self.settings.search_limit = self.search_limit_spin.value()
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.current_records = []
        self.columns = []
        
        self.setWindowTitle("Papers Desktop Database")
        self.resize(1200, 800)
        
        self.setup_ui()
        self.setup_actions()
        self.setup_toolbar()
        self.setup_statusbar()
        
        # Restore window state
        if self.settings.window_geometry:
            self.restoreGeometry(self.settings.window_geometry)
        if self.settings.window_state:
            self.restoreState(self.settings.window_state)
        
        # Initialize database if configured or auto-detect
        if self.settings.is_configured():
            self.load_database()
        else:
            # Check if test database exists in current directory
            test_db_path = os.path.join(os.getcwd(), "test_papers.db")
            test_pdf_path = os.path.join(os.path.dirname(os.getcwd()), "PDFs")
            
            if os.path.exists(test_db_path):
                # Auto-configure with test database
                self.settings.db_path = test_db_path
                if os.path.exists(test_pdf_path):
                    self.settings.pdf_root = test_pdf_path
                
                self.status_bar.showMessage("Auto-configured with test database")
                self.load_database()
            else:
                self.show_welcome()
    
    def setup_ui(self):
        """Setup main UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Search and filter section
        filter_group = QGroupBox("Search & Filter")
        filter_layout = QHBoxLayout(filter_group)
        
        # Search box
        filter_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter search terms...")
        self.search_edit.returnPressed.connect(self.search_records)
        filter_layout.addWidget(self.search_edit)
        
        # Year filter
        filter_layout.addWidget(QLabel("Year:"))
        self.year_edit = QLineEdit()
        self.year_edit.setPlaceholderText("2024")
        self.year_edit.setMaximumWidth(80)
        filter_layout.addWidget(self.year_edit)
        
        # Journal filter
        filter_layout.addWidget(QLabel("Journal:"))
        self.journal_edit = QLineEdit()
        self.journal_edit.setPlaceholderText("Contains...")
        filter_layout.addWidget(self.journal_edit)
        
        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_records)
        filter_layout.addWidget(self.search_btn)
        
        # Sort dropdown
        filter_layout.addWidget(QLabel("Sort:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "ID (Default)",
            "Date Added (Newest)",
            "Date Added (Oldest)", 
            "Title (A-Z)",
            "Title (Z-A)",
            "Year (Newest)",
            "Year (Oldest)"
        ])
        self.sort_combo.setMaximumWidth(150)
        self.sort_combo.currentTextChanged.connect(self.search_records)
        filter_layout.addWidget(self.sort_combo)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_btn)
        
        layout.addWidget(filter_group)
        
        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSortingEnabled(True)
        # Make table read-only - editing only through dialogs
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_record)
        # Handle clicks for read checkbox functionality
        self.table.cellClicked.connect(self.on_cell_clicked)
        
        layout.addWidget(self.table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Record")
        self.add_btn.clicked.connect(self.add_record)
        button_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("Edit Record")
        self.edit_btn.clicked.connect(self.edit_record)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete Record")
        self.delete_btn.clicked.connect(self.delete_record)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        self.open_pdf_btn = QPushButton("Open PDF")
        self.open_pdf_btn.clicked.connect(self.open_pdf)
        self.open_pdf_btn.setEnabled(False)
        button_layout.addWidget(self.open_pdf_btn)
        
        layout.addLayout(button_layout)
        
        # Connect table selection and item changes
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)

    
    def setup_actions(self):
        """Setup menu actions."""
        # File menu
        self.import_action = QAction("Import Excel...", self)
        self.import_action.setShortcut(QKeySequence.StandardKey.Open)
        self.import_action.triggered.connect(self.import_excel)
        
        self.export_action = QAction("Export CSV...", self)
        self.export_action.setShortcut(QKeySequence("Ctrl+E"))
        self.export_action.triggered.connect(self.export_csv)
        
        self.export_zotero_action = QAction("Export to Zotero...", self)
        self.export_zotero_action.setShortcut(QKeySequence("Ctrl+Z"))
        self.export_zotero_action.triggered.connect(self.export_zotero_dialog)
        
        self.settings_action = QAction("Settings...", self)
        self.settings_action.setShortcut(QKeySequence.StandardKey.Preferences)
        self.settings_action.triggered.connect(self.show_settings)
        
        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)
        
        # View menu
        self.refresh_action = QAction("Refresh", self)
        self.refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        self.refresh_action.triggered.connect(self.load_records)
        
        # Tools menu
        self.validate_action = QAction("Validate Database", self)
        self.validate_action.triggered.connect(self.validate_database)
        
        self.stats_action = QAction("Database Statistics", self)
        self.stats_action.triggered.connect(self.show_statistics)
        
        self.manage_categories_action = QAction("Manage Categories...", self)
        self.manage_categories_action.triggered.connect(self.manage_categories)
    
    def setup_toolbar(self):
        """Setup toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        toolbar.addAction(self.import_action)
        toolbar.addAction(self.export_action)
        toolbar.addAction(self.export_zotero_action)
        toolbar.addSeparator()
        toolbar.addAction(self.settings_action)
        toolbar.addSeparator()
        toolbar.addAction(self.refresh_action)
        
        # Add menu bar
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.import_action)
        file_menu.addAction(self.export_action)
        file_menu.addAction(self.export_zotero_action)
        file_menu.addSeparator()
        file_menu.addAction(self.settings_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        view_menu = menubar.addMenu("View")
        view_menu.addAction(self.refresh_action)
        
        tools_menu = menubar.addMenu("Tools")
        tools_menu.addAction(self.manage_categories_action)
        tools_menu.addSeparator()
        tools_menu.addAction(self.validate_action)
        tools_menu.addAction(self.stats_action)
    
    def setup_statusbar(self):
        """Setup status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def show_welcome(self):
        """Show welcome message for first-time users."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Welcome to Papers Database")
        msg.setText("Welcome! To get started, please configure your database and PDF paths.")
        msg.setInformativeText("Click 'Settings' to configure paths, then 'Import Excel' to load your data.")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        
        self.show_settings()
    
    def load_database(self):
        """Load database and initialize table."""
        try:
            db_path = self.settings.db_path
            if not db_path or not os.path.exists(db_path):
                self.status_bar.showMessage("Database not found")
                return
            
            # Initialize lookup tables
            init_lookup_tables(db_path)
            
            # Get columns
            self.columns = list_columns(db_path)
            self.setup_table_columns()
            self.load_records()
            
            self.status_bar.showMessage(f"Loaded database: {os.path.basename(db_path)}")
            
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load database: {e}")
            self.status_bar.showMessage("Database error")
    
    def setup_table_columns(self):
        """Setup table columns based on database schema."""
        if not self.columns:
            return
        
        # Filter out unnecessary columns for display
        hidden_columns = [
            'id', 'unique_name', 'pdf', 'created_at', 'updated_at', 'added_date',
            'url', 'entry_number', 'journal', 'authors', 'keywords', 'tags', 'notes', 'status'
        ]
        display_columns = [col for col in self.columns if col not in hidden_columns]
        
        # Store all columns for internal use but only display the filtered ones
        self.display_columns = display_columns
        
        self.table.setColumnCount(len(display_columns))
        self.table.setHorizontalHeaderLabels([col.replace('_', ' ').title() for col in display_columns])
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Set specific resize modes for different columns
        for i, col in enumerate(display_columns):
            if col == 'title':
                # Title column stretches to fill available space
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            elif col == 'abstract':
                # Abstract column has a fixed reasonable width
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.table.setColumnWidth(i, 300)
            elif col in ['year', 'read']:
                # Small columns for year and read
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.table.setColumnWidth(i, 80)
            elif col in ['relates_to', 'project_id']:
                # Medium width for category columns
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.table.setColumnWidth(i, 120)
        
        # Enable word wrap for all cells
        self.table.setWordWrap(True)
        
        # Set row height to accommodate wrapped text
        self.table.verticalHeader().setDefaultSectionSize(60)
        
        # Restore saved column widths where applicable
        saved_widths = self.settings.table_column_widths
        for i, col in enumerate(display_columns):
            if col in saved_widths and col not in ['title', 'abstract', 'year', 'read', 'relates_to', 'project_id']:
                self.table.setColumnWidth(i, saved_widths[col])
    
    def load_records(self):
        """Load records from database into table."""
        try:
            db_path = self.settings.db_path
            if not db_path:
                return
            
            # Get search and filter parameters
            search = self.search_edit.text().strip() or None
            filters = {}
            
            if self.year_edit.text().strip():
                try:
                    filters['year'] = int(self.year_edit.text().strip())
                except ValueError:
                    pass
            
            if self.journal_edit.text().strip():
                filters['journal'] = self.journal_edit.text().strip()
            
            # Load records
            self.current_records = read_all(db_path, search, filters, self.settings.search_limit)
            
            # Apply sorting
            self.apply_sorting()
            
            self.populate_table()
            
            count = len(self.current_records)
            self.status_bar.showMessage(f"Showing {count} records")
            
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load records: {e}")
            self.status_bar.showMessage("Error loading records")
    
    def apply_sorting(self):
        """Apply sorting to current records based on sort dropdown selection."""
        if not hasattr(self, 'sort_combo') or not self.current_records:
            return
        
        sort_option = self.sort_combo.currentText()
        
        if sort_option == "ID (Default)":
            # Sort by ID (ascending)
            self.current_records.sort(key=lambda x: x.get('id', 0))
        elif sort_option == "Date Added (Newest)":
            # Sort by created_at (descending - newest first)
            self.current_records.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_option == "Date Added (Oldest)":
            # Sort by created_at (ascending - oldest first)
            self.current_records.sort(key=lambda x: x.get('created_at', ''))
        elif sort_option == "Title (A-Z)":
            # Sort by title (ascending)
            self.current_records.sort(key=lambda x: (x.get('title', '') or '').lower())
        elif sort_option == "Title (Z-A)":
            # Sort by title (descending)
            self.current_records.sort(key=lambda x: (x.get('title', '') or '').lower(), reverse=True)
        elif sort_option == "Year (Newest)":
            # Sort by year (descending - newest first)
            self.current_records.sort(key=lambda x: x.get('year', 0) or 0, reverse=True)
        elif sort_option == "Year (Oldest)":
            # Sort by year (ascending - oldest first)
            self.current_records.sort(key=lambda x: x.get('year', 0) or 0)
    
    def populate_table(self):
        """Populate table with current records."""
        if not self.current_records:
            self.table.setRowCount(0)
            return
        
        # Use the display columns we defined in setup_table_columns
        display_columns = getattr(self, 'display_columns', self.columns)
        
        self.table.setRowCount(len(self.current_records))
        
        for row, record in enumerate(self.current_records):
            for col, column_name in enumerate(display_columns):
                value = record.get(column_name, '')
                if value is None:
                    value = ''
                
                # Handle read column as checkbox (display only)
                if column_name == 'read':
                    item = QTableWidgetItem()
                    is_read = value and str(value).lower() in ['yes', 'true', '1', 'checked']
                    # Use checkmark symbols for display only
                    item.setText("☑" if is_read else "☐")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setData(Qt.ItemDataRole.UserRole, record['id'])  # Store record ID
                    # Store the read status for toggling
                    item.setData(Qt.ItemDataRole.UserRole + 1, is_read)
                else:
                    item = QTableWidgetItem(str(value))
                    item.setData(Qt.ItemDataRole.UserRole, record['id'])  # Store record ID
                
                self.table.setItem(row, col, item)
    
    def on_cell_clicked(self, row, col):
        """Handle cell clicks - specifically for read checkbox toggling."""
        display_columns = getattr(self, 'display_columns', [])
        
        if col < len(display_columns) and display_columns[col] == 'read':
            item = self.table.item(row, col)
            if item:
                record_id = item.data(Qt.ItemDataRole.UserRole)
                current_read_status = item.data(Qt.ItemDataRole.UserRole + 1)
                
                if record_id:
                    try:
                        # Toggle read status
                        new_status = not current_read_status
                        new_value = 'Yes' if new_status else 'No'
                        
                        # Update database
                        update_record(self.settings.db_path, record_id, {'read': new_value})
                        
                        # Update display
                        item.setText("☑" if new_status else "☐")
                        item.setData(Qt.ItemDataRole.UserRole + 1, new_status)
                        
                        self.status_bar.showMessage(f"Updated read status")
                        
                    except DatabaseError as e:
                        QMessageBox.critical(self, "Database Error", f"Failed to update read status: {e}")
    
    def search_records(self):
        """Perform search with current filters."""
        self.load_records()
    
    def clear_filters(self):
        """Clear all search filters."""
        self.search_edit.clear()
        self.year_edit.clear()
        self.journal_edit.clear()
        if hasattr(self, 'sort_combo'):
            self.sort_combo.setCurrentIndex(0)  # Reset to "ID (Default)"
        self.load_records()
    
    def on_selection_changed(self):
        """Handle table selection changes."""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        has_selection = len(selected_rows) > 0
        has_single_selection = len(selected_rows) == 1
        
        # Edit and Open PDF only work with single selection
        self.edit_btn.setEnabled(has_single_selection)
        self.open_pdf_btn.setEnabled(has_single_selection)
        
        # Delete can work with multiple selection
        self.delete_btn.setEnabled(has_selection)
        
        # Update status bar with selection info
        if len(selected_rows) == 0:
            self.status_bar.showMessage(f"Showing {len(self.current_records)} records")
        elif len(selected_rows) == 1:
            self.status_bar.showMessage(f"1 record selected")
        else:
            self.status_bar.showMessage(f"{len(selected_rows)} records selected")
    
    def get_selected_record_id(self) -> Optional[int]:
        """Get ID of currently selected record."""
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        
        item = self.table.item(current_row, 0)
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def add_record(self):
        """Show dialog to add new record."""
        if not self.settings.db_path:
            QMessageBox.warning(self, "No Database", "Please configure database path in settings.")
            return
        
        dialog = RecordDialog(self, db_path=self.settings.db_path)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                
                # Handle PDF upload if provided
                pdf_upload_path = data.pop('pdf_upload', None)
                
                # Create the record first to get an ID
                record_id = create_record(self.settings.db_path, data)
                
                # If PDF was uploaded, handle it
                if pdf_upload_path and os.path.exists(pdf_upload_path):
                    self.handle_pdf_upload(record_id, pdf_upload_path, data)
                
                self.load_records()
                self.status_bar.showMessage("Record added successfully")
                
            except DatabaseError as e:
                QMessageBox.critical(self, "Database Error", f"Failed to add record: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to process PDF: {e}")
    
    def handle_pdf_upload(self, record_id: int, pdf_path: str, record_data: Dict[str, Any]):
        """Handle PDF upload for a new record."""
        import shutil
        from .unique import unique_name_from_row, NamingScheme
        
        try:
            # Get the record from database to have the complete data
            record = get_record(self.settings.db_path, record_id)
            if not record:
                raise Exception("Failed to retrieve created record")
            
            # Generate unique name using the record data
            unique_name = unique_name_from_row(record, record_number=record_id, scheme=NamingScheme.HIERARCHICAL)
            
            # Ensure PDF root directory exists
            pdf_root = self.settings.pdf_root or os.path.join(os.path.dirname(self.settings.db_path), "PDFs")
            os.makedirs(pdf_root, exist_ok=True)
            
            # Create new PDF filename
            new_pdf_filename = f"{unique_name}.pdf"
            new_pdf_path = os.path.join(pdf_root, new_pdf_filename)
            
            # Copy PDF to the PDFs folder with new name
            shutil.copy2(pdf_path, new_pdf_path)
            
            # Update the record with the unique_name and pdf path
            update_data = {
                'unique_name': unique_name,
                'pdf': new_pdf_filename
            }
            update_record(self.settings.db_path, record_id, update_data)
            
            self.status_bar.showMessage(f"PDF saved as {new_pdf_filename}")
            
        except Exception as e:
            # If PDF handling fails, still keep the record but show error
            QMessageBox.warning(self, "PDF Upload Warning", 
                              f"Record created successfully, but PDF upload failed: {e}")
    
    def edit_record(self):
        """Show dialog to edit selected record."""
        record_id = self.get_selected_record_id()
        if not record_id:
            return
        
        try:
            record = get_record(self.settings.db_path, record_id)
            if not record:
                QMessageBox.warning(self, "Record Not Found", "Selected record no longer exists.")
                self.load_records()
                return
            
            dialog = RecordDialog(self, record, db_path=self.settings.db_path)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                update_record(self.settings.db_path, record_id, data)
                self.load_records()
                self.status_bar.showMessage("Record updated successfully")
                
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", f"Failed to edit record: {e}")
    
    def delete_record(self):
        """Delete selected record(s)."""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            return
        
        # Get selected record IDs
        record_ids = []
        for row in selected_rows:
            if row < len(self.current_records):
                record_ids.append(self.current_records[row]['id'])
        
        if not record_ids:
            return
        
        # Confirm deletion
        if len(record_ids) == 1:
            message = "Are you sure you want to delete this record?"
        else:
            message = f"Are you sure you want to delete {len(record_ids)} records?"
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                deleted_count = 0
                pdf_deletion_errors = []
                
                for record_id in record_ids:
                    # Get record info before deleting to find associated PDF
                    record = get_record(self.settings.db_path, record_id)
                    
                    # Delete associated PDF file if it exists
                    if record and record.get('pdf'):
                        pdf_root = self.settings.pdf_root or os.path.join(os.path.dirname(self.settings.db_path), "PDFs")
                        pdf_path = os.path.join(pdf_root, record['pdf'])
                        
                        if os.path.exists(pdf_path):
                            try:
                                os.remove(pdf_path)
                            except OSError as e:
                                pdf_deletion_errors.append(f"Could not delete PDF {record['pdf']}: {e}")
                    
                    # Delete the database record
                    delete_record(self.settings.db_path, record_id)
                    deleted_count += 1
                
                self.load_records()
                
                # Show status message
                if deleted_count == 1:
                    message = "Record deleted successfully"
                else:
                    message = f"{deleted_count} records deleted successfully"
                
                if pdf_deletion_errors:
                    message += f" (PDF deletion warnings: {'; '.join(pdf_deletion_errors)})"
                
                self.status_bar.showMessage(message)
                
                # Show PDF deletion warnings if any
                if pdf_deletion_errors:
                    QMessageBox.warning(self, "PDF Deletion Warning", 
                                      f"Records deleted successfully, but some PDFs could not be deleted:\n\n" + 
                                      "\n".join(pdf_deletion_errors))
                
            except DatabaseError as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete record(s): {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred during deletion: {e}")
    
    def open_pdf(self):
        """Open PDF file for selected record."""
        record_id = self.get_selected_record_id()
        if not record_id:
            return
        
        try:
            record = get_record(self.settings.db_path, record_id)
            if not record:
                return
            
            pdf_path = record.get('pdf', '').strip()
            if not pdf_path:
                QMessageBox.information(self, "No PDF", "No PDF file specified for this record.")
                return
            
            # Handle relative paths
            if not os.path.isabs(pdf_path):
                pdf_root = self.settings.pdf_root
                if pdf_root:
                    pdf_path = os.path.join(pdf_root, pdf_path)
            
            if not os.path.exists(pdf_path):
                QMessageBox.warning(self, "File Not Found", f"PDF file not found: {pdf_path}")
                return
            
            # Open file with system default application
            if platform.system() == "Windows":
                os.startfile(pdf_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", pdf_path])
            else:  # Linux and others
                subprocess.run(["xdg-open", pdf_path])
            
            self.status_bar.showMessage(f"Opened PDF: {os.path.basename(pdf_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open PDF: {e}")
    
    def import_excel(self):
        """Import data from Excel file."""
        if not self.settings.db_path:
            QMessageBox.warning(self, "No Database", "Please configure database path in settings first.")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Excel File",
            self.settings.last_import_dir or "",
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Save directory for next time
        self.settings.last_import_dir = os.path.dirname(file_path)
        
        # Confirm if database exists
        if os.path.exists(self.settings.db_path):
            reply = QMessageBox.question(
                self, "Database Exists",
                "Database file already exists. Import will replace all existing data. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Show progress dialog
        progress = QProgressDialog("Importing Excel data...", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        # Start import worker
        self.import_worker = ImportWorker(file_path, self.settings.db_path)
        self.import_worker.progress.connect(progress.setLabelText)
        self.import_worker.finished.connect(self.on_import_finished)
        self.import_worker.start()
        
        # Handle cancel
        progress.canceled.connect(self.import_worker.terminate)
    
    def on_import_finished(self, success: bool, message: str):
        """Handle import completion."""
        if success:
            QMessageBox.information(self, "Import Complete", message)
            self.load_database()
        else:
            QMessageBox.critical(self, "Import Failed", message)
        
        self.status_bar.showMessage("Import finished")
    
    def export_csv(self):
        """Export records to CSV file."""
        if not self.settings.db_path or not os.path.exists(self.settings.db_path):
            QMessageBox.warning(self, "No Database", "No database loaded.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV File",
            self.settings.last_export_dir or "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Save directory for next time
        self.settings.last_export_dir = os.path.dirname(file_path)
        
        try:
            export_csv(self.settings.db_path, file_path)
            QMessageBox.information(self, "Export Complete", f"Data exported to: {file_path}")
            self.status_bar.showMessage(f"Exported to {os.path.basename(file_path)}")
        except DatabaseError as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export data: {e}")
    
    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload database if path changed
            self.load_database()
    
    def validate_database(self):
        """Validate database integrity."""
        if not self.settings.db_path or not os.path.exists(self.settings.db_path):
            QMessageBox.warning(self, "No Database", "No database loaded.")
            return
        
        try:
            issues = validate_database(self.settings.db_path)
            if issues:
                message = "Database validation found issues:\n\n" + "\n".join(f"• {issue}" for issue in issues)
                QMessageBox.warning(self, "Validation Issues", message)
            else:
                QMessageBox.information(self, "Validation Complete", "Database validation passed - no issues found.")
        except DatabaseError as e:
            QMessageBox.critical(self, "Validation Error", f"Failed to validate database: {e}")
    
    def show_statistics(self):
        """Show database statistics."""
        if not self.settings.db_path or not os.path.exists(self.settings.db_path):
            QMessageBox.warning(self, "No Database", "No database loaded.")
            return
        
        try:
            stats = get_stats(self.settings.db_path)
            
            message = f"""Database Statistics:

Total Records: {stats['total_records']:,}
Recent Additions (last 7 days): {stats['recent_additions']:,}
Full-Text Search: {'Enabled' if stats['has_fts'] else 'Disabled'}

Records by Year:"""
            
            for year, count in list(stats['by_year'].items())[:10]:
                message += f"\n  {year}: {count:,}"
            
            QMessageBox.information(self, "Database Statistics", message)
            
        except DatabaseError as e:
            QMessageBox.critical(self, "Statistics Error", f"Failed to get statistics: {e}")
    
    def manage_categories(self):
        """Show categories management dialog."""
        if not self.settings.db_path or not os.path.exists(self.settings.db_path):
            QMessageBox.warning(self, "No Database", "No database loaded.")
            return
        
        dialog = CategoriesDialog(self, db_path=self.settings.db_path)
        dialog.exec()
    
    def export_zotero_dialog(self):
        """Show Zotero export dialog."""
        if not self.settings.db_path or not os.path.exists(self.settings.db_path):
            QMessageBox.warning(self, "No Database", "No database loaded.")
            return
        
        # Check if any records are selected
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            reply = QMessageBox.question(
                self, "Export All Papers", 
                "No papers are selected. Export all papers in the current view to Zotero?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            # Export all current records
            records_to_export = self.current_records
        else:
            # Export only selected records
            records_to_export = [self.current_records[row] for row in sorted(selected_rows)]
        
        if not records_to_export:
            QMessageBox.information(self, "No Papers", "No papers to export.")
            return
        
        # Show export dialog
        dialog = ZoteroExportDialog(self, records_to_export, self.settings.pdf_root)
        dialog.exec()
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save window state
        self.settings.window_geometry = self.saveGeometry()
        self.settings.window_state = self.saveState()
        
        # Save column widths
        if self.columns:
            display_columns = [col for col in self.columns if col not in ['created_at', 'updated_at']]
            for i, col in enumerate(display_columns):
                width = self.table.columnWidth(i)
                self.settings.set_table_column_width(col, width)
        
        event.accept()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    app.setApplicationName("Papers Desktop Database")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("PapersDB")
    
    # Set application icon (if available)
    # app.setWindowIcon(QIcon("icon.png"))
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

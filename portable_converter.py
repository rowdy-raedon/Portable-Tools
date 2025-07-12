#!/usr/bin/env python3
"""
Portable App Converter - Main Application
Converts regular applications into portable apps for space-efficient management
"""

import sys
import os
import json
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QFileDialog,
    QTextEdit, QTabWidget, QProgressBar, QMessageBox, QInputDialog,
    QGroupBox, QSplitter, QStatusBar, QMenuBar, QAction, QComboBox,
    QCheckBox, QSpinBox, QFormLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor

import psutil
import py7zr


class PortableApp:
    """Represents a portable application"""
    
    def __init__(self, name: str, original_path: str, portable_path: str, 
                 size: int = 0, created_date: str = "", version: str = ""):
        self.name = name
        self.original_path = original_path
        self.portable_path = portable_path
        self.size = size
        self.created_date = created_date or datetime.now().isoformat()
        self.version = version
        self.last_run = ""
        
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'original_path': self.original_path,
            'portable_path': self.portable_path,
            'size': self.size,
            'created_date': self.created_date,
            'version': self.version,
            'last_run': self.last_run
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PortableApp':
        app = cls(
            data['name'], data['original_path'], data['portable_path'],
            data.get('size', 0), data.get('created_date', ''),
            data.get('version', '')
        )
        app.last_run = data.get('last_run', '')
        return app


class ConversionWorker(QThread):
    """Worker thread for app conversion to avoid UI freezing"""
    
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, app_path: str, output_dir: str, compression_level: int = 5):
        super().__init__()
        self.app_path = app_path
        self.output_dir = output_dir
        self.compression_level = compression_level
        self.cancelled = False
    
    def cancel(self):
        self.cancelled = True
    
    def run(self):
        try:
            self.status.emit("Analyzing application...")
            self.progress.emit(10)
            
            if self.cancelled:
                return
                
            app_name = Path(self.app_path).stem
            portable_dir = Path(self.output_dir) / f"{app_name}_Portable"
            portable_dir.mkdir(exist_ok=True)
            
            self.status.emit("Scanning dependencies...")
            self.progress.emit(25)
            
            dependencies = self._scan_dependencies()
            if self.cancelled:
                return
                
            self.status.emit("Copying application files...")
            self.progress.emit(40)
            
            self._copy_application_files(portable_dir)
            if self.cancelled:
                return
                
            self.status.emit("Copying dependencies...")
            self.progress.emit(60)
            
            self._copy_dependencies(dependencies, portable_dir)
            if self.cancelled:
                return
                
            self.status.emit("Creating launcher script...")
            self.progress.emit(80)
            
            self._create_launcher(portable_dir, app_name)
            if self.cancelled:
                return
                
            self.status.emit("Compressing portable app...")
            self.progress.emit(90)
            
            archive_path = self._compress_portable_app(portable_dir)
            if self.cancelled:
                return
                
            self.progress.emit(100)
            self.status.emit("Conversion completed successfully!")
            self.finished.emit(True, str(archive_path))
            
        except Exception as e:
            self.finished.emit(False, str(e))
    
    def _scan_dependencies(self) -> List[str]:
        """Scan for application dependencies"""
        dependencies = []
        try:
            # Use basic file scanning for dependencies
            app_dir = Path(self.app_path).parent
            for file in app_dir.rglob("*.dll"):
                if file.is_file():
                    dependencies.append(str(file))
        except Exception:
            pass
        return dependencies
    
    def _copy_application_files(self, portable_dir: Path):
        """Copy main application files"""
        app_path = Path(self.app_path)
        dest_path = portable_dir / app_path.name
        shutil.copy2(self.app_path, dest_path)
        
        # Copy any config files in the same directory
        for file in app_path.parent.glob("*.ini"):
            shutil.copy2(file, portable_dir / file.name)
        for file in app_path.parent.glob("*.cfg"):
            shutil.copy2(file, portable_dir / file.name)
    
    def _copy_dependencies(self, dependencies: List[str], portable_dir: Path):
        """Copy application dependencies"""
        lib_dir = portable_dir / "lib"
        lib_dir.mkdir(exist_ok=True)
        
        for dep in dependencies[:20]:  # Limit to avoid too many files
            if self.cancelled:
                break
            try:
                dep_path = Path(dep)
                shutil.copy2(dep, lib_dir / dep_path.name)
            except Exception:
                continue
    
    def _create_launcher(self, portable_dir: Path, app_name: str):
        """Create a launcher script for the portable app"""
        launcher_content = f'''@echo off
cd /d "%~dp0"
start "" "{app_name}.exe"
'''
        launcher_path = portable_dir / f"{app_name}_Portable.bat"
        launcher_path.write_text(launcher_content)
    
    def _compress_portable_app(self, portable_dir: Path) -> Path:
        """Compress the portable app directory"""
        archive_path = portable_dir.with_suffix('.7z')
        
        with py7zr.SevenZipFile(archive_path, 'w', compression_level=self.compression_level) as archive:
            for file_path in portable_dir.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(portable_dir)
                    archive.write(file_path, relative_path)
        
        # Clean up the directory after compression
        shutil.rmtree(portable_dir)
        return archive_path


class PortableAppConverter(QMainWindow):
    """Main application window for the Portable App Converter"""
    
    def __init__(self):
        super().__init__()
        self.portable_apps: List[PortableApp] = []
        self.settings = QSettings('PortableConverter', 'Settings')
        self.worker = None
        
        self.init_ui()
        self.load_portable_apps()
        self.apply_dark_theme()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Portable App Converter v1.0")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Conversion
        self.create_conversion_panel(splitter)
        
        # Right panel - Management
        self.create_management_panel(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        refresh_action = QAction('Refresh Apps', self)
        refresh_action.triggered.connect(self.refresh_apps)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        
        preferences_action = QAction('Preferences', self)
        preferences_action.triggered.connect(self.show_preferences)
        settings_menu.addAction(preferences_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_conversion_panel(self, parent):
        """Create the conversion panel"""
        conversion_widget = QWidget()
        parent.addWidget(conversion_widget)
        layout = QVBoxLayout(conversion_widget)
        
        # Title
        title = QLabel("Convert Application")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # App selection
        selection_group = QGroupBox("Select Application")
        selection_layout = QVBoxLayout(selection_group)
        
        self.app_path_label = QLabel("No application selected")
        self.app_path_label.setWordWrap(True)
        selection_layout.addWidget(self.app_path_label)
        
        select_btn = QPushButton("Browse for Application")
        select_btn.clicked.connect(self.select_application)
        selection_layout.addWidget(select_btn)
        
        layout.addWidget(selection_group)
        
        # Conversion options
        options_group = QGroupBox("Conversion Options")
        options_layout = QFormLayout(options_group)
        
        self.compression_combo = QComboBox()
        self.compression_combo.addItems(["Ultra (Slowest)", "High", "Normal", "Fast", "Fastest"])
        self.compression_combo.setCurrentIndex(2)  # Normal
        options_layout.addRow("Compression:", self.compression_combo)
        
        self.include_deps_check = QCheckBox("Include Dependencies")
        self.include_deps_check.setChecked(True)
        options_layout.addRow("", self.include_deps_check)
        
        layout.addWidget(options_group)
        
        # Convert button
        self.convert_btn = QPushButton("Convert to Portable")
        self.convert_btn.setEnabled(False)
        self.convert_btn.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_btn)
        
        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to convert")
        progress_layout.addWidget(self.status_label)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_conversion)
        progress_layout.addWidget(self.cancel_btn)
        
        layout.addWidget(progress_group)
        
        layout.addStretch()
    
    def create_management_panel(self, parent):
        """Create the management panel"""
        management_widget = QWidget()
        parent.addWidget(management_widget)
        layout = QVBoxLayout(management_widget)
        
        # Title
        title = QLabel("Portable Apps Manager")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Apps list
        self.apps_list = QListWidget()
        self.apps_list.itemDoubleClicked.connect(self.launch_app)
        layout.addWidget(self.apps_list)
        
        # Management buttons
        btn_layout = QHBoxLayout()
        
        launch_btn = QPushButton("Launch")
        launch_btn.clicked.connect(self.launch_selected_app)
        btn_layout.addWidget(launch_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_selected_app)
        btn_layout.addWidget(delete_btn)
        
        info_btn = QPushButton("Info")
        info_btn.clicked.connect(self.show_app_info)
        btn_layout.addWidget(info_btn)
        
        layout.addLayout(btn_layout)
        
        # Info panel
        info_group = QGroupBox("Application Information")
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(150)
        info_layout.addWidget(self.info_text)
        
        layout.addWidget(info_group)
    
    def apply_dark_theme(self):
        """Apply dark theme to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #606060;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QPushButton:disabled {
                background-color: #2b2b2b;
                color: #808080;
            }
            QListWidget {
                background-color: #353535;
                border: 1px solid #606060;
            }
            QTextEdit {
                background-color: #353535;
                border: 1px solid #606060;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #606060;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QProgressBar {
                border: 1px solid #606060;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
    
    def select_application(self):
        """Open file dialog to select application"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Application", "",
            "Executable Files (*.exe);;All Files (*)"
        )
        
        if file_path:
            self.app_path_label.setText(file_path)
            self.convert_btn.setEnabled(True)
    
    def start_conversion(self):
        """Start the conversion process"""
        if not self.app_path_label.text() or self.app_path_label.text() == "No application selected":
            QMessageBox.warning(self, "Warning", "Please select an application first.")
            return
        
        output_dir = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", str(Path.home() / "Documents")
        )
        
        if not output_dir:
            return
        
        # Get compression level
        compression_levels = [9, 7, 5, 3, 1]
        compression_level = compression_levels[self.compression_combo.currentIndex()]
        
        # Start worker thread
        self.worker = ConversionWorker(
            self.app_path_label.text(), output_dir, compression_level
        )
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.status_label.setText)
        self.worker.finished.connect(self.conversion_finished)
        
        self.convert_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.worker.start()
    
    def cancel_conversion(self):
        """Cancel the conversion process"""
        if self.worker:
            self.worker.cancel()
            self.worker.wait()
        self.conversion_finished(False, "Cancelled by user")
    
    def conversion_finished(self, success: bool, message: str):
        """Handle conversion completion"""
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready to convert")
        
        if success:
            QMessageBox.information(self, "Success", f"Conversion completed!\nPortable app saved to: {message}")
            
            # Add to portable apps list
            app_name = Path(self.app_path_label.text()).stem
            portable_app = PortableApp(
                name=app_name,
                original_path=self.app_path_label.text(),
                portable_path=message,
                size=Path(message).stat().st_size if Path(message).exists() else 0
            )
            self.portable_apps.append(portable_app)
            self.save_portable_apps()
            self.refresh_apps_list()
        else:
            QMessageBox.critical(self, "Error", f"Conversion failed: {message}")
    
    def refresh_apps_list(self):
        """Refresh the portable apps list"""
        self.apps_list.clear()
        for app in self.portable_apps:
            size_mb = app.size / (1024 * 1024) if app.size > 0 else 0
            item_text = f"{app.name} ({size_mb:.1f} MB)"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, app)
            self.apps_list.addItem(item)
    
    def launch_selected_app(self):
        """Launch the selected portable app"""
        current_item = self.apps_list.currentItem()
        if current_item:
            self.launch_app(current_item)
    
    def launch_app(self, item: QListWidgetItem):
        """Launch a portable app"""
        app = item.data(Qt.UserRole)
        if not app:
            return
        
        try:
            if app.portable_path.endswith('.7z'):
                QMessageBox.information(
                    self, "Info", 
                    "This is a compressed portable app. Please extract it first to run."
                )
                return
            
            subprocess.Popen([app.portable_path], shell=True)
            app.last_run = datetime.now().isoformat()
            self.save_portable_apps()
            self.status_bar.showMessage(f"Launched {app.name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch {app.name}: {str(e)}")
    
    def delete_selected_app(self):
        """Delete the selected portable app"""
        current_item = self.apps_list.currentItem()
        if not current_item:
            return
        
        app = current_item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{app.name}'?\nThis will remove the portable app file.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if Path(app.portable_path).exists():
                    Path(app.portable_path).unlink()
                self.portable_apps.remove(app)
                self.save_portable_apps()
                self.refresh_apps_list()
                self.status_bar.showMessage(f"Deleted {app.name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete {app.name}: {str(e)}")
    
    def show_app_info(self):
        """Show information about the selected app"""
        current_item = self.apps_list.currentItem()
        if not current_item:
            self.info_text.clear()
            return
        
        app = current_item.data(Qt.UserRole)
        size_mb = app.size / (1024 * 1024) if app.size > 0 else 0
        
        info = f"""Name: {app.name}
Original Path: {app.original_path}
Portable Path: {app.portable_path}
Size: {size_mb:.1f} MB
Created: {app.created_date[:10] if app.created_date else 'Unknown'}
Last Run: {app.last_run[:10] if app.last_run else 'Never'}
Version: {app.version or 'Unknown'}
"""
        self.info_text.setText(info)
    
    def refresh_apps(self):
        """Refresh the apps list"""
        self.load_portable_apps()
        self.refresh_apps_list()
        self.status_bar.showMessage("Apps list refreshed")
    
    def show_preferences(self):
        """Show preferences dialog"""
        QMessageBox.information(self, "Preferences", "Preferences dialog will be implemented in future version.")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About",
            "Portable App Converter v1.0\n\n"
            "A tool for converting regular applications into portable apps.\n"
            "Built with PyQt5 for efficient app management."
        )
    
    def load_portable_apps(self):
        """Load portable apps from configuration"""
        config_path = Path("portable_apps.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                self.portable_apps = [PortableApp.from_dict(app_data) for app_data in data]
            except Exception as e:
                print(f"Error loading portable apps: {e}")
                self.portable_apps = []
        else:
            self.portable_apps = []
    
    def save_portable_apps(self):
        """Save portable apps to configuration"""
        try:
            config_path = Path("portable_apps.json")
            with open(config_path, 'w') as f:
                json.dump([app.to_dict() for app in self.portable_apps], f, indent=2)
        except Exception as e:
            print(f"Error saving portable apps: {e}")
    
    def closeEvent(self, event):
        """Handle application close event"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "A conversion is in progress. Do you want to cancel it and exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.worker.cancel()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Portable App Converter")
    app.setApplicationVersion("1.0")
    
    # Set application icon if available
    icon_path = Path("Icons/converter.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    window = PortableAppConverter()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
#!/usr/bin/env pythonw
"""
Portable Apps Launcher - Simple GUI for launching portable applications
"""

import sys
import os
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QLineEdit,
    QMenu, QAction, QMessageBox, QInputDialog, QGridLayout,
    QScrollArea, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QMimeData, QUrl
from PyQt5.QtGui import QIcon, QFont, QPixmap, QDrag, QPainter


class PortableAppItem:
    """Represents a portable application item"""
    
    def __init__(self, name: str, path: str, icon_path: str = ""):
        self.name = name
        self.path = path
        self.icon_path = icon_path
        self.favorite = False
        self.last_run = ""
        self.run_count = 0
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'path': self.path,
            'icon_path': self.icon_path,
            'favorite': self.favorite,
            'last_run': self.last_run,
            'run_count': self.run_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PortableAppItem':
        item = cls(data['name'], data['path'], data.get('icon_path', ''))
        item.favorite = data.get('favorite', False)
        item.last_run = data.get('last_run', '')
        item.run_count = data.get('run_count', 0)
        return item


class AppButton(QPushButton):
    """Custom button for portable apps with drag support"""
    
    def __init__(self, app_item: PortableAppItem, parent=None):
        super().__init__(parent)
        self.app_item = app_item
        self.setup_button()
    
    def setup_button(self):
        """Setup button appearance and behavior"""
        self.setText(self.app_item.name)
        self.setMinimumSize(120, 100)
        self.setMaximumSize(150, 120)
        
        # Load icon if available
        icon_path = Path("Icons") / f"{self.app_item.name}.ico"
        if icon_path.exists():
            self.setIcon(QIcon(str(icon_path)))
            self.setIconSize(self.size() * 0.6)
        
        # Style the button
        self.setStyleSheet(self._get_button_style())
    
    def _get_button_style(self) -> str:
        """Get button stylesheet"""
        favorite_border = "3px solid #FFD700" if self.app_item.favorite else "1px solid #606060"
        return f"""
            QPushButton {{
                background-color: #404040;
                border: {favorite_border};
                border-radius: 8px;
                padding: 5px;
                text-align: center;
                font-weight: bold;
                color: white;
            }}
            QPushButton:hover {{
                background-color: #505050;
                border: 2px solid #4CAF50;
            }}
            QPushButton:pressed {{
                background-color: #353535;
            }}
        """
    
    def mousePressEvent(self, event):
        """Handle mouse press for drag and drop"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for drag and drop"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if ((event.pos() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
        
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setText(self.app_item.path)
        drag.setMimeData(mimeData)
        
        # Create drag pixmap
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        self.render(painter)
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.exec_(Qt.CopyAction)


class PortableLauncher(QMainWindow):
    """Main launcher window for portable applications"""
    
    def __init__(self):
        super().__init__()
        self.apps: List[PortableAppItem] = []
        self.filtered_apps: List[PortableAppItem] = []
        self.app_buttons: List[AppButton] = []
        
        self.init_ui()
        self.load_apps()
        self.scan_portable_apps()
        self.update_apps_display()
        self.apply_dark_theme()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Portable Apps Launcher")
        self.setGeometry(200, 200, 800, 600)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Portable Apps")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Settings button
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(30, 30)
        settings_btn.clicked.connect(self.show_settings)
        header_layout.addWidget(settings_btn)
        
        layout.addLayout(header_layout)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search apps...")
        self.search_input.textChanged.connect(self.filter_apps)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Filter buttons
        filter_layout = QHBoxLayout()
        
        all_btn = QPushButton("All")
        all_btn.clicked.connect(lambda: self.set_filter("all"))
        filter_layout.addWidget(all_btn)
        
        favorites_btn = QPushButton("Favorites")
        favorites_btn.clicked.connect(lambda: self.set_filter("favorites"))
        filter_layout.addWidget(favorites_btn)
        
        recent_btn = QPushButton("Recent")
        recent_btn.clicked.connect(lambda: self.set_filter("recent"))
        filter_layout.addWidget(recent_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Apps grid
        self.create_apps_grid(layout)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        self.current_filter = "all"
    
    def create_apps_grid(self, parent_layout):
        """Create scrollable grid for app buttons"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.apps_widget = QWidget()
        self.apps_layout = QGridLayout(self.apps_widget)
        self.apps_layout.setSpacing(10)
        
        scroll_area.setWidget(self.apps_widget)
        parent_layout.addWidget(scroll_area)
    
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
            QLineEdit {
                background-color: #404040;
                border: 1px solid #606060;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #606060;
                padding: 5px;
                border-radius: 3px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QScrollArea {
                border: 1px solid #606060;
                border-radius: 5px;
            }
            QLabel {
                color: #ffffff;
            }
        """)
    
    def scan_portable_apps(self):
        """Scan for portable applications in the Portable apps directory"""
        portable_dir = Path("Portable apps")
        if not portable_dir.exists():
            portable_dir.mkdir()
            return
        
        # Find all .exe files
        exe_files = list(portable_dir.rglob("*.exe"))
        
        for exe_file in exe_files:
            app_name = exe_file.stem
            
            # Check if app already exists in our list
            if not any(app.name == app_name for app in self.apps):
                app_item = PortableAppItem(app_name, str(exe_file))
                self.apps.append(app_item)
        
        # Remove apps that no longer exist
        self.apps = [app for app in self.apps if Path(app.path).exists()]
    
    def update_apps_display(self):
        """Update the apps grid display"""
        # Clear existing buttons
        for button in self.app_buttons:
            button.deleteLater()
        self.app_buttons.clear()
        
        # Clear layout
        for i in reversed(range(self.apps_layout.count())):
            self.apps_layout.itemAt(i).widget().setParent(None)
        
        # Filter apps based on current filter and search
        self.apply_current_filter()
        
        # Create new buttons
        columns = 5
        for i, app in enumerate(self.filtered_apps):
            button = AppButton(app, self)
            button.clicked.connect(lambda checked, a=app: self.launch_app(a))
            
            # Add context menu
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(
                lambda pos, a=app, b=button: self.show_context_menu(a, b, pos)
            )
            
            row = i // columns
            col = i % columns
            self.apps_layout.addWidget(button, row, col)
            self.app_buttons.append(button)
        
        self.status_label.setText(f"Showing {len(self.filtered_apps)} apps")
    
    def apply_current_filter(self):
        """Apply the current filter to the apps list"""
        search_text = self.search_input.text().lower()
        
        if self.current_filter == "all":
            filtered = self.apps
        elif self.current_filter == "favorites":
            filtered = [app for app in self.apps if app.favorite]
        elif self.current_filter == "recent":
            filtered = sorted(
                [app for app in self.apps if app.last_run],
                key=lambda x: x.last_run,
                reverse=True
            )[:10]
        else:
            filtered = self.apps
        
        # Apply search filter
        if search_text:
            filtered = [app for app in filtered if search_text in app.name.lower()]
        
        self.filtered_apps = filtered
    
    def set_filter(self, filter_type: str):
        """Set the current filter type"""
        self.current_filter = filter_type
        self.update_apps_display()
    
    def filter_apps(self):
        """Filter apps based on search text"""
        self.update_apps_display()
    
    def launch_app(self, app: PortableAppItem):
        """Launch a portable application"""
        try:
            subprocess.Popen([app.path], cwd=Path(app.path).parent)
            app.last_run = datetime.now().isoformat()
            app.run_count += 1
            self.save_apps()
            self.status_label.setText(f"Launched {app.name}")
            
            # Auto-hide after launch (optional)
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch {app.name}: {str(e)}")
    
    def show_context_menu(self, app: PortableAppItem, button: AppButton, pos):
        """Show context menu for an app"""
        menu = QMenu(self)
        
        # Run as admin
        admin_action = QAction("Run as Administrator", self)
        admin_action.triggered.connect(lambda: self.run_as_admin(app))
        menu.addAction(admin_action)
        
        menu.addSeparator()
        
        # Toggle favorite
        fav_text = "Remove from Favorites" if app.favorite else "Add to Favorites"
        fav_action = QAction(fav_text, self)
        fav_action.triggered.connect(lambda: self.toggle_favorite(app, button))
        menu.addAction(fav_action)
        
        # Rename
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self.rename_app(app, button))
        menu.addAction(rename_action)
        
        menu.addSeparator()
        
        # Open location
        location_action = QAction("Open File Location", self)
        location_action.triggered.connect(lambda: self.open_location(app))
        menu.addAction(location_action)
        
        # Remove
        remove_action = QAction("Remove from List", self)
        remove_action.triggered.connect(lambda: self.remove_app(app))
        menu.addAction(remove_action)
        
        menu.exec_(button.mapToGlobal(pos))
    
    def run_as_admin(self, app: PortableAppItem):
        """Run application as administrator"""
        try:
            subprocess.run([
                "powershell", "-Command", 
                f"Start-Process '{app.path}' -Verb RunAs"
            ], check=True)
            app.last_run = datetime.now().isoformat()
            app.run_count += 1
            self.save_apps()
            self.status_label.setText(f"Launched {app.name} as admin")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run as admin: {str(e)}")
    
    def toggle_favorite(self, app: PortableAppItem, button: AppButton):
        """Toggle app favorite status"""
        app.favorite = not app.favorite
        button.setStyleSheet(button._get_button_style())
        self.save_apps()
        status = "Added to" if app.favorite else "Removed from"
        self.status_label.setText(f"{status} favorites: {app.name}")
    
    def rename_app(self, app: PortableAppItem, button: AppButton):
        """Rename an application"""
        new_name, ok = QInputDialog.getText(
            self, "Rename App", "Enter new name:", text=app.name
        )
        if ok and new_name.strip():
            app.name = new_name.strip()
            button.setText(app.name)
            self.save_apps()
            self.status_label.setText(f"Renamed to: {app.name}")
    
    def open_location(self, app: PortableAppItem):
        """Open the file location in explorer"""
        try:
            subprocess.run([
                "explorer", "/select,", app.path
            ], check=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open location: {str(e)}")
    
    def remove_app(self, app: PortableAppItem):
        """Remove app from the list"""
        reply = QMessageBox.question(
            self, "Remove App",
            f"Remove '{app.name}' from the launcher?\n(This won't delete the actual file)",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.apps.remove(app)
            self.save_apps()
            self.update_apps_display()
            self.status_label.setText(f"Removed: {app.name}")
    
    def show_settings(self):
        """Show settings dialog"""
        QMessageBox.information(
            self, "Settings",
            "Settings dialog will be available in future version.\n\n"
            "Current features:\n"
            "- Drag and drop .exe files to add them\n"
            "- Right-click apps for more options\n"
            "- Use search and filters to find apps\n"
            "- Double-click to launch apps"
        )
    
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop event to add new apps"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.exe'):
                self.add_dropped_app(file_path)
        event.accept()
    
    def add_dropped_app(self, file_path: str):
        """Add a dropped application to the list"""
        app_name = Path(file_path).stem
        
        # Check if app already exists
        if any(app.name == app_name for app in self.apps):
            self.status_label.setText(f"{app_name} already exists in the list")
            return
        
        # Copy to portable apps directory
        try:
            portable_dir = Path("Portable apps")
            portable_dir.mkdir(exist_ok=True)
            
            dest_path = portable_dir / Path(file_path).name
            shutil.copy2(file_path, dest_path)
            
            # Add to apps list
            app_item = PortableAppItem(app_name, str(dest_path))
            self.apps.append(app_item)
            self.save_apps()
            self.update_apps_display()
            
            self.status_label.setText(f"Added: {app_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add app: {str(e)}")
    
    def load_apps(self):
        """Load apps configuration from file"""
        config_path = Path("config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                self.apps = [
                    PortableAppItem.from_dict(app_data) 
                    for app_data in data.get('apps', [])
                ]
            except Exception as e:
                print(f"Error loading config: {e}")
                self.apps = []
        else:
            self.apps = []
    
    def save_apps(self):
        """Save apps configuration to file"""
        try:
            config_data = {
                'apps': [app.to_dict() for app in self.apps],
                'last_updated': datetime.now().isoformat()
            }
            
            with open("config.json", 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Portable Apps Launcher")
    app.setApplicationVersion("1.0")
    
    # Set application icon if available
    icon_path = Path("Icons/launcher.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    launcher = PortableLauncher()
    launcher.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
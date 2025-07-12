# Portable App Tools

A comprehensive suite for converting regular applications into portable apps and managing them efficiently. Built with PyQt5 for Windows.

## 🚀 Features

### Portable App Converter
- Convert regular Windows applications into portable versions
- Intelligent dependency scanning and packaging
- Multiple compression levels for size optimization
- Progress tracking with cancellation support
- Automatic launcher script generation
- 7-Zip archive creation for distribution

### Portable Apps Launcher
- Auto-detects and displays portable .exe apps by folder
- Custom icons for each app (place .ico files in the `Icons/` folder)
- Search, favorites, and recent apps support
- Drag-and-drop to add new apps instantly
- Modern dark-themed UI with responsive design
- Right-click context menus with admin options
- Grid layout with resizable interface

### PowerShell CLI
- Complete command-line interface for power users
- Launch apps, manage favorites, search functionality
- Add/remove apps from command line
- View app statistics and information
- Integration with GUI launcher

## 📦 Installation

### Quick Start
1. **Install Python 3.7+** (https://www.python.org/downloads/)
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the tools:**
   ```bash
   # Conversion tool
   python portable_converter.py
   
   # Launcher
   pythonw launcher.pyw
   
   # CLI interface
   powershell .\Portable.ps1 list
   ```

### Building Executables
```bash
# Windows only
.\build.bat
```
This creates standalone executables in the `build/` directory.

## 📁 Directory Structure
```
Portable-Tools/
├── portable_converter.py    # Main conversion application
├── launcher.pyw            # GUI launcher for portable apps
├── Portable.ps1           # PowerShell CLI interface
├── setup.py               # Build script for executables
├── build.bat              # Windows build automation
├── Portable apps/         # Place your portable .exe files here
├── Icons/                 # Custom .ico files for apps
├── config.json           # App settings and favorites
└── portable_apps.json    # Converter app database
```

## 🎯 Usage

### Converting Applications
1. **Launch Converter:** Run `portable_converter.py`
2. **Select App:** Browse for the .exe file to convert
3. **Choose Options:** Set compression level and dependencies
4. **Convert:** Click "Convert to Portable" and select output directory
5. **Manage:** View and launch converted apps in the manager

### Using the Launcher
- **Search:** Type in the search box to filter apps
- **Launch:** Double-click or press Enter to run apps
- **Favorites:** Right-click → "Add to Favorites" for quick access
- **Admin:** Right-click → "Run as Administrator" for elevated apps
- **Organize:** Drag and drop .exe files to add them instantly

### PowerShell Commands
```powershell
# List all apps
.\Portable.ps1 list

# Launch an app
.\Portable.ps1 launch notepad

# Search for apps
.\Portable.ps1 search editor

# Add new app
.\Portable.ps1 add "C:\Tools\app.exe"

# Show favorites
.\Portable.ps1 favorites

# Get app info
.\Portable.ps1 info myapp

# Launch GUI
.\Portable.ps1 gui
```

## 🔧 Configuration

### Custom Icons
Place `.ico` files in the `Icons/` folder named exactly as your executable:
- `MyApp.exe` → `Icons/MyApp.ico`
- Case-sensitive on some systems

### Settings
- `config.json` - Launcher preferences and app metadata
- `portable_apps.json` - Converter database and app information
- Settings are automatically saved and restored

## 🛠️ Advanced Features

### Conversion Options
- **Ultra Compression:** Maximum space savings (slowest)
- **Fast Compression:** Quick conversion with larger files
- **Dependency Inclusion:** Automatically package required DLLs
- **Custom Launchers:** Generated batch scripts for easy execution

### Management Features
- **Launch Tracking:** Track usage statistics and last run times
- **Batch Operations:** Manage multiple apps simultaneously
- **Export/Import:** Share app configurations between systems
- **Update Detection:** Monitor for app changes and updates

## 🐛 Troubleshooting

### Common Issues
- **Icons not appearing:** Ensure .ico files are in `Icons/` folder with correct names
- **Apps not detected:** Verify .exe files are in `Portable apps/` or subfolders
- **Conversion fails:** Check app permissions and available disk space
- **GUI not launching:** Verify Python and PyQt5 installation

### Error Messages
- **"Failed to launch":** Check file path and permissions
- **"Conversion error":** Ensure source app isn't running
- **"Dependencies missing":** Install required Python packages

### Debug Mode
Run with Python console for detailed error messages:
```bash
python portable_converter.py
python launcher.pyw
```

## 📋 Requirements
- **OS:** Windows 10+ (some features require Windows-specific APIs)
- **Python:** 3.7+ with pip
- **Dependencies:** PyQt5, psutil, py7zr, configparser
- **Optional:** cx-Freeze for building executables

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License
MIT License - see LICENSE file for details

## 🔮 Future Features
- Cross-platform support (Linux, macOS)
- Cloud synchronization of app lists
- Automatic updates for portable apps
- Plugin system for custom converters
- Batch conversion from installers
- Integration with popular app stores
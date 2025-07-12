# Portable Apps Launcher

A modern, customizable launcher for your portable Windows applications, built with PyQt5.

## Features
- Auto-detects and groups portable .exe apps by folder
- Custom icons for each app (place .ico files in the `Icons/` folder)
- Search, favorites, and recent apps support
- Drag-and-drop to add new apps
- Modern, dark-themed UI
- Settings dialog (future expansion)
- PowerShell script alternative for CLI launching

## Setup
1. **Install Python 3.7+** (https://www.python.org/downloads/)
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the launcher:**
   ```bash
   pythonw launcher.pyw
   ```

## Directory Structure
- `launcher.pyw` — Main GUI launcher
- `Portable apps/` — Place your portable .exe files here (subfolders supported)
- `Icons/` — Place .ico files named after your .exe (e.g., `qBittorrent.ico`)
- `config.json` — Stores launcher settings, favorites, and recents
- `Portable.ps1` — PowerShell CLI launcher

## Usage
- **Search:** Type in the search box to filter apps
- **Right-click app:** Run as admin, favorite, open location, or rename
- **Drag-and-drop:** Drop .exe files to add them
- **Settings:** Click ⚙ for settings (future features)

## Troubleshooting
- If icons do not appear, ensure .ico files are in the `Icons/` folder and named exactly as the .exe (case-sensitive)
- If the launcher does not detect your apps, ensure they are in the `Portable apps/` folder or subfolders
- For issues, check the console output or open an issue

## Requirements
- Windows 10+
- Python 3.7+
- PyQt5

## License
MIT
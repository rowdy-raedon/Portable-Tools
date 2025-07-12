"""
Setup script for creating executable from the Portable App Converter
"""

from cx_Freeze import setup, Executable
import sys
import os

# Dependencies
packages = ["PyQt5", "psutil", "py7zr", "configparser"]
excludes = ["tkinter"]

# Include files (only if they exist)
include_files = []
if os.path.exists("Icons/"):
    include_files.append(("Icons/", "Icons/"))
if os.path.exists("Portable apps/"):
    include_files.append(("Portable apps/", "Portable apps/"))

# Build options
build_exe_options = {
    "packages": packages,
    "excludes": excludes,
    "include_files": include_files,
    "optimize": 2,
}

# Executables
executables = [
    Executable(
        "portable_converter.py",
        base="Win32GUI" if sys.platform == "win32" else None,
        target_name="PortableConverter.exe",
        icon="Icons/converter.ico" if os.path.exists("Icons/converter.ico") else None
    ),
    Executable(
        "launcher.pyw",
        base="Win32GUI" if sys.platform == "win32" else None,
        target_name="PortableLauncher.exe",
        icon="Icons/launcher.ico" if os.path.exists("Icons/launcher.ico") else None
    )
]

setup(
    name="Portable App Tools",
    version="1.0.0",
    description="Tools for managing and converting portable applications",
    options={"build_exe": build_exe_options},
    executables=executables
)
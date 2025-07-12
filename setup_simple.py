"""
Simplified setup script for creating executables
"""

from cx_Freeze import setup, Executable
import sys

# Simple build options
build_exe_options = {
    "packages": ["PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets"],
    "excludes": ["tkinter", "unittest"],
    "optimize": 2,
}

# Executables
executables = [
    Executable(
        "portable_converter.py",
        base="Win32GUI" if sys.platform == "win32" else None,
        target_name="PortableConverter.exe"
    ),
    Executable(
        "launcher.pyw",
        base="Win32GUI" if sys.platform == "win32" else None,
        target_name="PortableLauncher.exe"
    )
]

setup(
    name="PortableAppTools",
    version="1.0",
    description="Portable Application Tools",
    options={"build_exe": build_exe_options},
    executables=executables
)
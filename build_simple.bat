@echo off
echo Building Portable App Tools (Simple)...
echo.

echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Creating required directories...
if not exist "Portable apps" mkdir "Portable apps"
if not exist "Icons" mkdir "Icons"

echo.
echo Installing/updating dependencies...
pip install --upgrade cx-Freeze PyQt5 psutil py7zr

echo.
echo Building executables...
python setup_simple.py build

echo.
if exist "build\exe.win-amd64-*" (
    echo Build completed successfully!
    echo Executables are in the build directory:
    dir "build\exe.win-amd64-*" /b
    echo.
    echo Ready to run:
    echo - PortableConverter.exe
    echo - PortableLauncher.exe
) else (
    echo Build failed - no executables found.
    echo Try the troubleshooting guide in BUILD_TROUBLESHOOTING.md
)

echo.
pause
@echo off
echo Building Portable App Tools (Simple)...
echo.

echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Installing/updating dependencies...
pip install --upgrade cx-Freeze PyQt5 psutil py7zr

echo.
echo Building executables...
python setup_simple.py build

echo.
if exist build (
    echo Build completed successfully!
    echo Executables are in the 'build' directory.
    dir build\exe.win-amd64-* /b 2>nul
) else (
    echo Build failed - no build directory created.
)

echo.
pause
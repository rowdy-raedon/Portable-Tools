@echo off
echo Building Portable App Tools...
echo.

echo Creating required directories...
if not exist "Portable apps" mkdir "Portable apps"
if not exist "Icons" mkdir "Icons"

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building executables...
python setup.py build

echo.
if exist "build\exe.win-amd64-*" (
    echo Build completed successfully!
    echo Executables are in the build directory:
    dir "build\exe.win-amd64-*" /b
    echo.
    echo Files created:
    echo - PortableConverter.exe ^(Main conversion tool^)
    echo - PortableLauncher.exe ^(App launcher^)
) else (
    echo Build failed - no executables found in build directory.
    echo Check the error messages above.
)
echo.
pause
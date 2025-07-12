@echo off
echo Building Portable App Tools...
echo.

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building executables...
python setup.py build

echo.
echo Build complete! Executables are in the 'build' directory.
echo.
echo Files created:
echo - PortableConverter.exe (Main conversion tool)
echo - PortableLauncher.exe (App launcher)
echo.
pause
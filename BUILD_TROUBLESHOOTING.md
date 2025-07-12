# Build Troubleshooting Guide

## Common Build Issues

### Error: "include_msvcrt" option not supported
**Cause:** You're using a cached version of setup.py or an older cx-Freeze version.

**Solutions:**
1. **Use the simple build script:**
   ```batch
   .\build_simple.bat
   ```

2. **Clear build cache:**
   ```batch
   rmdir /s /q build
   rmdir /s /q dist
   pip install --upgrade cx-Freeze
   python setup.py build
   ```

3. **Manual build:**
   ```batch
   python setup_simple.py build
   ```

### Error: Module not found during build
**Solutions:**
1. **Install missing packages:**
   ```batch
   pip install --upgrade PyQt5 psutil py7zr configparser
   ```

2. **Use virtual environment:**
   ```batch
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python setup.py build
   ```

### Error: Permission denied
**Solutions:**
1. **Run as Administrator**
2. **Close any running applications**
3. **Disable antivirus temporarily**

### Build succeeds but executables don't run
**Solutions:**
1. **Copy missing DLLs to exe directory**
2. **Install Visual C++ Redistributables**
3. **Run from command line to see error messages**

## Alternative Build Methods

### PyInstaller (Alternative)
```batch
pip install pyinstaller
pyinstaller --onefile --windowed portable_converter.py
pyinstaller --onefile --windowed launcher.pyw
```

### Auto-py-to-exe (GUI)
```batch
pip install auto-py-to-exe
auto-py-to-exe
```

## Verification Steps

1. **Check build directory:**
   ```batch
   dir build\exe.win-amd64-*
   ```

2. **Test executables:**
   ```batch
   cd build\exe.win-amd64-*
   PortableConverter.exe
   PortableLauncher.exe
   ```

3. **Check dependencies:**
   ```batch
   python -c "import PyQt5; print('PyQt5 OK')"
   python -c "import psutil; print('psutil OK')"
   python -c "import py7zr; print('py7zr OK')"
   ```

## Quick Fixes

### Just want to run the apps?
```batch
# Run directly with Python
python portable_converter.py
pythonw launcher.pyw
```

### Need portable versions?
Use PyInstaller for more reliable builds:
```batch
pip install pyinstaller
pyinstaller --onefile --noconsole portable_converter.py
pyinstaller --onefile --noconsole launcher.pyw
```

## Getting Help

If builds continue to fail:
1. Check Python version: `python --version` (need 3.7+)
2. Check cx-Freeze version: `pip show cx-Freeze`
3. Try the simple build script: `build_simple.bat`
4. Use PyInstaller as alternative
5. Run apps directly with Python
@echo off
REM ========================================
REM Clean Sheet v2.1.0 - Build Script
REM Professional Data Cleaning Made Simple
REM ========================================

echo.
echo ========================================
echo Building Clean Sheet v2.1.0
echo Professional Data Cleaning Made Simple
echo ========================================
echo.

REM Check Python installation
echo [1/7] Checking Python installation...
py --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python 'py' command not found!
    echo Please install Python 3.13.3 or later from python.org
    pause
    exit /b 1
)
py --version
echo.

REM Install/update pip
echo [2/7] Updating pip...
py -m pip install --upgrade pip
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Failed to upgrade pip, continuing anyway...
)
echo.

REM Install dependencies
echo [3/7] Installing/updating dependencies...
py -m pip install --upgrade pyinstaller packaging requests pillow
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install PyInstaller dependencies!
    pause
    exit /b 1
)

if exist requirements.txt (
    echo Installing application dependencies from requirements.txt...
    py -m pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to install application dependencies!
        pause
        exit /b 1
    )
) else (
    echo WARNING: requirements.txt not found, skipping application dependencies
)
echo.

REM Create application icon
echo [4/7] Creating application icon...
if exist create_icon.py (
    py create_icon.py
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to create icon!
        pause
        exit /b 1
    )
) else (
    echo ERROR: create_icon.py not found!
    pause
    exit /b 1
)
echo.

REM Clean previous builds
echo [5/7] Cleaning previous builds...
if exist "build" (
    echo Removing build directory...
    rmdir /s /q build
)
if exist "dist" (
    echo Removing dist directory...
    rmdir /s /q dist
)
if exist "CleanSheet.exe" (
    echo Removing old CleanSheet.exe...
    del /f CleanSheet.exe
)
echo Build directories cleaned.
echo.

REM Build executable
echo [6/7] Building executable with PyInstaller...
echo This may take several minutes...
echo.
py -m PyInstaller clean_sheet.spec --clean --noconfirm
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: PyInstaller build failed!
    echo.
    echo Common issues:
    echo 1. Missing dependencies - check requirements.txt
    echo 2. Import errors - check Python path
    echo 3. Icon file missing - run create_icon.py first
    echo.
    pause
    exit /b 1
)
echo.

REM Verify output
echo [7/7] Verifying build output...
if exist "dist\CleanSheet.exe" (
    echo.
    echo ========================================
    echo ✓ BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Output: dist\CleanSheet.exe
    echo.
    dir "dist\CleanSheet.exe" | find "CleanSheet.exe"
    echo.
    echo File size:
    for %%A in ("dist\CleanSheet.exe") do echo   %%~zA bytes (%%~zAk KB)
    echo.
    echo ========================================
    echo NEXT STEPS
    echo ========================================
    echo.
    echo 1. Test the executable:
    echo    dist\CleanSheet.exe
    echo.
    echo 2. Verify all operations work correctly:
    echo    - File import/export
    echo    - All 51 operations
    echo    - Preset management
    echo    - AI Assistant (if API key configured)
    echo    - Data Quality Analyzer
    echo.
    echo 3. Test auto-update notification:
    echo    - Create a fake newer version in GitHub releases
    echo    - Start application and check for update prompt
    echo.
    echo 4. Create GitHub release:
    echo    - Tag: v2.1.0
    echo    - Upload: dist\CleanSheet.exe
    echo    - See create_release.md for details
    echo.
    echo 5. Distribute to users!
    echo.
) else (
    echo.
    echo ERROR: CleanSheet.exe not found in dist directory!
    echo Build may have failed or output is in unexpected location.
    echo.
    pause
    exit /b 1
)

pause

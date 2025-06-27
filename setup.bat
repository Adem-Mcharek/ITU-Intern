@echo off
echo ITU WebTV Processing System - First Time Setup
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python from https://python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found: 
python --version

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing dependencies (this may take several minutes)...
pip install -r requirements.txt

REM Initialize database
echo.
echo Initializing database...
python init_db.py

REM Create admin user
echo.
echo Creating admin user...
python create_admin.py

echo.
echo Setup complete! You can now start the application with:
echo start.bat
echo.
echo Or manually with:
echo venv\Scripts\activate
echo python run.py
echo.
pause 
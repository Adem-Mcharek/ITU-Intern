@echo off
echo Starting ITU WebTV Processing System...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run setup first: python -m venv venv
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate

REM Check if database exists
if not exist "app.db" (
    if not exist "instance\app.db" (
        echo No database found. Initializing...
        python init_db.py
    )
)

REM Start the application
echo Starting server...
python run.py

pause 
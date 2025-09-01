@echo off
REM Papers Desktop Database - Windows Launcher
REM Double-click this file to start the app on Windows

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "venv\.deps_installed" (
    echo Installing dependencies...
    pip install --upgrade pip
    cd papers-desktop-app
    pip install -r requirements.txt
    cd ..
    echo. > venv\.deps_installed
)

REM Change to app directory and run
cd papers-desktop-app

echo Starting Papers Desktop Database...
echo Close this window to quit the app.

REM Run the application
python -m app.main

echo.
echo App closed. Press any key to close this window...
pause > nul

@echo off
chcp 65001 >nul
title Rule Editor Setup

REM Change to script directory
cd /d "%~dp0"

echo ====================================
echo    Rule Editor - Setup Wizard
echo ====================================
echo.

REM Check if Python is installed
echo [1/4] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8 or higher.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM Create virtual environment
echo [2/4] Creating virtual environment...
if exist "venv" (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)
echo.

REM Activate virtual environment
echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies
echo [4/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo ====================================
echo    Setup Complete!
echo ====================================
echo.
echo Run "start.bat" to launch the application
echo.
pause

@echo off
title TahaTyper Pro - Automated Setup & Launch 🤖🚀
echo --------------------------------------------------
echo Welcome to TahaTyper Pro Setup!
echo This script will install everything you need to run
echo the latest Ghost Mode and Scheduler features.
echo --------------------------------------------------
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed on your computer.
    echo Please install Python from https://www.python.org/
    pause
    exit /b
)

echo [1/3] Installing professional tools (pynput, keyboard, pyautogui, pillow)...
python -m pip install --upgrade pip
python -m pip install pynput keyboard pyautogui pillow

echo.
echo [2/3] Verifying TahaTyper.py is in this folder...
if not exist "TahaTyper.py" (
    echo [ERROR] TahaTyper.py not found in this folder!
    echo Please make sure this .bat file is in the AutoTyper folder.
    pause
    exit /b
)

echo.
echo [3/3] Launching TahaTyper Pro...
echo (The app window should appear in a few seconds)
start "" pythonw "TahaTyper.py"

echo.
echo --------------------------------------------------
echo SETUP COMPLETE! You can now use TahaTyper Pro.
echo This window will close in 5 seconds...
echo --------------------------------------------------
timeout /t 5 >nul
exit

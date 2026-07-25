@echo off
:: Navigate to the script's directory
cd /d "%~dp0"

echo Pulling latest updates from Git...
git pull

if %errorlevel% neq 0 (
    echo.
    echo [Warning] Git pull failed. Starting the program anyway...
    echo.
)

echo Starting Sunako...
python run.py

pause

@echo off
:: Navigate to the script's directory
cd /d "%~dp0"

echo [warning] "run_encryptor.bat" is deprecated and will be removed in a future update.
echo Please use "start_sunako_windows.bat" to launch Sunako from now on.
echo.
timeout /t 3 >nul

:: Launch the new script and exit immediately
if exist "start_sunako_windows.bat" (
    start "" "start_sunako_windows.bat"
    exit
) else (
    echo [error] "start_sunako_windows.bat" was not found. 
    echo Please pull the latest updates or check your repository files.
    pause
)
@echo off
:: Navigate to the script's directory
cd /d "%~dp0"

:: Set the repo url
set REPO_URL=https://github.com/fatahillah2606/sunako.git

:: Check if .git directory exists (for ZIP download users)
if not exist ".git" (
    echo Initializing Git repository...
    git init
    git remote add origin %REPO_URL%
    git fetch
    git checkout -t origin/main -f
) else (
    :: For existing users: update the remote URL to the new repository link
    git remote set-url origin %REPO_URL%
)

:: Pull latest changes
echo Pulling latest updates from Git...
git pull

if %errorlevel% neq 0 (
    echo.
    echo [Warning] Git pull failed. Starting the program anyway...
    echo.
)

:: Run the application
echo Starting Sunako...
python run.py

pause

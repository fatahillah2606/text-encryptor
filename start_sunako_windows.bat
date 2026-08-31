@echo off
:: Navigate to the script's directory
cd /d "%~dp0"

:: Set the repo url
set REPO_URL=https://github.com/fatahillah2606/sunako.git

:: Check if .git directory exists (for ZIP download users)
if not exist ".git" (
    echo [info] Initializing Git repository...
    git init
    git remote add origin %REPO_URL%
    git fetch
    git checkout -t origin/main -f
) else (
    :: For existing users: update the remote URL to the new repository link
    git remote set-url origin %REPO_URL%
)

:: Pull latest changes
echo [info] Pulling latest updates from Git...
git pull

if %errorlevel% neq 0 (
    echo.
    echo [warning] Git pull failed. Starting the program anyway...
    echo.
)

:: Check and create virtual environment if missing
if not exist ".venv" (
    echo [info] Creating virtual environment...
    python -m venv .venv
)

:: Activate the virtual environment
echo [info] Activating virtual environment...
call .venv\Scripts\activate.bat

:: Run the application
echo [info] Starting Sunako...
python run.py

pause
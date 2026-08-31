#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")" || exit

# Set the repo url
REPO_URL="https://github.com/fatahillah2606/sunako.git"

# Check if .git directory exists (for ZIP download users)
if [ ! -d ".git" ]; then
    echo "[info] Initializing Git repository..."
    git init
    git remote add origin "$REPO_URL"
    git fetch
    git checkout -t origin/main -f
else
    # For existing users: update the remote URL to the new repository link
    git remote set-url origin "$REPO_URL"
fi

# Pull latest changes
echo "[info] Pulling latest updates from Git..."
git pull

if [ $? -ne 0 ]; then
    echo ""
    echo "[warning] Git pull failed. Starting the program anyway..."
    echo ""
fi

# Check and create virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "[info] Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate the virtual environment
echo "[info] Activating virtual environment..."
source .venv/bin/activate

# Run the application
echo "[info] Starting Sunako..."
python3 run.py

read -p "Press [Enter] key to exit..."
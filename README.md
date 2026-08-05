# Sunako

## Description

Sunako is a privacy-focused security tool. Its name is inspired by a character from the game Blue Archive, Sunaookami Shiroko, though this project is entirely independent.

This program is a simple project that I made to practice my coding skills, featuring text encryption, file encryption, a password manager, a password generator, and text conversion.

## Requirement

- Python (v3.13 or higher)
- Git
- Node.js (Optional, only required if you want to build or modify the project yourself)

## Usage

### Windows

Simply execute the `run_encryptor.bat` file

### Linux & macOS

1.  Clone the repository:

    ```bash
    git clone https://github.com/fatahillah2606/sunako.git
    ```

2.  Create and activate a virtual environment:

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  Run the application:

    ```bash
    python run.py
    ```

## Building from Source

If you want to modify or build the project assets yourself, follow these steps:

1.  Clone the repository:

    ```bash
    git clone https://github.com/fatahillah2606/sunako.git
    ```

2.  Create and activate a virtual environment:

    ```bash
    python -m venv .venv
    ```

    - Windows: `.venv\Scripts\activate`
    - Linux/macOS: `source .venv/bin/activate`

3.  Install Python dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4.  Install Node packages:

    ```bash
    npm install
    ```

5.  Start the Tailwind CSS CLI watcher:

    ```bash
    npx @tailwindcss/cli -i ./static/styles/tailwindcss/import-tailwind.css -o ./static/styles/tailwindcss/tailwind.css --watch
    ```

6.  Bundle `material-web` using `esbuild`:

    ```bash
    npx esbuild ./static/scripts/import-m3.js --bundle --outfile=./static/scripts/material-web.js
    ```

7.  Run the application:

    ```bash
    python app.py
    ```

8.  Open your browser and navigate to [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## Disclaimer

This project is an independent open-source tool and is not affiliated with, endorsed by, or connected to the NEXON Korea Corp. and NEXON Games Co., Ltd.

---

Made with ❤️ by Fatahillah

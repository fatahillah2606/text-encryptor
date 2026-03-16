# Text Encryptor

## Description

A simple project for text encryption and decryption, featuring a password manager and password generator. The purpose of this project is to practice my coding skills.

## Requirement

- Python 3
- Node.js (optional)

## Installation

1.  Clone this repository:

    ```bash
    git clone https://github.com/fatahillah2606/text-encryptor.git
    ```

2.  Create and activate a virtual environment:

    ```bash
    python -m venv .venv
    ```

    For Windows:

        .venv\Scripts\activate

    For Linux/MacOS:

        source .venv/bin/activate

    Install dependencies:

        pip install -r requirements.txt

3.  Install node packages (optional)

    ```bash
    npm install
    ```

## Usage

### Start the Flask

```bash
python app.py
```

### Start Tailwindcss cli (optional)

```bash
npx @tailwindcss/cli -i ./static/styles/input.css -o ./static/styles/output.css --watch
```

Open your browser and navigate to http://127.0.0.1:5000/

**Note**: The Tailwindcss and Flowbite CDNs are already included in the code. So, there is no need to install Node.js packages—or even use Node.js at all.

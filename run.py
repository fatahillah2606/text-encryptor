import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from threading import Thread

from colorama import Fore, init

init(autoreset=True)


# ========== Install the requirements ==========
def install_requirements():
    req_file = "requirements.txt"

    if os.path.exists(req_file):
        print(f" * Found {req_file}. Checking dependencies...")
        try:
            # use -m pip to ensure it uses the correct Python environment
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", req_file]
            )
            print(" + Dependencies are up to date.")
        except Exception as e:
            print(f"{Fore.RED} - Failed to install requirements: {e}")
            sys.exit(1)
    else:
        print(f"{Fore.YELLOW} ! {req_file} not found. Skipping installation.")


# ========== Wait for the Flask is ready ==========
def wait_for_flask(url, timeout=15):
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Try to connect to the Flask server
            urllib.request.urlopen(url, timeout=1)

            # If successful, open the browser
            webbrowser.open(url)
            return
        except Exception:
            # Connection failed (server not ready yet). Wait a moment and try again.
            time.sleep(0.2)

    print(f"{Fore.RED} - Timeout reached. Could not detect Flask server.")


# ========== Start the program ==========
def start_app():
    print(" * Launching Sunako...")
    target_url = "http://127.0.0.1:5000"
    try:
        # Start Flask as a background process
        process = subprocess.Popen([sys.executable, "app.py"])

        # Start the polling thread
        poll_thread = Thread(target=wait_for_flask, args=(target_url,), daemon=True)
        poll_thread.start()

        # Keep run.py alive while Flask runs
        process.wait()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW} ! Operation cancelled by user. Goodbye.")
        if "process" in locals():
            process.terminate()


if __name__ == "__main__":
    install_requirements()
    start_app()

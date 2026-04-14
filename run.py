import subprocess
import sys
import os

def install_requirements():
    req_file = "requirements.txt"

    if os.path.exists(req_file):
        print(f"[*] Found {req_file}. Checking dependencies...")
        try:
            # use -m pip to ensure it uses the correct Python environment
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
            print("[+] Dependencies are up to date.")
        except Exception as e:
            print(f"[-] Failed to install requirements: {e}")
            sys.exit(1)
    else:
        print(f"[!] {req_file} not found. Skipping installation.")

def start_app():
    print("[*] Launching Text Encryptor...")
    try:
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n[!] Operation cancelled by user. Goodbye.")

if __name__ == "__main__":
    install_requirements()
    start_app()

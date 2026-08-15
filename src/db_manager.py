import os
import sqlite3

from colorama import Fore, init

init(autoreset=True)
db_path = "db/vault_manager.db"
old_db_path = "db/old_vault_manager.db"


# ========== Get database version ==========
def get_db_version(path):
    if not os.path.exists(path):
        return None

    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version;")
    version = cursor.fetchone()[0]
    conn.close()

    return version


# ========== Initialize the database ==========
def initialize_db():
    if os.path.exists(db_path):
        version = get_db_version(db_path)

        # Check if it was the old version
        if not version == 2:
            if not os.path.exists(old_db_path):
                os.rename(db_path, old_db_path)
                print(" * Old database found. Renaming to old_vault_db for recovery.")

            else:
                # If old db already exist, create another one
                duplicate_count = 1
                duplicate_name = f"db/old_vault_manager_{duplicate_count}.db"

                while os.path.exists(duplicate_name):
                    print(f" * {duplicate_name} already exist. Creating another one")
                    duplicate_count += 1
                    duplicate_name = f"db/old_vault_manager_{duplicate_count}.db"

                os.rename(db_path, duplicate_name)

        else:
            print(" * Database found!")

    if not os.path.exists(db_path):
        create_database()


# ========== Create the database ==========
def create_database():
    # check if db folder exist
    if not os.path.exists("db"):
        os.makedirs("db")

    try:
        with sqlite3.connect(db_path) as conn:
            # Connect to db or created it if not exist.
            cursor = conn.cursor()

            # Enable foreign key support
            cursor.execute("PRAGMA foreign_keys = ON;")

            # Set database version
            cursor.execute("PRAGMA user_version = 2;")

            # 1. Tabel "Users"
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(50) NOT NULL,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password_hash BLOB NOT NULL
                )
                """)

            # 2. Tabel "Keys"
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keys (
                    key_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    key_name VARCHAR(50) NOT NULL,
                    encrypted_key BLOB NOT NULL,
                    key_iv BLOB NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
                """)

            # 3. Tabel "Passwords"
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS passwords (
                    password_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    key_id INTEGER NOT NULL,
                    service_url TEXT NULL,
                    service_name VARCHAR(50) NOT NULL,
                    username_account BLOB NOT NULL,
                    username_iv BLOB NOT NULL,
                    encrypted_password BLOB NOT NULL,
                    password_iv BLOB NOT NULL,
                    service_notes TEXT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (key_id) REFERENCES keys(key_id) ON DELETE CASCADE
                )
                """)

            conn.commit()

        print(" * Generation complete.")

    except sqlite3.Error as e:
        print(f"{Fore.RED} * An error occurred: {e}")

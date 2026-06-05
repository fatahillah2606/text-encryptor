import os
import sqlite3


def create_database():
    # check if db folder exist
    if not os.path.exists("db"):
        os.makedirs("db")

    db_path = "db/vault_manager.db"

    try:
        # Connect to db or created it if not exist.
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Enable foreign key support
        cursor.execute("PRAGMA foreign_keys = ON;")

        # 1. Tabel "Users"
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) NOT NULL,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(60) NOT NULL
            )
        """)

        # 2. Tabel "Keys"
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keys (
                key_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key_name VARCHAR(50) NOT NULL,
                encrypted_key BLOB NOT NULL,
                iv BLOB NOT NULL,
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
                username_account VARCHAR(100) NOT NULL,
                encrypted_password BLOB NOT NULL,
                iv BLOB NOT NULL,
                service_notes TEXT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (key_id) REFERENCES keys(key_id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        print("Generation complete.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()


# Update the database
def update_database():
    db_path = "db/vault_manager.db"
    if not os.path.exists(db_path):
        return  # Cancle operation if database doesn't exist

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Get existing column in 'passwords' table
            cursor.execute("PRAGMA table_info(passwords);")
            existing_columns = [column[1] for column in cursor.fetchall()]

            # List of new field
            new_columns = {"service_url": "TEXT", "service_notes": "TEXT"}

            for col_name, col_type in new_columns.items():
                if col_name not in existing_columns:
                    print(f"Updating database: adding {col_name} column...")
                    cursor.execute(
                        f"ALTER TABLE passwords ADD COLUMN {col_name} {col_type}"
                    )

            conn.commit()
    except sqlite3.Error as e:
        print(f"Failed updating schema: {e}")

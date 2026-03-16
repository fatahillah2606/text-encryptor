import binascii
import os
import sqlite3

from src.encryptor import decrypt_aes, encrypt_aes, get_valid_key

# Database path
db_path = os.path.join("db", "vault_manager.db")


# 
# Key manager
# 

# Get all user key
def get_user_key_all(user_id, master_key):
    query = "SELECT * FROM keys WHERE user_id = ?"

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            cursor.execute(query, (user_id,))

            rows = cursor.fetchall()

            # Add master key at the beginning of the list
            result = [{"key_name": "master_key", "encryption_key": master_key}]

            for row in rows:
                # Combine iv + encrypted_key and unhexlify
                key_from_db = binascii.hexlify(
                    row["iv"] + row["encrypted_key"]
                ).decode()
                key_from_db = binascii.unhexlify(key_from_db)

                # Get valid key
                valid_key = get_valid_key(master_key)

                # Decrypt key
                decrypted_key = decrypt_aes(key_from_db, valid_key["encoded_key"])

                result.append(
                    {
                        "key_id": row["key_id"],
                        "user_id": row["user_id"],
                        "key_name": row["key_name"],
                        "encryption_key": decrypted_key,
                    }
                )

            return result

    except sqlite3.Error as err:
        return f"Database error: {str(err)}"


# Get user key
def get_user_key(key_id, user_id, master_key):
    query = "SELECT * FROM keys WHERE key_id = ? AND user_id = ?"

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            cursor.execute(query, (key_id, user_id))

            key = cursor.fetchone()

            result = {}

            if key:
                # Combine iv + encrypted_key and unhexlify
                key_from_db = binascii.hexlify(
                    key["iv"] + key["encrypted_key"]
                ).decode()
                key_from_db = binascii.unhexlify(key_from_db)

                # Get valid key
                valid_key = get_valid_key(master_key)

                # Decrypt key
                decrypted_key = decrypt_aes(key_from_db, valid_key["encoded_key"])

                result = {
                    "key_id": key["key_id"],
                    "user_id": key["user_id"],
                    "key_name": key["key_name"],
                    "encryption_key": decrypted_key,
                }

            return result

    except sqlite3.Error as err:
        return f"Database error: {str(err)}"
    

# Delete key
def delete_user_key(key_id):
    query = "DELETE FROM keys WHERE key_id = ?"

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            cursor.execute(query, (key_id,))

            # It's already deleted?
            if cursor.rowcount == 0:
                return "The key is not available or may have been deleted previously."
            
            conn.commit()
            return True

    except sqlite3.Error as err:
        return f"Database error: {str(err)}"


# 
# Password manager
# 

# Get all user passwords
def get_user_password_all(user_id, master_key):
    query = "SELECT * FROM passwords WHERE user_id = ?"

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            cursor.execute(query, (user_id,))

            rows = cursor.fetchall()

            result = []

            for row in rows:
                # Combine iv + encrypted_key and unhexlify
                password_from_db = binascii.hexlify(
                    row["iv"] + row["encrypted_password"]
                ).decode()
                password_from_db = binascii.unhexlify(password_from_db)

                # Get valid key
                passwordKey = get_user_key(row["key_id"], user_id, master_key)

                result.append(
                    {
                        "password_id": row["password_id"],
                        "user_id": row["user_id"],
                        "key_id": row["key_id"],
                        "key_name": passwordKey["key_name"],
                        "service_name": row["service_name"],
                    }
                )

            return result

    except sqlite3.Error as err:
        return f"Database error: {str(err)}"


# Get user password
def get_user_password(password_id, user_id, master_key):
    query = "SELECT * FROM passwords WHERE password_id = ? AND user_id = ?"

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            cursor.execute(query, (password_id, user_id))

            password = cursor.fetchone()

            result = {}

            if password:
                # Combine iv + encrypted_key and unhexlify
                password_from_db = binascii.hexlify(
                    password["iv"] + password["encrypted_password"]
                ).decode()
                password_from_db = binascii.unhexlify(password_from_db)

                # Get valid key
                passwordKey = get_user_key(password["key_id"], user_id, master_key)
                valid_key = get_valid_key(passwordKey["encryption_key"])

                # Decrypt key
                decrypted_password = decrypt_aes(password_from_db, valid_key["encoded_key"])

                result = {
                    "password_id": password["password_id"],
                    "user_id": password["user_id"],
                    "key_id": password["key_id"],
                    "service_name": password["service_name"],
                    "username_account": password["username_account"],
                    "decrypted_password": decrypted_password,
                }

            return result

    except sqlite3.Error as err:
        return f"Database error: {str(err)}"


# Delete password
def delete_user_password(password_id):
    query = "DELETE FROM passwords WHERE password_id = ?"

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            cursor.execute(query, (password_id,))

            # It's already deleted?
            if cursor.rowcount == 0:
                return "The password is not available or may have been deleted previously."
            
            conn.commit()
            return True

    except sqlite3.Error as err:
        return f"Database error: {str(err)}"
import binascii
import os
import sqlite3

from src.encryptor import decrypt_aes, encrypt_aes, get_valid_key
from src.essentials import bcryptCheck, bcryptHashing

#
# User manager
#


class UserManager:
    def __init__(self, db_path=os.path.join("db", "vault_manager.db")):
        self.db_path = db_path

    # Register
    def register(self, name, username, password):
        query = "INSERT INTO users (name, username, password_hash) VALUES (?, ?, ?)"

        try:
            # hash the password first
            hashedPassword = bcryptHashing(password)

            # Insert into database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(query, (name, username, hashedPassword))

                user_id = cursor.lastrowid
                conn.commit()

            # Return the data
            userData = {"user_id": user_id, "name": name, "username": username}

            return userData

        except sqlite3.Error as err:
            return f"Database error: {str(err)}"

    # Authentication
    def authenticate(self, username, password):
        query = "SELECT * FROM users WHERE username = ?"

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(query, (username,))
                userdata = cursor.fetchone()

                if userdata:
                    # Check the password
                    valid = bcryptCheck(password, userdata["password_hash"])

                    if valid:
                        return "success", userdata
                    else:
                        return "fail", "Incorrect username or password!"

                # If username not found
                else:
                    return "fail", "Incorrect username or password!"

        except sqlite3.Error as err:
            return "error", f"Database error: {str(err)}"


#
# Key manager
#


class KeyManager:
    def __init__(self, db_path=os.path.join("db", "vault_manager.db")):
        self.db_path = db_path

    # Get all user key
    def get_user_key_all(self, user_id, master_key):
        query = "SELECT * FROM keys WHERE user_id = ?"

        try:
            with sqlite3.connect(self.db_path) as conn:
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
    def get_user_key(self, key_id, user_id, master_key):
        query = "SELECT * FROM keys WHERE key_id = ? AND user_id = ?"

        try:
            with sqlite3.connect(self.db_path) as conn:
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

    # Create key
    def create_user_key(self, keyName, theKey, user_id, session_key):
        query = "INSERT INTO keys (user_id, key_name, encrypted_key, iv) VALUES (?, ?, ?, ?)"

        try:
            # Encrypt the key
            master_key = get_valid_key(session_key)
            iv, encrypted_key = encrypt_aes(theKey, master_key["encoded_key"])

            # Insert into db
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(query, (user_id, keyName, encrypted_key, iv))

                conn.commit()

                return "success", f"Successfully added key: {keyName}"

        except sqlite3.Error as err:
            return "error", f"Database error: {str(err)}"

    # Delete key
    def delete_user_key(self, key_id):
        query = "DELETE FROM keys WHERE key_id = ?"

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")

                cursor.execute(query, (key_id,))

                # It's already deleted?
                if cursor.rowcount == 0:
                    return (
                        "success",
                        "The key is not available or may have been deleted previously.",
                    )

                conn.commit()
                return "success", "Key deleted successfully."

        except sqlite3.Error as err:
            return "error", f"Database error: {str(err)}"


#
# Password manager
#


class PasswordManager:
    def __init__(self, db_path=os.path.join("db", "vault_manager.db")):
        self.db_path = db_path

        # Create an instance from class KeyManager
        self.keys = KeyManager()

    # Get all user passwords
    def get_user_password_all(self, user_id, master_key):
        query = "SELECT * FROM passwords WHERE user_id = ?"

        try:
            with sqlite3.connect(self.db_path) as conn:
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
                    passwordKey = self.keys.get_user_key(
                        row["key_id"], user_id, master_key
                    )

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
    def get_user_password(self, password_id, user_id, master_key):
        query = "SELECT * FROM passwords WHERE password_id = ? AND user_id = ?"

        try:
            with sqlite3.connect(self.db_path) as conn:
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
                    passwordKey = self.keys.get_user_key(
                        password["key_id"], user_id, master_key
                    )
                    valid_key = get_valid_key(passwordKey["encryption_key"])

                    # Decrypt key
                    decrypted_password = decrypt_aes(
                        password_from_db, valid_key["encoded_key"]
                    )

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

    # Create password
    def create_user_password(
        self, serviceName, username, password, selectedKeyId, user_id, session_key
    ):
        query = "INSERT INTO passwords (user_id, key_id, service_name, username_account, encrypted_password, iv) VALUES (?, ?, ?, ?, ?, ?)"

        try:
            # Encrypt the password with selected key
            selected_key = self.keys.get_user_key(selectedKeyId, user_id, session_key)
            valid_selected_key = get_valid_key(selected_key["encryption_key"])
            iv, encrypted_password = encrypt_aes(
                password, valid_selected_key["encoded_key"]
            )

            # insert into db
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(
                    query,
                    (
                        user_id,
                        selectedKeyId,
                        serviceName,
                        username,
                        encrypted_password,
                        iv,
                    ),
                )

                conn.commit()

                return "success", f"Successfully added password: {serviceName}"

        except sqlite3.Error as err:
            return "error", f"Database error: {str(err)}"

    # Delete password
    def delete_user_password(self, password_id):
        query = "DELETE FROM passwords WHERE password_id = ?"

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")

                cursor.execute(query, (password_id,))

                # It's already deleted?
                if cursor.rowcount == 0:
                    return (
                        "success",
                        "The password is not available or may have been deleted previously.",
                    )

                conn.commit()
                return "success", "Password deleted successfully."

        except sqlite3.Error as err:
            return "error", f"Database error: {str(err)}"

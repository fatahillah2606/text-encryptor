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

        # Create an instance from class KeyManager
        self.keys = KeyManager()

    # Get availabel users
    def getAvailableUsers(self):
        query = "SElECT name, username FROM users"

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(query)

                rows = cursor.fetchall()

                result = []

                for row in rows:
                    result.append({"name": row["name"], "username": row["username"]})

                return result

        except sqlite3.Error as err:
            return f"An error occurred in the database. \nError message: {str(err)}"

    # Check user availablity
    def checkUsername(self, username):
        query = "SELECT username FROM users WHERE username = ?"

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(query, (username,))

                data = cursor.fetchone()

                if data:
                    return (
                        "failed",
                        "Username is already in use. Please try another one.",
                    )
                else:
                    return "success", "Username available!"

        except sqlite3.Error as err:
            return (
                "error",
                f"An error occurred in the database. \nError message: {str(err)}",
            )

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
            return f"An error occurred in the database. \nError message: {str(err)}"

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
                        return "fail", "Incorrect password. Please try again."

                # If username not found
                else:
                    return (
                        "fail",
                        "Username not found. Make sure you entered the correct username.",
                    )

        except sqlite3.Error as err:
            return (
                "error",
                f"An error occurred in the database. \nError message: {str(err)}",
            )

    # Update profile
    def updateProfile(self, user_id, updates):
        try:
            if not updates:
                return "failed", "No data provided."

            # Make a dynamic query
            set_clause = ", ".join([f"{column} = ?" for column in updates.keys()])
            values = list(updates.values())
            values.append(user_id)
            query = f"UPDATE users SET {set_clause} WHERE user_id = ?"

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(query, values)

                conn.commit()

            return "success", "Profile successfully updated."

        except sqlite3.Error as err:
            return (
                "error",
                f"An error occurred in the database. \nError message: {str(err)}",
            )

    # update password
    def updateProfilePassword(self, new_password, userId, currentPassword):
        try:
            # Get all keys made by user
            keyList = []

            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM keys WHERE user_id = ?"

                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")

                cursor.execute(query, (userId,))
                rows = cursor.fetchall()

                if rows:
                    for row in rows:
                        keyFromDb = binascii.hexlify(
                            row["iv"] + row["encrypted_key"]
                        ).decode()
                        keyFromDb = binascii.unhexlify(keyFromDb)

                        # get valid key
                        validKey = get_valid_key(currentPassword)

                        # Decrypt the key
                        decryptedKey = decrypt_aes(keyFromDb, validKey["encoded_key"])

                        keyList.append({"key_id": row["key_id"], "key": decryptedKey})

            # Proceed to change the password
            with sqlite3.connect(self.db_path) as conn:
                query = "UPDATE users SET password_hash = ? WHERE user_id = ?"

                hashedPw = bcryptHashing(new_password)

                # Save to database
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(query, (hashedPw, userId))
                conn.commit()

            # Re-encrypt the keys
            if keyList:
                for eachKey in keyList:
                    with sqlite3.connect(self.db_path) as conn:
                        query = "UPDATE keys SET encrypted_key = ?, iv = ? WHERE key_id = ? AND user_id = ?"

                        master_key = get_valid_key(new_password)
                        iv, encrypted_key = encrypt_aes(
                            eachKey["key"], master_key["encoded_key"]
                        )

                        cursor = conn.cursor()
                        cursor.execute("PRAGMA foreign_keys = ON;")
                        cursor.execute(
                            query, (encrypted_key, iv, eachKey["key_id"], userId)
                        )

                        conn.commit()

            return "success", "Password changed successfully"

        except sqlite3.Error as err:
            return (
                "error",
                f"An error occurred in the database. \nError message: {str(err)}",
            )

    # Import data
    # Key importing
    def import_keys(self, dataSheet, user_id, master_key):
        query = "INSERT INTO keys (user_id, key_name, encrypted_key, iv) VALUES (?, ?, ?, ?)"

        try:
            # Serialize the data
            keyName = dataSheet["key_name"]
            theKey = dataSheet["encryption_key"]

            # Encrypt the key
            master_key = get_valid_key(master_key)
            iv, encrypted_key = encrypt_aes(theKey, master_key["encoded_key"])

            # Insert into db
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(query, (user_id, keyName, encrypted_key, iv))

                key_id = cursor.lastrowid
                conn.commit()

                return "success", key_id

        except sqlite3.Error as err:
            return (
                "error",
                f"An error occurred in the database. \nError message: {str(err)}",
            )

    # Account importing
    def import_accounts(self, dataSheet, selectedKeyId, user_id, session_key):
        query = "INSERT INTO passwords (user_id, key_id, service_url, service_name, username_account, encrypted_password, iv, service_notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"

        try:
            # Serialize data
            serviceUrl = dataSheet["url"]
            serviceName = dataSheet["name"]
            username = dataSheet["username"]
            password = dataSheet["password"]
            serviceNotes = dataSheet["note"]

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
                        serviceUrl,
                        serviceName,
                        username,
                        encrypted_password,
                        iv,
                        serviceNotes,
                    ),
                )

                conn.commit()

        except sqlite3.Error as err:
            return (
                "error",
                f"An error occurred in the database. \nError message: {str(err)}",
            )

    # Export data
    def user_saved_keys(self, user_id, key):
        query = "SELECT * FROM keys WHERE user_id = ?"

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
                    key_from_db = binascii.hexlify(
                        row["iv"] + row["encrypted_key"]
                    ).decode()
                    key_from_db = binascii.unhexlify(key_from_db)

                    # Get valid key
                    valid_key = get_valid_key(key)

                    # Decrypt key
                    decrypted_key = decrypt_aes(key_from_db, valid_key["encoded_key"])

                    result.append(
                        {
                            "key_id": row["key_id"],
                            "key_name": row["key_name"],
                            "encryption_key": decrypted_key,
                        }
                    )

                return result

        except sqlite3.Error as err:
            return f"An error occurred in the database. \nError message: {str(err)}"

    def user_saved_accounts(self, user_id, key):
        try:
            query = "SELECT * FROM passwords WHERE user_id = ?"

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
                    passwordKey = self.keys.get_user_key(row["key_id"], user_id, key)
                    valid_key = get_valid_key(passwordKey["encryption_key"])

                    # Decrypt password
                    decrypted_password = decrypt_aes(
                        password_from_db, valid_key["encoded_key"]
                    )

                    result.append(
                        {
                            "password_id": row["password_id"],
                            "key_id": row["key_id"],
                            "name": row["service_name"],
                            "url": row["service_url"],
                            "username": row["username_account"],
                            "password": decrypted_password,
                            "note": row["service_notes"],
                        }
                    )

                return result

        except sqlite3.Error as err:
            return (
                "error",
                f"An error occurred in the database. \nError message: {str(err)}",
            )

    # Delete profile
    def deleteProfile(self, user_id):
        try:
            query = "DELETE FROM users WHERE user_id = ?"

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")

                cursor.execute(query, (user_id,))

                # It's already deleted?
                if cursor.rowcount == 0:
                    return (
                        "success",
                        "The profile is not available or may have been deleted previously.",
                    )

                conn.commit()
                return "success", "Profile successfully deleted."

        except sqlite3.Error as err:
            return (
                "error",
                f"An error occurred in the database. \nError message: {str(err)}",
            )


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
            return f"An error occurred in the database. \nError message: {str(err)}"

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
            return f"An error occurred in the database. \nError message: {str(err)}"

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
            return (
                "error",
                f"An error occurred in the database. \nError message: {str(err)}",
            )

    # Edit key
    def edit_user_key(self, key_id, keyName, theKey, user_id, session_key):
        try:
            # Get the current key first
            currentKey = self.get_user_key(key_id, user_id, session_key)

            # Get all user passwords releted to the key
            passwordList = []

            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM passwords WHERE key_id = ? AND user_id = ?"

                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")

                cursor.execute(query, (key_id, user_id))
                rows = cursor.fetchall()

                if rows:
                    for row in rows:
                        # Combine iv + encrypted_key and unhexlify
                        password_from_db = binascii.hexlify(
                            row["iv"] + row["encrypted_password"]
                        ).decode()
                        password_from_db = binascii.unhexlify(password_from_db)

                        # Make it valid
                        valid_key = get_valid_key(currentKey["encryption_key"])

                        # Decrypt password
                        decrypted_password = decrypt_aes(
                            password_from_db, valid_key["encoded_key"]
                        )

                        passwordList.append(
                            {
                                "password_id": row["password_id"],
                                "password": decrypted_password,
                            }
                        )

            # Now change the key
            newKey = ""

            with sqlite3.connect(self.db_path) as conn:
                query = "UPDATE keys SET key_name = ?, encrypted_key = ?, iv = ? WHERE key_id = ?"

                master_key = get_valid_key(session_key)
                iv, encrypted_key = encrypt_aes(theKey, master_key["encoded_key"])

                # Save to newKey
                newKey = binascii.hexlify(iv + encrypted_key).decode()
                newKey = binascii.unhexlify(newKey)

                # Save new key to database
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(query, (keyName, encrypted_key, iv, key_id))

                conn.commit()

            # Re-encrypt related password
            if passwordList:
                for eachPassword in passwordList:
                    with sqlite3.connect(self.db_path) as conn:
                        query = "UPDATE passwords SET encrypted_password = ?, iv = ? WHERE password_id = ?"

                        # Decrypt the key first
                        master_key = get_valid_key(session_key)
                        decrypted_key = decrypt_aes(newKey, master_key["encoded_key"])

                        # Encrypt the password
                        validate_key = get_valid_key(decrypted_key)
                        iv, encrypted_password = encrypt_aes(
                            eachPassword["password"], validate_key["encoded_key"]
                        )

                        # Insert the re-encrypted password
                        cursor = conn.cursor()
                        cursor.execute("PRAGMA foreign_keys = ON;")
                        cursor.execute(
                            query, (encrypted_password, iv, eachPassword["password_id"])
                        )

                        conn.commit()

            return "success", f"Successfully edited key: {keyName}"

        except sqlite3.Error as err:
            return (
                "error",
                f"An error occurred in the database. \nError message: {str(err)}",
            )

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
            return (
                "error",
                f"An error occurred in the database. \nError message: {str(err)}",
            )


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
            return f"An error occurred in the database. \nError message: {str(err)}"

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

                    # Decrypt password
                    decrypted_password = decrypt_aes(
                        password_from_db, valid_key["encoded_key"]
                    )

                    # Prevent material-web error: length undefined
                    service_url = (
                        password["service_url"] if password["service_url"] else ""
                    )
                    service_notes = (
                        password["service_notes"] if password["service_notes"] else ""
                    )

                    result = {
                        "password_id": password["password_id"],
                        "user_id": password["user_id"],
                        "key_id": password["key_id"],
                        "service_url": service_url,
                        "service_name": password["service_name"],
                        "username_account": password["username_account"],
                        "decrypted_password": decrypted_password,
                        "service_note": service_notes,
                    }

                return result

        except sqlite3.Error as err:
            return f"An error occurred in the database. \nError message: {str(err)}"

    # Create password
    def create_user_password(
        self,
        serviceUrl,
        serviceName,
        username,
        password,
        serviceNotes,
        selectedKeyId,
        user_id,
        session_key,
    ):
        query = "INSERT INTO passwords (user_id, key_id, service_url, service_name, username_account, encrypted_password, iv, service_notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"

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
                        serviceUrl,
                        serviceName,
                        username,
                        encrypted_password,
                        iv,
                        serviceNotes,
                    ),
                )

                conn.commit()

                return "success", f"Successfully added password: {serviceName}"

        except sqlite3.Error as err:
            return (
                "error",
                f"An error occurred in the database. \nError message: {str(err)}",
            )

    # Edit password
    def edit_user_password(
        self,
        serviceUrl,
        serviceName,
        username,
        password,
        serviceNotes,
        selectedKeyId,
        user_id,
        session_key,
        password_id,
    ):
        query = "UPDATE passwords SET key_id = ?, service_url = ?, service_name = ?, username_account = ?, encrypted_password = ?, iv = ?, service_notes = ? WHERE password_id = ?"

        try:
            # Encrypt the password with selected key
            selected_key = self.keys.get_user_key(selectedKeyId, user_id, session_key)
            valid_selected_key = get_valid_key(selected_key["encryption_key"])
            iv, encrypted_password = encrypt_aes(
                password, valid_selected_key["encoded_key"]
            )

            # Insert into db
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(
                    query,
                    (
                        selectedKeyId,
                        serviceUrl,
                        serviceName,
                        username,
                        encrypted_password,
                        iv,
                        serviceNotes,
                        password_id,
                    ),
                )

                conn.commit()

                return "success", f"Successfully edited password: {serviceName}"

        except sqlite3.Error as err:
            return (
                "error",
                f"An error occurred in the database. \nError message: {str(err)}",
            )

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
            return (
                "error",
                f"An error occurred in the database. \nError message: {str(err)}",
            )

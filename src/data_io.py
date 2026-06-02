import base64
import csv
import io
import json
import os
from datetime import datetime, timezone

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2

from src.data_manager import UserManager


# Importer
class DataImporter:
    def __init__(self):
        self.usermgr = UserManager()

    # Derive key from user password
    def _derive_key(self, password: str, salt: bytes, iterations: int) -> bytes:
        return PBKDF2(
            password=password,
            salt=salt,
            dkLen=32,
            count=iterations,
            hmac_hash_module=SHA256,
        )

    # Decrypt the data
    def decrypt_data(self, json_data, password: str) -> list:
        metadata = json_data["metadata"]
        payload = json_data["payload"]

        # Extract KDF parameters from metadata
        kdf_info = metadata["kdf_info"]
        iterations = kdf_info["iterations"]
        salt = base64.b64decode(kdf_info["salt"])

        # Regenerate the cryptographic key using the provided password
        stretched_key = self._derive_key(password, salt, iterations)

        # Extract cryptographic components from payload
        nonce = base64.b64decode(payload["nonce"])
        combined_payload = base64.b64decode(payload["ciphertext"])

        # Split the 16-byte authentication tag from the end of the ciphertext
        ciphertext = combined_payload[:-16]
        tag = combined_payload[-16:]

        # Initialize the cipher and decrypt
        cipher = AES.new(stretched_key, AES.MODE_GCM, nonce=nonce)

        try:
            # decrypt_and_verify
            plaintext_bytes = cipher.decrypt_and_verify(ciphertext, tag)

            # Return the data
            parsed_data = json.loads(plaintext_bytes.decode("utf-8"))
            return "success", parsed_data

        except ValueError:
            return (
                "error",
                "The encryption password is incorrect or the data is corrupted. Ensure the password is correct and try again.",
            )

    # Import into database
    def import_into_db(self, json_data, user_id, master_key):
        try:
            keys = json_data.get("keys", [])
            passwords = json_data.get("passwords", [])

            # Group the passwords
            passwords_by_key = {}

            for pw_data in passwords:
                json_key_id = pw_data.get("key_id")

                if json_key_id not in passwords_by_key:
                    passwords_by_key[json_key_id] = []

                passwords_by_key[json_key_id].append(pw_data)

            # Process keys and their matching passwords
            for key_data in keys:
                json_key_id = key_data.get("key_id")

                # Insert the key into db
                status, db_key_id = self.usermgr.import_keys(
                    key_data, user_id, master_key
                )

                if status == "success":
                    # Retrieve only the passwords that belong to this specific key
                    matching_passwords = passwords_by_key.get(json_key_id, [])

                    for pw_data in matching_passwords:
                        self.usermgr.import_accounts(
                            pw_data, db_key_id, user_id, master_key
                        )

            return "success", ""

        except Exception as err:
            return "error", str(err)

    # Compatibility mode import (csv)
    def process_csv(self, csv_data):
        if csv_data.startswith("\ufeff"):
            csv_data = csv_data.lstrip("\ufeff")

        csv_file = io.StringIO(csv_data)

        # Use DictReader to automatically map the header row to keys
        reader = csv.DictReader(csv_file)

        # Target headers
        expected_headers = {"name", "url", "username", "password", "note"}

        # Quick validation check on headers
        if not reader.fieldnames or not expected_headers.issubset(
            set(reader.fieldnames)
        ):
            return (
                "error",
                "CSV format is not supported. Make sure the CSV file you attach contains name, url, username, password and note columns.",
            )

        parsed_passwords = []

        # Create dict/json
        for row in reader:
            parsed_passwords.append(
                {
                    "name": row.get("name", "").strip(),
                    "url": row.get("url", "").strip(),
                    "username": row.get("username", "").strip(),
                    "password": row.get("password", ""),
                    "note": row.get("note", "").strip(),
                }
            )

        return "success", parsed_passwords


# Exporter
class DataExporter:
    def __init__(self, version: str = "2.2.5"):
        self.version = version

    # For generating header/metadata
    def _generate_metadata(self, is_encrypted: bool, salt: bytes = None) -> dict:
        metadata = {
            "version": self.version,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "export_type": "secure_json",
            "encrypted": is_encrypted,
            "crypto_algorithm": "AES-256-GCM" if is_encrypted else "None",
        }
        if is_encrypted and salt:
            metadata["kdf_info"] = {
                "algorithm": "PBKDF2-HMAC-SHA256",
                "iterations": 600000,
                "salt": base64.b64encode(salt).decode("utf-8"),
            }
        return metadata

    # Derives a secure 256-bit key from user password
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        return PBKDF2(
            password=password,
            salt=salt,
            dkLen=32,
            count=600000,
            hmac_hash_module=SHA256,
        )

    # Export data without encryption
    def export_unencrypted(self, vault_items: list) -> str:
        output = {}
        keys = []
        passwords = []

        # Loop the keys
        for key in vault_items["keys"]:
            keys.append(
                {
                    "key_id": key["key_id"],
                    "key_name": key["key_name"],
                    "encryption_key": key["encryption_key"],
                }
            )

        # Loop the passwords
        for password in vault_items["passwords"]:
            passwords.append(
                {
                    "password_id": password["password_id"],
                    "key_id": password["key_id"],
                    "name": password["name"],
                    "url": password["url"],
                    "username": password["username"],
                    "password": password["password"],
                    "note": password["note"],
                }
            )

        # Serialize data
        output = {
            "metadata": self._generate_metadata(is_encrypted=False),
            "vault": {"keys": keys, "passwords": passwords},
        }

        return json.dumps(output, indent=4)

    # Export the data with encryption
    def export_encrypted(self, vault_items: list, encrypt_pw: str) -> str:
        keys = []
        passwords = []

        # Loop the keys
        for key in vault_items["keys"]:
            keys.append(
                {
                    "key_id": key["key_id"],
                    "key_name": key["key_name"],
                    "encryption_key": key["encryption_key"],
                }
            )

        # Loop the passwords
        for password in vault_items["passwords"]:
            passwords.append(
                {
                    "password_id": password["password_id"],
                    "key_id": password["key_id"],
                    "name": password["name"],
                    "url": password["url"],
                    "username": password["username"],
                    "password": password["password"],
                    "note": password["note"],
                }
            )

        # Generate random salt
        salt = os.urandom(16)

        # Derive key from password
        stretched_key = self._derive_key(encrypt_pw, salt)

        # Serialize data
        plaintext_vault = json.dumps({"keys": keys, "passwords": passwords}).encode(
            "utf-8"
        )

        # Initialize AES-GCM cipher
        nonce = os.urandom(12)
        cipher = AES.new(stretched_key, AES.MODE_GCM, nonce=nonce)

        # encrypt_and_digest generates both ciphertext and the integrity tag
        ciphertext, tag = cipher.encrypt_and_digest(plaintext_vault)

        # Build final payload.
        combined_payload = ciphertext + tag

        output = {
            "metadata": self._generate_metadata(is_encrypted=True, salt=salt),
            "payload": {
                "nonce": base64.b64encode(nonce).decode("utf-8"),
                "ciphertext": base64.b64encode(combined_payload).decode("utf-8"),
            },
        }
        return json.dumps(output, indent=4)

    # Compatibility mode export (csv)
    def export_csv(self, user_passwords):
        # Create in-memory string buffer
        output = io.StringIO()
        headers = ["name", "url", "username", "password", "note"]

        # Write into csv format
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for eachUsrPw in user_passwords:
            writer.writerow(eachUsrPw)

        # Return the result
        result = {"file_type": "csv", "data_sheet": output.getvalue()}
        return result

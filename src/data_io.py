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


# ========== Importer ==========
class DataImporter:
    def __init__(self):
        self._ITERATIONS = 600000
        self.usermgr = UserManager()

    # ========== Derive key from user password ==========
    def _derive_key(self, password: str, salt: bytes, iterations: int) -> bytes:
        return PBKDF2(
            password=password,
            salt=salt,
            dkLen=32,
            count=iterations,
            hmac_hash_module=SHA256,
        )

    # ========== Decrypt the data ==========
    def decrypt_data(self, json_data, password: str) -> list:
        payload = base64.b64decode(json_data["data"])

        # Extract KDF parameters from metadata
        iterations = self._ITERATIONS
        salt = payload[-24:-8]

        # Regenerate the cryptographic key using the provided password
        stretched_key = self._derive_key(password, salt, iterations)

        # Extract cryptographic components from payload
        nonce = payload[54:66]

        # Split authentication tag from the end of the ciphertext
        ciphertext = payload[94:-41]
        tag = payload[32:48]

        # Initialize the cipher and decrypt
        cipher = AES.new(stretched_key, AES.MODE_GCM, nonce=nonce)

        try:
            # decrypt_and_verify
            plaintext_bytes = cipher.decrypt_and_verify(ciphertext, tag)

            # Return the data
            parsed_data = json.loads(plaintext_bytes.decode("utf-8"))
            return "SUCCESS", 200, parsed_data

        except ValueError:
            return (
                "INCORRECT_PASSWORD",
                401,
                "The encryption password is incorrect. Ensure the password is correct and try again.",
            )

    # ========== Import into database ==========
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
                status, code, db_key_id = self.usermgr.import_keys(
                    key_data, user_id, master_key
                )

                if status == "SUCCESS":
                    # Retrieve only the passwords that belong to this specific key
                    matching_passwords = passwords_by_key.get(json_key_id, [])

                    for pw_data in matching_passwords:
                        self.usermgr.import_accounts(
                            pw_data, db_key_id, user_id, master_key
                        )

            return "SUCCESS", 200, "Successfully imported to the database."

        except Exception as err:
            return "SERVER_ERROR", 500, str(err)

    # ========== Compatibility mode import (csv) ==========
    def process_csv(self, csv_data):
        if csv_data.startswith("\ufeff"):
            csv_data = csv_data.lstrip("\ufeff")

        csv_file = io.StringIO(csv_data)

        # Use DictReader to automatically map the header row to keys
        reader = csv.DictReader(csv_file)

        # Target headers
        chromium_based = {"name", "url", "username", "password", "note"}
        firefox = {
            "url",
            "username",
            "password",
            "httpRealm",
            "formActionOrigin",
            "guid",
            "timeCreated",
            "timeLastUsed",
            "timePasswordChanged",
        }

        # Quick validation check on headers
        if not reader.fieldnames:
            return (
                "UNSUPPORTED_FILE",
                400,
                "CSV format is not supported. Make sure the CSV file you select is from a Chromium-based browser, Firefox, or Sunako.",
            )

        parsed_passwords = []

        # For chromium based
        if chromium_based.issubset(set(reader.fieldnames)):
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

        # For Firefox browser
        elif firefox.issubset(set(reader.fieldnames)):
            for row in reader:
                parsed_passwords.append(
                    {
                        "name": row.get("url", "").strip(),
                        "url": row.get("formActionOrigin", "").strip(),
                        "username": row.get("username", "").strip(),
                        "password": row.get("password", ""),
                        "note": "",
                    }
                )

        else:
            return (
                "UNSUPPORTED_FORMAT",
                400,
                "CSV format is not supported. Make sure the CSV file you select is from a Chromium-based browser, Firefox, or Sunako.",
            )

        return "SUCCESS", 200, parsed_passwords


# ========== Exporter ==========
class DataExporter:
    def __init__(self, version: str = "2.3.0"):
        self.version = version
        self._ITERATIONS = 600000

    # ========== For generating header/metadata ==========
    def _generate_metadata(self, is_encrypted: bool, salt: bytes = None) -> dict:
        metadata = {
            "version": self.version,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "export_type": "secure_json",
            "encrypted": is_encrypted,
        }
        return metadata

    # ========== Derives a secure 256-bit key from user password ==========
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        return PBKDF2(
            password=password,
            salt=salt,
            dkLen=32,
            count=600000,
            hmac_hash_module=SHA256,
        )

    # ========== Export data without encryption ==========
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
            "data": {"keys": keys, "passwords": passwords},
        }

        return json.dumps(output, indent=4)

    # ========== Export the data with encryption ==========
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

        # Abydos Foreclosure Task Force
        hoshino = os.urandom(32)
        nonomi = os.urandom(6)
        shiroko = os.urandom(12)
        kuroko = os.urandom(16)
        serika = os.urandom(12)
        ayane = os.urandom(5)
        sensei = os.urandom(8)

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

        # Protect the vault with Foreclosure Task Force team.
        combined_payload = (
            hoshino
            + tag
            + nonomi
            + nonce
            + shiroko
            + kuroko
            + ciphertext
            + serika
            + ayane
            + salt
            + sensei
        )

        output = {
            "metadata": self._generate_metadata(is_encrypted=True, salt=salt),
            "data": base64.b64encode(combined_payload).decode("utf-8"),
        }
        return json.dumps(output, indent=4)

    # ========== Compatibility mode export (csv) ==========
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

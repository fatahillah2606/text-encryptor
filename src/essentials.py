import base64
import binascii
import hashlib
import hmac
import json
import os
import time
import zlib
from datetime import datetime, timedelta, timezone

from flask import session

from src.encryptor import NewEncryption


# bcrypt hashing
def scryptHashing(text):
    salt = os.urandom(16)
    hashed_bytes = hashlib.scrypt(text.encode("utf-8"), salt=salt, n=16384, r=8, p=1)
    return salt + hashed_bytes


# bcrypt check
def scryptCheck(text, hashedText):
    try:
        salt = hashedText[:16]
        original_hash = hashedText[16:]

        new_hash = hashlib.scrypt(text.encode("utf-8"), salt=salt, n=16384, r=8, p=1)

        return hmac.compare_digest(original_hash, new_hash)
    except Exception:
        return False


# Create login session
def createLoginSession(user_id, name, username, key):
    session.permanent = True
    session["expired"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    session["user_id"] = user_id
    session["name"] = name
    session["username"] = username
    session["key"] = key


# Generate share link
linkEncryptor = NewEncryption()


def generate_share_link(raw_text):
    current_time = int(time.time())
    expiration_time = current_time + 300  # 5 minutes

    # Generate one time key
    one_time_key = os.urandom(16).hex()

    # Encrypt the raw text
    validate_key = linkEncryptor.get_valid_key(one_time_key)
    vi, encrypted_text = linkEncryptor.encrypt_aes(
        raw_text, validate_key["encoded_key"]
    )
    encrypted_text = binascii.hexlify(vi + encrypted_text).decode()

    # Generate payload
    payload = {"d": encrypted_text, "e": expiration_time}

    # Serialize and Compress the raw layout
    serialized = json.dumps(payload).encode("utf-8")
    compressed = zlib.compress(serialized)

    # Convert ciphertext to a clean URL parameter
    blob = base64.urlsafe_b64encode(compressed).decode("utf-8")

    # Assemble the definitive uniform link mapping
    share_url = f"http://127.0.0.1:5000/t/{blob}#{one_time_key}"
    return share_url


# Decrypt payload
def decrypt_payload(ciphertext_b64, key):
    # Decode URL-safe base64 and decompress
    compressed_data = base64.urlsafe_b64decode(ciphertext_b64)
    decrypted_json_bytes = zlib.decompress(compressed_data)

    # Convert to dictionary and decrypt the content
    try:
        data = json.loads(decrypted_json_bytes.decode('utf-8'))

        # Check the expired time first
        current_time = int(time.time())
        if current_time > data["e"]:
            return "expired", "The link has expired"

        valid_key = linkEncryptor.get_valid_key(key)
        convert_content = binascii.unhexlify(data["d"])
        decrypted_content = linkEncryptor.decrypt_aes(convert_content, valid_key["encoded_key"])

        return "success", decrypted_content

    except Exception as err:
        return "error", f"An error occurred when decrypting.\n Error message: {err}"

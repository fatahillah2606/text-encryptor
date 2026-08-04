import binascii
import gc
import hashlib
import hmac
import os
import random
import string
import struct
from pathlib import Path
from urllib.parse import quote

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from flask import Response, stream_with_context

# Set 'tmp' folder relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = PROJECT_ROOT / "tmp"

# Ensure the tmp directory exists on startup
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def get_secure_temp_path(prefix="file"):
    """Generate a unique temporary path inside the root 'tmp' folder."""
    filename = f"{prefix}_{os.urandom(8).hex()}.tmp"
    return str(TEMP_DIR / filename)


def cleanup_temp_file(path):
    """Safely delete the temporary file and force Python garbage collection."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
            gc.collect()
    except Exception as e:
        print(f"[TMP CLEANUP] Failed to delete {path}: {e}")


# AES-128 Encryption
class OldEncryption:
    def __init__(self) -> None:
        pass

    # Get valid key from user input
    def get_valid_key(self, user_key):
        if not user_key:  # If empty, make new one
            generate_key = binascii.hexlify(
                get_random_bytes(16)
            ).decode()  # Create 16 byte key (AES-128)
            generated_key = generate_key
            key = generate_key.ljust(16)[:16].encode()

        else:
            generated_key = user_key
            key = user_key.ljust(16)[:16].encode()  # Make sure the length is 16

        valid_key = {"encoded_key": key, "generated_key": generated_key}
        return valid_key

    # Encryptor
    def encrypt_aes(self, text, key):
        cipher = AES.new(key, AES.MODE_CBC)
        iv = cipher.iv  # Initialization Vector
        encrypted_message = cipher.encrypt(pad(text.encode(), AES.block_size))
        return iv, encrypted_message

    # Decryptor
    def decrypt_aes(self, text, key):
        iv = text[:16]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_message = unpad(cipher.decrypt(text[16:]), AES.block_size)
        return decrypted_message.decode()


# AES-256 Encryption
class NewEncryption:
    def __init__(self) -> None:
        pass

    # Get valid key from user input
    def get_valid_key(self, user_key):
        if not user_key:
            generate_key = binascii.hexlify(get_random_bytes(32)).decode()
            generated_key = generate_key
            key = generate_key.ljust(32)[:32].encode()

        else:
            generated_key = user_key
            key = user_key.ljust(32)[:32].encode()

        valid_key = {"encoded_key": key, "generated_key": generated_key}
        return valid_key

    # Encryptor
    def encrypt_aes(self, text, key):
        cipher = AES.new(key, AES.MODE_CBC)
        iv = cipher.iv
        encrypted_message = cipher.encrypt(pad(text.encode(), AES.block_size))
        return iv, encrypted_message

    # Decryptor
    def decrypt_aes(self, text, key):
        iv = text[:16]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_message = unpad(cipher.decrypt(text[16:]), AES.block_size)
        return decrypted_message.decode()


class FileEncryptor:
    def __init__(self) -> None:
        pass

    def encrypt_file(self, file, password):
        # Save to project's /tmp directory
        temp_path = get_secure_temp_path("encrypt")
        file.save(temp_path)

        try:
            # Prepare keys
            salt = os.urandom(16)
            key = PBKDF2(
                password, salt, dkLen=32, count=100000, hmac_hash_module=SHA256
            )
            cipher = AES.new(key, AES.MODE_CTR)

            hmac_key = PBKDF2(
                password,
                salt + b"hmac",
                dkLen=32,
                count=100000,
                hmac_hash_module=SHA256,
            )
            h = hmac.new(hmac_key, digestmod=hashlib.sha256)

            # Encode metadata & random padding
            original_filename = file.filename or "file"
            encoded_filename = original_filename.encode("utf-8")
            filename_length = len(encoded_filename)

            # Generate 16 to 64 bytes of random header padding
            padding_len = int.from_bytes(os.urandom(1), "big") % 49 + 16
            random_padding = os.urandom(padding_len)

            # Pack header:
            magic = b"SUNAKO"
            header_metadata = (
                magic
                + bytes([padding_len])
                + random_padding
                + salt
                + cipher.nonce
                + struct.pack(">H", filename_length)
                + encoded_filename
            )

            def generate_stream():
                try:
                    # Yield Header Metadata
                    h.update(header_metadata)
                    yield header_metadata

                    # Stream Encrypted File Contents
                    chunk_size = 64 * 1024
                    with open(temp_path, "rb") as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break

                            encrypted_chunk = cipher.encrypt(chunk)
                            h.update(encrypted_chunk)
                            yield encrypted_chunk

                    # Yield Final HMAC Signature
                    yield h.digest()

                finally:
                    cleanup_temp_file(temp_path)

            # Fix foreign language characters
            output_filename = f"encrypted_{original_filename}.sunako"
            utf8_filename = quote(output_filename)
            ascii_fallback = (
                output_filename.encode("ascii", "ignore").decode("ascii")
                or "encrypted_file.sunako"
            )
            content_disposition = f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{utf8_filename}"

            response = Response(
                stream_with_context(generate_stream()),
                mimetype="application/octet-stream",
            )
            response.headers["Content-Disposition"] = content_disposition
            return "success", response

        except Exception as e:
            cleanup_temp_file(temp_path)
            return "error", str(e)

    def decrypt_file(self, file, password):
        # Tempoary save the file
        temp_path = get_secure_temp_path("decrypt")
        file.save(temp_path)

        try:
            file_size = os.path.getsize(temp_path)

            # Minimum valid size check:
            if file_size < 82:
                cleanup_temp_file(temp_path)
                return "error", "Invalid or corrupted file"

            with open(temp_path, "rb") as f:
                # Verify Magic Signature
                magic = f.read(6)
                if magic != b"SUNAKO":
                    cleanup_temp_file(temp_path)
                    return "error", "Invalid file format. Not a .sunako file."

                # Read Random Padding Length & Skip Padding
                padding_len = int.from_bytes(f.read(1), "big")
                random_padding = f.read(padding_len)

                # Extract Salt & Nonce
                salt = f.read(16)
                nonce = f.read(8)

                # Extract Filename Metadata
                filename_len = struct.unpack(">H", f.read(2))[0]
                original_filename_bytes = f.read(filename_len)

                try:
                    restored_filename = original_filename_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    restored_filename = "decrypted_file"

                # Reconstruct the header bytes read so far to verify HMAC
                header_metadata = (
                    magic
                    + bytes([padding_len])
                    + random_padding
                    + salt
                    + nonce
                    + struct.pack(">H", filename_len)
                    + original_filename_bytes
                )

                # Verify HMAC Signature
                ciphertext_length = file_size - len(header_metadata) - 32
                if ciphertext_length < 0:
                    cleanup_temp_file(temp_path)
                    return "error", "Corrupted file header"

                f.seek(file_size - 32)
                expected_hmac = f.read(32)

                # Compute HMAC across Header + Ciphertext
                hmac_key = PBKDF2(
                    password,
                    salt + b"hmac",
                    dkLen=32,
                    count=100000,
                    hmac_hash_module=SHA256,
                )
                h = hmac.new(hmac_key, digestmod=hashlib.sha256)
                h.update(header_metadata)

                f.seek(len(header_metadata))
                chunk_size = 64 * 1024
                bytes_to_read = ciphertext_length

                while bytes_to_read > 0:
                    read_amount = min(chunk_size, bytes_to_read)
                    chunk = f.read(read_amount)
                    h.update(chunk)
                    bytes_to_read -= len(chunk)

                # If HMAC fails, wrong key or file was modified
                if not hmac.compare_digest(h.digest(), expected_hmac):
                    cleanup_temp_file(temp_path)
                    return "error", "Incorrect decryption key"

            # Key derivation & Cipher setup for Streaming Decryption
            key = PBKDF2(
                password, salt, dkLen=32, count=100000, hmac_hash_module=SHA256
            )
            cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)

            def generate_decrypted_stream():
                try:
                    chunk_size = 64 * 1024
                    with open(temp_path, "rb") as f:
                        # Skip header
                        f.seek(len(header_metadata))
                        bytes_remaining = ciphertext_length

                        while bytes_remaining > 0:
                            read_amount = min(chunk_size, bytes_remaining)
                            chunk = f.read(read_amount)
                            if not chunk:
                                break

                            decrypted_chunk = cipher.decrypt(chunk)
                            bytes_remaining -= len(chunk)
                            yield decrypted_chunk
                finally:
                    cleanup_temp_file(temp_path)

            # Fix foreign language characters
            utf8_filename = quote(restored_filename)
            name_part, ext_part = os.path.splitext(restored_filename)
            clean_ascii_name = (
                name_part.encode("ascii", "ignore").decode("ascii").strip()
            )
            ascii_fallback = f"{clean_ascii_name or 'decrypted_file'}{ext_part}"
            content_disposition = f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{utf8_filename}"

            response = Response(
                stream_with_context(generate_decrypted_stream()),
                mimetype="application/octet-stream",
            )
            response.headers["Content-Disposition"] = content_disposition
            return "success", response

        except Exception as e:
            cleanup_temp_file(temp_path)
            return "error", str(e)


# Password Generator
def generate_password(passLenth):
    try:
        characters = string.ascii_letters + string.digits + string.punctuation
        password = "".join(random.choice(characters) for i in range(int(passLenth)))
        return password

    except ValueError:
        return "The password length value must be numeric."

    except Exception as error:
        return error

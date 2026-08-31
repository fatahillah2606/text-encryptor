import gc
import os
import struct
from pathlib import Path
from urllib.parse import quote

from colorama import Fore, Style
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes
from flask import Response, stream_with_context

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = PROJECT_ROOT / "tmp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

MAGIC_BYTES = b"SNK1"


# ========== Encoder ==========
class StegoEncoder:
    @staticmethod
    def get_secure_temp_path(prefix="stego") -> str:
        # Generate a unique temporary path inside the root 'tmp' folder.
        filename = f"{prefix}_{os.urandom(8).hex()}.tmp"
        return str(TEMP_DIR / filename)

    @staticmethod
    def cleanup_temp_file(path: str):
        # Safely delete the temporary file and force Python garbage collection.
        try:
            if path and os.path.exists(path):
                os.remove(path)
                gc.collect()

        except Exception as e:
            print(f"[{Fore.YELLOW}TMP CLEANUP{Style.RESET_ALL}] Failed to delete {path}: {e}")

    @staticmethod
    def prepare_payload(data_bytes: bytes, filename: str = "") -> bytes:
        # Packs metadata with foreign character support and random padding.
        filename_bytes = filename.encode("utf-8")
        filename_len = len(filename_bytes)
        data_len = len(data_bytes)

        padding_len = int.from_bytes(get_random_bytes(1), "big") % 49 + 16
        padding = get_random_bytes(padding_len)

        header = struct.pack(">HQI", filename_len, data_len, padding_len)
        return header + filename_bytes + data_bytes + padding

    @classmethod
    def build_stego_block(cls, raw_payload: bytes, password: str = None) -> bytes:
        # Builds the stego binary block, applying AES-256-GCM only if a password is provided.
        if password:
            is_encrypted = b"\x01"
            salt = get_random_bytes(16)
            key = scrypt(password.encode("utf-8"), salt, key_len=32, N=2**14, r=8, p=1)

            # Force a standard 12-byte (96-bit) nonce
            nonce = get_random_bytes(12)
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            ciphertext, tag = cipher.encrypt_and_digest(raw_payload)

            payload_size = len(ciphertext)
            # Total header size = 4B (MAGIC) + 1B (FLAG) + 16B (SALT) + 12B (NONCE) + 16B (TAG) + 4B (SIZE) = 53 bytes
            header = (
                MAGIC_BYTES
                + is_encrypted
                + salt
                + nonce
                + tag
                + struct.pack(">I", payload_size)
            )
            return header + ciphertext

        else:
            is_encrypted = b"\x00"
            payload_size = len(raw_payload)
            header = MAGIC_BYTES + is_encrypted + struct.pack(">I", payload_size)
            return header + raw_payload

    @classmethod
    def hide_secret(
        cls,
        media_carrier,
        secret_type: str,
        secret_message: str = None,
        secret_file=None,
        password: str = None,
    ):

        # Main entry point for API call.
        # Processes inputs, creates temp files, appends stego block, and returns a streaming Flask Response.

        temp_carrier_path = cls.get_secure_temp_path(prefix="carrier")
        temp_output_path = None

        try:
            # Save uploaded carrier file to disk
            media_carrier.save(temp_carrier_path)

            # Extract payload bytes based on type
            if secret_type == "text":
                payload_bytes = (secret_message or "").encode("utf-8")
                filename = "secret_message.txt"

            elif secret_type == "file" and secret_file:
                payload_bytes = secret_file.read()
                filename = secret_file.filename or "secret_file.bin"

            else:
                cls.cleanup_temp_file(temp_carrier_path)
                return (
                    "INVALID",
                    400,
                    "Invalid or missing secret payload. Make sure you provide the text or files you want to hide.",
                )

            # Build stego block and prepare output file path
            raw_payload = cls.prepare_payload(payload_bytes, filename)
            stego_block = cls.build_stego_block(raw_payload, password)

            carrier_ext = os.path.splitext(media_carrier.filename)[1] or ".bin"
            temp_output_path = (
                cls.get_secure_temp_path(prefix="stego_out") + carrier_ext
            )

            # Copy carrier and append EOF payload
            with (
                open(temp_carrier_path, "rb") as f_in,
                open(temp_output_path, "wb") as f_out,
            ):
                while chunk := f_in.read(65536):
                    f_out.write(chunk)
                f_out.write(stego_block)

            # Define streaming generator with automatic file deletion
            def generate():
                with open(temp_output_path, "rb") as f:
                    while chunk := f.read(65536):
                        yield chunk
                cls.cleanup_temp_file(temp_output_path)

            # Cleanup input carrier immediately
            cls.cleanup_temp_file(temp_carrier_path)

            # Fix foreign language characters
            utf8_filename = quote(media_carrier.filename)
            ascii_fallback = (
                media_carrier.filename.encode("ascii", "ignore").decode("ascii").strip()
            )
            content_disposition = f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{utf8_filename}"

            response = Response(
                stream_with_context(generate()),
                mimetype=media_carrier.mimetype or "application/octet-stream",
            )
            response.headers["Content-Disposition"] = content_disposition
            return "SUCCESS", 400, response

        except Exception as e:
            cls.cleanup_temp_file(temp_carrier_path)

            if temp_output_path:
                cls.cleanup_temp_file(temp_output_path)

            return "SERVER_ERROR", 500, str(e)


# ========== Decoder ==========
class StegoDecoder:
    @staticmethod
    def get_secure_temp_path(prefix="stego_dec") -> str:
        filename = f"{prefix}_{os.urandom(8).hex()}.tmp"
        return str(TEMP_DIR / filename)

    @staticmethod
    def cleanup_temp_file(path: str):
        try:
            if path and os.path.exists(path):
                os.remove(path)
                gc.collect()

        except Exception as e:
            print(f"[{Fore.YELLOW}TMP CLEANUP{Style.RESET_ALL}] Failed to delete {path}: {e}")

    @classmethod
    def unpack_payload(cls, raw_payload: bytes) -> tuple[str, bytes]:
        # Parses header structure
        filename_len, data_len, padding_len = struct.unpack(">HQI", raw_payload[:14])

        offset = 14
        filename_bytes = raw_payload[offset : offset + filename_len]
        filename = filename_bytes.decode("utf-8", errors="replace")

        offset += filename_len
        content_bytes = raw_payload[offset : offset + data_len]

        return filename, content_bytes

    @classmethod
    def decrypt_stego_block(cls, encrypted_block: bytes, password: str) -> bytes:
        salt = encrypted_block[:16]
        nonce = encrypted_block[16:28]
        tag = encrypted_block[28:44]
        payload_size = struct.unpack(">I", encrypted_block[44:48])[0]

        # Exact ciphertext block
        ciphertext = encrypted_block[48 : 48 + payload_size]

        key = scrypt(password.encode("utf-8"), salt, key_len=32, N=2**14, r=8, p=1)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

        return cipher.decrypt_and_verify(ciphertext, tag)

    @classmethod
    def reveal_secret(cls, media_carrier, password: str = None):
        temp_carrier_path = cls.get_secure_temp_path(prefix="carrier_dec")

        try:
            media_carrier.save(temp_carrier_path)

            with open(temp_carrier_path, "rb") as f:
                file_bytes = f.read()

            # Find Magic Bytes SNK1 from the back
            magic_idx = file_bytes.rfind(MAGIC_BYTES)
            if magic_idx == -1:
                cls.cleanup_temp_file(temp_carrier_path)
                return "NO_SECRET", 400, "No hidden secret found in this carrier file."

            # Read 1-byte encryption flag immediately after SNK1
            flag_idx = magic_idx + len(MAGIC_BYTES)
            is_encrypted = file_bytes[flag_idx : flag_idx + 1]

            if is_encrypted == b"\x01":
                if not password:
                    cls.cleanup_temp_file(temp_carrier_path)
                    return (
                        "PASSWORD_REQUIRED",
                        401,
                        "Secret locked; you need to enter the password to view it.",
                    )

                # Encrypted block starts right after the 1-byte flag
                encrypted_block = file_bytes[flag_idx + 1 :]
                try:
                    raw_payload = cls.decrypt_stego_block(encrypted_block, password)

                except Exception:
                    cls.cleanup_temp_file(temp_carrier_path)
                    return (
                        "INCORRECT_KEY",
                        400,
                        "Invalid password or corrupted payload.",
                    )
            else:
                # Unencrypted payload: Payload Size (4B) + Payload
                payload_size = struct.unpack(
                    ">I", file_bytes[flag_idx + 1 : flag_idx + 5]
                )[0]
                raw_payload = file_bytes[flag_idx + 5 : flag_idx + 5 + payload_size]

            # Unpack metadata and raw content
            filename, content_bytes = cls.unpack_payload(raw_payload)
            cls.cleanup_temp_file(temp_carrier_path)

            # Return text dict or file download response
            if filename == "secret_message.txt":
                text_content = content_bytes.decode("utf-8", errors="replace")
                return "SUCCESS", 200, {"type": "text", "content": text_content}

            else:
                temp_output_path = cls.get_secure_temp_path(prefix="dec_out")
                with open(temp_output_path, "wb") as f_out:
                    f_out.write(content_bytes)

                def generate():
                    with open(temp_output_path, "rb") as f:
                        while chunk := f.read(65536):
                            yield chunk
                    cls.cleanup_temp_file(temp_output_path)

                # Fix foreign language characters
                utf8_filename = quote(filename)
                ascii_fallback = (
                    filename.encode("ascii", "ignore").decode("ascii").strip()
                )
                content_disposition = f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{utf8_filename}"

                response = Response(
                    stream_with_context(generate()),
                    mimetype="application/octet-stream",
                )
                response.headers["Content-Disposition"] = content_disposition

                return "SUCCESS", 200, response

        except Exception as e:
            cls.cleanup_temp_file(temp_carrier_path)
            return "SERVER_ERROR", 500, f"Extraction failed: {str(e)}"

import gc
import os
import struct
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes
from flask import Response, stream_with_context

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = PROJECT_ROOT / "tmp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

MAGIC_BYTES = b"SNK1"


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
            print(f"[TMP CLEANUP] Failed to delete {path}: {e}")

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

            cipher = AES.new(key, AES.MODE_GCM)
            ciphertext, tag = cipher.encrypt_and_digest(raw_payload)

            payload_size = len(ciphertext)
            header = (
                MAGIC_BYTES
                + is_encrypted
                + salt
                + cipher.nonce
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
            # 1. Save uploaded carrier file to disk
            media_carrier.save(temp_carrier_path)

            # 2. Extract payload bytes based on type
            if secret_type == "text":
                payload_bytes = (secret_message or "").encode("utf-8")
                filename = "secret_message.txt"
            elif secret_type == "file" and secret_file:
                payload_bytes = secret_file.read()
                filename = secret_file.filename or "secret_file.bin"
            else:
                cls.cleanup_temp_file(temp_carrier_path)
                return "error", "Invalid or missing secret payload."

            # 3. Build stego block and prepare output file path
            raw_payload = cls.prepare_payload(payload_bytes, filename)
            stego_block = cls.build_stego_block(raw_payload, password)

            carrier_ext = os.path.splitext(media_carrier.filename)[1] or ".bin"
            temp_output_path = (
                cls.get_secure_temp_path(prefix="stego_out") + carrier_ext
            )

            # 4. Copy carrier and append EOF payload
            with (
                open(temp_carrier_path, "rb") as f_in,
                open(temp_output_path, "wb") as f_out,
            ):
                while chunk := f_in.read(65536):
                    f_out.write(chunk)
                f_out.write(stego_block)

            # 5. Define streaming generator with automatic file deletion
            def generate():
                with open(temp_output_path, "rb") as f:
                    while chunk := f.read(65536):
                        yield chunk
                cls.cleanup_temp_file(temp_output_path)

            # Cleanup input carrier immediately
            cls.cleanup_temp_file(temp_carrier_path)

            download_name = f"stego_{media_carrier.filename}"
            response = Response(
                stream_with_context(generate()),
                mimetype=media_carrier.mimetype or "application/octet-stream",
                headers={
                    "Content-Disposition": f'attachment; filename="{download_name}"'
                },
            )

            return "success", response

        except Exception as e:
            cls.cleanup_temp_file(temp_carrier_path)

            if temp_output_path:
                cls.cleanup_temp_file(temp_output_path)

            return "error", str(e)

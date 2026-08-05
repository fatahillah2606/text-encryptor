import gc
import os
import struct
from pathlib import Path

import imageio.v3 as iio
import numpy as np
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes

# Set 'tmp' folder relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = PROJECT_ROOT / "tmp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

MAGIC_BYTES = b"SNK1"


def get_secure_temp_path(prefix="stego") -> str:
    # Generate a unique temporary path inside the root 'tmp' folder.
    filename = f"{prefix}_{os.urandom(8).hex()}.tmp"
    return str(TEMP_DIR / filename)


def cleanup_temp_file(path: str):
    # Safely delete the temporary file and force Python garbage collection.
    try:
        if path and os.path.exists(path):
            os.remove(path)
            gc.collect()
    except Exception as e:
        print(f"[TMP CLEANUP] Failed to delete {path}: {e}")


def prepare_payload(data_bytes: bytes, filename: str = "") -> bytes:
    # Packs metadata with foreign character support and random padding.
    filename_bytes = filename.encode("utf-8")
    filename_len = len(filename_bytes)
    data_len = len(data_bytes)

    # 16 to 64 bytes of random noise as padding
    padding_len = int.from_bytes(get_random_bytes(1), "big") % 49 + 16
    padding = get_random_bytes(padding_len)

    header = struct.pack(">HQI", filename_len, data_len, padding_len)
    return header + filename_bytes + data_bytes + padding


def encrypt_payload(payload: bytes, password: str) -> bytes:
    # Encrypts raw payload using AES-256-GCM and Scrypt key derivation.
    salt = get_random_bytes(16)
    key = scrypt(password.encode("utf-8"), salt, key_len=32, N=2**14, r=8, p=1)

    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(payload)

    payload_size = len(ciphertext)
    # Header: Magic Bytes (4B) + Salt (16B) + Nonce (12B) + Tag (16B) + Payload Size (4B)
    header = MAGIC_BYTES + salt + cipher.nonce + tag + struct.pack(">I", payload_size)
    return header + ciphertext


def check_capacity(img_array: np.ndarray, required_bytes: int) -> tuple[bool, int]:
    # Checks if PNG carrier array has sufficient LSB capacity.
    max_bytes = img_array.size // 8
    return (max_bytes >= required_bytes), max_bytes


def hide_data(
    carrier_path: str, secret_bytes: bytes, password: str, filename: str = ""
) -> str:
    # Encrypts payload and embeds into PNG carrier LSBs.
    # 1. Validate PNG Extension
    if not carrier_path.lower().endswith(".png"):
        raise ValueError("Only PNG carrier images are supported for LSB steganography.")

    # 2. Read PNG Image
    img = iio.imread(carrier_path)

    if img.ndim < 3:
        raise ValueError("Carrier image must be a color PNG (RGB/RGBA).")

    # 3. Prepare & Encrypt Payload
    raw_payload = prepare_payload(secret_bytes, filename)
    encrypted_payload = encrypt_payload(raw_payload, password)

    # 4. Capacity Check
    has_capacity, max_bytes = check_capacity(img, len(encrypted_payload))
    if not has_capacity:
        raise ValueError(
            f"Carrier image capacity insufficient. Required: {len(encrypted_payload)} bytes, "
            f"Available: {max_bytes} bytes."
        )

    # 5. Embed Bits into Pixel LSBs
    original_shape = img.shape
    flat_img = img.flatten()

    payload_np = np.frombuffer(encrypted_payload, dtype=np.uint8)
    bits = np.unpackbits(payload_np)
    num_bits = len(bits)

    flat_img[:num_bits] = (flat_img[:num_bits] & ~1) | bits

    # 6. Reshape and Save as lossless PNG
    stego_img = flat_img.reshape(original_shape)

    output_path = get_secure_temp_path(prefix="stego_out") + ".png"
    iio.imwrite(output_path, stego_img, extension=".png")

    return output_path

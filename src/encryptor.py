import binascii
import random
import string

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


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

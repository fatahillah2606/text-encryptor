import binascii
import random
import string
import sys

from colorama import Back, Fore, Style
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

# Variable
key = None
no_key = True


# Get valid key from user input
def get_valid_key(user_key):
    if not user_key:  # If empty, make new one
        generate_key = binascii.hexlify(
            get_random_bytes(16)
        ).decode()  # Create 16 byte key (AES-128)
        key = generate_key.ljust(16)[:16].encode()
        print(f"Encryption key created: {Style.BRIGHT}{generate_key}{Style.RESET_ALL}")
        no_key = True

    else:
        key = user_key.ljust(16)[:16].encode()  # Make sure the length is 16
        no_key = False

    return key, no_key


# Encryptor
def encrypt_aes(text):
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv  # Initialization Vector
    encrypted_message = cipher.encrypt(pad(text.encode(), AES.block_size))
    return iv + encrypted_message


# Decryptor
def decrypt_aes(text):
    iv = text[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_message = unpad(cipher.decrypt(text[16:]), AES.block_size)
    return decrypted_message.decode()


# Ask for the key
def askKey():
    if key == None and no_key == True:
        user_key = input(
            "Enter the encryption key, leave it blank to create a new one: "
        )
        return get_valid_key(user_key)
    elif key != None:
        return key, False


# Show option
def showOption():
    try:
        print(
            f"\nSelect an option:\n1. Change key\n2. Create password\n3. Encrypt text\n4. Decrypt text\n0. Exit\n"
        )

        optionChosed = input("Enter your options: ")
        return int(optionChosed)

    except ValueError:
        print(f"{Fore.RED}Please fill in with numbers!{Style.RESET_ALL}")


# Change key
def changeKey():
    global key
    global no_key

    key, no_key = get_valid_key(input("Enter new key: "))
    print(f"{Fore.GREEN}Key changed successfully!{Style.RESET_ALL}")


# Create password
def createPassword(password_length=None):
    while True:
        if password_length == None:
            password_length = input(f"How long do you want the password to be? (int): ")

        try:
            password_length = int(password_length)
            characters = string.ascii_letters + string.digits + string.punctuation
            password = "".join(
                random.choice(characters) for i in range(password_length)
            )
            print(
                f"\nPassword: {Style.BRIGHT}{password}{Style.RESET_ALL} \n{Fore.YELLOW}Make sure you keep your password safe!\n{Style.RESET_ALL}"
            )

            # Encrypt password?
            enkrip = input(f"Do you want to encrypt the password? (Y/n) ")
            enkrip = enkrip.lower()

            if enkrip == "y":
                encrypted_password = encrypt_aes(password)
                print(
                    f"\nThe password has been successfully encrypted:\n {Style.BRIGHT}{binascii.hexlify(encrypted_password).decode()}{Style.RESET_ALL}"
                )

            confirm = input(f"\nWant to create another password? (Y/n) ").lower()
            createPassword() if confirm == "y" else start()
            break

        except ValueError:
            print(
                f"{Fore.RED}Please enter a long password with numbers!{Style.RESET_ALL}\n"
            )
            password_length = None

        except Exception as err:
            sys.exit(f"{Fore.RED}An error occurred: '{err}'{Style.RESET_ALL}")


# Encrypt text
def encryptText(text=None):
    if text == None:
        text = input(f"\nEnter the text you want to encrypt: ")

    try:
        encrypt_text = encrypt_aes(text)
        print(
            f"\nThe text has been successfully encrypted:\n {Style.BRIGHT}{binascii.hexlify(encrypt_text).decode()}{Style.RESET_ALL}"
        )

        confirm = input(f"\nWant to encrypt the text again? (Y/n) ").lower()
        encryptText() if confirm == "y" else start()

    except Exception as err:
        sys.exit(f"{Fore.RED}An error occurred: '{err}'{Style.RESET_ALL}")


# Decrypt text
def decryptText(text=None):
    if text == None:
        text = input(f"\nEnter the text you want to decrypt: ")

    try:
        convert_text = binascii.unhexlify(text)
        decrypted_message = decrypt_aes(convert_text)
        print(
            f"\nText successfully decrypted:\n {Style.BRIGHT}{decrypted_message}{Style.RESET_ALL}"
        )

        confirm = input(f"\nWant to decrypt the text again? (Y/n) ").lower()
        decryptText() if confirm == "y" else start()

    # If invalid
    except (ValueError, binascii.Error) as err:
        print(
            f"{Fore.RED}Error: Decryption failed.\n{err}\n\nEnsure that the encrypted text and the key you entered are correct and match. {Style.RESET_ALL}"
        )

        while True:
            try:
                print(
                    f"Select Option:\n1. Change key\n2. Try decrypting again\n3. Return to main menu"
                )
                optionChosed = input("\nEnter your options: ")

                match int(optionChosed):
                    case 1:
                        changeKey()
                        decryptText()

                    case 2:
                        decryptText()

                    case 3:
                        start()

                    case _:
                        print(f"Invalid option: {optionChosed}")

            except ValueError as e:
                print(f"{Fore.RED}Please fill in with numbers!{Style.RESET_ALL}")

    except Exception as err:
        sys.exit(f"{Fore.RED}An error occurred: '{err}'{Style.RESET_ALL}")


# Start
def start():
    global key
    global no_key

    # Ask for the key
    key, no_key = askKey()

    # show option
    optionChosed = showOption()

    match optionChosed:
        # Change key
        case 1:
            changeKey()
            start()

        # Create password
        case 2:
            password_length = input(f"How long do you want the password to be? (int): ")
            createPassword(password_length)

        # Encrypt text
        case 3:
            text = input("\nEnter the text you want to encrypt: ")
            encryptText(text)

        # Decrypt text
        case 4:
            text = input("\nEnter the text you want to decrypt: ")
            decryptText(text)

        case 0:
            sys.exit("Bye.")

        # Invalid option
        case _:
            print(f"{Fore.RED}Invalid option: {optionChosed}{Style.RESET_ALL}")
            start()


# Call the progtam
start()

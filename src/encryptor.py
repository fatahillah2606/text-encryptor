from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from colorama import Back, Fore, Style
import binascii, random, string, sys

# Variabel
key = None
no_key = True

# Get valid key from user input
def get_valid_key(user_key):
  if not user_key:  # If empty, make new one
    generate_key = binascii.hexlify(get_random_bytes(16)).decode() # Create 16 byte key (AES-128)
    key = generate_key.ljust(16)[:16].encode()
    print(f"Kunci enkripsi dibuat: {Style.BRIGHT}{generate_key}{Style.RESET_ALL}")
    no_key = True
  
  else:
    key = user_key.ljust(16)[:16].encode() # Make sure the length is 16
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
    user_key = input("Masukan kunci enkripsi, biarkan kosong untuk membuat baru: ")
    return get_valid_key(user_key)
  elif key != None:
    return key, False

# Show option
def showOption():
  try:
    print(f"\nPilih opsi:\n1. Ganti kunci\n2. Buatkan sandi\n3. Enkripsi teks\n4. Dekripsi teks\n0. Keluar\n")

    optionChosed = input("Masukan pilihan: ")
    return int(optionChosed)
  
  except ValueError:
    print(f"{Fore.RED}Mohon isi dengan angka!{Style.RESET_ALL}")

# Change key
def changeKey():
  global key
  global no_key

  key, no_key = get_valid_key(input("Masukan kunci baru: "))
  print(f"{Fore.GREEN}Kunci berhasil diubah{Style.RESET_ALL}")

# Create password
def createPassword(password_length=None):
  while True:
    if password_length == None:
      password_length = input(f"Berapa panjang sandi yang di inginkan? (int): ")

    try:
      password_length = int(password_length)
      characters = string.ascii_letters + string.digits + string.punctuation
      password = ''.join(random.choice(characters) for i in range(password_length))
      print(f"\nSandi: {Style.BRIGHT}{password}{Style.RESET_ALL} \n{Fore.YELLOW}Pastikan anda menyimpan sandi anda dengan baik!\n{Style.RESET_ALL}")
    
      # Encrypt password?
      enkrip = input(f"Apakah anda ingin enkripsi sandinya? (Y/n) ")
      enkrip = enkrip.lower()
    
      if enkrip == "y":
        encrypted_password = encrypt_aes(password)
        print(f"\nSandi berhasil di enkripsi:\n {Style.BRIGHT}{binascii.hexlify(encrypted_password).decode()}{Style.RESET_ALL}")

      confirm = input(f"\nIngin membuat sandi lagi? (Y/n) ").lower()
      createPassword() if confirm == "y" else start()
      break

    except ValueError:
      print(f"{Fore.RED}Mohon isi panjang sandi dengan angka!{Style.RESET_ALL}\n")
      password_length = None

    except Exception as err:
      sys.exit(f"{Fore.RED}Terjadi kesalahan: '{err}'{Style.RESET_ALL}")


# Encrypt text
def encryptText(text=None):
  if text == None:
    text = input(f"\nMasukan teks yang ingin di enkripsi: ")

  try:
    encrypt_text = encrypt_aes(text)
    print(f"\nTeks berhasil di enkripsi:\n {Style.BRIGHT}{binascii.hexlify(encrypt_text).decode()}{Style.RESET_ALL}")
      
    confirm = input(f"\nIngin enkripsi text lagi? (Y/n) ").lower()
    encryptText() if confirm == "y" else start()
    
  except Exception as err:
    sys.exit(f"{Fore.RED}Terjadi kesalahan: '{err}'{Style.RESET_ALL}")

# Decrypt text
def decryptText(text=None):
  if text == None:
    text = input(f"\nMasukan teks yang ingin di dekripsi: ")

  try:
    convert_text = binascii.unhexlify(text)
    decrypted_message = decrypt_aes(convert_text)
    print(f"\nTeks berhasil di dekripsi:\n {Style.BRIGHT}{decrypted_message}{Style.RESET_ALL}")
    
    confirm = input(f"\nIngin dekripsi text lagi? (Y/n) ").lower()
    decryptText() if confirm == "y" else start()

  # If invalid
  except (ValueError, binascii.Error) as err:
    print(f"{Fore.RED}Kesalahan: Proses dekripsi gagal.\n{err}\n\nPastikan teks terenkripsi dan kunci yang Anda masukkan sudah benar dan sesuai. {Style.RESET_ALL}")

    while True:
      try:
        print(f"\nPilih Opsi:\n1. Ganti kunci\n2. Coba dekripsi lagi\n3. Kembali ke menu utama")
        optionChosed = input("\nMasukan pilihan: ")

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
        print(f"{Fore.RED}Mohon isi dengan angka!{Style.RESET_ALL}")

  except Exception as err:
    sys.exit(f"{Fore.RED}Terjadi kesalahan: '{err}'{Style.RESET_ALL}")

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
      password_length = input(f"Berapa panjang sandi yang di inginkan? (int): ")
      createPassword(password_length)

    # Encrypt text
    case 3:
      text = input("\nMasukan teks yang ingin di enkripsi: ")
      encryptText(text)

    # Decrypt text
    case 4:
      text = input("\nMasukan teks yang ingin di dekripsi: ")
      decryptText(text)

    case 0:
      sys.exit("Bye.")

    # Invalid option
    case _:
      print(f"{Fore.RED}Invalid option: {optionChosed}{Style.RESET_ALL}")
      start()

# Call the progtam
start()
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import binascii, random, string

# Variabel
key = None
tidak_punya = True

# Fungsi untuk memastikan panjang kunci sesuai (misalnya 16 byte untuk AES-128)
def get_valid_key(user_key):
  if not user_key:  # Jika kunci kosong, buat kunci baru
    generate_key = binascii.hexlify(get_random_bytes(16)).decode() # Buat kunci baru 16 byte (AES-128)
    key = generate_key.ljust(16)[:16].encode()
    print(f"Kunci enkripsi yang dibuat oleh sistem: {generate_key}")
    tidak_punya = True
  else:
    key = user_key.ljust(16)[:16].encode()  # Pastikan panjang kunci 16 karakter
    tidak_punya = False
  return key, tidak_punya

# Membuat sandi
def create_password(panjang):
  # Definisikan karakter untuk dijadikan sandi
  characters = string.ascii_letters + string.digits + string.punctuation

  # Buat sandi
  password = ''.join(random.choice(characters) for i in range(panjang))
  return password

# Enkripsi
def encrypt_aes(message):
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv  # Initialization Vector
    encrypted_message = cipher.encrypt(pad(message.encode(), AES.block_size))
    return iv + encrypted_message  # Gabungkan IV dengan pesan terenkripsi

# Dekripsi
def decrypt_aes(encrypted_message):
    iv = encrypted_message[:16]  # Ambil IV dari bagian awal pesan
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_message = unpad(cipher.decrypt(encrypted_message[16:]), AES.block_size)
    return decrypted_message.decode()

# Mulai
def mulai():
  global key
  global tidak_punya
  
  # Tanyakan kunci
  if key == None and tidak_punya == True:
    user_key = input("Mohon masukan kunci enkripsi, jika tidak punya biarkan kosong untuk membuat baru: ")
    key, tidak_punya = get_valid_key(user_key)
  elif key != None:
    tidak_punya = False

  # tampilkan pilihan
  if tidak_punya == True:
    print("\nPilih opsi:\n1. Ganti kunci\n2. Buatkan sandi\n3. Enkripsi teks\n")
  else:
    print("\nPilih opsi:\n1. Ganti kunci\n2. Buatkan sandi\n3. Enkripsi teks\n4. Dekripsi teks\n")

  pilihan = input("Pilihanmu: ")
  pilihan = int(pilihan)

  # Cek pilihan
  if pilihan == 1:
    # Ganti kunci
    kunci = input("Masukan kunci baru: ")
    key, tidak_punya = get_valid_key(user_key)
    print("Kunci berhasil diubah")

  elif pilihan == 2:
    # Buat sandi
    panjang_sandi = input("Berapa panjang sandi yang di inginkan? (int): ")
    sandi = create_password(int(panjang_sandi))
    print("\nSandi: ", sandi, "\nPastikan anda menyimpan sandi anda dengan baik!\n")
    
    # Enkripsi sandi?
    enkrip = input("Apakah anda ingin enkripsi sandinya? (Y/n) ")
    enkrip = enkrip.lower()
    
    if enkrip == "y":
      hasil_enkrip = encrypt_aes(sandi)
      print("Sandi berhasil di enkripsi:\n", binascii.hexlify(hasil_enkrip).decode())

  elif pilihan == 3:
    # Enkripsi teks
    teks = input("\nMasukan teks yang ingin di enkripsi: ")

    # proses enkripsi
    hasil = encrypt_aes(teks)
    print("Teks berhasil di enkripsi:\n", binascii.hexlify(hasil).decode())

  elif pilihan == 4 and tidak_punya == False:
    # Dekripsi teks
    teks = input("\nMasukan teks yang ingin di dekripsi: ")

    # proses dekripsi
    try:
      hasil = binascii.unhexlify(teks)
      hasil_dekripsi = decrypt_aes(hasil)
      print("Teks berhasil di dekripsi:\n", hasil_dekripsi)
    
    # Jika tidak valid
    except (ValueError, binascii.Error) as e:
      print("Input tidak valid atau format hex salah.")
  
  # Tanya jika ingin melakukannya lagi
  rerun = input("\nIngin melakukan hal lain? (Y/n) ")
  rerun = rerun.lower()
  if rerun == "y":
    mulai()

# Panggil fungsi mulai() ketika program dijalankan
mulai()
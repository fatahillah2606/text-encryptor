import base64
import codecs


class TextConverter:
    def __init__(self):
        self.MORSE_CODE_DICT = {
            # Letters
            "A": ".-",
            "B": "-...",
            "C": "-.-.",
            "D": "-..",
            "E": ".",
            "F": "..-.",
            "G": "--.",
            "H": "....",
            "I": "..",
            "J": ".---",
            "K": "-.-",
            "L": ".-..",
            "M": "--",
            "N": "-.",
            "O": "---",
            "P": ".--.",
            "Q": "--.-",
            "R": ".-.",
            "S": "...",
            "T": "-",
            "U": "..-",
            "V": "...-",
            "W": ".--",
            "X": "-..-",
            "Y": "-.--",
            "Z": "--..",
            # Numbers
            "0": "-----",
            "1": ".----",
            "2": "..---",
            "3": "...--",
            "4": "....-",
            "5": ".....",
            "6": "-....",
            "7": "--...",
            "8": "---..",
            "9": "----.",
            # Standard Punctuation
            ".": ".-.-.-",
            ",": "--..--",
            "?": "..--..",
            "'": ".----.",
            "!": "-.-.--",
            "/": "-..-.",
            "(": "-.--.",
            ")": "-.--.-",
            "&": ".-...",
            ":": "---...",
            ";": "-.-.-.",
            "=": "-...-",
            "+": ".-.-.",
            "-": "-....-",
            "_": "..--.-",
            '"': ".-..-.",
            "$": "...-..-",
            "@": ".--.-.",
        }

        self.REVERSE_MORSE = {v: k for k, v in self.MORSE_CODE_DICT.items()}

    # ========== Morse code ==========
    def to_morse(self, text: str) -> str:
        result = []
        for char in text.upper():
            if char in self.MORSE_CODE_DICT:
                result.append(self.MORSE_CODE_DICT[char])
            elif char == " ":
                result.append("/")
        return " ".join(result)

    def from_morse(self, morse_str: str) -> str:
        words = morse_str.split(" / ")
        decoded_words = []
        for word in words:
            letters = word.split()
            decoded_words.append(
                "".join(self.REVERSE_MORSE.get(code, "") for code in letters)
            )
        return " ".join(decoded_words)

    # ========== Binary ==========
    @classmethod
    def to_binary(cls, text: str) -> str:
        return " ".join(format(ord(c), "08b") for c in text)

    @classmethod
    def from_binary(cls, binary_str: str) -> str:
        return "".join(chr(int(b, 2)) for b in binary_str.split())

    # ========== Hexadecimal ==========
    @classmethod
    def to_hex(cls, text: str) -> str:
        return text.encode("utf-8").hex()

    @classmethod
    def from_hex(cls, hex_str: str) -> str:
        try:
            return bytes.fromhex(hex_str).decode("utf-8")
        except ValueError:
            return ""

    # ========== Caesar Cipher ==========
    @classmethod
    def to_rot13(cls, text: str) -> str:
        return codecs.encode(text, "rot_13")

    @classmethod
    def from_rot13(cls, rot13_str: str) -> str:
        return codecs.decode(rot13_str, "rot_13")

    # ========== Atbash Cipher ==========
    _ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    _REVERSED_ALPHA = "ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba"
    _ATBASH_TABLE = str.maketrans(_ALPHA, _REVERSED_ALPHA)

    @classmethod
    def to_atbash(cls, text: str) -> str:
        return text.translate(cls._ATBASH_TABLE)

    @classmethod
    def from_atbash(cls, atbash_str: str) -> str:
        return atbash_str.translate(cls._ATBASH_TABLE)

    # ========== A1Z26 ==========
    @classmethod
    def to_a1z26(cls, text: str) -> str:
        return " ".join(str(ord(c.upper()) - 64) for c in text if c.isalpha())

    @classmethod
    def from_a1z26(cls, a1z26_str: str) -> str:
        numbers = a1z26_str.split()
        result = []
        for num in numbers:
            if num.isdigit() and 1 <= int(num) <= 26:
                result.append(chr(int(num) + 64))
        return "".join(result)

    # ========== Base64 ==========
    @classmethod
    def to_base64(cls, text: str) -> str:
        return base64.b64encode(text.encode("utf-8")).decode("utf-8")

    @classmethod
    def from_base64(cls, b64_str: str) -> str:
        try:
            return base64.b64decode(b64_str.encode("utf-8")).decode("utf-8")
        except Exception:
            return ""

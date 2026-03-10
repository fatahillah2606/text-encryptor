import binascii
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, session

from src.encryptor import decrypt_aes, encrypt_aes, generate_password, get_valid_key

api_route = Blueprint("api", __name__)


# API Response
def api_response(status, code, message, data, pagination):
    response = {
        "status": status,
        "code": code,
        "message": message,
        "data": data if data else [],
        "pagination": pagination if pagination else {},
    }
    return jsonify(response)


# encription key
@api_route.route("/encryptor/encryption_key", methods=["POST", "GET"])
def encryption_key():
    if request.method == "POST":
        try:
            data = request.json
            valid_key = get_valid_key(str(data.get("key")))

            # Create session
            session.permanent = True
            session["exipred"] = (
                datetime.now(timezone.utc) + timedelta(hours=1)
            ).isoformat()
            session["encoded_key"] = valid_key["encoded_key"]
            session["key"] = valid_key["generated_key"]

            return api_response(
                "success",
                200,
                "The encryption key has been set",
                {"key": session["key"]},
                {},
            )

        except Exception as err:
            return api_response("error", 500, str(err), [], {}), 500

    else:
        if "encoded_key" in session or "key" in session:
            return api_response(
                "success", 200, "Encryption key available", {"key": session["key"]}, {}
            )
        else:
            return api_response(
                "error", 404, "No encryption key available", [], {}
            ), 404


# Encrypt text
@api_route.route("/encryptor/encrypt_text", methods=["POST"])
def encrypt_text():
    try:
        data = request.json
        key = str(data.get("key"))
        text = str(data.get("unencrypted_text"))

        # Check if the key is available to prevent get_valid_key auto generated key
        if not key or key == "":
            if "key" in session:
                key = session["key"]

            else:
                return api_response(
                    "error", 404, "No encryption key available", [], {}
                ), 404

        valid_key = get_valid_key(key)

        encrypted_text = binascii.hexlify(
            encrypt_aes(text, valid_key["encoded_key"])
        ).decode()

        return api_response(
            "success",
            200,
            "The text has been successfully encrypted",
            {"encrypted_text": encrypted_text},
            {},
        )

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Decrypt text
@api_route.route("/encryptor/decrypt_text", methods=["POST"])
def decrypt_text():
    try:
        data = request.json
        key = str(data.get("key"))
        text = str(data.get("encrypted_text"))

        # Check if the key is available to prevent get_valid_key auto generated key
        if not key or key == "":
            if "key" in session:
                key = session["key"]

            else:
                return api_response(
                    "error", 404, "No encryption key available", [], {}
                ), 404

        valid_key = get_valid_key(key)
        convert_text = binascii.unhexlify(text)

        decrypted_text = decrypt_aes(convert_text, valid_key["encoded_key"])

        return api_response(
            "success",
            200,
            "The text has been successfully decrypted",
            {"decrypted_text": decrypted_text},
            {},
        )

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Password generator
@api_route.route("/encryptor/password_generator", methods=["POST"])
def password_generator():
    try:
        data = request.json
        key = str(data.get("key"))
        length = int(data.get("password_length"))
        encrypt = bool(int(data.get("encrypt_password")))

        # Check if the key is available to prevent get_valid_key auto generated key
        if not key or key == "":
            if "key" in session:
                key = session["key"]

            else:
                return api_response(
                    "error", 404, "No encryption key available", [], {}
                ), 404

        # Check if password length is 0 or bellow
        if length <= 0:
            raise ValueError("Password length must be at least 1 character long!")

        password = generate_password(length)
        valid_key = get_valid_key(key)

        encrypted = (
            binascii.hexlify(encrypt_aes(password, valid_key["encoded_key"])).decode()
            if encrypt
            else ""
        )

        data = {"password": password, "encrypted_password": encrypted}

        return api_response("success", 200, "Password successfully created", data, {})

    except ValueError as err:
        return api_response("error", 400, str(err), [], {}), 400

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500

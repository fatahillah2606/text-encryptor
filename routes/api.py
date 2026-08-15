import binascii
import json
from functools import wraps

from flask import Blueprint, Response, jsonify, request, session

from src.converter import TextConverter
from src.data_io import DataExporter, DataImporter
from src.data_manager import KeyManager, PasswordManager, Recovery, UserManager
from src.encryptor import (
    FileEncryptor,
    NewEncryption,
    create_zip_response,
    generate_password,
)
from src.essentials import createLoginSession, decrypt_payload, generate_share_link
from src.stego_encoder import StegoDecoder, StegoEncoder

encryption_method = NewEncryption()
text_converter = TextConverter()
file_encryptor = FileEncryptor()
stego_encoder = StegoEncoder()


# ========== API Response ==========
def api_response(status, code, message, data, pagination):
    response = {
        "status": status,
        "code": code,
        "message": message,
        "data": data if data else [],
        "pagination": pagination if pagination else {},
    }
    return jsonify(response)


# ========== API protection ==========
def logged_in_only_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return api_response(
                "FORBIDDEN",
                403,
                "Your session has expired. Please log in again.",
                [],
                {},
            ), 403

        return f(*args, **kwargs)

    return decorated_function


api_route = Blueprint("api", __name__)

#
# Encrptor process
#


# ========== encription key ==========
@api_route.route("/encryptor/encryption_key", methods=["POST", "GET"])
def encryption_key():
    if request.method == "POST":
        try:
            data = request.json
            valid_key = encryption_method.get_valid_key(str(data.get("key")))

            return api_response(
                "SUCCESS",
                200,
                "The encryption key has been set",
                {"key": valid_key["generated_key"]},
                {},
            )

        except Exception as err:
            return api_response(
                "SERVER_ERROR",
                500,
                f"An error occurred on the server. \nError message:{str(err)}",
                [],
                {},
            ), 500

    else:
        if "encoded_key" in session or "key" in session:
            return api_response(
                "SUCCESS", 200, "Encryption key available", {"key": session["key"]}, {}
            )
        else:
            return api_response(
                "NO_ENCRYPTION_KEY",
                404,
                "The encryption key is not available. Please create one in the keys menu in the navigation menu.",
                [],
                {},
            ), 404


# ========== Encrypt text ==========
@api_route.route("/encryptor/encrypt_text", methods=["POST"])
def encrypt_text():
    try:
        data = request.json
        key = str(data.get("key"))
        text = str(data.get("encryptor_input_text"))

        # Check if the key is available to prevent get_valid_key auto generated key
        if not key or key == "":
            return api_response(
                "NO_ENCRYPTION_KEY",
                400,
                "The encryption key is not available. Please create one in the keys menu in the navigation menu.",
                [],
                {},
            ), 400

        valid_key = encryption_method.get_valid_key(key)

        vi, encrypted_text = encryption_method.encrypt_aes(
            text, valid_key["encoded_key"]
        )
        encrypted_text = binascii.hexlify(vi + encrypted_text).decode()

        return api_response(
            "SUCCESS",
            200,
            "Successfully encrypted text",
            {"result_text": encrypted_text},
            {},
        )

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Generate share link ==========
@api_route.route("/encryptor/generate_link", methods=["POST"])
def generate_link():
    try:
        data = request.json
        text = str(data.get("text_to_share"))

        blob, one_time_key = generate_share_link(text)
        link = f"http://127.0.0.1:5000/t/{blob}#{one_time_key}"

        return api_response(
            "SUCCESS",
            200,
            "Successfully generated link.",
            {"link": link},
            {},
        )

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Decrypt text ==========
@api_route.route("/encryptor/decrypt_text", methods=["POST"])
def decrypt_text():
    try:
        data = request.json
        key = str(data.get("key"))
        text = str(data.get("encryptor_input_text"))

        # Check if the key is available to prevent get_valid_key auto generated key
        if not key or key == "":
            return api_response(
                "NO_ENCRYPTION_KEY",
                400,
                "The encryption key is not available. Please create one in the keys menu in the navigation menu.",
                [],
                {},
            ), 400

        valid_key = encryption_method.get_valid_key(key)
        convert_text = binascii.unhexlify(text)

        decrypted_text = encryption_method.decrypt_aes(
            convert_text, valid_key["encoded_key"]
        )

        return api_response(
            "SUCCESS",
            200,
            "Successfully decrypted text",
            {"result_text": decrypted_text},
            {},
        )

    except Exception:
        return api_response(
            "SERVER_ERROR",
            500,
            "The text is corrupted, incomplete, or the wrong key was used. Check your key, and ensure you copied the entire encrypted text block.",
            {
                "result_text": "The text is corrupted, incomplete, or the wrong key was used. Check your key, and ensure you copied the entire encrypted text block."
            },
            {},
        ), 500


# ========== Decrypt shared link ==========
@api_route.route("/encryptor/decrypt_link", methods=["POST"])
def decrypt_shared_link():
    data = request.json
    blob = data.get("blob")
    key = data.get("key")

    if not blob or not key:
        return api_response("INVALID", 400, "Invalid transmission format.", [], {}), 400

    status, code, decrypted = decrypt_payload(blob, key)
    if status == "SUCCESS":
        return api_response(
            status, code, "Successfully decrypted the link", decrypted, {}
        )

    elif status == "EXPIRED":
        return api_response(
            status,
            code,
            "This shared session has expired (5-minute limit exceeded).",
            [],
            {},
        ), code

    else:
        return api_response(
            "CORRUPTED",
            400,
            "Decryption failed. The key or payload might be corrupted.",
            [],
            {},
        ), 400


# ========== File encryption ==========
@api_route.route("/encryptor/encrypt_file", methods=["POST"])
def proceed_file_encryption():
    files = request.files.getlist("files")
    password = request.form.get("key")

    if not files or not password:
        return api_response(
            "NO_FILE_OR_PASSWORD_PROVIDED",
            400,
            "Failed to receive file and encryption key. Please try again.",
            [],
            {},
        ), 400

    status = None
    code = None
    result = None

    # Check if multiple file selected
    if len(files) > 1:
        status, code, result = create_zip_response(
            files,
            password,
            file_encryptor.encrypt_file,
            bundle_name="encrypted_files.zip",
        )

    else:
        status, code, result = file_encryptor.encrypt_file(files[0], password)

    # Return the response
    if status == "SUCCESS":
        return result
    else:
        return api_response(
            status,
            code,
            str(result),
            [],
            {},
        ), code


# ========== File decryption ==========
@api_route.route("/encryptor/decrypt_file", methods=["POST"])
def proceed_file_decryption():
    files = request.files.getlist("files")
    password = request.form.get("key")

    if not files or not password:
        return api_response(
            "NO_FILE_OR_PASSWORD_PROVIDED",
            400,
            "Failed to receive file and decryption key. Please try again.",
            [],
            {},
        ), 400

    status = None
    code = None
    result = None

    # Check if multiple file selected
    if len(files) > 1:
        status, code, result = create_zip_response(
            files,
            password,
            file_encryptor.decrypt_file,
            bundle_name="decrypted_files.zip",
        )
    else:
        status, code, result = file_encryptor.decrypt_file(files[0], password)

    # Return the response
    if status == "SUCCESS":
        return result
    else:
        return api_response(
            status,
            code,
            str(result),
            [],
            {},
        ), code


# ========== Password generator ==========
@api_route.route("/encryptor/password_generator", methods=["POST"])
def password_generator():
    try:
        data = request.json
        key = str(data.get("key"))
        length = int(data.get("password_length"))
        encrypt = bool(int(data.get("encrypt_password")))

        # Check if the key is available to prevent get_valid_key auto generated key
        if not key or key == "":
            return api_response(
                "NO_ENCRYPTION_KEY",
                400,
                "The encryption key is not available. Please create one in the keys menu in the navigation menu.",
                [],
                {},
            ), 400

        # Check if password length is bellow 8
        if length < 8:
            raise ValueError(
                "The character length you entered is less than 8. At least 8 or more characters long to generate a password."
            )

        password = generate_password(length)
        valid_key = encryption_method.get_valid_key(key)

        encrypted = ""
        if encrypt:
            iv, encrypted_text = encryption_method.encrypt_aes(
                password, valid_key["encoded_key"]
            )
            encrypted = binascii.hexlify(iv + encrypted_text).decode()

        data = {"password": password, "encrypted_password": encrypted}

        return api_response("SUCCESS", 200, "Password generated.", data, {})

    except ValueError as err:
        return api_response("LENGTH_BELLOW_MINIMUM", 400, str(err), [], {}), 400

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Text Converter ==========
@api_route.route("/converter", methods=["POST"])
def converter_text():
    try:
        data = request.json
        convert_to_option = str(data.get("convert_to_option"))
        converter_input_text = str(data.get("converter_input_text"))
        reverse_convert = bool(1 if data.get("reverse_convert") == "true" else 0)

        # Convert to morse code
        if convert_to_option == "morse":
            result = (
                text_converter.from_morse(converter_input_text)
                if reverse_convert
                else text_converter.to_morse(converter_input_text)
            )
            return api_response("SUCCESS", 200, "Ok", {"result_text": result}, {})

        # Convert to binary
        elif convert_to_option == "binary":
            result = (
                text_converter.from_binary(converter_input_text)
                if reverse_convert
                else text_converter.to_binary(converter_input_text)
            )
            return api_response("SUCCESS", 200, "Ok", {"result_text": result}, {})

        # Convert to Hexadecimal
        elif convert_to_option == "hexa":
            result = (
                text_converter.from_hex(converter_input_text)
                if reverse_convert
                else text_converter.to_hex(converter_input_text)
            )
            return api_response("SUCCESS", 200, "Ok", {"result_text": result}, {})

        # Convert to Caesar Cipher
        elif convert_to_option == "caesar":
            result = (
                text_converter.from_rot13(converter_input_text)
                if reverse_convert
                else text_converter.to_rot13(converter_input_text)
            )
            return api_response("SUCCESS", 200, "Ok", {"result_text": result}, {})

        # Convert to Atbash Cipher
        elif convert_to_option == "atbash":
            result = (
                text_converter.from_atbash(converter_input_text)
                if reverse_convert
                else text_converter.to_atbash(converter_input_text)
            )
            return api_response("SUCCESS", 200, "Ok", {"result_text": result}, {})

        # Convert to A1Z26
        elif convert_to_option == "A1Z26":
            result = (
                text_converter.from_a1z26(converter_input_text)
                if reverse_convert
                else text_converter.to_a1z26(converter_input_text)
            )
            return api_response("SUCCESS", 200, "Ok", {"result_text": result}, {})

        # Convert to Base64
        elif convert_to_option == "base64":
            result = (
                text_converter.from_base64(converter_input_text)
                if reverse_convert
                else text_converter.to_base64(converter_input_text)
            )
            return api_response("SUCCESS", 200, "Ok", {"result_text": result}, {})

        else:
            return api_response("UNAVAILABLE", 503, "Feature unavailable", [], {}), 503

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Steganography ==========


# Hide secret
@api_route.route("/steganography/hide", methods=["POST"])
def hideSecret():
    if "media_carrier" not in request.files:
        return api_response(
            "CARRIER_NOT_PROVIDED",
            400,
            "No media carrier is provided. Make sure to select a file to serve as the container for hiding your secret.",
            [],
            {},
        ), 400

    secret_type = str(request.form.get("secret_type"))
    media_carrier = request.files["media_carrier"]

    raw_password = request.form.get("secret_password")
    password = str(raw_password) if raw_password else None

    secret_message = request.form.get("secret_message")
    secret_file = request.files.get("secret_file_input")

    status, code, result = stego_encoder.hide_secret(
        media_carrier=media_carrier,
        secret_type=secret_type,
        secret_message=secret_message,
        secret_file=secret_file,
        password=password,
    )

    if status == "SUCCESS":
        return result

    else:
        return api_response(
            status,
            code,
            str(result),
            [],
            {},
        ), code


# Reveal secret
@api_route.route("/steganography/reveal", methods=["POST"])
def revealSecret():
    if "media_carrier_input" not in request.files:
        return api_response(
            "CARRIER_NOT_PROVIDED",
            400,
            "No media carrier provided.",
            [],
            {},
        ), 400

    media_carrier = request.files["media_carrier_input"]
    raw_password = request.form.get("secret_password")
    password = str(raw_password) if raw_password else None

    status, code, result = StegoDecoder.reveal_secret(media_carrier, password)

    if status == "SUCCESS":
        # If result is Flask streaming Response (file download)
        if isinstance(result, Response):
            return result

        # If result is dictionary (text content)
        return api_response(status, code, "Secret extracted successfully.", result, {})

    else:
        return api_response(status, code, str(result), [], {}), code


#
# ========== Auth process ==========
#

user = UserManager()


# ========== Register ==========
@api_route.route("/auth/register", methods=["POST"])
def register():
    try:
        # Data
        data = request.json
        name = str(data.get("name"))
        username = str(data.get("username"))
        password = str(data.get("password"))
        retypePassword = str(data.get("retype_password"))

        # name and username length check
        if len(name) > 50:
            return api_response(
                "NAME_LENGTH_EXCEEDED",
                400,
                "The maximum length for a name is 50.",
                [],
                {},
            ), 400

        if len(username) > 50:
            return api_response(
                "USERNAME_LENGTH_EXCEEDED",
                400,
                "The maximum length for username is 50.",
                [],
                {},
            ), 400

        # Check if password match
        if password == retypePassword:
            # Insert into database
            result = user.register(name, username, retypePassword)

            # Log in
            createLoginSession(
                result["user_id"], result["name"], result["username"], retypePassword
            )

            # Respond to client
            return api_response("SUCCESS", 200, "Successfully registered", [], {})

        else:
            return api_response(
                "PASSWORDS_DO_NOT_MATCH",
                400,
                "Passwords do not match. Please try again.",
                [],
                {},
            ), 400

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Login ==========
@api_route.route("/auth/login", methods=["POST"])
def login():
    try:
        # Data
        data = request.json
        username = str(data.get("username"))
        password = str(data.get("password"))

        # Check into database
        status, code, result = user.authenticate(username, password)

        if status == "SUCCESS":
            createLoginSession(
                result["user_id"], result["name"], result["username"], password
            )
            return api_response(status, code, "User verified", [], {})

        else:
            return api_response(status, code, result, [], {}), code

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Who am I? ==========
@api_route.route("/auth/whoami", methods=["GET"])
@logged_in_only_api
def whoAmI():
    userData = {
        "user_id": session["user_id"],
        "name": session["name"],
        "username": session["username"],
        "key": session["key"],
    }

    return api_response("SUCCESS", 200, f"Hello, {session['name']}", userData, {})


# ========== Check username availablity ==========
@api_route.route("/account/username/available", methods=["POST"])
def checkAvailablity():
    try:
        # Data
        data = request.json
        username = str(data.get("username"))

        # Check into database
        status, code, result = user.checkUsername(username)

        return api_response(status, code, result, [], {}), code

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Account update ==========
@api_route.route("/account/update", methods=["PATCH"])
def updateProfile():
    try:
        # data
        data = request.json
        user_id = session["user_id"]

        updates = {}
        if "name" in data:
            name = str(data.get("name"))
            if len(name) > 50:
                return api_response(
                    "NAME_LENGTH_EXCEEDED",
                    400,
                    "The maximum length for a name is 50.",
                    [],
                    {},
                ), 400

            updates["name"] = name

        if "username" in data:
            username = str(data.get("username"))
            if len(username) > 50:
                return api_response(
                    "USERNAME_LENGTH_EXCEEDED",
                    400,
                    "The maximum length for username is 50.",
                    [],
                    {},
                ), 400

            # Check the availablity first
            status, code, result = user.checkUsername(username)
            if status == "SUCCESS":
                updates["username"] = username

            else:
                return api_response(
                    status,
                    code,
                    "Username is already in use. Please try another one.",
                    [],
                    {},
                ), code

        # If no data provided
        if not updates:
            return api_response(
                "BAD_REQUEST",
                400,
                "No data was sent to the server. Please ensure you have filled in the required fields.",
                [],
                {},
            ), 400

        # Save changes
        status, code, result = user.updateProfile(user_id, updates)

        if status == "SUCCESS":
            # Update the session
            if "name" in data:
                session["name"] = str(data.get("name"))

            if "username" in data:
                session["username"] = str(data.get("username"))

            # Return success response
            return api_response("SUCCESS", 200, result, [], {})

        else:
            return api_response(
                status,
                code,
                "No data was sent to the server. Please ensure you have filled in the required fields.",
                [],
                {},
            ), code

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Change account password ==========
@api_route.route("/account/change-password", methods=["PUT"])
@logged_in_only_api
def updateUserPassword():
    try:
        # data
        data = request.json
        new_password = str(data.get("password"))
        user_id = session["user_id"]
        current_password = session["key"]

        # Proceed to change the password
        status, code, result = user.updateProfilePassword(
            new_password, user_id, current_password
        )

        if status == "SUCCESS":
            session["key"] = str(data.get("password"))
            return api_response("SUCCESS", 200, result, [], {})

        else:
            return api_response(status, code, result, [], {}), code

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Import data ==========
importer = DataImporter()


@api_route.route("/account/import", methods=["POST"])
@logged_in_only_api
def importData():
    try:
        # Data
        data = request.json
        typeFile = str(data.get("type_file"))

        # If CSV
        if typeFile == "csv":
            csvSheet = data.get("data_sheet")
            selectedKey = int(data.get("select_key"))

            status, code, result = importer.process_csv(csvSheet)

            if status == "SUCCESS":
                # Import into database
                for eachPw in result:
                    try:
                        user.import_accounts(
                            eachPw, selectedKey, session["user_id"], session["key"]
                        )

                    except Exception as err:
                        return api_response(
                            "SERVER_ERROR",
                            500,
                            f"An error occurred on the server. \nError message:{str(err)}",
                            [],
                            {},
                        ), 500

            else:
                return api_response(status, code, result, [], {}), code

        # If JSON
        elif typeFile == "json":
            try:
                jsonData = data.get("json_data")
                metadata = jsonData.get("metadata")
                encrypted = metadata.get("encrypted")

                # Check If password protected
                if encrypted:
                    filePassword = str(data.get("file_password"))

                    # Fix form handler issue on client-side
                    if not filePassword:
                        return api_response(
                            "PASSWORD_REQUIRED",
                            403,
                            "Encryption password required",
                            [],
                            {},
                        ), 403

                    # Decrypt data
                    status, code, result = importer.decrypt_data(jsonData, filePassword)
                    if status != "SUCCESS":
                        return api_response(status, code, result, [], {}), code

                    else:
                        # Import into db
                        importer.import_into_db(
                            result, session["user_id"], session["key"]
                        )

                # If unprotected
                else:
                    userData = jsonData.get("data")
                    importer.import_into_db(
                        userData, session["user_id"], session["key"]
                    )

            # If unable to read the json file
            except Exception:
                return api_response(
                    "UNSUPPORTED_FILE",
                    400,
                    "The selected file is corrupted or unsupported. Ensure the file is not corrupted and comes from Sunako.",
                    [],
                    {},
                ), 400

        # If file type is other than CSV and JSON
        else:
            return api_response(
                "UNSUPPORTED_FILE",
                400,
                "The selected file could not be recognized. Please upload a valid backup file with a .json or .csv extension.",
                [],
                {},
            ), 400

        # return process successful
        return api_response("SUCCESS", 200, "Successfully imported data", [], {})

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Export data ==========
exporter = DataExporter()


@api_route.route("/account/export", methods=["POST"])
@logged_in_only_api
def exportData():
    try:
        # Data
        data = request.json
        exportFormat = str(data.get("export_format"))
        exportPassword = str(data.get("export_password"))

        # Get all user keys and password
        allUserKey = user.user_saved_keys(session["user_id"], session["key"])
        allUserPw = user.user_saved_accounts(session["user_id"], session["key"])

        # Export file into json format
        if exportFormat == "json":
            userData = {"keys": allUserKey, "passwords": allUserPw}

            if exportPassword:
                result = {
                    "file_type": "json",
                    "json_file": exporter.export_encrypted(userData, exportPassword),
                }

                return api_response(
                    "SUCCESS", 200, "Successfully exported data", result, {}
                )

            else:
                result = {
                    "file_type": "json",
                    "json_file": exporter.export_unencrypted(userData),
                }

                return api_response(
                    "SUCCESS", 200, "Successfully exported data", result, {}
                )

        # Export file into csv format
        elif exportFormat == "csv":
            dataSheet = []

            # Serialize data for support Excel and Browser
            for pw in allUserPw:
                service_url = (
                    pw["url"] if pw["url"] else "https://from.text-encryptor.app/"
                )
                service_notes = pw["note"] if pw["note"] else ""

                dataSheet.append(
                    {
                        "name": pw["name"],
                        "url": service_url,
                        "username": pw["username"],
                        "password": pw["password"],
                        "note": service_notes,
                    }
                )

            result = exporter.export_csv(dataSheet)
            return api_response(
                "SUCCESS", 200, "Successfully exported data", result, {}
            )

        else:
            return api_response(
                "UNSUPPORTED_FILE",
                400,
                "File format not supported. Only .json and .csv are supported.",
                [],
                {},
            ), 400

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message: {str(err)}",
            [],
            {},
        ), 500


# ========== Account delete ==========
@api_route.route("/account/delete", methods=["DELETE"])
@logged_in_only_api
def deleteUserAccount():
    try:
        user_id = session["user_id"]

        # Proceed with deletion
        status, code, result = user.deleteProfile(user_id)

        if status == "SUCCESS":
            # Clear the session
            session.clear()

            # Return success response
            return api_response(status, code, result, [], {})

        else:
            return api_response(status, code, result, [], {}), code

    except Exception as err:
        return api_response(
            "error",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


#
# ========== Key manager ==========
#

keys = KeyManager()


# ========== Get all user keys ==========
@api_route.route("/user/keys", methods=["GET"])
@logged_in_only_api
def listUserKeys():
    try:
        userKeys = keys.get_user_key_all(session["user_id"], session["key"])
        return api_response("SUCCESS", 200, "Keys available", userKeys, {})

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Get some user key ==========
@api_route.route("/user/key/<key_id>", methods=["GET"])
@logged_in_only_api
def listUserKey(key_id):
    try:
        userKeys = keys.get_user_key(key_id, session["user_id"], session["key"])

        if userKeys:
            return api_response("SUCCESS", 200, "Keys available", userKeys, {})
        else:
            return api_response(
                "KEY_NOT_AVAILABLE",
                404,
                "The encryption key may have been deleted. Please refresh the page and try again.",
                [],
                {},
            ), 404

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Create new encryption key ==========
@api_route.route("/user/key/create", methods=["POST"])
@logged_in_only_api
def createEncryptionKey():
    try:
        # Data
        data = request.json
        keyName = str(data.get("key_name"))
        theKey = str(data.get("the_key"))

        user_id = session["user_id"]
        session_key = session["key"]

        # Check key name length
        if len(keyName) > 20:
            return api_response(
                "KEY_NAME_LENGTH_EXCEEDED",
                400,
                "The maximum length for a key name is 20.",
                [],
                {},
            ), 400

        # Insert into db
        status, code, result = keys.create_user_key(
            keyName, theKey, user_id, session_key
        )
        return api_response(status, code, result, [], {}), code

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Edit encryption key ==========
@api_route.route("/user/key/<key_id>/edit", methods=["PUT"])
@logged_in_only_api
def editEncryptionKey(key_id):
    try:
        # Data
        data = request.json
        keyName = str(data.get("edit_key_name"))
        theKey = str(data.get("edit_the_key"))

        user_id = session["user_id"]
        session_key = session["key"]

        # Check key name length
        if len(keyName) > 20:
            return api_response(
                "KEY_NAME_LENGTH_EXCEEDED",
                400,
                "The maximum length for a key name is 20.",
                [],
                {},
            ), 400

        # Insert into db
        status, code, result = keys.edit_user_key(
            key_id, keyName, theKey, user_id, session_key
        )

        return api_response(status, code, result, [], {}), code

    except Exception as err:
        return api_response(
            "error",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Delete key ==========
@api_route.route("/user/key/<key_id>/delete", methods=["DELETE"])
@logged_in_only_api
def deleteKey(key_id):
    try:
        status, code, result = keys.delete_user_key(key_id)
        return api_response(status, code, result, [], {}), code

    except Exception as err:
        return api_response(
            "error",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


@api_route.route("/user/key/delete_many", methods=["PUT"])
@logged_in_only_api
def deleteManyKey():
    try:
        data = request.json
        selectedKeyIds = data.get("selected_key")

        for eachKey in selectedKeyIds:
            status, code, result = keys.delete_user_key(eachKey)

            if status == "DATABASE_ERROR":
                return api_response(
                    status,
                    code,
                    f"An error occurred when deleting keys. \nError message:{str(result)}",
                    [],
                    {},
                ), code

        return api_response(
            "SUCCESS",
            200,
            f"{len(selectedKeyIds)} Keys deleted.",
            [],
            {},
        )

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


#
# ========== Password manager ==========
#

passwords = PasswordManager()


# ========== Get all user passwords ==========
@api_route.route("/user/passwords", methods=["GET"])
@logged_in_only_api
def listUserPasswords():
    try:
        userPasswords = passwords.get_user_password_all(
            session["user_id"], session["key"]
        )
        return api_response("SUCCESS", 200, "Passwords available", userPasswords, {})

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Get some user password ==========
@api_route.route("/user/password/<password_id>", methods=["GET"])
@logged_in_only_api
def listUserPassword(password_id):
    try:
        userPassword = passwords.get_user_password(
            password_id, session["user_id"], session["key"]
        )

        if userPassword:
            return api_response("SUCCESS", 200, "Password available", userPassword, {})

        else:
            return api_response(
                "PASSWORD_NOT_AVAILABLE",
                404,
                "The password may have been deleted. Please refresh the page and try again.",
                [],
                {},
            ), 404

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Create new password ==========
@api_route.route("/user/password/create", methods=["POST"])
@logged_in_only_api
def createPassword():
    try:
        # Data
        data = request.json
        serviceUrl = str(data.get("new_service_url"))
        serviceName = str(data.get("new_service_name"))
        username = str(data.get("new_username"))
        password = str(data.get("new_password"))
        serviceNotes = str(data.get("new_service_notes"))
        selectedKeyId = int(data.get("new_selected_key"))

        user_id = session["user_id"]
        session_key = session["key"]

        # Check serviceName and username length
        if len(serviceName) > 50:
            return api_response(
                "SERVICE_NAME_LENGTH_EXCEEDED",
                400,
                "The maximum length for service name is 50.",
                [],
                {},
            ), 400

        if len(username) > 50:
            return api_response(
                "USERNAME_LENGTH_EXCEEDED",
                400,
                "The maximum length for username is 50.",
                [],
                {},
            ), 400

        # Insert into db
        status, code, result = passwords.create_user_password(
            serviceUrl,
            serviceName,
            username,
            password,
            serviceNotes,
            selectedKeyId,
            user_id,
            session_key,
        )

        return api_response(status, code, result, [], {}), code

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Save password from link ==========
@api_route.route("/user/password/save", methods=["POST"])
@logged_in_only_api
def savePassword():
    try:
        data = request.json
        passwordList = data.get("passwords")
        key = data.get("key")

        user_id = session["user_id"]
        session_key = session["key"]

        success_status = []
        error_list = []

        for password in passwordList:
            # Check serviceName and username length
            if len(password["name"]) > 50:
                success_status.append("error")
                error_list.append(
                    {
                        "service_name": password["name"],
                        "error_info": "The maximum length for service name is 50.",
                    }
                )

            if len(password["username"]) > 50:
                success_status.append("error")
                error_list.append(
                    {
                        "service_name": password["name"],
                        "error_info": "The maximum length for username is 50.",
                    }
                )

            # Insert into db
            status, code, result = passwords.create_user_password(
                password["url"],
                password["name"],
                password["username"],
                password["password"],
                password["note"],
                key,
                user_id,
                session_key,
            )

            if status == "DATABASE_ERROR":
                error_list.append(
                    {"service_name": password["name"], "error_info": result}
                )

            success_status.append(status)

        success_count = success_status.count("success")
        error_count = success_status.count("error")

        if error_count == len(success_status):
            return api_response(
                "ERROR_SAVING_PASSWORDS",
                500,
                "Failed to save all password.",
                error_list,
                {},
            ), 500
        else:
            return api_response(
                "SUCCESS",
                200,
                f"{success_count} out of {len(success_status)} passwords were saved successfully.",
                error_list,
                {},
            )

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Edit password ==========
@api_route.route("/user/password/<password_id>/edit", methods=["PUT"])
@logged_in_only_api
def editPassword(password_id):
    try:
        # Data
        data = request.json
        serviceUrl = str(data.get("edit_service_url"))
        serviceName = str(data.get("edit_service_name"))
        username = str(data.get("edit_username"))
        password = str(data.get("edit_password"))
        serviceNotes = str(data.get("edit_service_notes"))
        selectedKeyId = int(data.get("edit_selected_key"))

        user_id = session["user_id"]
        session_key = session["key"]

        # Check serviceName and username length
        if len(serviceName) > 50:
            return api_response(
                "SERVICE_NAME_LENGTH_EXCEEDED",
                400,
                "The maximum length for service name is 50.",
                [],
                {},
            ), 400

        if len(username) > 50:
            return api_response(
                "USERNAME_LENGTH_EXCEEDED",
                400,
                "The maximum length for username is 50.",
                [],
                {},
            ), 400

        # Insert into db
        status, code, result = passwords.edit_user_password(
            serviceUrl,
            serviceName,
            username,
            password,
            serviceNotes,
            selectedKeyId,
            user_id,
            session_key,
            password_id,
        )

        return api_response(status, code, result, [], {}), code

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Share password ==========
@api_route.route("/user/password/share", methods=["POST"])
@logged_in_only_api
def sharePassword():
    try:
        data = request.json
        selectedPasswordIds = data.get("selected_password")

        passwordList = []

        # Get the passwords based on selected
        for eachPw in selectedPasswordIds:
            passwd = passwords.get_user_password(
                eachPw, session["user_id"], session["key"]
            )

            passwordList.append(
                {
                    "password_id": passwd["password_id"],
                    "name": passwd["service_name"],
                    "url": passwd["service_url"],
                    "username": passwd["username_account"],
                    "password": passwd["decrypted_password"],
                    "note": passwd["service_note"],
                }
            )

        blob, one_time_key = generate_share_link(json.dumps(passwordList))
        link = f"http://127.0.0.1:5000/p/{blob}#{one_time_key}"

        return api_response(
            "SUCCESS", 200, "Successfully generated link.", {"link": link}, {}
        )

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Export password ==========
@api_route.route("/user/password/export", methods=["POST"])
@logged_in_only_api
def exportPassword():
    try:
        data = request.json
        exportFormat = str(data.get("export_format"))
        exportPassword = str(data.get("export_password"))
        selectedPasswordIds = data.get("selected_password")

        keyList = []
        passwordList = []

        # Get the passwords based on selected
        for eachPw in selectedPasswordIds:
            passwd = passwords.get_user_password(
                eachPw, session["user_id"], session["key"]
            )

            passwordList.append(
                {
                    "password_id": passwd["password_id"],
                    "key_id": passwd["key_id"],
                    "name": passwd["service_name"],
                    "url": passwd["service_url"],
                    "username": passwd["username_account"],
                    "password": passwd["decrypted_password"],
                    "note": passwd["service_note"],
                }
            )

        # Get the keys based on selected password
        existing_ids = {item["key_id"] for item in keyList}

        for eachPwIds in passwordList:
            if eachPwIds["key_id"] not in existing_ids:
                keyList.append(
                    keys.get_user_key(
                        eachPwIds["key_id"], session["user_id"], session["key"]
                    )
                )

            existing_ids.add(eachPwIds["key_id"])

        # Export file into json format
        if exportFormat == "json":
            userData = {"keys": keyList, "passwords": passwordList}

            if exportPassword:
                result = {
                    "file_type": "json",
                    "json_file": exporter.export_encrypted(userData, exportPassword),
                }

                return api_response(
                    "SUCCESS", 200, "Successfully exported data", result, {}
                )

            else:
                result = {
                    "file_type": "json",
                    "json_file": exporter.export_unencrypted(userData),
                }

                return api_response(
                    "SUCCESS", 200, "Successfully exported data", result, {}
                )

        # Export file into csv format
        elif exportFormat == "csv":
            dataSheet = []

            # Serialize data for support Excel and Browser
            for pw in passwordList:
                service_url = (
                    pw["url"] if pw["url"] else "https://from.text-encryptor.app/"
                )
                service_notes = pw["note"] if pw["note"] else ""

                dataSheet.append(
                    {
                        "name": pw["name"],
                        "url": service_url,
                        "username": pw["username"],
                        "password": pw["password"],
                        "note": service_notes,
                    }
                )

            result = exporter.export_csv(dataSheet)
            return api_response(
                "SUCCESS", 200, "Successfully exported data", result, {}
            )

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


# ========== Delete password ==========
@api_route.route("/user/password/<password_id>/delete", methods=["DELETE"])
@logged_in_only_api
def deletePassword(password_id):
    try:
        status, code, result = passwords.delete_user_password(password_id)
        return api_response(status, code, result, [], {}), code

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


@api_route.route("/user/password/delete_many", methods=["PUT"])
@logged_in_only_api
def deleteManyPassword():
    try:
        data = request.json
        selectedPasswordIds = data.get("selected_password")

        for eachPw in selectedPasswordIds:
            status, code, result = passwords.delete_user_password(eachPw)

            if status == "DATABASE_ERROR":
                return api_response(
                    status,
                    code,
                    f"An error occurred when deleting passwords. \nError message:{str(result)}",
                    [],
                    {},
                ), code

        return api_response(
            "SUCCESS",
            200,
            f"{len(selectedPasswordIds)} Passwords deleted.",
            [],
            {},
        )

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500


recovery_method = Recovery()


# ========== Recovery ==========
@api_route.route("/account/recovery", methods=["POST"])
def recoverAccount():
    try:
        data = request.json
        username = str(data.get("username"))
        password = data.get("password")

        recovered_data = {}

        # Get user information
        user_info = recovery_method.get_user_information(username)

        # Try to decrypt first
        status, code, result = recovery_method.user_saved_keys(
            user_info["user_id"], password
        )

        if status == "SUCCESS":
            user_keys = result
            user_passwords = recovery_method.user_saved_accounts(
                user_info["user_id"], password
            )

            recovered_data = {"keys": user_keys, "passwords": user_passwords}

            # Then check for duplicate user account
            status, code, result = user.checkUsername(username)
            if status == "SUCCESS":
                # Recover the account
                recovered_account = user.register(
                    user_info["name"], user_info["username"], password
                )

                # Recover the data
                importer.import_into_db(
                    recovered_data, recovered_account["user_id"], password
                )

                # Log-in the user with recovered account
                createLoginSession(
                    recovered_account["user_id"],
                    recovered_account["name"],
                    recovered_account["username"],
                    password,
                )

                # Delete the old account
                recovery_method.delete_old_account(user_info["user_id"])

                return api_response("SUCCESS", 200, "Account recovered.", [], {})

            elif status == "DUPLICATE_USERNAME":
                duplicate_action = data.get("action")

                if duplicate_action:
                    option = duplicate_action.get("option")

                    if option == "export":
                        result = {
                            "file_type": "json",
                            "json_file": exporter.export_encrypted(
                                recovered_data, password
                            ),
                        }

                        return api_response(
                            "SUCCESS", 201, "Successfully exported data", result, {}
                        ), 201

                    else:
                        new_username = duplicate_action.get("username")

                        # Check username length
                        if len(new_username) > 50:
                            return api_response(
                                "USERNAME_LENGTH_EXCEEDED",
                                400,
                                "The maximum length for username is 50.",
                                [],
                                {},
                            ), 400

                        status, code, result = user.checkUsername(new_username)

                        if status == "SUCCESS":
                            # Recover the account
                            recovered_account = user.register(
                                user_info["name"], new_username, password
                            )

                            # Recover the data
                            importer.import_into_db(
                                recovered_data, recovered_account["user_id"], password
                            )

                            # Log-in the user with recovered account
                            createLoginSession(
                                recovered_account["user_id"],
                                recovered_account["name"],
                                recovered_account["username"],
                                password,
                            )

                            # Delete the old account
                            recovery_method.delete_old_account(user_info["user_id"])

                            return api_response(
                                "SUCCESS", 200, "Account recovered.", [], {}
                            )

                        else:
                            return api_response(status, code, result, [], {}), code

                # Return this if duplicate_action is empty
                else:
                    return api_response("NO_ACTION_PROVIDED", 400, result, [], {}), 400

            else:
                return api_response("DATABASE_ERROR", 500, result, [], {}), 500
        else:
            return api_response("INCORRECT_PASSWORD", 403, result, [], {}), 403

    except Exception as err:
        return api_response(
            "SERVER_ERROR",
            500,
            f"An error occurred on the server. \nError message:{str(err)}",
            [],
            {},
        ), 500

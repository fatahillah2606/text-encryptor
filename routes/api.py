import binascii
from functools import wraps

from flask import Blueprint, jsonify, request, session

from src.data_manager import KeyManager, PasswordManager, UserManager
from src.encryptor import decrypt_aes, encrypt_aes, generate_password, get_valid_key
from src.essentials import createLoginSession


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


# API protection
def logged_in_only_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return api_response("error", 403, str("Access denied."), [], {}), 403

        return f(*args, **kwargs)

    return decorated_function


api_route = Blueprint("api", __name__)

#
# Encrptor process
#


# encription key
@api_route.route("/encryptor/encryption_key", methods=["POST", "GET"])
def encryption_key():
    if request.method == "POST":
        try:
            data = request.json
            valid_key = get_valid_key(str(data.get("key")))

            return api_response(
                "success",
                200,
                "The encryption key has been set",
                {"key": valid_key["generated_key"]},
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
            return api_response(
                "error", 400, "The encryption key is not provided.", [], {}
            ), 400

        valid_key = get_valid_key(key)

        vi, encrypted_text = encrypt_aes(text, valid_key["encoded_key"])
        encrypted_text = binascii.hexlify(vi + encrypted_text).decode()

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
            return api_response(
                "error", 400, "The encryption key is not provided.", [], {}
            ), 400

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
            return api_response(
                "error", 400, "The encryption key is not provided.", [], {}
            ), 400

        # Check if password length is 0 or bellow
        if length <= 0:
            raise ValueError("Password length must be at least 1 character long!")

        password = generate_password(length)
        valid_key = get_valid_key(key)

        encrypted = ""
        if encrypt:
            iv, encrypted_text = encrypt_aes(password, valid_key["encoded_key"])
            encrypted = binascii.hexlify(iv + encrypted_text).decode()

        data = {"password": password, "encrypted_password": encrypted}

        return api_response("success", 200, "Password successfully created", data, {})

    except ValueError as err:
        return api_response("error", 400, str(err), [], {}), 400

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


#
# Auth process
#

user = UserManager()


# Register
@api_route.route("/auth/register", methods=["POST"])
def register():
    try:
        # Data
        data = request.json
        name = str(data.get("name"))
        username = str(data.get("username"))
        password = str(data.get("password"))
        retypePassword = str(data.get("retype_password"))

        # Check if password match
        if password == retypePassword:
            # Insert into database
            result = user.register(name, username, retypePassword)

            # Log in
            createLoginSession(
                result["user_id"], result["name"], result["username"], retypePassword
            )

            # Respond to client
            return api_response("success", 200, "Successfully registered", [], {})

        else:
            return api_response("error", 400, "Password does not match!", [], {}), 400

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Login
@api_route.route("/auth/login", methods=["POST"])
def login():
    try:
        # Data
        data = request.json
        username = str(data.get("username"))
        password = str(data.get("password"))

        # Check into database
        status, result = user.authenticate(username, password)

        if status == "success":
            createLoginSession(
                result["user_id"], result["name"], result["username"], password
            )
            return api_response("success", 200, "User verified", [], {})

        elif status == "fail":
            return api_response("error", 403, result, [], {}), 403

        # If database error
        else:
            return api_response("error", 500, result, [], {}), 500

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Who am I?
@api_route.route("/auth/whoami", methods=["GET"])
@logged_in_only_api
def whoAmI():
    userData = {
        "user_id": session["user_id"],
        "name": session["name"],
        "username": session["username"],
        "key": session["key"],
    }

    return api_response("success", 200, f"Hello, {session['name']}", userData, {})


# Check username availablity
@api_route.route("/account/username/available", methods=["POST"])
def checkAvailablity():
    try:
        # Data
        data = request.json
        username = str(data.get("username"))

        # Check into database
        status, result = user.checkUsername(username)

        if status == "success":
            return api_response("success", 200, "Username available!", [], {})
        elif status == "failed":
            return api_response("error", 409, "Username already in use!", [], {}), 409
        else:
            return api_response("error", 500, result, [], {}), 500

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Account update
@api_route.route("/account/update", methods=["PATCH"])
def updateProfile():
    try:
        # data
        data = request.json
        user_id = session["user_id"]

        updates = {}
        if "name" in data:
            updates["name"] = str(data.get("name"))

        if "username" in data:
            username = str(data.get("username"))

            # Check the availablity first
            status, result = user.checkUsername(username)
            if status == "success":
                updates["username"] = username
            elif status == "failed":
                return api_response(
                    "error", 409, "Username already in use!", [], {}
                ), 409

        # If no data provided
        if not updates:
            return api_response("error", 400, "No data provided", [], {}), 400

        # Save changes
        status, result = user.updateProfile(user_id, updates)

        if status == "success":
            # Update the session
            if "name" in data:
                session["name"] = str(data.get("name"))

            if "username" in data:
                session["username"] = str(data.get("username"))

            # Return success response
            return api_response("success", 200, "Account updated", [], {})
        elif status == "failed":
            return api_response("failed", 400, "No data provided", [], {})
        else:
            return api_response("error", 500, result, [], {}), 500

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Change account password
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
        status, result = user.updateProfilePassword(
            new_password, user_id, current_password
        )

        if status == "success":
            session["key"] = str(data.get("password"))
            return api_response("success", 200, result, [], {})
        else:
            return api_response("error", 500, result, [], {}), 500

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Account delete
@api_route.route("/account/delete", methods=["DELETE"])
@logged_in_only_api
def deleteUserAccount():
    try:
        user_id = session["user_id"]

        # Proceed with deletion
        status, result = user.deleteProfile(user_id)

        if status == "success":
            # Clear the session
            session.clear()

            # Return success response
            return api_response("success", 200, "Account updated", [], {})
        else:
            return api_response("error", 500, result, [], {}), 500

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


#
# Key manager
#

keys = KeyManager()


# Get all user keys
@api_route.route("/user/keys", methods=["GET"])
@logged_in_only_api
def listUserKeys():
    try:
        userKeys = keys.get_user_key_all(session["user_id"], session["key"])
        return api_response("success", 200, "Keys available", userKeys, {})

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Get some user key
@api_route.route("/user/key/<key_id>", methods=["GET"])
@logged_in_only_api
def listUserKey(key_id):
    try:
        userKeys = keys.get_user_key(key_id, session["user_id"], session["key"])

        if userKeys:
            return api_response("success", 200, "Keys available", userKeys, {})
        else:
            return api_response("error", 404, "Keys unavailable", [], {})

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Create new encryption key
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

        # Insert into db
        status, result = keys.create_user_key(keyName, theKey, user_id, session_key)

        if status == "success":
            return api_response("success", 200, result, [], {})
        else:
            return api_response("error", 500, result, [], {}), 500

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Edit encryption key
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

        # Insert into db
        status, result = keys.edit_user_key(
            key_id, keyName, theKey, user_id, session_key
        )

        if status == "success":
            return api_response("success", 200, result, [], {})
        else:
            return api_response("error", 500, result, [], {}), 500

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Delete key
@api_route.route("/user/key/<key_id>/delete", methods=["DELETE"])
@logged_in_only_api
def deleteKey(key_id):
    try:
        status, result = keys.delete_user_key(key_id)

        if status == "success":
            return api_response("success", 200, result, [], {})
        else:
            return api_response("error", 500, result, [], {}), 500

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


#
# Password manager
#

passwords = PasswordManager()


# Get all user passwords
@api_route.route("/user/passwords", methods=["GET"])
@logged_in_only_api
def listUserPasswords():
    try:
        userPasswords = passwords.get_user_password_all(
            session["user_id"], session["key"]
        )
        return api_response("success", 200, "Passwords available", userPasswords, {})

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Get some user password
@api_route.route("/user/password/<password_id>", methods=["GET"])
@logged_in_only_api
def listUserPassword(password_id):
    try:
        userPassword = passwords.get_user_password(
            password_id, session["user_id"], session["key"]
        )

        if userPassword:
            return api_response("success", 200, "Password available", userPassword, {})
        else:
            return api_response("error", 404, "Password unavailable", [], {})

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Create new password
@api_route.route("/user/password/create", methods=["POST"])
@logged_in_only_api
def createPassword():
    try:
        # Data
        data = request.json
        serviceName = str(data.get("new_service_name"))
        username = str(data.get("new_username"))
        password = str(data.get("new_password"))
        selectedKeyId = int(data.get("new_selected_key"))

        user_id = session["user_id"]
        session_key = session["key"]

        # Insert into db
        status, result = passwords.create_user_password(
            serviceName, username, password, selectedKeyId, user_id, session_key
        )

        if status == "success":
            return api_response("success", 200, result, [], {})
        else:
            return api_response("error", 500, result, [], {}), 500

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Edit password
@api_route.route("/user/password/<password_id>/edit", methods=["PUT"])
@logged_in_only_api
def editPassword(password_id):
    try:
        # Data
        data = request.json
        serviceName = str(data.get("edit_service_name"))
        username = str(data.get("edit_username"))
        password = str(data.get("edit_password"))
        selectedKeyId = int(data.get("edit_selected_key"))

        user_id = session["user_id"]
        session_key = session["key"]

        # Insert into db
        status, result = passwords.edit_user_password(
            serviceName,
            username,
            password,
            selectedKeyId,
            user_id,
            session_key,
            password_id,
        )

        if status == "success":
            return api_response("success", 200, result, [], {})
        else:
            return api_response("error", 500, result, [], {}), 500

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Delete password
@api_route.route("/user/password/<password_id>/delete", methods=["DELETE"])
@logged_in_only_api
def deletePassword(password_id):
    try:
        status, result = passwords.delete_user_password(password_id)

        if status == "success":
            return api_response("success", 200, result, [], {})
        else:
            return api_response("error", 500, result, [], {}), 500

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500

import binascii
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
from flask import Blueprint, jsonify, request, session

from src.data_manager import get_user_key, get_user_key_all, delete_user_key, get_user_password, get_user_password_all, delete_user_password
from src.encryptor import decrypt_aes, encrypt_aes, generate_password, get_valid_key


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


# bcrypt hashing
def bcryptHashing(text):
    hashedText = bcrypt.hashpw(text.encode("utf-8"), bcrypt.gensalt())
    hashedText = hashedText.decode("utf-8")
    return hashedText


# bcrypt check
def bcryptCheck(text, hashedText):
    encodeText = text.encode("utf-8")
    encodeHashedText = hashedText.encode("utf-8")
    return bcrypt.checkpw(encodeText, encodeHashedText)


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

# Register
@api_route.route("/auth/register", methods=["POST"])
def register():
    try:
        # Database path
        db_path = os.path.join("db", "vault_manager.db")

        # Data
        data = request.json
        name = str(data.get("name"))
        username = str(data.get("username"))
        password = str(data.get("password"))
        retypePassword = str(data.get("retype_password"))

        # Check if password match
        if password == retypePassword:
            hashedPassword = bcryptHashing(retypePassword)

            # Insert into database
            with sqlite3.connect(db_path) as conn:
                query = (
                    "INSERT INTO users (name, username, password_hash) VALUES (?, ?, ?)"
                )

                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(query, (name, username, hashedPassword))

                user_id = cursor.lastrowid
                conn.commit()

            # Log in
            session.permanent = True
            session["exipred"] = (
                datetime.now(timezone.utc) + timedelta(hours=1)
            ).isoformat()
            session["user_id"] = user_id
            session["name"] = name
            session["username"] = username
            session["key"] = retypePassword

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
        # Database path
        db_path = os.path.join("db", "vault_manager.db")

        # Data
        data = request.json
        username = str(data.get("username"))
        password = str(data.get("password"))

        # Check into database
        with sqlite3.connect(db_path) as conn:
            query = "SELECT * FROM users WHERE username = ?"

            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute(query, (username,))
            userdata = cursor.fetchone()

            # If user available
            if userdata:
                # Check the password
                valid = bcryptCheck(password, userdata["password_hash"])
                if valid:
                    # Log in
                    session.permanent = True
                    session["expired"] = (
                        datetime.now(timezone.utc) + timedelta(hours=1)
                    ).isoformat()
                    session["user_id"] = userdata["user_id"]
                    session["name"] = userdata["name"]
                    session["username"] = userdata["username"]
                    session["key"] = password

                    return api_response("success", 200, "User verified", [], {})
                else:
                    return api_response(
                        "error", 403, "Incorrect username or password", [], {}
                    ), 403

            else:
                return api_response(
                    "error", 403, "Incorrect username or password", [], {}
                ), 403

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


#
# Data manager process
#

# Get all user keys
@api_route.route("/user/keys", methods=["GET"])
@logged_in_only_api
def listUserKeys():
    try:
        userKeys = get_user_key_all(session["user_id"], session["key"])
        return api_response("success", 200, "Keys available", userKeys, {})

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Get some user key
@api_route.route("/user/key/<key_id>", methods=["GET"])
@logged_in_only_api
def listUserKey(key_id):
    try:
        userKeys = get_user_key(key_id, session["user_id"], session["key"])

        if userKeys:
            return api_response("success", 200, "Keys available", userKeys, {})
        else:
            return api_response("error", 404, "Keys unavailable", [], {})

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500
    

# Delete key
@api_route.route("/user/key/<key_id>/delete", methods=["DELETE"])
@logged_in_only_api
def deleteKey(key_id):
    try:
        result = delete_user_key(key_id)

        if result is True:
            return api_response("success", 200, "Key deleted successfully.", [], {})
        else:
            return api_response("error", 500, result, [], {}), 500
        
    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500


# Create new encryption key
@api_route.route("/user/create/key", methods=["POST"])
@logged_in_only_api
def createEncryptionKey():
    try:
        # Database path
        db_path = os.path.join("db", "vault_manager.db")

        # Data
        data = request.json
        keyName = str(data.get("key_name"))
        theKey = str(data.get("the_key"))
        user_id = session["user_id"]

        # Encrypt the key with master key
        master_key = get_valid_key(session["key"])
        iv, encrypted_key = encrypt_aes(theKey, master_key["encoded_key"])

        # Proceed into database
        with sqlite3.connect(db_path) as conn:
            query = "INSERT INTO keys (user_id, key_name, encrypted_key, iv) VALUES (?, ?, ?, ?)"

            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute(query, (user_id, keyName, encrypted_key, iv))

            conn.commit()

        return api_response(
            "success", 200, f"Successfully added key: {keyName}", [], {}
        )

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500
    

# 
# Password manager
# 

# Get all user passwords
@api_route.route("/user/passwords", methods=["GET"])
@logged_in_only_api
def listUserPasswords():
    try:
        userPasswords = get_user_password_all(session["user_id"], session["key"])
        return api_response("success", 200, "Passwords available", userPasswords, {})

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500
    

# Get some user password
@api_route.route("/user/password/<password_id>", methods=["GET"])
@logged_in_only_api
def listUserPassword(password_id):
    try:
        userPassword = get_user_password(password_id, session["user_id"], session["key"])

        if userPassword:
            return api_response("success", 200, "Password available", userPassword, {})
        else:
            return api_response("error", 404, "Password unavailable", [], {})

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500
    


# Delete password
@api_route.route("/user/password/<password_id>/delete", methods=["DELETE"])
@logged_in_only_api
def deletePassword(password_id):
    try:
        result = delete_user_password(password_id)

        if result is True:
            return api_response("success", 200, "Password deleted successfully.", [], {})
        else:
            return api_response("error", 500, result, [], {}), 500
        
    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500



# Create new password
@api_route.route("/user/create/password", methods=["POST"])
@logged_in_only_api
def createPassword():
    try:
        # Database path
        db_path = os.path.join("db", "vault_manager.db")

        # Data
        data = request.json
        serviceName = str(data.get("new_service_name"))
        username = str(data.get("new_username"))
        password = str(data.get("new_password"))
        selectedKeyId = int(data.get("new_selected_key"))
        user_id = session["user_id"]

        # Encrypt the password with selected key
        selected_key = get_user_key(selectedKeyId, user_id, session["key"])
        valid_selected_key = get_valid_key(selected_key["encryption_key"])
        iv, encrypted_password = encrypt_aes(password, valid_selected_key["encoded_key"])

        # Proceed into database
        with sqlite3.connect(db_path) as conn:
            query = "INSERT INTO passwords (user_id, key_id, service_name, username_account, encrypted_password, iv) VALUES (?, ?, ?, ?, ?, ?)"

            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute(query, (user_id, selectedKeyId, serviceName, username, encrypted_password, iv))

            conn.commit()

        return api_response(
            "success", 200, f"Successfully added password: {serviceName}", [], {}
        )

    except Exception as err:
        return api_response("error", 500, str(err), [], {}), 500

import binascii
import os
import sqlite3
from functools import wraps

from flask import Blueprint, redirect, render_template, session, url_for

from src.encryptor import decrypt_aes, get_valid_key


# pages protection
def logged_in_only_pages(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("pages.login"))

        return f(*args, **kwargs)

    return decorated_function


pages_route = Blueprint("pages", __name__)


@pages_route.context_processor
def inject_globals():
    if "username" in session:
        user_keys = []

        # Database path
        db_path = os.path.join("db", "vault_manager.db")

        # Check user keys into database
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Try to get all keys from user
            query = "SELECT * FROM keys WHERE user_id = ?"
            cursor.execute(query, (session["user_id"],))

            rows = cursor.fetchall()

            if rows:
                for row in rows:
                    # Combine iv + encrypted_key and unhexlify
                    key_from_db = binascii.hexlify(
                        row["iv"] + row["encrypted_key"]
                    ).decode()
                    key_from_db = binascii.unhexlify(key_from_db)

                    # Get valid key
                    master_key = get_valid_key(session["key"])

                    # Decrypt key
                    decrypted_key = decrypt_aes(key_from_db, master_key["encoded_key"])

                    user_keys.append(
                        {
                            "key_id": row["key_id"],
                            "key_name": row["key_name"],
                            "encrypted_key": decrypted_key,
                        }
                    )
    else:
        user_keys = []

    return {
        "name": session.get("name"),
        "username": session.get("username"),
        "key": session.get("key"),
        "active_page": None,
        "user_keys": user_keys,
    }


@pages_route.route("/login")
def login():
    if "username" in session:
        return redirect(url_for("pages.dashboard"))
    else:
        return render_template("login.html")


@pages_route.route("/register")
def register():
    if "username" in session:
        return redirect(url_for("pages.dashboard"))
    else:
        return render_template("register.html")


@pages_route.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("pages.login"))


@pages_route.route("/dashboard")
@logged_in_only_pages
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")


@pages_route.route("/key_manager")
@logged_in_only_pages
def key_manager():
    return render_template("key_manager.html", active_page="key_manager")


@pages_route.route("/password_manager")
@logged_in_only_pages
def password_manager():
    return render_template("password_manager.html", active_page="password_manager")


@pages_route.route("/password_generator")
@logged_in_only_pages
def password_generator():
    return render_template("password_generator.html", active_page="password_generator")


@pages_route.route("/text_encryptor")
@logged_in_only_pages
def text_encryptor():
    return render_template("text_encryptor.html", active_page="text_encryptor")


@pages_route.route("/text_decryptor")
@logged_in_only_pages
def text_decryptor():
    return render_template("text_decryptor.html", active_page="text_decryptor")


# Guest menu
@pages_route.route("/guest/password-generator")
def passwordGenerator():
    return render_template(
        "guest/password-generator.html", active_page="passwordGenerator"
    )


@pages_route.route("/guest/text-encryptor")
def textEncryptor():
    return render_template("guest/text-encryptor.html", active_page="textEncryptor")


@pages_route.route("/guest/text-decryptor")
def textDecryptor():
    return render_template("guest/text-decryptor.html", active_page="textDecryptor")

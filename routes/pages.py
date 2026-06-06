import binascii
import os
import sqlite3
from functools import wraps

from flask import Blueprint, redirect, render_template, session, url_for

from src.data_manager import UserManager
from src.encryptor import decrypt_aes, get_valid_key

# Get available users
user = UserManager()


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
    # Get user list
    userList = user.getAvailableUsers()

    if "username" in session:
        return redirect(url_for("pages.dashboard"))
    elif userList:
        return render_template("pages/login.html", userlist=userList)
    else:
        return redirect(url_for("pages.register"))


@pages_route.route("/register")
def register():
    # Get user list
    userList = user.getAvailableUsers()

    if "username" in session:
        return redirect(url_for("pages.dashboard"))
    else:
        notice = (
            "No user accounts have been registered yet. To begin using the full password manager suite, please create an account."
            if not userList
            else ""
        )
        return render_template("pages/register.html", notice=notice)


@pages_route.route("/recovery")
def recovery():
    userList = user.getAvailableUsers()
    return render_template("pages/recovery.html", userlist=userList)


@pages_route.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("pages.login"))


@pages_route.route("/dashboard")
def dashboard():
    return render_template("pages/dashboard.html", active_page="dashboard")


@pages_route.route("/account_manager")
@logged_in_only_pages
def account_manager():
    return render_template("pages/account_manager.html", active_page="account_manager")


@pages_route.route("/key_manager")
@logged_in_only_pages
def key_manager():
    return render_template("pages/key_manager.html", active_page="key_manager")


@pages_route.route("/password_manager")
@logged_in_only_pages
def password_manager():
    return render_template(
        "pages/password_manager.html", active_page="password_manager"
    )


@pages_route.route("/tools")
def encryption_tools():
    return render_template("pages/tools.html", active_page="tools")

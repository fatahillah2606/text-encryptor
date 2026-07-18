from functools import wraps

from flask import Blueprint, redirect, render_template, session, url_for

from src.data_manager import Recovery, UserManager
from src.encryptor import NewEncryption

# Get available users
user = UserManager()

encryption_method = NewEncryption()
recovery_method = Recovery()


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
    user_keys = []
    if "username" in session:
        user_keys = user.user_saved_keys(session.get("user_id"), session.get("key"))

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

    recoveryAvailable = recovery_method.check_old_users()

    if "username" in session:
        return redirect(url_for("pages.dashboard"))
    elif userList:
        return render_template(
            "pages/login.html", userlist=userList, recovery=recoveryAvailable
        )
    else:
        return redirect(url_for("pages.register"))


@pages_route.route("/register")
def register():
    # Get user list
    userList = user.getAvailableUsers()

    recoveryAvailable = recovery_method.check_old_users()

    if "username" in session:
        return redirect(url_for("pages.dashboard"))
    else:
        notice = (
            "No user accounts have been registered yet. To begin using the full password manager suite, please create an account."
            if not userList
            else ""
        )
        return render_template(
            "pages/register.html", notice=notice, recovery=recoveryAvailable
        )


@pages_route.route("/recovery")
def recovery():
    userList = recovery_method.getRecoverableAccounts()

    recoveryAvailable = recovery_method.check_old_users()
    if recoveryAvailable:
        return render_template("pages/recovery.html", userlist=userList)
    else:
        return redirect(url_for("pages.login"))


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

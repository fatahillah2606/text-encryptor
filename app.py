import os
import secrets
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, abort, redirect, send_from_directory, session, url_for
from flask.sansio.app import timedelta
from flask.templating import render_template

from routes.api import api_route
from routes.pages import pages_route
from src.data_manager import UserManager
from src.db_manager import initialize_db

from colorama import Fore, Style

load_dotenv()


SESSION_KEY = secrets.token_hex()
# SESSION_KEY = os.getenv("SESSION_KEY") # for development, to prevent logged out when restarting


# ========== Check db ==========
db_path = os.path.join("db", "vault_manager.db")


def check_and_setup_db():
    print(f"[{Fore.GREEN}info{Style.RESET_ALL}] Checking database...")
    initialize_db()


app = Flask(__name__)
app.secret_key = SESSION_KEY
app.permanent_session_lifetime = timedelta(minutes=5)


app.register_blueprint(pages_route, url_prefix="/pages/")
app.register_blueprint(api_route, url_prefix="/api/")


# ========== Check session ==========
@app.before_request
def check_session():
    expired = session.get("expired")

    if expired:
        current_time = datetime.now(timezone.utc)
        expired_time = datetime.fromisoformat(expired)

        if current_time > expired_time:
            session.clear()
            redirect(url_for("pages.login"))

        session["expired"] = (current_time + timedelta(minutes=5)).isoformat()


# ========== Error handler ==========
@app.errorhandler(404)
def page_not_found(error):
    return "Page not found", 404


# ========== Favicon ==========
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/")
def home():
    return redirect(url_for("pages.home"))


user = UserManager()


@app.context_processor
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


# ========== Open shared link ==========
@app.route("/<shared_type>/<blob>")
def share_page(shared_type, blob):
    if shared_type == "t":
        return render_template(
            "pages/shared_text.html", active_page="shared_text", blob=blob
        )
    elif shared_type == "p":
        return render_template(
            "pages/shared_passwords.html", active_page="shared_passwords", blob=blob
        )
    else:
        abort(404, description="Invalid shared type")


if __name__ == "__main__":
    check_and_setup_db()
    app.run(debug=False)

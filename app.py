import os
import secrets
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, redirect, session, url_for
from flask.sansio.app import timedelta

from routes.api import api_route
from routes.pages import pages_route
from src.init_db import create_database, update_database

load_dotenv()

# SESSION_KEY = secrets.token_hex()
SESSION_KEY = os.getenv(
    "SESSION_KEY"
)  # for development, to prevent logged out when restarting

# Check db
db_path = os.path.join("db", "vault_manager.db")


def check_and_setup_db():
    print("Checking database...")
    if not os.path.exists(db_path):
        print("Database not found. Generating...")
        create_database()
    else:
        print("Database found!")
        update_database()


app = Flask(__name__)
app.secret_key = SESSION_KEY
app.permanent_session_lifetime = timedelta(minutes=5)


app.register_blueprint(pages_route, url_prefix="/pages/")
app.register_blueprint(api_route, url_prefix="/api/")


# Check session
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


@app.route("/")
def home():
    return redirect(url_for("pages.dashboard"))


if __name__ == "__main__":
    check_and_setup_db()
    app.run(debug=True)

import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, url_for
from flask.sansio.app import timedelta

from routes.api import api_route
from routes.pages import pages_route

load_dotenv()

SESSION_KEY = os.getenv("SESSION_KEY")

app = Flask(__name__)
app.secret_key = SESSION_KEY
app.permanent_session_lifetime = timedelta(hours=1)


app.register_blueprint(pages_route, url_prefix="/pages/")
app.register_blueprint(api_route, url_prefix="/api/")


@app.route("/")
def home():
    return redirect(url_for("pages.login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

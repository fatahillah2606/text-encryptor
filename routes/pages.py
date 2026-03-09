from flask import Blueprint, render_template, request, session, url_for

pages_route = Blueprint("pages", __name__)


@pages_route.route("/login")
def login():
    return render_template("login.html")


@pages_route.route("/encryptor/password-generator")
def passwordGenerator():
    return render_template("guest/password-generator.html")


@pages_route.route("/encryptor/text-encryptor")
def textEncryptor():
    return render_template("guest/text-encryptor.html")


@pages_route.route("/encryptor/text-decryptor")
def textDecryptor():
    return render_template("guest/text-decryptor.html")

from datetime import datetime, timedelta, timezone

import bcrypt
from flask import session


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


# Create login session
def createLoginSession(user_id, name, username, key):
    session.permanent = True
    session["expired"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    session["user_id"] = user_id
    session["name"] = name
    session["username"] = username
    session["key"] = key

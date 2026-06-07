import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from flask import session


# bcrypt hashing
def scryptHashing(text):
    salt = os.urandom(16)
    hashed_bytes = hashlib.scrypt(text.encode("utf-8"), salt=salt, n=16384, r=8, p=1)
    return salt + hashed_bytes


# bcrypt check
def scryptCheck(text, hashedText):
    try:
        salt = hashedText[:16]
        original_hash = hashedText[16:]

        new_hash = hashlib.scrypt(text.encode("utf-8"), salt=salt, n=16384, r=8, p=1)

        return hmac.compare_digest(original_hash, new_hash)
    except Exception:
        return False


# Create login session
def createLoginSession(user_id, name, username, key):
    session.permanent = True
    session["expired"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    session["user_id"] = user_id
    session["name"] = name
    session["username"] = username
    session["key"] = key

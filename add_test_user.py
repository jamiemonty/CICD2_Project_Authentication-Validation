#!/usr/bin/env python
"""Small helper to insert a test user with a bcrypt-hashed password.

Usage: python add_test_user.py

This script will attempt to insert a single test user. If the email
already exists it will report that and exit without duplicating.
"""
from pathlib import Path
import sqlite3
import os
import hashlib
import secrets

# Prefer bcrypt if available, otherwise fall back to PBKDF2-HMAC (stdlib)
try:
    import bcrypt  # type: ignore
    USE_BCRYPT = True
except Exception:
    USE_BCRYPT = False

DB_PATH = Path(__file__).parent / "users.db"


def hash_password(plain: str) -> str:
    """Return a password hash. Uses bcrypt when available, else PBKDF2-HMAC-SHA256.

    The returned format indicates the algorithm so it can be parsed later:
    - bcrypt:<hash>
    - pbkdf2$iterations$salt$hex
    """
    if USE_BCRYPT:
        hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())
        return f"bcrypt:{hashed.decode('utf-8')}"

    # PBKDF2 fallback
    iterations = 100_000
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, iterations)
    return f"pbkdf2${iterations}${salt.hex()}${dk.hex()}"


def insert_test_user(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    name = "Test User"
    email = "test.user@example.com"
    age = 30
    password = "s3cret-password"
    hashed = hash_password(password)

    try:
        cur.execute(
            """
            INSERT INTO users (name, email, age, hashed_password, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, email, age, hashed, "user"),
        )
        conn.commit()
        print(f"Inserted user {email}")
    except sqlite3.IntegrityError as e:
        # likely UNIQUE constraint on email
        print(f"Could not insert user: {e}")
    finally:
        conn.close()


def show_user(email: str, db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT user_id, name, email, age, role FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    if row:
        print("Found user:")
        print(row)
    else:
        print("User not found")


if __name__ == "__main__":
    insert_test_user()
    show_user("test.user@example.com")

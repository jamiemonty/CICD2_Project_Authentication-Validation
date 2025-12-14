# create_test_user_auth.py
import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    age INTEGER,
    hashed_password TEXT NOT NULL,
    role TEXT DEFAULT 'user'
)
""")

try:
    hashed = pwd_context.hash("testpass")
    cursor.execute(
        "INSERT INTO users (name, email, age, hashed_password, role) VALUES (?, ?, ?, ?, ?)",
        ("Test User4", "test4@sync.com", 25, hashed, "user")
    )
    conn.commit()
    print(f" User created in AUTH database with ID: {cursor.lastrowid}")
except Exception as e:
    print(f"Error:  {e}")

conn.close()
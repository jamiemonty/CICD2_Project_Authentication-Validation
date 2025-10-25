# create_db.py 
import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    age INTEGER NOT NULL,
    hashed_password TEXT NOT NULL,
    role TEXT DEFAULT 'user'
)
""")

conn.commit()
conn.close()
print("Database initialized.")
import sqlite3
from fastapi import FastAPI, HTTPException, Depends, status
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm
import os
from dotenv import load_dotenv

# Load .env file for secret key and admin credentials
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "JAMIESKEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "G00419525@atu.ie")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password")

app = FastAPI(title="User Authentication API")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Create default admin if not exists
@app.on_event("startup")
def create_admin():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (ADMIN_EMAIL,))
    admin = cursor.fetchone()
    if not admin:
        hashed_pw = hash_password(ADMIN_PASSWORD)
        cursor.execute(
            "INSERT INTO users (name, email, age, hashed_password, role) VALUES (?, ?, ?, ?, ?)",
            ("System Admin", ADMIN_EMAIL, 22, hashed_pw, "admin")
        )
        conn.commit()
        print(f"✅ Admin user created: {ADMIN_EMAIL}")
    else:
        print(f"🔒 Admin already exists: {ADMIN_EMAIL}")
    conn.close()

# User registration — cannot register as admin
@app.post("/api/users/register", status_code=status.HTTP_201_CREATED)
def register_user(name: str, email: str, age: int, password: str):
    if email == ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Cannot register as admin")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="Email already exists")
    hashed_password = hash_password(password)
    cursor.execute(
        "INSERT INTO users (name, email, age, hashed_password, role) VALUES (?, ?, ?, ?, ?)",
        (name, email, age, hashed_password, "user")
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return {"msg": "User registered successfully", "user_id": user_id}

# Login (returns JWT token)
@app.post("/api/users/login", status_code=status.HTTP_202_ACCEPTED)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (form_data.username,))
    user = cursor.fetchone()
    conn.close()
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        {"sub": user["email"], "role": user["role"]},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}

import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from .database import get_db
from .models import Base
from jose import jwt, JWTError
from datetime import datetime, timedelta
import aio_pika
import json
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import os
from dotenv import load_dotenv

# Load .env file for secret key and admin credentials
load_dotenv()

RABBIT_URL = os.getenv("RABBIT_URL")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "G00419525@atu.ie")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

async def publish_event(event_type: str, payload: dict):
    try:
        connection = await aio_pika.connect_robust(RABBIT_URL)
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "user_events", aio_pika.ExchangeType.TOPIC, durable=True
        )
        message = aio_pika.Message(body=json.dumps(payload).encode())
        await exchange.publish(message, routing_key=event_type)
        await connection.close()
    except Exception as e:
        print(f"Failed to publish event:", e)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database and admin user on startup
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
        print(f"Admin user created: {ADMIN_EMAIL}")
    else:
        print(f"Admin already exists: {ADMIN_EMAIL}")
    conn.close()
    yield


app = FastAPI(title="Authentication Service", lifespan=lifespan)

# CORS (add this block)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev-friendly
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "aud": "delete-service"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# User registration — cannot register as admin
@app.post("/api/users/register", status_code=status.HTTP_201_CREATED)
async def register_user(name: str, email: str, age: int, password: str):
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
#Publish event to RabbitMQ
    await publish_event("user.created", {
        "user_id": cursor.lastrowid,
        "name": name,
        "email": email,
        "age": age,
        "role": "user"
    })

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
    return {"access_token": access_token, "token_type": "bearer"}

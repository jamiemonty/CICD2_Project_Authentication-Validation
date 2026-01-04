from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from sqlalchemy.orm import Session, SessionLocal
from .database import engine, get_db
from .models import Base, User
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
    print(f"Attempting to publish event: {event_type} with payload: {payload}")
    print(f"RABBIT_URL: {RABBIT_URL}")
    try:
        if not RABBIT_URL:
            print("ERROR: RABBIT_URL is None or empty")
            return
        
        connection = await aio_pika.connect_robust(RABBIT_URL)
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "user_events", aio_pika.ExchangeType.TOPIC, durable=True
        )
        message = aio_pika.Message(body=json.dumps(payload).encode())
        await exchange.publish(message, routing_key=event_type)
        await connection.close()
        print(f"Successfully published event: {event_type}")
    except Exception as e:
        print(f"Failed to publish event: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create admin user on startup
    db = get_db()
    try:
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not admin:
            hashed_pw = hash_password(ADMIN_PASSWORD)
            admin_user = User(
                name="System Admin",
                email=ADMIN_EMAIL,
                age=22,
                hashed_password=hashed_pw,
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            print(f"Admin user created: {ADMIN_EMAIL}")
        else:
            print(f"Admin already exists: {ADMIN_EMAIL}")
    finally:
        db.close()
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
async def register_user(name: str, email: str, age: int, password: str, db: Session = Depends(get_db)):
    if email == ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Cannot register as admin")
    
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already exists")
    
    hashed_password = hash_password(password)
    new_user = User(
        name=name,
        email=email,
        age=age,
        hashed_password=hashed_password,
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Publish event to RabbitMQ
    await publish_event("user.created", {
        "user_id": new_user.user_id,
        "name": name,
        "email": email,
        "age": age,
        "role": "user",
        "hashed_password": hashed_password
    })

    return {"msg": "User registered successfully", "user_id": new_user.user_id}

# Login (returns JWT token)
@app.post("/api/users/login", status_code=status.HTTP_202_ACCEPTED)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        {"sub": user.email, "role": user.role},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

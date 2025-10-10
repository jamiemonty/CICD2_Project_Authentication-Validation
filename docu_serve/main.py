# app/main.py

from fastapi import FastAPI, HTTPException, status, Depends
from .schemas import User, UserBase, UserCreate
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm

SECRET_KEY = "JAMIESKEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

users: list[User] = []

pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.get("/api/users")
def get_users():
    return users

@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    for u in users:
        if u.user_id == user_id:
           return u
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@app.post("/api/users", status_code=status.HTTP_201_CREATED)
def add_user(user: User):
    if any(u.user_id == user.user_id for u in users):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="user_id already exists")
    users.append(user)
    return user

#Registeration for a user, checks if the user already exists, if not adds it to the list. Hashes the password 
#for security using bcrypt to generate gibberish
@app.post("/api/users/register", status_code=status.HTTP_201_CREATED)
def register_user(user:UserCreate):
    if any(u.email == user.email for u in users):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    user_id = len(users) + 1
    hashed_password = hash_password(user.password)
    new_user = User(user_id=user_id, name=user.name, email=user.email, age=user.age, hashed_password=hashed_password)
    users.append(new_user)
    return {"msg":"USer registered successfully", "user_id": user_id}


#Login endpoint, used JWT token so user can stay logged in for time set, 
#Finds the user by email, verifies the password using the stored hash password,
#creates a JWT token and returns the token to the client.
@app.post("/api/users/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = next((u for u in users if u.email == form_data.username), None)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login credentials")
    access_token = create_access_token({"sub": user.email}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type":"bearer"}
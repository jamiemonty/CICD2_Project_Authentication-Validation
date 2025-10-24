
# app/main.py

from fastapi import FastAPI, HTTPException, status, Depends
from .schemas import User, UserBase, UserCreate
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "JAMIESKEY") #fallback key for development
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title = "Login and Registration API")

users: list[User] = []


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")
pwd_context = CryptContext(schemes=["argon2"], deprecated = "auto")

PRESET_ADMIN = {
    "email": os.getenv("ADMIN_EMAIL", "G00419525@atu.ie"),
    "hashed_password": os.getenv("ADMIN_PASSWORD_HASHED", pwd_context.hash("password")), # Pre-hashed password for admin
    "role": "admin"
}

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

#This protects endpoints and only allows users with a valid JWT token to use the endpoints.
#The bearer token is what all the protected routes expect. 
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials entered", headers={"WWW-Authenticate": "Bearer"},)
    try: 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = next((u for u in users if u.email == email), None)
    if user is None:
        raise credentials_exception
    return user

#Preset admin user details
@app.on_event("startup")
def startup_event(): 
    admin_user = User(
        user_id = 0,
        name = "System Admin",
        email = PRESET_ADMIN["email"],
        age = 22,
        hashed_password = PRESET_ADMIN["hashed_password"],
        role = "admin"
    )
    users.append(admin_user)
    print("Admin account loaded: {admin_user.email}")

@app.get("/api/users")
def get_users():
    return users


@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    for u in users:
        if u.user_id == user_id:
            return u
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


#Registeration for a user, checks if the user already exists, if not adds it to the list. Hashes the password 
#for security using bcrypt to generate gibberish
@app.post("/api/users/register", status_code=status.HTTP_201_CREATED)
def register_user(user:UserCreate):
    if user.email == PRESET_ADMIN["email"]:
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail="Cannot registe as admin")
    if any(u.email == user.email for u in users):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    user_id = len(users) + 1
    hashed_password = hash_password(user.password)
    new_user = User(user_id=user_id, name=user.name, email=user.email, age=user.age, hashed_password=hashed_password, role="user")
    users.append(new_user)
    return {"msg":"User registered successfully", "user_id": user_id}


#Login endpoint, used JWT token so user can stay logged in for time set, 
#Finds the user by email, verifies the password using the stored hash password,
#creates a JWT token and returns the token to the client.
@app.post("/api/users/login", status_code=status.HTTP_202_ACCEPTED)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = next((u for u in users if u.email == form_data.username), None)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login credentials")
    role = "admin" if user.email.endswith("@admin.com") else "user"
    access_token = create_access_token({"sub": user.email, "role": user.role}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type":"bearer", "role": user.role}

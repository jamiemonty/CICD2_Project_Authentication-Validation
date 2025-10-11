# app/main.py
from fastapi import FastAPI, HTTPException, status
from .schemas import User
from pydantic import BaseModel
from typing import Optional

app = FastAPI()
users: list[User] = []


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[int] = None


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


@app.put("/api/users/{user_id}")
def update_user(user_id: int, updated_user: User):
    for index, u in enumerate(users):
        if u.user_id == user_id:
            users[index] = updated_user
            return updated_user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int):
    for index, u in enumerate(users):
        if u.user_id == user_id:
            del users[index]
            return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@app.post("/api/login", response_model=LoginResponse)
def login(login_request: LoginRequest):
    """Login endpoint - checks if username and password match a registered user"""
    for user in users:
        if user.username == login_request.username and user.password == login_request.password:
            return LoginResponse(
                success=True,
                message="Login successful",
                user_id=user.user_id,
            )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
    )

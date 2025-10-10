# app/schemas.py
from pydantic import BaseModel, EmailStr, constr, conint

class UserBase(BaseModel):
    name: constr(min_length=2, max_length=50)
    email: EmailStr
    age: conint(gt=18)

class UserCreate(UserBase):
     password: constr(min_length=8, max_length=60, pattern=r'^(?=.*[A-Z])(?=.*\d).*$')

class User(UserBase):
     user_id: int
     hashed_password: str
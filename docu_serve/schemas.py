# app/schemas.py
from pydantic import BaseModel, EmailStr, constr, conint, field_validator
import re

class UserBase(BaseModel):
    name: constr(min_length=2, max_length=50)
    email: EmailStr
    age: conint(gt=18)

class UserCreate(UserBase):
     password: constr(min_length=8, max_length=60)
     
     @field_validator('password')
     @classmethod
     def validate_password_complexity(cls, v: str) -> str:
         if not re.search(r'[A-Z]', v):
             raise ValueError('Password must contain at least one uppercase letter')
         if not re.search(r'[0-9]', v):
             raise ValueError('Password must contain at least one number')
         if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
             raise ValueError('Password must contain at least one symbol (!@#$%^&*(),.?":{}|<>)')
         return v

class User(UserBase):
     user_id: int
     hashed_password: str
     role: str

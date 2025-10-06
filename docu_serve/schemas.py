# app/schemas.py
from pydantic import BaseModel, EmailStr, constr, conint

class User(BaseModel):
    user_id: int
    name: constr(min_length=2, max_length=50)
    email: EmailStr
    age: conint(gt=18)
    password: costr(min_length = 8, max_length = 60, pattern=r'^(?=.*[A-Z])(?=.*\d).*$')
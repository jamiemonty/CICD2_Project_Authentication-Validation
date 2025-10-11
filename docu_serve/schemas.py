from pydantic import BaseModel, EmailStr, Field 
from typing import Annotated 

class User(BaseModel): 
    user_id: int 
    name: Annotated[str, Field(min_length=2, max_length=50)] 
    email: EmailStr 
    age: Annotated[int, Field(gt=18)] 
    username: Annotated[str, Field(min_length=3, max_length=20)] 
    password: Annotated[str, Field(min_length=6)]
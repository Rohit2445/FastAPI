# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ---- User schemas ----
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    full_name: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

# ---- Token schema ----
class Token(BaseModel):
    access_token: str
    token_type: str

# ---- Item schemas ----
class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    tags: List[str] = []

class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class ItemOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    tags: List[str] = []
    owner_id: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True

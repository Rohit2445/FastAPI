# models.py
from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy import JSON as SA_JSON

class UserTable(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str
    hashed_password: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ItemTable(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    # JSON column to store list of tags
    tags: List[str] = Field(default_factory=list, sa_column=Column(SA_JSON))
    owner_id: Optional[int] = Field(default=None, foreign_key="usertable.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

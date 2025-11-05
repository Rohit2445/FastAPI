# crud.py
from sqlmodel import Session, select
from passlib.context import CryptContext
from models import UserTable, ItemTable
from schemas import ItemCreate, ItemUpdate
from typing import Optional, List

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- User helpers (existing) ---
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_username(session: Session, username: str) -> Optional[UserTable]:
    statement = select(UserTable).where(UserTable.username == username)
    return session.exec(statement).first()

def create_user_db(session: Session, username: str, email: str, password: str) -> UserTable:
    hashed_password = get_password_hash(password)
    db_user = UserTable(username=username, email=email, hashed_password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def authenticate_user_db(session: Session, username: str, password: str) -> Optional[UserTable]:
    user = get_user_by_username(session, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# --- Item helpers (new) ---
def create_item_db(session: Session, owner_id: int, item_in: ItemCreate) -> ItemTable:
    item = ItemTable(
        title=item_in.title,
        description=item_in.description,
        tags=item_in.tags,
        owner_id=owner_id
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def get_items_for_user(session: Session, owner_id: int, limit: int = 100) -> List[ItemTable]:
    statement = select(ItemTable).where(ItemTable.owner_id == owner_id).limit(limit)
    return session.exec(statement).all()

def get_item_by_id(session: Session, item_id: int) -> Optional[ItemTable]:
    statement = select(ItemTable).where(ItemTable.id == item_id)
    return session.exec(statement).first()

def update_item_db(session: Session, item: ItemTable, item_in: ItemUpdate) -> ItemTable:
    updated = False
    if item_in.title is not None:
        item.title = item_in.title
        updated = True
    if item_in.description is not None:
        item.description = item_in.description
        updated = True
    if item_in.tags is not None:
        item.tags = item_in.tags
        updated = True
    if updated:
        session.add(item)
        session.commit()
        session.refresh(item)
    return item

def delete_item_db(session: Session, item: ItemTable) -> None:
    session.delete(item)
    session.commit()

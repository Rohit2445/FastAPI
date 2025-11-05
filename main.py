# main.py
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session
from datetime import timedelta
from typing import Optional
import jwt, time, traceback, sys

from database import create_db_and_tables, get_session
from models import UserTable
from schemas import UserCreate, UserOut, Token, ItemCreate, ItemOut, ItemUpdate
from crud import create_user_db, authenticate_user_db, get_user_by_username
from crud import create_item_db, get_items_for_user, get_item_by_id, update_item_db, delete_item_db

# ---- CONFIG ----
SECRET_KEY = "my_secret_key_change_me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI(title="FastAPI + SQLModel — Users & Items")

# create tables at startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- Auth pieces ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now_ts = int(time.time())
    if expires_delta:
        expire_ts = now_ts + int(expires_delta.total_seconds())
    else:
        expire_ts = now_ts + ACCESS_TOKEN_EXPIRE_MINUTES * 60
    to_encode.update({"exp": expire_ts, "iat": now_ts, "nbf": now_ts})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/token", response_model=Token)
def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    try:
        user = authenticate_user_db(session, form_data.username, form_data.password)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception:
        traceback.print_exc(file=sys.stdout)
        raise HTTPException(status_code=500, detail="Internal server error during login")

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> UserTable:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate":"Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise credentials_exception

    user = get_user_by_username(session, username)
    if user is None:
        raise credentials_exception
    return user

# --- User routes ---
@app.post("/users/", response_model=UserOut)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    if get_user_by_username(session, user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    created = create_user_db(session, user.username, user.email, user.password)
    return UserOut(
        id=created.id,
        username=created.username,
        email=created.email,
        full_name=created.full_name,
        age=created.age,
        bio=created.bio,
        created_at=created.created_at
    )

@app.get("/users/me", response_model=UserOut)
def read_users_me(current_user: UserTable = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        age=current_user.age,
        bio=current_user.bio,
        created_at=current_user.created_at
    )

# --- Items CRUD (protected) ---
@app.post("/items/", response_model=ItemOut, status_code=201)
def create_item(item: ItemCreate, session: Session = Depends(get_session), current_user: UserTable = Depends(get_current_user)):
    created = create_item_db(session, current_user.id, item)
    return ItemOut.from_orm(created)

@app.get("/items/", response_model=list[ItemOut])
def list_items(limit: int = 50, session: Session = Depends(get_session), current_user: UserTable = Depends(get_current_user)):
    items = get_items_for_user(session, current_user.id, limit=limit)
    return [ItemOut.from_orm(i) for i in items]

@app.get("/items/{item_id}", response_model=ItemOut)
def read_item(item_id: int, session: Session = Depends(get_session), current_user: UserTable = Depends(get_current_user)):
    item = get_item_by_id(session, item_id)
    if not item or item.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemOut.from_orm(item)

@app.put("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, item_in: ItemUpdate, session: Session = Depends(get_session), current_user: UserTable = Depends(get_current_user)):
    item = get_item_by_id(session, item_id)
    if not item or item.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found or not yours")
    updated = update_item_db(session, item, item_in)
    return ItemOut.from_orm(updated)

@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, session: Session = Depends(get_session), current_user: UserTable = Depends(get_current_user)):
    item = get_item_by_id(session, item_id)
    if not item or item.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found or not yours")
    delete_item_db(session, item)
    return None

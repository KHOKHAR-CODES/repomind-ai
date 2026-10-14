from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.schemas.auth import UserCreate, UserLogin, Token, UserOut
from app.core.security import verify_password, get_hash, create_access_token
from app.dependencies import get_current_user
from fastapi.security import OAuth2PasswordRequestForm
import logging

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/signup", response_model=dict)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    user = User(username=payload.username, email=payload.email, password_hash=get_hash(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Account created successfully", "user": {"id": user.id, "username": user.username, "email": user.email}}

@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token)

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

@router.post("/logout")
def logout():
    return {"message": "Logged out"}

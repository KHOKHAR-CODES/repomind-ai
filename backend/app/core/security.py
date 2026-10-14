from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)
def get_hash(password):
    return pwd_context.hash(password)
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

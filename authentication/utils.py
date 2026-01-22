from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlmodel import Session, select

from app.config import get_settings
from db import engine
from models.authentication import User

password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer()
bearer_scheme_optional = HTTPBearer(auto_error=False)
settings = get_settings()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def get_user(username: str):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        return user


def authenticate_user(username: str, password: str)->Optional[User]:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=1440)) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Security(bearer_scheme)]):
    """returns the currently logged in user"""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username=username)
    if user is None:
        raise credentials_exception
    return user

def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Security(bearer_scheme_optional)] = None,
):
    """returns the currently logged in user. If User is not logged in, return None"""
    if not credentials:
        return None
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username=username)
    return user


def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    """Returns the currently logged in user, if they are `active`"""
    if current_user.status == 'Inactive':
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

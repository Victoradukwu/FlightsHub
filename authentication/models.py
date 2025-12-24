
from __future__ import annotations  # noqa: F401

import hashlib
from typing import Annotated  # noqa: F401

from annotated_types import MinLen  # noqa: F401
from pydantic import AfterValidator, EmailStr
from sqlmodel import SQLModel


def _hash(val: str) -> str:
    return hashlib.sha256(val.encode()).hexdigest()


class UserBase(SQLModel):
    username: str
    email: EmailStr
    full_name: str | None = None


class UserIn(UserBase):
    password: Annotated[str, MinLen(8), AfterValidator(_hash)]


class UserOut(UserBase):
    pass


class UserInDB(UserBase):
    hashed_password: str


def fake_save_user(user_in: UserIn):
    user_in_db = UserInDB(**user_in.model_dump())
    print("User saved! ..not really")
    return user_in_db

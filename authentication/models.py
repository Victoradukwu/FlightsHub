from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Annotated, Literal, Optional

from annotated_types import MinLen
from pydantic import AfterValidator, BaseModel, EmailStr, model_validator
from sqlmodel import Field

from common.models import TimestampMixin


def _hash(val: str) -> str:
    return hashlib.sha256(val.encode()).hexdigest()


class UserBaseMixin(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    phone_number: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class PasswordMixin(BaseModel):
    password: Annotated[str, MinLen(8), AfterValidator(_hash)]
    confirm_password: Annotated[str, MinLen(8), AfterValidator(_hash)]


class UserCreate(UserBaseMixin, PasswordMixin):
    @model_validator(mode="after")
    def check_passwords_match(self) -> "UserCreate":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    password: Annotated[str, MinLen(6), AfterValidator(_hash)]
    username: str


class UserOut(BaseModel):
    id: Optional[int]
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    phone_number: str
    created_at: datetime
    updated_at: datetime
    status: Literal["Active", "Inactive"]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class User(UserBaseMixin, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password: str

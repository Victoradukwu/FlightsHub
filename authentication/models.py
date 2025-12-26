from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Annotated, Literal, Optional

from annotated_types import MinLen
from fastapi import Form
from fastapi.exceptions import RequestValidationError
from pydantic import AfterValidator, BaseModel, EmailStr, ValidationError, model_validator
from sqlmodel import Field, SQLModel

from common.models import TimestampMixin


def _hash(val: str) -> str:
    return hashlib.sha256(val.encode()).hexdigest()


class UserBaseMixin(SQLModel):
    first_name: str
    last_name: str
    username: str = Field(unique=True, index=True)
    email: EmailStr = Field(unique=True)
    phone_number: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class PasswordMixin(BaseModel):
    password: Annotated[str, MinLen(6), AfterValidator(_hash)]
    confirm_password: Annotated[str, MinLen(6), AfterValidator(_hash)]


class UserCreate(UserBaseMixin, PasswordMixin):  # type: ignore
    @model_validator(mode="after")
    def check_passwords_match(self) -> "UserCreate":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

    @classmethod
    def as_form(
        cls,
        first_name: str = Form(...),
        last_name: str = Form(...),
        username: str = Form(...),
        email: EmailStr = Form(...),
        phone_number: str = Form(...),
        password: str = Form(...),
        confirm_password: str = Form(...),
    ):
        """Helper to receive model data from form fields (for multipart/form-data endpoints)."""
        try:
            return cls(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email,
                phone_number=phone_number,
                password=password,
                confirm_password=confirm_password,
            )
        except ValidationError as exc:
            # Convert Pydantic ValidationError into FastAPI RequestValidationError so it is handled
            # by the framework and returns a 422 Unprocessable Entity instead of 500
            # Pydantic v1 ValidationError has `raw_errors`; pydantic v2 (pydantic-core) provides `errors()`
            errors = getattr(exc, "raw_errors", None)
            if errors is None:
                errors = exc.errors()
            raise RequestValidationError(errors)


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
    status: Literal["Active", "Inactive"]
    avatar: Optional[str]
    created_at: datetime
    updated_at: datetime

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class User(UserBaseMixin, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
    avatar: str
    status: Optional[str] = Field(default="Active")

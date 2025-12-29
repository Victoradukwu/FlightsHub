from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal, Optional

from annotated_types import MinLen
from fastapi import Form
from fastapi.exceptions import RequestValidationError
from pwdlib import PasswordHash
from pydantic import AfterValidator, BaseModel, EmailStr, ValidationError, model_validator
from sqlmodel import Field, SQLModel

from common.models import TimestampMixin

password_hash = PasswordHash.recommended()
def _hash(val: str) -> str:
    hashed_ = password_hash.hash(val)
    return hashed_


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
    confirm_password: Annotated[str, MinLen(6)]


class UserCreate(UserBaseMixin, PasswordMixin):  # type: ignore
    @model_validator(mode="before")
    def check_passwords_match(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Ensure plaintext passwords match before any field validators (e.g., hashing) run."""
        password = values.get("password")
        confirm = values.get("confirm_password")
        # If either value is missing, leave validation to other validators
        if password is None or confirm is None:
            return values
        if password != confirm:
            raise ValueError("Passwords do not match")
        return values

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


# class UserLogin(BaseModel):
#     password: Annotated[str, MinLen(6), AfterValidator(_hash)]
#     username: str


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


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Optional

from annotated_types import MinLen
from fastapi import Form
from fastapi.exceptions import RequestValidationError
from pwdlib import PasswordHash
from pydantic import (AfterValidator, BaseModel, EmailStr, ValidationError,
                      model_validator)
from sqlalchemy import Column, String
from sqlmodel import Field, Relationship, SQLModel

from models.flights import PassengerNameRecord

from .common import AirlineAdminLink, TimestampMixin

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
                first_name=first_name,  # type: ignore
                last_name=last_name,
                username=username,
                email=email,
                phone_number=phone_number,
                password=password,
                confirm_password=confirm_password,
            )
        except ValidationError as exc:
            errors = exc.errors()
            raise RequestValidationError(errors)


class PasswordChange(BaseModel):
    old_password: Annotated[str, MinLen(6)]
    new_password: Annotated[str, MinLen(6)]
    confirm_password: Annotated[str, MinLen(6)]

    @model_validator(mode="before")
    def check_passwords_match(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Ensure plaintext passwords match before any field validators (e.g., hashing) run."""
        password = values.get("new_password")
        confirm = values.get("confirm_password")
        if password is None or confirm is None:
            return values
        if password != confirm:
            raise ValueError("Passwords do not match")
        return values


class PasswordReset(BaseModel):
    token: str
    password: Annotated[str, MinLen(6)]
    confirm_password: Annotated[str, MinLen(6)]

    @model_validator(mode="before")
    def check_passwords_match(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Ensure plaintext passwords match before any field validators (e.g., hashing) run."""
        password = values.get("password")
        confirm = values.get("confirm_password")
        if password is None or confirm is None:
            return values
        if password != confirm:
            raise ValueError("Passwords do not match")
        return values


class UserOut(BaseModel):
    id: Optional[int]
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    phone_number: str
    status: str
    role: str
    avatar: Optional[str]
    created_at: datetime
    updated_at: datetime


class UserRole(StrEnum):
    GLOBAL_ADMIN = "Global Admin"
    AIRLINE_ADMIN = "Airline Admin"
    PASSENGER = "Passenger"


class User(UserBaseMixin, TimestampMixin, table=True):
    __tablename__ = "users" # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
    avatar: str
    status: str = Field(default="Active")
    role: UserRole  = Field(default=UserRole.PASSENGER, sa_column=Column(String, nullable=False))
    airlines: list["Airline"] = Relationship(  # type: ignore  # noqa: F821
        back_populates="admins",
        link_model=AirlineAdminLink,
        sa_relationship_kwargs={"viewonly": True},
    )  # pyright: ignore[reportUndefinedVariable]
    airline_links: list["AirlineAdminLink"] = Relationship(back_populates="user")
    reservations: list["PassengerNameRecord"] = Relationship(back_populates="user")


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut
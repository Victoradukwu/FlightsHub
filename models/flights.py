
from typing import Optional

from pydantic import BaseModel, field_validator
from pydantic_extra_types.timezone_name import (TimeZoneName,
                                                timezone_name_settings)
from sqlmodel import Field, Relationship, SQLModel

from .common import AirlineAdminLink, TimestampMixin


@timezone_name_settings(strict=False)
class TZNonStrict(TimeZoneName):
    pass


class AirportBase(SQLModel):
    airport_name: str = Field(unique=True, index=True)
    city: str
    iata_code: str = Field(unique=True, index=True)
    time_zone: TZNonStrict

    @property
    def full_name(self) -> str:
        return f"{self.airport_name}-{self.iata_code}"

    @field_validator("iata_code")
    def must_have_exactly_three_uppercase_letters(cls, v: str) -> str:
        """
        Validates that the input string contains exactly three uppercase letters.
        """
        if not (len(v) == 3 and v.isalpha() and v.isupper()):
            raise ValueError("Field must contain exactly three uppercase letters")
        return v


class AirportUpdate(BaseModel):
    airport_name: Optional[str] = Field(default=None)
    city: Optional[str] = Field(default=None)
    iata_code: Optional[str] = Field(default=None)
    time_zone: Optional[TZNonStrict] = Field(default=None)


class Airport(AirportBase, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


# class AirlineAdminLink(TimestampMixin, table=True):
#     user_id: int = Field(foreign_key="users.id", primary_key=True)
#     airline_id: int = Field(foreign_key="airline.id", primary_key=True)
#     status: str = Field(default="Active")
#     user: Optional["User"] = Relationship(back_populates="airlineadmin_links")
#     airline: "Airline" = Relationship(back_populates="airlineadmin_links")


class AirlineUpdate(SQLModel):
    airline_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    contact_phone: Optional[str] = Field(default=None)
    icao_code: Optional[str] = Field(default=None)
    admins: list[int] = Field(default=[])
    

class AirlineOut(BaseModel):
    id: int
    airline_name: str
    email: str
    contact_phone: str
    icao_code: str
    admins: list["UserOut"]  # pyright: ignore[reportUndefinedVariable] # noqa: F821


class Airline(TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    airline_name: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    contact_phone: str = Field(unique=True)
    icao_code: str = Field(unique=True)
    admins: list["User"] = Relationship(back_populates="airlines", link_model=AirlineAdminLink)  # pyright: ignore[reportUndefinedVariable] # noqa: F821
    admin_links: list[AirlineAdminLink] = Relationship(back_populates="airline")

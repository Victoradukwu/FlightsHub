
from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, field_validator
from pydantic_extra_types.timezone_name import (TimeZoneName,
                                                timezone_name_settings)
from sqlalchemy import Column, String
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
    incoming_flights: list["Flight"] = Relationship(
        back_populates="destination_port", sa_relationship_kwargs={"foreign_keys": "[Flight.destination_port_id]"}
    )
    outgoing_flights: list["Flight"] = Relationship(
        back_populates="departure_port", sa_relationship_kwargs={"foreign_keys": "[Flight.departure_port_id]"}
    )


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
    admins: list["User"] = Relationship(  # noqa: F821 # type: ignore
        back_populates="airlines",
        link_model=AirlineAdminLink,
        sa_relationship_kwargs={"viewonly": True},
    )  # pyright: ignore[reportUndefinedVariable]
    admin_links: list[AirlineAdminLink] = Relationship(back_populates="airline")
    flights: list["Flight"] = Relationship(back_populates="airline")


class FlightStatus(StrEnum):
    PENDING = "Pending"
    CANCELLED = "Cancelled"
    CONDUCTED = "Conducted"


class FlightCreate(BaseModel):
    airline_id: int
    flight_number: int = Field(description="The numerical portion of the flight number")
    date_time: datetime
    departure_port_id: int
    destination_port_id: int

    @field_validator("flight_number")
    def validate_flight_number(cls, v: int) -> int:
        """
        Validates that flight_number is between 1 and 9999.
        """
        if not (1 <= v <= 9999):
            raise ValueError("flight_number must be between 1 and 9999")
        return v


class FlightUpdate(BaseModel):
    airline_id: int | None = Field(default=None)
    flight_number: int | None = Field(default=None, description="The numerical portion of the flight number")
    date_time: datetime | None = Field(default=None)
    departure_port_id: int | None = Field(default=None)
    destination_port_id: int | None = Field(default=None)
    status: FlightStatus | None = Field(default=None)

    @field_validator("flight_number")
    def validate_flight_number(cls, v: int) -> int:
        """
        Validates that flight_number is between 1 and 9999.
        """
        if not (1 <= v <= 9999):
            raise ValueError("flight_number must be between 1 and 9999")
        return v


class Flight(TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    airline_id: int | None = Field(foreign_key="airline.id")
    flight_number: str
    date_time: datetime
    departure_port_id: int | None = Field(foreign_key="airport.id")
    destination_port_id: int | None = Field(foreign_key="airport.id")
    status: FlightStatus = Field(default=FlightStatus.PENDING, sa_column=Column(String, nullable=False))
    # Convenient relationships
    airline: Airline = Relationship(back_populates="flights")
    destination_port: Airport = Relationship(
        back_populates="incoming_flights", sa_relationship_kwargs={"foreign_keys": "[Flight.destination_port_id]"}
    )
    departure_port: Airport = Relationship(
        back_populates="outgoing_flights", sa_relationship_kwargs={"foreign_keys": "[Flight.departure_port_id]"}
    )


class FlightRead(BaseModel):
    id: int
    airline_id: int
    flight_number: str
    date_time: datetime
    departure_port_id: int
    destination_port_id: int
    status: FlightStatus
    airline: Airline | None
    destination_port: Airport | None
    departure_port: Airport | None
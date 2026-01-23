import datetime
from dataclasses import field
from typing import Optional

import strawberry


@strawberry.input
class AirportInput:
    airport_name: str
    city: str
    iata_code: str
    time_zone: str


@strawberry.input
class AirportUpdateInput:
    airport_name: Optional[str] = None
    city: Optional[str] = None
    iata_code: Optional[str] = None
    time_zone: Optional[str] = None


@strawberry.type
class AirportType:
    id: int
    airport_name: str
    city: str
    iata_code: str
    time_zone: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

strawberry.type


@strawberry.type
class UserType:
    id: strawberry.ID


@strawberry.input
class AirlineCreateInput:
    airline_name: str
    email: str
    contact_phone: str
    icao_code: str
    admins: list[int] = field(default_factory=list)


@strawberry.input
class AirlineUpdateInput:
    airline_name: Optional[str] = None
    email: Optional[str] = None
    contact_phone: Optional[str] = None
    icao_code: Optional[str] = None
    admins: Optional[list[int]] = field(default_factory=list)


@strawberry.type
class AirlineType:
    id: int
    airline_name: str
    email: str
    contact_phone: str
    icao_code: str
    admins: list[UserType] = field(default_factory=list)
    created_at: datetime.datetime
    updated_at: datetime.datetime
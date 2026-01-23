import datetime
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

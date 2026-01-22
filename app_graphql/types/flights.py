import datetime
import strawberry


@strawberry.type
class AirportType:
    id: int
    airport_name: str
    city: str
    iata_code: str
    time_zone: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

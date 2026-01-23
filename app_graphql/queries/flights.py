from typing import Optional

import strawberry

from app_graphql.types.flights import AirlineType, AirportType
from models.flights import Airline, Airport


@strawberry.type
class AirportsQuery:
    @strawberry.field
    def airports(self, info: strawberry.Info) -> list[AirportType]:
        session = info.context["session"]
        return session.query(Airport).all()

    @strawberry.field
    def airport(self, id: strawberry.ID, info: strawberry.Info) -> Optional[AirportType]:
        session = info.context["session"]
        return session.get(Airport, id)


@strawberry.type
class AirlinesQuery:
    @strawberry.field
    def airlines(self, info: strawberry.Info) -> list[AirlineType]:
        session = info.context["session"]
        return session.query(Airline).all()

    @strawberry.field
    def airline(self, id: strawberry.ID, info: strawberry.Info) -> Optional[AirlineType]:
        session = info.context["session"]
        return session.get(Airline, id)

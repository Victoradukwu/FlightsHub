from typing import Optional

import strawberry

from app_graphql.types.flights import AirportType
from models.flights import Airport


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

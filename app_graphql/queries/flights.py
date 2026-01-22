import strawberry

from app_graphql.types.flights import AirportType
from models.flights import Airport


@strawberry.type
class FlightsQuery:

    # @strawberry.field(permission_classes=[IsAdminUser])
    @strawberry.field
    def airports(self, info) -> list[AirportType]:
        session = info.context["session"]
        return session.query(Airport).all()

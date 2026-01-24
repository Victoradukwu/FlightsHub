import strawberry
from fastapi import HTTPException

from app_graphql.permissions import IsAdminUser
from models.common import AirlineAdminLink
from models.flights import Airline, Airport

from ..types.flights import (
    AirlineCreateInput,
    AirlineType,
    AirlineUpdateInput,
    AirportInput,
    AirportType,
    AirportUpdateInput,
)


@strawberry.type
class AirportsMutation:
    @strawberry.mutation(permission_classes=[IsAdminUser])
    def create_airport(self, input: AirportInput, info: strawberry.Info) -> AirportType:
        """
        Creates a new airport record in the system.
        """
        session = info.context["session"]
        port_ = Airport(
            airport_name=input.airport_name,
            city=input.city,
            iata_code=input.iata_code,
            time_zone=input.time_zone,  # type: ignore
        )
        session.add(port_)
        try:
            session.commit()
            session.refresh(port_)
        except Exception as exc_:
            session.rollback()
            raise HTTPException(detail=str(exc_), status_code=400)
        return AirportType(
            id=port_.id,  # type: ignore
            airport_name=port_.airport_name,
            city=port_.city,
            iata_code=port_.iata_code,
            time_zone=port_.time_zone,
            created_at=port_.created_at,
            updated_at=port_.updated_at,
        )

    @strawberry.mutation(permission_classes=[IsAdminUser])
    def update_airport(self, id: strawberry.ID, input: AirportUpdateInput, info: strawberry.Info) -> AirportType:
        """
        Updates a new airport record in the system.
        """
        session = info.context["session"]
        stored_port = session.get(Airport, id)
        if not stored_port:
            raise HTTPException(status_code=404, detail="Airport not found")

        input_dict = strawberry.asdict(input)
        for key, value in input_dict.items():
            if value is not None:
                setattr(stored_port, key, value)

        session.add(stored_port)
        try:
            session.commit()
            session.refresh(stored_port)
        except Exception as exc_:
            session.rollback()
            raise HTTPException(detail=str(exc_), status_code=400)
        return AirportType(
            id=stored_port.id,  # type: ignore
            airport_name=stored_port.airport_name,
            city=stored_port.city,
            iata_code=stored_port.iata_code,
            time_zone=stored_port.time_zone,
            created_at=stored_port.created_at,
            updated_at=stored_port.updated_at,
        )


@strawberry.type
class AirlinesMutation:
    @strawberry.mutation(permission_classes=[IsAdminUser])
    def create_airline(self, input: AirlineCreateInput, info: strawberry.Info) -> AirlineType:
        """
        Creates a new airline record in the system.
        """
        session = info.context["session"]
        airline = Airline(
            airline_name=input.airline_name,
            email=input.email,
            contact_phone=input.contact_phone,
            icao_code=input.icao_code,
        )
        session.add(airline)
        for admin in input.admins:
            lnk = AirlineAdminLink(user_id=admin, airline=airline)  # type: ignore
            session.add(lnk)
        try:
            session.commit()
            session.refresh(airline)
        except Exception as exc_:
            session.rollback()
            raise HTTPException(detail=str(exc_), status_code=400)
        return AirlineType(
            id=airline.id,  # type: ignore
            airline_name=airline.airline_name,
            email=airline.email,
            contact_phone=airline.contact_phone,
            icao_code=airline.icao_code,
            admins=airline.admins,
            created_at=airline.created_at,
            updated_at=airline.updated_at,
        )

    @strawberry.mutation(permission_classes=[IsAdminUser])
    def update_airline(self, id: strawberry.ID, input: AirlineUpdateInput, info: strawberry.Info) -> AirlineType:
        """
        Updates an airline record in the system.
        """
        session = info.context["session"]
        stored_airline = session.get(Airline, id)
        if not stored_airline:
            raise HTTPException(status_code=404, detail="Airline not found")

        input_dict = strawberry.asdict(input)
        for key, value in input_dict.items():
            if value is not None:
                setattr(stored_airline, key, value)

        session.add(stored_airline)
        try:
            session.commit()
            session.refresh(stored_airline)
        except Exception as exc_:
            session.rollback()
            raise HTTPException(detail=str(exc_), status_code=400)
        return AirlineType(
            id=stored_airline.id,  # type: ignore
            airline_name=stored_airline.airline_name,
            email=stored_airline.email,
            contact_phone=stored_airline.contact_phone,
            icao_code=stored_airline.icao_code,
            admins=stored_airline.admins,
            created_at=stored_airline.created_at,
            updated_at=stored_airline.updated_at,
        )


@strawberry.type
class FlightsMgtMutation:
    @strawberry.field
    def airports_mutation(self) -> AirportsMutation:
        return AirportsMutation()

    @strawberry.field
    def airlines_mutation(self) -> AirlinesMutation:
        return AirlinesMutation()
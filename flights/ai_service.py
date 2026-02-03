from __future__ import annotations

from datetime import date
from typing import Sequence

from sqlalchemy import func
from sqlmodel import select

from ai.factory import get_ai_provider
from ai.provider import ExternalFlight
from db import SessionDep
from models.flights import Airport, Flight


def find_internal_flights(session: SessionDep, origin_iata: str, destination_iata: str, date: date) -> Sequence[Flight]:
    
    origin = session.exec(select(Airport).where(Airport.iata_code == origin_iata)).first()
    dest = session.exec(select(Airport).where(Airport.iata_code == destination_iata)).first()
    if not origin or not dest:
        return []
    stmt = select(Flight).where(
        Flight.departure_port_id == origin.id,
        Flight.destination_port_id == dest.id,
        func.date(Flight.date_time) == date,
    )
    return session.exec(stmt).all()


def search_flights(session: SessionDep, origin_iata: str, destination_iata: str, date: date) -> tuple[Sequence[Flight], Sequence[ExternalFlight]]:
    internal = find_internal_flights(session, origin_iata, destination_iata, date)
    provider = get_ai_provider()
    external = provider.search_external_flights(origin_iata, destination_iata, date)
    return internal, external

from __future__ import annotations

from datetime import date
from typing import Any, Sequence

from sqlalchemy import func
from sqlmodel import select

from ai.factory import get_ai_provider
from app.websocket_manager import manager
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


# def search_flights(session: SessionDep, origin_iata: str, destination_iata: str, date: date) -> tuple[Sequence[Flight], Sequence[ExternalFlight]]:
#     internal = find_internal_flights(session, origin_iata, destination_iata, date)
#     provider = get_ai_provider()
#     external = provider.search_external_flights(origin_iata, destination_iata, date)
#     return internal, external


async def notify_external_flights(search_key: str, origin_iata: str, destination_iata: str, dt: date) -> None:
    """
    Runs the external flights search and broadcasts results to websocket subscribers
    for the given search key ("ORIGIN-DESTINATION-YYYY-MM-DD").
    """

    try:
        provider = get_ai_provider()
        results = provider.search_external_flights(origin_iata, destination_iata, dt)
        payload: list[dict[str, Any]] = [
            {
                "airline_name": x.airline_name,
                "flight_number": x.flight_number,
                "departure_time": x.departure_time.isoformat(),
                "arrival_time": x.arrival_time.isoformat() if getattr(x, "arrival_time", None) else None,
                "departure_iata": x.departure_iata,
                "destination_iata": x.destination_iata,
                "airfare": str(x.airfare) if getattr(x, "airfare", None) is not None else None,
                "booking_url": getattr(x, "booking_url", None),
            }
            for x in results
        ]
        await manager.broadcast_search_results(search_key, payload)
    except Exception:
        # Intentionally ignore failures to avoid breaking the response flow.
        pass

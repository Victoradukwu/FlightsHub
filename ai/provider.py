
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Protocol

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import get_settings
from models.flights import ExternalFlight, ExternalFlightsResponse


class AIProvider(Protocol):
    def search_external_flights(self, origin_iata: str, destination_iata: str, date: date) -> list[ExternalFlight]:
        """Return a list of external flights suggested by the AI/provider.
        Implementations should best-effort return booking URL when available.
        """
        ...


class OpenAIProvider(AIProvider):
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL or "gpt-4.1-mini"
        self._llm = ChatOpenAI(model=self.model, api_key=self.api_key, temperature=0.2) if self.api_key else None # type: ignore

    def search_external_flights(self, origin_iata: str, destination_iata: str, date: date) -> list[ExternalFlight]:
        if not self._llm:
            return []

        structured_llm = self._llm.with_structured_output(ExternalFlightsResponse)

        sys = SystemMessage(
            content=(
                "You are a travel assistant. Return external flight options not in our system. "
                "Use realistic carriers/routes. Only output the requested structure."
            )
        )
        usr = HumanMessage(
            content=(
                "Provide up to 5 flights as a structured object. "
                f"Origin: {origin_iata}. Destination: {destination_iata}. Date: {date}. "
                "Fill ISO8601 times and booking_url when available."
            )
        )
        try:
            result = structured_llm.invoke([sys, usr])
            return result.flights # type: ignore
        except Exception:
            return []


class MockProvider(AIProvider):
    def search_external_flights(self, origin_iata: str, destination_iata: str, date: date) -> list[ExternalFlight]:
        base_dep = datetime.combine(date, time()) + timedelta(hours=9)
        return [
            ExternalFlight(
                airline_name="Sample Air",
                flight_number="SA123",
                departure_time=base_dep,
                arrival_time=base_dep + timedelta(hours=2),
                departure_iata=origin_iata,
                destination_iata=destination_iata,
                airfare=Decimal("250.00"),
                booking_url="https://example.com/book/SA123",
            ),
            ExternalFlight(
                airline_name="Demo Airways",
                flight_number="DA456",
                departure_time=base_dep + timedelta(hours=4),
                arrival_time=base_dep + timedelta(hours=6),
                departure_iata=origin_iata,
                destination_iata=destination_iata,
                airfare=None,
                booking_url="https://example.com/book/DA456",
            ),
        ]


import json
import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Protocol

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_openai import ChatOpenAI

from app.config import get_settings
from models.flights import ExternalFlight, ExternalFlightsResponse


class AIProvider(Protocol):
    def search_external_flights(self, origin_iata: str, destination_iata: str, date: date) -> list:
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
                "Use realistic carriers/routes. Only output the requested structure. "
                "For each flight, set booking_url to the airline's official website or direct booking page. "
                "If no official site is known, set booking_url to null."
            )
        )
        usr = HumanMessage(
            content=(
                "Provide up to 5 flights as a structured object. "
                f"Origin: {origin_iata}. Destination: {destination_iata}. Date: {date}. "
                "Times must be ISO8601. booking_url must be the airline's official website or booking page; "
                "return null if unknown."
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


class HuggingFaceProvider(AIProvider):
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.HUGGINGFACE_API_KEY
        self.model = settings.HUGGINGFACE_MODEL or "HuggingFaceH4/zephyr-7b-beta"
        # Initialize only if dependencies and token are available
        if self.api_key and HuggingFaceEndpoint and ChatHuggingFace:
            try:
                endpoint = HuggingFaceEndpoint(
                    repo_id=self.model,
                    task="text-generation",
                    huggingfacehub_api_token=self.api_key,
                    temperature=0.2,
                    max_new_tokens=1024,
                )  # type: ignore
                self._llm = ChatHuggingFace(llm=endpoint)  # type: ignore
            except Exception:
                self._llm = None  # type: ignore
        else:
            self._llm = None  # type: ignore

    def search_external_flights(self, origin_iata: str, destination_iata: str, date: date) -> list[ExternalFlight]:
        # HuggingFace chat models do not reliably support Pydantic/TypedDict structured outputs; parse JSON.
        if not getattr(self, "_llm", None):
            return []

        sys = SystemMessage(
            content=(
                "You are a travel assistant. Return external flight options not in our system. "
                "Use realistic carriers/routes. Respond ONLY with a compact JSON object matching: "
                '{"flights": [{"airline_name": string, "flight_number": string, "departure_time": ISO8601, "arrival_time": ISO8601|null, "departure_iata": string, "destination_iata": string, "airfare": number|null, "booking_url": string|null}]}. '
                "booking_url must be the airline's official website or booking page; set to null if unknown. "
                "Ensure every flight includes both departure_iata and destination_iata; set departure_iata to the Origin code."
            )
        )
        usr = HumanMessage(
            content=(
                "Provide up to 5 flights (to keep response small). "
                f"Origin: {origin_iata}. Destination: {destination_iata}. Date: {date}. "
                "Output JSON only, no commentary or markdown fences. Keep fields concise."
            )
        )
        try:
            msg = self._llm.invoke([sys, usr])  # type: ignore
            content = getattr(msg, "content", msg)
            # Normalize content to a plain string
            if isinstance(content, list):
                parts: list[str] = []
                for part in content:
                    if isinstance(part, str):
                        parts.append(part)
                    elif isinstance(part, dict):
                        text = part.get("text") or part.get("content") or ""
                        if isinstance(text, str):
                            parts.append(text)
                content = "".join(parts)
            if not isinstance(content, str):
                return []

            # Extract potential JSON (supports fenced blocks)
            json_str = content.strip()
            fence = re.search(r"```(?:json)?\n(.*?)```", json_str, flags=re.DOTALL)
            if fence:
                json_str = fence.group(1).strip()
            else:
                # Exclude every character outside the opening and closign curly braces
                start = json_str.find("{")
                end = json_str.rfind("}")
                if start != -1 and end != -1 and end > start:
                    json_str = json_str[start : end + 1]

            # First, try strict JSON
            try:
                data = json.loads(json_str)
            except Exception:

                def _sq_to_dq(m: re.Match[str]) -> str:
                    s = m.group(0)
                    inner = s[1:-1]
                    return '"' + inner.replace('"', '\\"') + '"'

                # Repair common non-JSON artifacts (single quotes, None/True/False, trailing commas)
                repaired = json_str
                repaired = re.sub(r"\bNone\b", "null", repaired)
                repaired = re.sub(r"\bTrue\b", "true", repaired)
                repaired = re.sub(r"\bFalse\b", "false", repaired)
                repaired = re.sub(r",\s*([}\]])", r"\1", repaired)  # Remove that occurs just before a closing bracket
                # Replace single quoytes with double quotes
                repaired = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", _sq_to_dq, repaired)
                try:
                    data = json.loads(repaired)
                except Exception:
                    return []

            flights: list[ExternalFlight] = []
            if isinstance(data, dict) and isinstance(data.get("flights"), list):
                for item in data["flights"]:
                    if isinstance(item, dict):
                        item.setdefault("departure_iata", origin_iata)
                        item.setdefault("destination_iata", destination_iata)
                        item.setdefault("arrival_time", None)
                        item.setdefault("airfare", None)
                        item.setdefault("booking_url", None)
                        try:
                            flights.append(ExternalFlight(**item))
                        except Exception:
                            continue
            return flights
        except Exception:
            return []

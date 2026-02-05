from collections import defaultdict
from typing import Any

from fastapi import WebSocket

from models.flights import SeatRead


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = defaultdict(list)
        # External search connections keyed by "{ORIGIN}-{DESTINATION}-{YYYY-MM-DD}"
        self.search_connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, flight_id: int):
        await websocket.accept()
        self.active_connections[flight_id].append(websocket)

    def disconnect(self, flight_id: int, websocket: WebSocket):
        if flight_id in self.active_connections:
            self.active_connections[flight_id].remove(websocket)

    async def broadcast_seats(self, flight_id: int, seats: list[SeatRead]):
        if flight_id in self.active_connections:
            for connection in self.active_connections[flight_id]:
                try:
                    await connection.send_json({"type": "seats_update", "data": [seat.model_dump() for seat in seats]})
                except Exception:
                    pass

    async def connect_search(self, websocket: WebSocket, search_key: str):
        await websocket.accept()
        self.search_connections[search_key].append(websocket)

    def disconnect_search(self, search_key: str, websocket: WebSocket):
        if search_key in self.search_connections:
            self.search_connections[search_key].remove(websocket)

    async def broadcast_search_results(self, search_key: str, results: list[dict[str, Any]]):
        if search_key in self.search_connections:
            for connection in self.search_connections[search_key]:
                try:
                    await connection.send_json({"type": "external_search", "data": results})
                except Exception:
                    pass


# Single instance for the entire application
manager = ConnectionManager()
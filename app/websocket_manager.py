from collections import defaultdict

from fastapi import WebSocket

from models.flights import SeatRead


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = defaultdict(list)

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

# Single instance for the entire application
manager = ConnectionManager()

from fastapi import FastAPI

# from authentication.router import router as auth_router
# from flights.router import router as flight_router
from common.router import router as common_router

app = FastAPI(title="FlightsHub API", version="0.1.0", description="FlightsHub API Project")

# app.include_router(auth_router)
app.include_router(common_router)
# app.include_router(flight_router)

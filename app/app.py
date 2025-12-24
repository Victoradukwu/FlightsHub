
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from authentication.router import router as auth_router
# from flights.router import router as flight_router
from common.router import router as common_router

from . import middlewares

api_v1_router = APIRouter(prefix="/api/v1")

# api_v1_router.include_router(auth_router, tags=['auth'])
api_v1_router.include_router(common_router, tags=['common'])
# api_v1_router.include_router(flight_router, tags=['flights])


app = FastAPI(title="FlightsHub API", version="0.1.0", description="FlightsHub API Project")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"]
)
app.middleware("http")(middlewares.add_process_time_header)

app.include_router(api_v1_router)

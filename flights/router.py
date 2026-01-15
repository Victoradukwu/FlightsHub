from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlmodel import select

from authentication.utils import get_current_active_user, get_settings
from db import SessionDep
from models.authentication import User
from models.flights import Airline  # noqa: F401
from models.flights import AirlineOut  # noqa: F401
from models.flights import AirlineUpdate  # noqa: F401
from models.flights import Airport, AirportBase, AirportUpdate

settings = get_settings()


router = APIRouter(
    prefix="/flights",
    responses={404: {"description": "Not found"}},
)


# @router.post("/register/", response_model=UserOut)
# async def register(
#     request: Request,
#     session: SessionDep,
#     user: UserCreate = Depends(UserCreate.as_form),
#     avatar: Annotated[UploadFile | None, File(description="User Registration")] = None,
# ):
#     """register new user."""

#     # Pre-check for duplicates to provide a friendly error message
#     if session.exec(select(User).where(User.username == user.username)).first():
#         raise HTTPException(status_code=409, detail="Username already exists")
#     if session.exec(select(User).where(User.email == user.email)).first():
#         raise HTTPException(status_code=409, detail="Email already exists")

#     # Save file under uploads/medias/avatars/<uuid>.<ext>
#     if avatar:
#         file_path = await file_upload(avatar, model_name="users")

#         # Build a full URL to the saved file using the mounted static route name 'uploads' if request available
#         url = request.url_for("uploads", path=file_path) if request is not None else f"/uploads/{file_path}"
#     else:
#         url = ""

#     usr = User(**user.model_dump(), avatar=str(url))
#     session.add(usr)
#     try:
#         session.commit()
#         session.refresh(usr)
#     except IntegrityError:
#         session.rollback()
#         # Race condition fallback: unique constraint at DB-level violated
#         raise HTTPException(status_code=409, detail="Username or email already in use")
#     return usr


@router.post("/airports/", response_model=Airport)
async def create_airport(
    port: AirportBase, session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]
):
    if not current_user or current_user.role != "Global Admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    port_ = Airport(**port.model_dump())
    session.add(port_)
    try:
        session.commit()
        session.refresh(port_)
    except Exception as exc_:
        session.rollback()
        raise HTTPException(detail=str(exc_), status_code=400)
    return port_


@router.get("/airports/", response_model=list[Airport])
async def list_airports(
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=10)] = None,
):
    stmt = select(Airport)
    conditions = []
    if q:
        # case-insensitive substring match on name
        conditions.append(Airport.airport_name.ilike(f"%{q}%"))  # type: ignore

    if conditions:
        stmt = stmt.where(*conditions)
    return session.exec(stmt).all()


@router.get("/airports/{id}/")
async def airport_retrieve(id: Annotated[int, Path(title="The Airport id")], session: SessionDep) -> Airport:
    band = session.get(Airport, id)
    if band is None:
        raise HTTPException(status_code=404, detail="Airport Not found")
    return band


@router.patch("/airports/{id}/", response_model=Airport)
async def update_airport(
    id: int, port: AirportUpdate, session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Please login")

    if current_user.role != "Global Admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    stored_port = session.get(Airport, id)
    if not stored_port:
        raise HTTPException(status_code=404, detail="Airport not found")

    update_data = port.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(stored_port, key, value)

    session.add(stored_port)
    session.commit()
    session.refresh(stored_port)
    return stored_port


# @router.post("/airlines/", response_model=Airline)
# async def create_airline(
#     airline: AirlineUpdate, session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]
# ):
#     if not current_user or current_user.role != "Global Admin":
#         raise HTTPException(status_code=403, detail="Permission denied")

#     airline_obj = Airline(**airline.model_dump())
#     session.add(airline_obj)
#     try:
#         session.commit()
#         session.refresh(airline_obj)
#     except Exception as exc_:
#         session.rollback()
#         raise HTTPException(detail=str(exc_), status_code=400)
#     return airline_obj


# @router.get("/airlines/", response_model=list[AirlineOut])
# async def list_airlines(
#     session: SessionDep,
#     q: Annotated[str | None, Query(max_length=10)] = None,
# ):
#     stmt = select(Airline)
#     conditions = []
#     if q:
#         # case-insensitive substring match on name
#         conditions.append(Airline.airline_name.ilike(f"%{q}%"))  # type: ignore

#     if conditions:
#         stmt = stmt.where(*conditions)
#     return session.exec(stmt).all()


# @router.get("/airlines/{id}/")
# async def airline_retrieve(id: Annotated[int, Path(title="The Airline id")], session: SessionDep) -> Airline:
#     airline = session.get(Airline, id)
#     if airline is None:
#         raise HTTPException(status_code=404, detail="Airline Not found")
#     return airline


# @router.patch("/airlines/{id}/", response_model=Airline)
# async def update_airline(
#     id: int,
#     airline: AirlineUpdate,
#     session: SessionDep,
#     current_user: Annotated[User, Depends(get_current_active_user)],
# ):
#     if not current_user:
#         raise HTTPException(status_code=401, detail="Please login")

#     if current_user.role != "Global Admin":
#         raise HTTPException(status_code=403, detail="Permission denied")

#     stored_airline = session.get(Airline, id)
#     if not stored_airline:
#         raise HTTPException(status_code=404, detail="Airline not found")

#     update_data = airline.model_dump(exclude_unset=True)
#     for key, value in update_data.items():
#         setattr(stored_airline, key, value)

#     session.add(stored_airline)
#     session.commit()
#     session.refresh(stored_airline)
#     return stored_airline

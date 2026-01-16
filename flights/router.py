from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlmodel import select

from authentication.utils import get_current_active_user, get_settings
from db import SessionDep
from models.authentication import User
from models.common import AdminStatus, AirlineAdminLink
from models.flights import Airline  # noqa: F401
from models.flights import AirlineOut  # noqa: F401
from models.flights import AirlineUpdate  # noqa: F401
from models.flights import Airport, AirportBase, AirportUpdate

settings = get_settings()


router = APIRouter(
    prefix="/flights",
    responses={404: {"description": "Not found"}},
)


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


@router.post("/airlines/", response_model=Airline)
async def create_airline(
    airline: AirlineUpdate, session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]
):
    if not current_user or current_user.role != "Global Admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    airline_data = airline.model_dump()
    admins = airline_data.pop("admins", [])
    airline_obj = Airline(**airline_data)
    for admin_id in admins:
        adm = session.get(User, admin_id)
        lnk = AirlineAdminLink(user=adm, airline=airline_obj)  # type: ignore
        session.add(lnk)
    session.add(airline_obj)
    try:
        session.commit()
        session.refresh(airline_obj)
    except Exception as exc_:
        session.rollback()
        raise HTTPException(detail=str(exc_), status_code=400)
    return airline_obj


@router.get("/airlines/", response_model=list[AirlineOut])
async def list_airlines(
    session: SessionDep,
    name: Annotated[str | None, Query(max_length=10)] = None,
):
    """Returns airlines and their active admins"""

    stmt = (
        select(Airline)
        .join(AirlineAdminLink, Airline.id == AirlineAdminLink.airline_id)  # pyright: ignore[reportArgumentType]
        .join(User, User.id == AirlineAdminLink.user_id)  # pyright: ignore[reportArgumentType]
        .where(AirlineAdminLink.status == "Active")
    )
    if name:
        stmt = stmt.where(Airline.airline_name.ilike(f"%{name}%"))  # type: ignore
    return session.exec(stmt).all()


@router.get("/airlines/{id}/", response_model=AirlineOut)
async def airline_retrieve(id: Annotated[int, Path(title="The Airline id")], session: SessionDep):
    airline = session.get(Airline, id)
    if airline is None:
        raise HTTPException(status_code=404, detail="Airline Not found")
    return airline


@router.patch("/airlines/{id}/", response_model=AirlineOut)
async def update_airline(
    id: int,
    airline: AirlineUpdate,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Please login")

    if current_user.role != "Global Admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    stored_airline = session.get(Airline, id)
    if not stored_airline:
        raise HTTPException(status_code=404, detail="Airline not found")

    update_data = airline.model_dump(exclude_unset=True)
    admins = update_data.pop("admins", [])
    existing_admin_links = session.exec(
        select(AirlineAdminLink).where(AirlineAdminLink.airline_id == id, AirlineAdminLink.status == AdminStatus.ACTIVE)
    ).all()
    existing_lnk_ids = [lnk.user_id for lnk in existing_admin_links]
    for lnk in existing_admin_links:
        if lnk.user_id not in admins:
            lnk.status = AdminStatus.INACTIVE
            session.add(lnk)
    for user_id in admins:
        if user_id not in existing_lnk_ids:
            new_lnk = AirlineAdminLink(user_id=user_id, airline_id=id)
            session.add(new_lnk)

    for key, value in update_data.items():
        setattr(stored_airline, key, value)

    session.add(stored_airline)
    session.commit()
    session.refresh(stored_airline)
    return stored_airline

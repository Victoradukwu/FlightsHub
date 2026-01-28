from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from sqlmodel import func, select

from authentication.utils import get_current_active_user, get_settings
from db import SessionDep
from flights.utils import generate_booking_ref, process_reservation
from models.authentication import User, UserRole
from models.common import AdminStatus, AirlineAdminLink
from models.flights import (
    Airline,
    AirlineOut,
    AirlineUpdate,
    Airport,
    AirportBase,
    AirportUpdate,
    Flight,
    FlightCreate,
    FlightRead,
    FlightSeat,
    FlightUpdate,
    PassengerNameRecord,
    PaymentInfo,
    PNRCreate,
    PNRRead,
    ReservationStatus,
    SeatRead,
    SeatStatus,
    validate_seat_number,
)

settings = get_settings()


router = APIRouter(
    prefix="/flights",
    responses={404: {"description": "Not found"}},
)


@router.post("/airports/", response_model=Airport)
def create_airport(
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
def list_airports(
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
def airport_retrieve(id: Annotated[int, Path(title="The Airport id")], session: SessionDep) -> Airport:
    band = session.get(Airport, id)
    if band is None:
        raise HTTPException(status_code=404, detail="Airport Not found")
    return band


@router.patch("/airports/{id}/", response_model=Airport)
def update_airport(
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
def create_airline(
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
def list_airlines(
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
def airline_retrieve(id: Annotated[int, Path(title="The Airline id")], session: SessionDep):
    airline = session.get(Airline, id)
    if airline is None:
        raise HTTPException(status_code=404, detail="Airline Not found")
    return airline


@router.patch("/airlines/{id}/", response_model=AirlineOut)
def update_airline(
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


@router.post("/flights/", response_model=FlightRead)
def create_flight(
    flight: FlightCreate, session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]
):
    airline = session.get(Airline, flight.airline_id)
    if not airline:
        raise HTTPException(status_code=404, detail="Airline does not exist")
    if not current_user or not (current_user.role == "Global Admin" or current_user in airline.admins):
        raise HTTPException(status_code=403, detail="Permission denied")

    flight_number = f"{airline.icao_code}{flight.flight_number}"
    existing_flight = session.exec(
        select(Flight).where(
            Flight.flight_number == flight_number,
            func.date(Flight.date_time) == flight.date_time.date(),
            Flight.departure_port_id == flight.departure_port_id,
        )
    ).first()
    if existing_flight:
        raise HTTPException(
            status_code=400, detail="A flight with this number has alreadey been schedulled for this day"
        )

    flight_ = Flight(**flight.model_dump())
    setattr(flight_, "flight_number", flight_number)
    session.add(flight_)
    try:
        session.commit()
        session.refresh(flight_)
    except Exception as exc_:
        session.rollback()
        raise HTTPException(detail=str(exc_), status_code=400)
    return flight_


@router.get("/flights/", response_model=list[FlightRead])
def list_flights(session: SessionDep):
    return session.exec(select(Flight))


@router.get("/flights/{id}/", response_model=FlightRead)
def flight_retrieve(id: Annotated[int, Path(title="The Airport id")], session: SessionDep):
    flight = session.get(Flight, id)
    if flight is None:
        raise HTTPException(status_code=404, detail="Airport Not found")
    return flight


@router.patch("/flights/{id}/", response_model=FlightRead)
def update_flight(
    id: int, flight: FlightUpdate, session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]
):
    stored_flight = session.get(Flight, id)
    if not stored_flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    if not current_user or not (current_user.role == "Global Admin" or current_user in stored_flight.airline.admins):
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        number_ = flight.flight_number or stored_flight.flight_number[3:]
        dep = flight.departure_port_id or stored_flight.departure_port_id
        if flight.date_time:
            date_ = flight.date_time.date()
        else:
            date_ = stored_flight.date_time.date()
    except Exception as exc:
        raise exc
    else:
        flight_number = f"{stored_flight.airline.icao_code}{number_}"
        existing_flight = session.exec(
            select(Flight).where(
                Flight.flight_number == flight_number,
                func.date(Flight.date_time) == date_,
                Flight.departure_port_id == dep,
                Flight.id != id,
            )
        ).first()
        if existing_flight:
            raise HTTPException(
                status_code=400, detail="A flight with this number has alreadey been schedulled for this day"
            )

    update_data = flight.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(stored_flight, key, value)
    stored_flight.flight_number = flight_number

    session.add(stored_flight)
    session.commit()
    session.refresh(stored_flight)
    return stored_flight


@router.post("/flights/{id}/seats", response_model=list[SeatRead])
def create_flight_seats(
    id: int, seats: list[str], session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]
):
    flight = session.get(Flight, id)
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    if not current_user or not (current_user.role == "Global Admin" or current_user in flight.airline.admins):
        raise HTTPException(status_code=403, detail="Permission denied")

    for seat in seats:
        if not validate_seat_number(seat):
            raise HTTPException(status_code=400, detail=f"{seat} is not in the right format")
        else:
            st = FlightSeat(flight_id=flight.id, seat_number=seat)  # type: ignore
            session.add(st)

    try:
        session.commit()
    except Exception as exc_:
        session.rollback()
        raise HTTPException(detail=str(exc_), status_code=400)
    created_seats = session.exec(select(FlightSeat).where(FlightSeat.flight_id == flight.id))
    return created_seats


@router.get("/flights/{id}/seats", response_model=list[SeatRead])
def get_flight_seats(id: int, session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]):
    flight = session.get(Flight, id)
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    flight_seats = session.exec(select(FlightSeat).where(FlightSeat.flight_id == flight.id))
    return flight_seats


@router.post("/flights/{id}/reserve_seats", response_model=list[SeatRead])
def reserve_flight_seats(
    id: int, seats: list[int], session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Reserve seats without assigning passengers"""
    flight = session.get(Flight, id)
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    if not current_user or not (current_user.role == "Global Admin" or current_user in flight.airline.admins):
        raise HTTPException(status_code=403, detail="Permission denied")

    for seat in seats:
        st = session.get(FlightSeat, seat)
        if not st:
            raise HTTPException(status_code=404, detail=f"Seat {seat} not found")
        st.status = SeatStatus.BOOKED
        session.add(st)

    try:
        session.commit()
    except Exception as exc_:
        session.rollback()
        raise HTTPException(detail=str(exc_), status_code=400)
    return JSONResponse(content="Request successful")


@router.post("/reservations/", response_model=PNRRead)
def create_reservation(
    data: PNRCreate,
    session: SessionDep,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    seat = session.exec(
        select(FlightSeat).where(FlightSeat.seat_number == data.seat_number, FlightSeat.flight_id == data.flight_id)
    ).first()
    if seat:
        seat.status = SeatStatus.BOOKED
        session.add(seat)
    data_dict = data.model_dump()
    payment_info = data_dict.pop("payment_info")
    data_dict["booking_reference"] = generate_booking_ref(data.flight_id, session=session)
    rsv = PassengerNameRecord(**data_dict)
    session.add(rsv)
    try:
        session.commit()
        session.refresh(rsv)
    except Exception as exc_:
        session.rollback()
        raise HTTPException(detail=str(exc_), status_code=400)
    if rsv:
        background_tasks.add_task(process_reservation, rsv.id, payment_info, session)  # type: ignore
    return rsv


@router.post("/reservations/{id}/pay")
def pay_for_reservation(
    id: int,
    data: PaymentInfo,
    session: SessionDep,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    rsv = session.get(PassengerNameRecord, id)
    if not rsv:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if not (
        rsv.user_id == current_user.id
        or current_user.role == UserRole.GLOBAL_ADMIN
        or current_user in rsv.flight.airline.admins
    ):
        raise HTTPException(status_code=403, detail="Permission Denied")
    payment_info = data.model_dump()
    background_tasks.add_task(process_reservation, rsv.id, payment_info, session)  # type: ignore
    return JSONResponse(content="Request is being processed. We will send a mail shortly")


@router.post("/reservations/{id}/cancel")
def cancel_reservation(
    id: int,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    rsv = session.get(PassengerNameRecord, id)
    if not rsv:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if not (
        current_user.id == rsv.user_id
        or current_user.role == UserRole.GLOBAL_ADMIN
        or current_user in rsv.flight.airline.admins
    ):
        raise HTTPException(status_code=403, detail="Permission Denied")
    if rsv.status == ReservationStatus.TICKETED:
        raise HTTPException(status_code=400, detail="The reservation is ticketed and cannot be cancelled")
    seat = session.exec(
        select(FlightSeat).where(FlightSeat.seat_number == rsv.seat_number, FlightSeat.flight_id == rsv.flight_id)
    ).first()
    if seat:
        seat.status = SeatStatus.AVAILABLE
        session.add(seat)
    rsv.status = ReservationStatus.CANCELLED
    session.add(rsv)
    session.commit()
    return JSONResponse(content="Reservation cancelled")
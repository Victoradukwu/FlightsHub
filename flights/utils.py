from datetime import datetime

from sqlmodel import select

from common.utils import send_email
from db import SessionDep
from models.flights import Flight, PassengerNameRecord, ReservationStatus


def send_ticket_email(rsv):
    msg = f"""
        <html>
        <head></head>
        <body>
        Hi {rsv.passenger_name},
        <p>
        Please find below, the details of your flight ticket. 
        </p>
        <p>
        Passenger name: {rsv.passenger_name}<br/>
        Ticket number: {rsv.ticket_number}<br/>
        Flight number: {rsv.flight.flight_number}<br/>
        Departure date: {rsv.date_time.date()}<br/>
        Departure time: {rsv.date_time.strftime('%H:%M')} hours<br/>
        Carrier: {rsv.flight.airline.airline_name}<br/>
        booking_reference: {rsv.booking_reference}<br/>
        seat_number: {rsv.seat_number}<br/>
        Travelling from: {rsv.departure_port}<br/>
        Travelling to: {rsv.destination_port}
        </p>
        <p>For more information, contact {rsv.flight.airline.contact_phone}</p>
        Thank you,
        <br>
        FlightsHub Team
        </body>
        </html>
        """
    send_email(rsv.email,"Flight Ticket", msg)

def generate_booking_ref(flight_id, session: SessionDep):
    flight = session.get(Flight, flight_id)
    if not flight:
        raise ValueError(f"Flight with id {flight_id} not found")
    records = session.exec(select(PassengerNameRecord).where(PassengerNameRecord.flight_id == flight.id).order_by(PassengerNameRecord.booking_reference.desc())) # type: ignore
    last_record = records.first()
    yr = datetime.now().year
    if last_record and last_record.booking_reference:
        last_ref = last_record.booking_reference
        num = int(last_ref.split('-')[-1])
        next_num = num + 1
        next_ref = f'PNR-{flight.airline.icao_code}-{yr}-{next_num:07}'
        return next_ref
    return f"PNR-{flight.airline.icao_code}-{yr}-0000001"


def generate_ticket_number(flight_id, session: SessionDep):
    flight = session.get(Flight, flight_id)
    if not flight:
        raise ValueError(f"Flight with id {flight_id} not found")

    records = session.exec(select(PassengerNameRecord).where(PassengerNameRecord.flight_id == flight.id).order_by(PassengerNameRecord.ticket_number.desc())) # type: ignore
    all_records = records.all()
    last_record = all_records[1] if len(all_records) > 1 else None
    if last_record and last_record.ticket_number:
        last_ref = last_record.ticket_number
        num = int(last_ref.split('-')[-1])
        next_num = num + 1
        next_ref = f'TKT-{flight.airline.icao_code}-{flight.flight_number}-{next_num:04}'
        return next_ref
    return f"TKT-{flight.airline.icao_code}-{flight.flight_number}-0001"

def process_payment(payment_info):
    """packages and send payment request to the payment processor"""
    pass


def process_reservation(pnr_id:int, payment_info, session: SessionDep):
    process_payment(payment_info)
    rsv = session.get(PassengerNameRecord, pnr_id)
    if not rsv:
        raise ValueError(f"Reservation with id {pnr_id} not found")
    ticket_number = generate_ticket_number(rsv.flight_id, session=session) # Should actually be done in response to successful webhook call from the payment processor
    # rsv = session.get(PassengerNameRecord, id)
    if rsv:
        rsv.ticket_number = ticket_number
        rsv.status = ReservationStatus.TICKETED
        session.add(rsv)
        session.commit()
    session.refresh(rsv)
    send_ticket_email(rsv)
    return True
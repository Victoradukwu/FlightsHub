from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.config import get_settings
from celery_app import celery_app
from common.utils import send_email
from db import engine
from models.flights import (FlightSeat, PassengerNameRecord, ReservationStatus,
                            SeatStatus)


@celery_app.task(name='tasks.send_payment_reminders')
def send_payment_reminders():
    "Send email reminders to passengers with unpaid reservations"
    session = Session(engine)
    settings = get_settings()
    try:
        # Find all PNRs with status=BOOKED (unpaid) and created before the last 30 minutes
        records = session.exec(select(PassengerNameRecord).where(
                PassengerNameRecord.status == ReservationStatus.BOOKED,
                PassengerNameRecord.created_at <= (datetime.now(timezone.utc) - timedelta(minutes=30))
            ))
        for record in records:
            email = record.email
            name = record.passenger_name
            flight = record.flight
            deadline1 = (record.created_at + timedelta(minutes=30))
            deadline2 = (record.date_time - timedelta(minutes=30))
            deadline = min(deadline1, deadline2).strftime('%Y-%m-%d %H:%M')
            subject = getattr(settings, 'EMAIL_SUBJECT', 'Payment Reminder: Complete Your Booking')
            body_template = getattr(settings, 'EMAIL_BODY_TEMPLATE',
                'Dear {name},<br><br>Your reservation for flight {flight_number} on {date_time} is pending payment. Please complete payment before {deadline} to avoid cancellation.<br><br>Thank you.')
            body = body_template.format(
                name=name,
                flight_number=flight.flight_number,
                date_time=flight.date_time,
                deadline=deadline,
            )
            send_email(email, subject, body)
    finally:
        session.close()



@celery_app.task(name='tasks.cancel_reservation')
def cancel_unpaid_reservations():
    "Cancel unpaid reservations, 30 minutes to flight take-off"
    session = Session(engine)
    settings = get_settings()
    try:
        # Find all PNRs with status=BOOKED (unpaid) and created before the last 30 minutes
        records = session.exec(select(PassengerNameRecord).where(
                PassengerNameRecord.status == ReservationStatus.BOOKED,
                PassengerNameRecord.created_at <= (datetime.now(timezone.utc) - timedelta(minutes=30))
            ))
        for record in records:
            flight = record.flight
            if datetime.now()  + timedelta(minutes=30) < record.flight.date_time:
                pass
            record.status = ReservationStatus.CANCELLED
            session.add(record)
            seat = session.exec(select(FlightSeat).where(
                FlightSeat.flight_id == flight.id,
                FlightSeat.seat_number == record.seat_number
            )).first()
            if seat:
                seat.status = SeatStatus.AVAILABLE
                session.add(seat)
            session.commit()

            #Send email to the passenger
            email = record.email
            name = record.passenger_name
            subject = getattr(settings, 'EMAIL_SUBJECT', 'Reservation Cancelled')
            body_template = getattr(settings, 'EMAIL_BODY_TEMPLATE',
                'Dear {name},<br><br>Your reservation for flight {flight_number} on {date_time} has been canceled. This is because the flight takes off in 30 minutes, and you have not effected your payment yet. Kindly rebook and pay immediately, if you are still interested.<br><br>Thank you.')
            body = body_template.format(
                name=name,
                flight_number=flight.flight_number,
                date_time=flight.date_time.strftime('%Y-%M-%d %H:%M')
            )
            send_email(email, subject, body)
    finally:
        session.close()

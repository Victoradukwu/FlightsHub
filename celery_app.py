
from celery import Celery
from celery.schedules import crontab  # noqa: F401

from app.config import get_settings

settings = get_settings()

celery_app = Celery('flightshub')
celery_app.config_from_object(settings, namespace='CELERY')
celery_app.conf.include = ['tasks']


celery_app.conf.beat_schedule = {
    # 'send-payment-reminders': {
    #     'task': 'tasks.send_payment_reminders',
    #     'schedule': crontab(minute='0,15,30,45'),
    # },
    # 'cancel_reservations': {
    #     'task': 'tasks.cancel_reservation',
    #     'schedule': crontab(minute='0,15,30,45'),
    # }
}
    
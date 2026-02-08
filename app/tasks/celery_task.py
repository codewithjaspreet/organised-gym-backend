# app/tasks/payment_reminders.py
from app.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def process_payment_reminder(self, payload: dict):
    logger.info("Received reminder event: %s", payload)

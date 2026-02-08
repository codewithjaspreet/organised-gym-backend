from app.celery_app import celery_app
import logging

from app.db.db import get_engine
from sqlmodel import Session
from app.utils.fcm_notification import send_fcm_notification_to_user

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3, autoretry_for=(Exception,))
def process_payment_reminder(self, payload: dict):
    """
    Payload comes from SNS → SQS
    """
    user_id = payload["user_id"]
    membership_id = payload["membership_id"]
    days_left = payload["days_left"]

    title = "Payment Reminder"
    body = (
        "Your gym membership expires today."
        if days_left == 0
        else f"Your gym membership expires in {days_left} days."
    )

    logger.info(
        f"[CELERY] Sending reminder to user={user_id}, membership={membership_id}"
    )

    engine = get_engine()
    with Session(engine) as session:
        send_fcm_notification_to_user(
            user_id=user_id,
            title=title,
            body=body,
            data={
                "type": "PAYMENT_REMINDER",
                "membership_id": membership_id,
                "days_left": days_left,
            },
            session=session,
        )

    logger.info(f"[CELERY] Notification sent to user={user_id}")

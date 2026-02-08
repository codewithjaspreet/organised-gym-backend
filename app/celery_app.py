# app/celery_app.py
import os
from celery import Celery
from app.core.config import settings

# Disable pycurl to avoid dependency issues
os.environ["CELERY_DISABLE_ALL_ASYNC"] = "False"

celery_app = Celery(
    "payment_reminders",
    broker=f"sqs://",
)

celery_app.conf.update(
    broker_transport_options={
        "region": settings.aws_region,
        "visibility_timeout": 60,
        "polling_interval": 5,
        "queue_name_prefix": "",
        "predefined_queues": {
            "og-payment-reminders-queue": {
                "url": "https://sqs.ap-south-1.amazonaws.com/324512687832/og-payment-reminders-dlq"
            }
        },
        "is_secure": True,
    },
    task_default_queue="og-payment-reminders-queue",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_disable_rate_limits=True,
    kombu_default_retry_delay=5,
    broker_pool_limit=None,
    broker_connection_retry_on_startup=False,
    # Use synchronous HTTP client instead of async
    kombu_default_exchange_kwargs={"durable": True},
)


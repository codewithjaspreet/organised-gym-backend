import boto3
import json
from app.core.config import settings

sns_client = boto3.client(
    "sns",
    region_name=settings.aws_region
)

def publish_reminder_event(payload: dict):
    sns_client.publish(
        TopicArn=settings.SNS_PAYMENT_REMINDERS_TOPIC_ARN,
        Message=json.dumps(payload)
    )

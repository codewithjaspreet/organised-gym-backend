# utils/email.py
import os
from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings
conf = ConnectionConfig(
    MAIL_USERNAME=settings.smtp_user,
    MAIL_PASSWORD=settings.smtp_password.get_secret_value(),
    MAIL_FROM=settings.no_reply_email,
    MAIL_PORT=settings.smtp_port,
    MAIL_SERVER=settings.smtp_host,
    MAIL_FROM_NAME="Organised Gym (OG)",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path("app/templates"),
)

async def send_reset_password_mail(
    recipient_email: str,
    user_name: str,
    url: str,
    expire_in_minutes: int,
) -> None:
    message = MessageSchema(
        subject="Reset your Organised Gym password",
        recipients=[recipient_email],
        template_body={
            "name": user_name,
            "url": url,
            "expire": expire_in_minutes,
        },
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    await fm.send_message(message, template_name="og_password_reset.html")


async def send_password_reset_confirmation_mail(
    recipient_email: str,
    name: str,
) -> None:
    message = MessageSchema(
        subject="Your Organised Gym password has been reset",
        recipients=[recipient_email],
        template_body={"name": name},
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    await fm.send_message(message, template_name="og_password_reset_confirmation.html")

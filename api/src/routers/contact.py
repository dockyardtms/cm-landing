from fastapi import APIRouter
from pydantic import BaseModel
import asyncio
import smtplib
import ssl
import logging
from email.message import EmailMessage

from config import get_settings
from exceptions import LandingAPIException


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/contact", tags=["contact"])


class ContactRequest(BaseModel):
    name: str
    phone: str


async def _send_contact_email(name: str, phone: str) -> None:
    settings = get_settings()


    # Log effective SMTP configuration (excluding password) for debugging
    logger.info(
        "SMTP settings for contact email host=%s port=%s username=%s use_tls=%s from=%s to=%s",
        settings.smtp_host,
        settings.smtp_port,
        settings.smtp_username,
        settings.smtp_use_tls,
        settings.email_from,
        settings.email_to,
    )

    message = EmailMessage()
    message["Subject"] = "New contact submission"
    message["From"] = settings.email_from
    message["To"] = settings.email_to

    body_lines = [
        f"Name: {name}",
        f"Phone: {phone}",
    ]
    message.set_content("\n".join(body_lines))

    def send_email() -> None:
        if settings.smtp_use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls(context=context)
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)

    await asyncio.to_thread(send_email)


@router.post("")
async def create_contact(request: ContactRequest):
    try:
        s = get_settings()
        logger.info(
            "Contact email submission host=%s port=%s username=%s use_tls=%s from=%s to=%s",
            s.smtp_host,
            s.smtp_port,
            s.smtp_username,
            s.smtp_use_tls,
            s.email_from,
            s.email_to,
        )
        await _send_contact_email(request.name, request.phone)
    except Exception as exc:  # noqa: BLE001
        raise LandingAPIException(
            status_code=500,
            error_code="EMAIL_SEND_FAILED",
            message="Failed to send contact email",
            details={"error": str(exc)},
        ) from exc

    return {"status": "ok"}

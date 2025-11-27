from fastapi import APIRouter
from pydantic import BaseModel
import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from config import get_settings
from exceptions import LandingAPIException


router = APIRouter(prefix="/contact", tags=["contact"])


class ContactRequest(BaseModel):
    name: str
    phone: str


async def _send_contact_email(name: str, phone: str) -> None:
    settings = get_settings()

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
        await _send_contact_email(request.name, request.phone)
    except Exception as exc:  # noqa: BLE001
        raise LandingAPIException(
            status_code=500,
            error_code="EMAIL_SEND_FAILED",
            message="Failed to send contact email",
            details={"error": str(exc)},
        ) from exc

    return {"status": "ok"}

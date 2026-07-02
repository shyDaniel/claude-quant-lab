from __future__ import annotations

from dataclasses import dataclass

from twilio.rest import Client

from qlab.briefing_service.config import Settings


@dataclass(frozen=True)
class SmsResult:
    sent: bool
    sid: str | None
    detail: str


def send_sms(settings: Settings, body: str) -> SmsResult:
    if settings.dry_run:
        return SmsResult(sent=False, sid=None, detail=f"DRY_RUN: {body}")
    if not settings.sms_to_phone:
        raise ValueError("BRIEF_TO_PHONE is required when BRIEFING_DRY_RUN=false")
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are required")
    if not settings.twilio_from_phone and not settings.twilio_messaging_service_sid:
        raise ValueError("Set TWILIO_FROM_PHONE or TWILIO_MESSAGING_SERVICE_SID")

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    kwargs = {"body": body, "to": settings.sms_to_phone}
    if settings.twilio_messaging_service_sid:
        kwargs["messaging_service_sid"] = settings.twilio_messaging_service_sid
    else:
        kwargs["from_"] = settings.twilio_from_phone
    message = client.messages.create(**kwargs)
    return SmsResult(sent=True, sid=message.sid, detail="sent")

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from qlab.briefing_service.briefing import build_briefing
from qlab.briefing_service.config import Settings
from qlab.briefing_service.sms import send_sms


def run_briefing_job(settings: Settings) -> dict[str, Any]:
    briefing = build_briefing(settings)
    sms_result = send_sms(settings, briefing.body)
    return {
        "briefing": briefing.body,
        "sms": asdict(sms_result),
    }

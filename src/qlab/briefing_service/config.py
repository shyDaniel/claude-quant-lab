from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is optional for local dry runs
    def load_dotenv(*_: object, **__: object) -> bool:
        return False


DEFAULT_FEEDS = (
    "https://feeds.bbci.co.uk/news/business/rss.xml,"
    "https://finance.yahoo.com/news/rssindex,"
    "https://www.cnbc.com/id/100003114/device/rss/rss.html"
)


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _csv_env(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str
    holdings_path: Path
    briefing_interval_hours: int
    briefing_timezone: str
    dry_run: bool
    send_on_start: bool
    admin_token: str | None
    sms_to_phone: str | None
    twilio_account_sid: str | None
    twilio_auth_token: str | None
    twilio_from_phone: str | None
    twilio_messaging_service_sid: str | None
    news_feeds: list[str]

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
            holdings_path=Path(os.getenv("HOLDINGS_PATH", "config/holdings.local.json")),
            briefing_interval_hours=_int_env("BRIEFING_INTERVAL_HOURS", 8),
            briefing_timezone=os.getenv("BRIEFING_TIMEZONE", "America/Los_Angeles"),
            dry_run=_bool_env("BRIEFING_DRY_RUN", True),
            send_on_start=_bool_env("BRIEFING_SEND_ON_START", False),
            admin_token=os.getenv("BRIEFING_ADMIN_TOKEN"),
            sms_to_phone=os.getenv("BRIEF_TO_PHONE"),
            twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
            twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
            twilio_from_phone=os.getenv("TWILIO_FROM_PHONE"),
            twilio_messaging_service_sid=os.getenv("TWILIO_MESSAGING_SERVICE_SID"),
            news_feeds=_csv_env("BRIEFING_NEWS_FEEDS", DEFAULT_FEEDS),
        )

    def with_dry_run(self, dry_run: bool) -> "Settings":
        return replace(self, dry_run=dry_run)

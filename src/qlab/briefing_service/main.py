from __future__ import annotations

import argparse
import json
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
import uvicorn

from qlab.briefing_service.app import create_app
from qlab.briefing_service.briefing import build_briefing
from qlab.briefing_service.config import Settings
from qlab.briefing_service.holdings import load_portfolio, load_portfolio_from_text
from qlab.briefing_service.runner import run_briefing_job
from qlab.briefing_service.sms import send_sms


def run_once(send: bool, force_dry_run: bool) -> None:
    settings = Settings.from_env()
    if force_dry_run:
        settings = settings.with_dry_run(True)
    briefing = build_briefing(settings)
    print(briefing.body)
    if send:
        result = send_sms(settings, briefing.body)
        print(json.dumps(result.__dict__, indent=2))


def run_scheduler() -> None:
    settings = Settings.from_env()
    scheduler = BlockingScheduler(timezone=settings.briefing_timezone)
    scheduler.add_job(
        lambda: print(json.dumps(run_briefing_job(settings), indent=2)),
        "interval",
        hours=settings.briefing_interval_hours,
        id="market_briefing",
        replace_existing=True,
    )
    if settings.send_on_start:
        print(json.dumps(run_briefing_job(settings), indent=2))
    scheduler.start()


def doctor(live: bool, include_briefing: bool) -> int:
    settings = Settings.from_env()
    errors: list[str] = []
    warnings: list[str] = []

    if settings.holdings_json:
        try:
            load_portfolio_from_text(settings.holdings_json, "HOLDINGS_JSON")
        except Exception as exc:  # noqa: BLE001 - config doctor should report all failures
            errors.append(f"HOLDINGS_JSON is invalid: {exc}")
    else:
        try:
            load_portfolio(settings.holdings_path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"HOLDINGS_PATH is invalid: {exc}")

    if live:
        required = {
            "OPENAI_API_KEY": settings.openai_api_key,
            "BRIEF_TO_PHONE": settings.sms_to_phone,
            "TWILIO_ACCOUNT_SID": settings.twilio_account_sid,
            "TWILIO_AUTH_TOKEN": settings.twilio_auth_token,
        }
        for name, value in required.items():
            if not value:
                errors.append(f"{name} is required for live SMS")
        if not settings.twilio_from_phone and not settings.twilio_messaging_service_sid:
            errors.append("TWILIO_FROM_PHONE or TWILIO_MESSAGING_SERVICE_SID is required for live SMS")
        if settings.dry_run:
            errors.append("BRIEFING_DRY_RUN must be false for live SMS")

    if include_briefing and not errors:
        try:
            briefing = build_briefing(settings.with_dry_run(True))
            print(briefing.body)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Dry-run briefing failed: {exc}")

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print("doctor: ok")
    return 0


def serve(host: str, port: int) -> None:
    app = create_app(Settings.from_env())
    uvicorn.run(app, host=host, port=port, workers=1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the quant-lab briefing service.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    once = subparsers.add_parser("once", help="Build one briefing and optionally send it.")
    once.add_argument("--send", action="store_true", help="Send via Twilio after generating.")
    once.add_argument("--dry-run", action="store_true", help="Force SMS dry-run mode.")

    server = subparsers.add_parser("serve", help="Run the 24/7 FastAPI scheduler service.")
    server.add_argument("--host", default="0.0.0.0")
    server.add_argument("--port", type=int, default=8080)

    subparsers.add_parser("scheduler", help="Run the foreground SMS scheduler worker.")

    doctor_cmd = subparsers.add_parser("doctor", help="Validate cloud/runtime configuration.")
    doctor_cmd.add_argument("--live", action="store_true", help="Require live SMS credentials.")
    doctor_cmd.add_argument("--briefing", action="store_true", help="Generate a dry-run briefing.")

    args = parser.parse_args()
    if args.command == "once":
        run_once(send=args.send, force_dry_run=args.dry_run)
    elif args.command == "serve":
        serve(host=args.host, port=args.port)
    elif args.command == "scheduler":
        run_scheduler()
    elif args.command == "doctor":
        raise SystemExit(doctor(live=args.live, include_briefing=args.briefing))


if __name__ == "__main__":
    main()

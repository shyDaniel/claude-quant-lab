from __future__ import annotations

import argparse
from dataclasses import asdict

import uvicorn

from qlab.briefing_service.app import create_app
from qlab.briefing_service.briefing import build_briefing
from qlab.briefing_service.config import Settings
from qlab.briefing_service.sms import send_sms


def run_once(send: bool, force_dry_run: bool) -> None:
    settings = Settings.from_env()
    if force_dry_run:
        settings = settings.with_dry_run(True)
    briefing = build_briefing(settings)
    print(briefing.body)
    if send:
        result = send_sms(settings, briefing.body)
        print(asdict(result))


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

    args = parser.parse_args()
    if args.command == "once":
        run_once(send=args.send, force_dry_run=args.dry_run)
    elif args.command == "serve":
        serve(host=args.host, port=args.port)


if __name__ == "__main__":
    main()

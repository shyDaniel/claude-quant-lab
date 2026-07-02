from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Header, HTTPException

from qlab.briefing_service.briefing import build_briefing
from qlab.briefing_service.config import Settings
from qlab.briefing_service.runner import run_briefing_job


def _authorize(settings: Settings, token: str | None) -> None:
    if settings.admin_token and token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Set X-Admin-Token to the configured token")


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or Settings.from_env()
    app = FastAPI(title="Quant Lab Briefing Service")
    scheduler = BackgroundScheduler(timezone=active_settings.briefing_timezone)

    def run_job() -> dict[str, object]:
        return run_briefing_job(active_settings)

    @app.on_event("startup")
    def startup() -> None:
        scheduler.add_job(
            run_job,
            "interval",
            hours=active_settings.briefing_interval_hours,
            id="market_briefing",
            replace_existing=True,
        )
        scheduler.start()
        if active_settings.send_on_start:
            run_job()

    @app.on_event("shutdown")
    def shutdown() -> None:
        scheduler.shutdown(wait=False)

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "ok": True,
            "dry_run": active_settings.dry_run,
            "interval_hours": active_settings.briefing_interval_hours,
        }

    @app.get("/briefing/preview")
    def preview(x_admin_token: str | None = Header(default=None)) -> dict[str, object]:
        _authorize(active_settings, x_admin_token)
        briefing = build_briefing(active_settings)
        return {"briefing": briefing.body, "context": briefing.context}

    @app.post("/briefing/send")
    def send_now(x_admin_token: str | None = Header(default=None)) -> dict[str, object]:
        _authorize(active_settings, x_admin_token)
        return run_job()

    return app


app = create_app()

"""Yaqeen FastAPI app: health, auth, banks, applications, documents and decisions."""
import asyncio
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.auth import routes as auth_routes
from app.config import ConfigurationError, CorsSettings, Settings, get_settings, load_settings
from app.db import get_session_factory
from app.models import Application
from app.pipeline.run import run_pipeline
from app.routes import applications as applications_routes
from app.routes import banks as banks_routes
from app.routes import decisions as decisions_routes
from app.routes import documents as documents_routes


def _startup_sweep(settings: Settings) -> None:
    """Re-queue applications stuck in processing for longer than five minutes."""
    try:
        factory = get_session_factory()
        with factory.begin() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
            apps = session.execute(
                select(Application).where(
                    Application.status == "processing",
                    Application.processing_started_at < cutoff,
                )
            ).scalars().all()
            for app in apps:
                app.processing_started_at = datetime.now(timezone.utc)
                app.processing_attempts += 1
    except Exception:
        # Sweep failures must not prevent the app from starting.
        return

    for app in apps:
        try:
            run_pipeline(app.id, settings)
        except Exception:
            pass


def create_app(*, validate_all: bool = True) -> FastAPI:
    # Validate environment values, but never connect to external services.
    # Tests may isolate CORS/health with validate_all=False.
    settings = get_settings() if validate_all else load_settings(CorsSettings)
    application = FastAPI(title="Yaqeen", docs_url=None, redoc_url=None, openapi_url=None)
    application.add_middleware(
        CORSMiddleware, allow_origins=[settings.FRONTEND_ORIGIN],
        allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"],
        allow_credentials=False,
    )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
    application.include_router(banks_routes.router)
    application.include_router(applications_routes.router)
    application.include_router(documents_routes.router)
    application.include_router(decisions_routes.router)

    @application.on_event("startup")
    async def startup() -> None:
        try:
            full_settings = get_settings()
        except ConfigurationError:
            return
        # Run sweep in a thread so startup is non-blocking.
        asyncio.create_task(asyncio.to_thread(_startup_sweep, full_settings))

    return application


# Full validation is available via create_app(validate_all=True). The default keeps
# the health endpoint usable when unrelated service settings are not yet configured.
app = create_app(validate_all=False)

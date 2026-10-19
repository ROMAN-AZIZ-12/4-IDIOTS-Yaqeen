"""Phase 1 public health endpoint only."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CorsSettings, get_settings, load_settings


def create_app(*, validate_all: bool = True) -> FastAPI:
    # Validate environment values, but never connect to external services.
    # Tests may isolate CORS/health with validate_all=False.
    settings = get_settings() if validate_all else load_settings(CorsSettings)
    application = FastAPI(title="Yaqeen", docs_url=None, redoc_url=None, openapi_url=None)
    application.add_middleware(
        CORSMiddleware, allow_origins=[settings.FRONTEND_ORIGIN],
        allow_methods=["GET"], allow_headers=[], allow_credentials=False,
    )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()

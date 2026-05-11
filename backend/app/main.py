from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import logging_middleware, setup_logging
from app.core.rate_limit import create_limiter, limiter


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()
    app = FastAPI(title="AI Interview Coach API")

    app.state.limiter = create_limiter()
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list() or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(logging_middleware)
    app.include_router(router)
    return app


app = create_app()


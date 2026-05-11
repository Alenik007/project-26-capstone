from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    logger = structlog.get_logger("api")
    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    session_id = None
    try:
        if request.method.upper() == "POST" and request.url.path.endswith("/chat"):
            body = await request.json()
            session_id = body.get("session_id")
    except Exception:
        session_id = None

    try:
        response = await call_next(request)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "request",
            request_id=request_id,
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            execution_time_ms=elapsed_ms,
            session_id=session_id,
        )
        response.headers["X-Request-Id"] = request_id
        return response
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.error(
            "request_error",
            request_id=request_id,
            endpoint=request.url.path,
            method=request.method,
            execution_time_ms=elapsed_ms,
            session_id=session_id,
            error=str(e),
        )
        raise


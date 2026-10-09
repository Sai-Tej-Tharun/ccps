"""
Response-time and error logging for the payment service. Rows go to the same
adminpanel_requestlog table as Django's, so the admin dashboard shows both.
Recording is best-effort: it can never fail a request.
"""

import logging
import os
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from starlette.concurrency import run_in_threadpool

from database import get_db
from models import RequestLog

logger = logging.getLogger("ccps.requests")
SLOW_REQUEST_MS = int(os.environ.get("SLOW_REQUEST_MS", "1000"))
ENABLED = os.environ.get("REQUEST_METRICS_ENABLED", "True") == "True"
SKIP_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


def _store(app: FastAPI, method: str, route: str, status_code: int, duration_ms: int, error: str) -> None:
    # Uses the app's own get_db (or the test override), so tests need no special wiring.
    factory = app.dependency_overrides.get(get_db, get_db)
    generator = factory()
    db = next(generator)
    try:
        db.add(
            RequestLog(
                service="fastapi",
                method=method[:8],
                path=route[:200],
                status_code=status_code,
                duration_ms=duration_ms,
                error=error[:255],
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
        raise
    finally:
        generator.close()


def install(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_metrics(request: Request, call_next):
        started = time.perf_counter()
        error = ""
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:  # noqa: BLE001 - recorded, then re-raised so FastAPI still returns its 500
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            if ENABLED and request.url.path not in SKIP_PATHS:
                route_obj = request.scope.get("route")
                route = getattr(route_obj, "path", request.url.path)
                level = logging.ERROR if status_code >= 500 else logging.WARNING if duration_ms >= SLOW_REQUEST_MS else logging.INFO
                logger.log(level, "%s %s -> %s in %sms", request.method, route, status_code, duration_ms)
                try:
                    await run_in_threadpool(_store, request.app, request.method, route, status_code, duration_ms, error)
                except Exception:  # noqa: BLE001
                    logger.warning("Could not store request metrics", exc_info=True)
        response.headers["X-Response-Time-ms"] = str(duration_ms)
        return response
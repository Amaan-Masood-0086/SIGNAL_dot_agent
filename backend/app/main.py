"""FastAPI application factory.

Error handling contract: errors MUST return `{"detail": "message"}` and MUST
NOT expose stack traces or internal details (backend contracts #7, MUST-NOT #1).
"""

from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.endpoints import admin as admin_endpoints
from app.api.v1.endpoints import audit as audit_endpoints
from app.api.v1.endpoints import auth as auth_endpoints
from app.api.v1.endpoints import children as children_endpoints
from app.api.v1.endpoints import credentials as credentials_endpoints
from app.api.v1.endpoints import flags as flags_endpoints
from app.api.v1.endpoints import reasoning as reasoning_endpoints
from app.api.v1.endpoints import referrals as referrals_endpoints
from app.api.v1.endpoints import sessions as sessions_endpoints
from app.api.v1.endpoints import stt as stt_endpoints
from app.api.v1.endpoints import usage as usage_endpoints
from app.core.config import Settings, get_settings
from app.core.envelope import envelope
from app.core.synthetic_gate import SyntheticDataViolation


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(
        title="SIGNAL API",
        version="0.1.0",
        # OpenAPI/docs hidden outside synthetic dev — no internal surface
        # leakage in any later environment.
        docs_url="/docs" if settings.ENVIRONMENT == "synthetic_only" else None,
        redoc_url=None,
    )
    app.state.settings = settings

    # Inject settings everywhere get_settings is used as a dependency.
    app.dependency_overrides[get_settings] = lambda: settings

    @app.exception_handler(SyntheticDataViolation)
    async def synthetic_violation_handler(request: Request, exc: SyntheticDataViolation):
        # Fail-closed: a non-synthetic write attempt is a forbidden action.
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)})

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        # Contract: 422 with {"detail": ...}; field errors stay structured
        # but never leak internals beyond the offending field names.
        # exc.errors()'s `ctx` can carry exception objects (model validators),
        # which are not JSON-serializable — coerce them to strings.
        detail = json.loads(json.dumps(exc.errors(), default=str))
        return JSONResponse(
            status_code=422,
            content={"detail": detail},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Never expose stack traces or DB errors (MUST-NOT #1).
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        """Defence-in-depth on the API itself.

        The browser never loads these responses as documents — it reaches the
        backend only through the Next proxies — so the frontend's headers do
        not cover this surface. A direct hit on the API (curl, a mobile
        client, a misrouted link) previously got no protective headers at all,
        and every response carried PHI with no cache directive.
        """
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        # This surface serves JSON only; it never needs to load anything.
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        )
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        # Every API response may carry child health data. Nothing here is
        # cacheable, by anyone, ever.
        response.headers["Cache-Control"] = "private, no-store"
        # Remove the server banner — free reconnaissance (OWASP A02).
        response.headers["Server"] = "SIGNAL"
        return response

    @app.get("/health")
    def health():
        return envelope({"status": "ok", "environment": settings.ENVIRONMENT})

    app.include_router(auth_endpoints.router, prefix="/api/v1")
    app.include_router(admin_endpoints.router, prefix="/api/v1")
    app.include_router(audit_endpoints.router, prefix="/api/v1")
    app.include_router(children_endpoints.router, prefix="/api/v1")
    app.include_router(credentials_endpoints.router, prefix="/api/v1")
    app.include_router(flags_endpoints.router, prefix="/api/v1")
    app.include_router(sessions_endpoints.router, prefix="/api/v1")
    app.include_router(reasoning_endpoints.router, prefix="/api/v1")
    app.include_router(referrals_endpoints.router, prefix="/api/v1")
    app.include_router(stt_endpoints.router, prefix="/api/v1")
    app.include_router(usage_endpoints.router, prefix="/api/v1")
    return app


# uvicorn entrypoint (`uvicorn app.main:app`): the ASGI server needs a real
# application object at import time — a lazy placeholder resolves to None and
# crashes every request. Tests use the create_app factory instead.
app = create_app()

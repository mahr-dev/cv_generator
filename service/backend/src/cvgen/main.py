"""
CV Generator API — FastAPI

CORS: middleware que fuerza cabeceras en la respuesta final (en Vercel a veces
CORSMiddleware no deja Access-Control-Allow-Origin en el 200). Misma idea que e-commerce.
"""
from __future__ import annotations

import os
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

from cvgen.adapters.http.routes import router as cv_router

# ---------------------------------------------------------------------------
# Orígenes permitidos (allow_credentials=True → origen reflejado, no "*")
# ---------------------------------------------------------------------------

ALLOW_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:80",
    "http://localhost",
]

_vercel = os.environ.get("VERCEL_URL")
if _vercel:
    ALLOW_ORIGINS.append(f"https://{_vercel}")

for _part in os.environ.get("CORS_EXTRA_ORIGINS", "").split(","):
    _o = _part.strip()
    if _o and _o not in ALLOW_ORIGINS:
        ALLOW_ORIGINS.append(_o)

_VERCEL_APP_ORIGIN = re.compile(r"^https://[\w-]+\.vercel\.app$")

_CORS_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"


def _resolve_allowed_origin(request: StarletteRequest) -> str | None:
    raw = request.headers.get("origin")
    if not raw:
        return None
    origin = raw.strip()
    if origin in ALLOW_ORIGINS or _VERCEL_APP_ORIGIN.match(origin):
        return origin
    return None


class StrictCorsMiddleware(BaseHTTPMiddleware):
    """Preflight OPTIONS + cabeceras CORS en todas las respuestas permitidas."""

    async def dispatch(self, request: StarletteRequest, call_next):
        origin = _resolve_allowed_origin(request)

        if request.method == "OPTIONS":
            if origin is None:
                return await call_next(request)
            req_headers = request.headers.get("access-control-request-headers")
            allow_headers = req_headers or "authorization, content-type, accept, origin, x-requested-with, x-cv-preview"
            return Response(
                status_code=204,
                headers={
                    "access-control-allow-origin": origin,
                    "access-control-allow-credentials": "true",
                    "access-control-allow-methods": _CORS_METHODS,
                    "access-control-allow-headers": allow_headers,
                    "access-control-max-age": "86400",
                    "vary": "Origin",
                },
            )

        response = await call_next(request)
        if origin is not None:
            response.headers["access-control-allow-origin"] = origin
            response.headers["access-control-allow-credentials"] = "true"
            response.headers["access-control-allow-methods"] = _CORS_METHODS
            existing = response.headers.get("vary", "")
            parts = [p.strip() for p in existing.split(",") if p.strip()] if existing else []
            if not any(p.lower() == "origin" for p in parts):
                parts.append("Origin")
            response.headers["vary"] = ", ".join(parts)
        return response


def create_app() -> FastAPI:
    app = FastAPI(title="CV Generator API")

    app.add_middleware(StrictCorsMiddleware)

    app.include_router(cv_router)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "cv-generator-api"}

    def _cors_headers_for_request(request: Request) -> dict[str, str]:
        o = _resolve_allowed_origin(request)
        if not o:
            return {}
        return {
            "access-control-allow-origin": o,
            "access-control-allow-credentials": "true",
            "access-control-allow-methods": _CORS_METHODS,
            "vary": "Origin",
        }

    @app.exception_handler(HTTPException)
    async def http_exception_with_cors(request: Request, exc: HTTPException) -> JSONResponse:
        hdrs: dict[str, str] = {}
        if exc.headers:
            hdrs = {k: v for k, v in exc.headers.items()}
        hdrs.update(_cors_headers_for_request(request))
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": jsonable_encoder(exc.detail)},
            headers=hdrs,
        )

    return app


app = create_app()

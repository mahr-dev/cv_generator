from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cvgen.adapters.http.routes import router as cv_router


def create_app() -> FastAPI:
    app = FastAPI(title="CV Generator API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(cv_router)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()


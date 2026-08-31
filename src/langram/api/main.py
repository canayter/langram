"""FastAPI application."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import auth, content, session

DESCRIPTION = (
    "Turkish for English speakers. Exercises are generated from a morphological "
    "grammar rather than drawn from a fixed list, and every wrong answer is "
    "classified by its linguistic cause."
)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Langram", version="0.1.0", description=DESCRIPTION)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router)
    app.include_router(content.router)
    app.include_router(session.router)

    @app.get("/api/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()

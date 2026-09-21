"""Entrypoint FastAPI — hub central WhatsApp Meta (DigitalOcean App Platform)."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app import __version__
from app.config import get_settings
from app.webhook import router as webhook_router

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(
    title="PH WhatsApp Meta Hub",
    version=__version__,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url=None,
)

app.include_router(webhook_router)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "whatsapp-meta-ph",
        "version": __version__,
        "env": settings.app_env,
    }

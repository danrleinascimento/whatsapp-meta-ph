"""Entrypoint FastAPI — hub (DigitalOcean) ou agente local (WHATSPH).

APP_ROLE=hub  → webhook Meta + pull events + Embedded Signup
APP_ROLE=agent → envio Graph + painel ticket + poller
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.config import get_settings
from app.db import db_ok

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("whatsmeta")


@asynccontextmanager
async def lifespan(app: FastAPI):
    role = settings.app_role
    logger.info("Iniciando whatsmeta role=%s version=%s", role, __version__)
    if role == "agent":
        from app.agent.poller import start_poller, stop_poller

        start_poller()
        try:
            yield
        finally:
            stop_poller()
    else:
        yield


app = FastAPI(
    title="PH WhatsApp Meta" + (" Hub" if settings.app_role == "hub" else " Agent"),
    version=__version__,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)

if settings.app_role == "hub":
    from app.hub.routes import router as hub_router
    from app.webhook import router as webhook_router

    app.include_router(webhook_router)
    app.include_router(hub_router)
else:
    from app.agent.routes import router as agent_router

    app.include_router(agent_router)


@app.get("/health")
def health() -> dict:
    payload = {
        "status": "ok",
        "service": "whatsapp-meta-ph",
        "role": settings.app_role,
        "version": __version__,
        "env": settings.app_env,
    }
    if settings.database_url:
        payload["db_ok"] = db_ok()
    else:
        payload["db_ok"] = None
    return payload

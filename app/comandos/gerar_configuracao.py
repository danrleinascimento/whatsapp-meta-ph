"""Cria o .env inicial do agente ao lado do whatsph.exe (nunca sobrescreve sem --force)."""

from __future__ import annotations

import json
import secrets
import uuid

from app.caminhos import env_file, install_dir, phsftw_root_from

DEFAULT_HUB = "https://whatsapp-meta-ph-wzewk.ondigitalocean.app"
# Mesmo valor configurado no hub DO (fabrica PH Softwares).
DEFAULT_HUB_PULL = "GQ_Lg0ELY-drZriuqQvgzSqJ7sUhdb00AOOq5n0zKEo"


def build_lines(phsftw: str) -> list[str]:
    return [
        "APP_ROLE=agent",
        "APP_ENV=production",
        "LOG_LEVEL=INFO",
        "PORT=8767",
        "BIND_HOST=127.0.0.1",
        f"INSTALLATION_ID={uuid.uuid4()}",
        f"PHSFTW_ROOT={phsftw}",
        f"TOKEN_ENCRYPTION_KEY={secrets.token_urlsafe(32)}",
        f"PH_API_KEY={secrets.token_urlsafe(32)}",
        f"PANEL_TICKET_SECRET={secrets.token_urlsafe(32)}",
        "GRAPH_API_VERSION=v25.0",
        f"HUB_BASE_URL={DEFAULT_HUB}",
        f"HUB_PULL_SECRET={DEFAULT_HUB_PULL}",
        "POLL_INTERVAL_SECONDS=10",
        "META_APP_ID=2053406131958490",
        "",
        "# Postgres local do escritorio (obrigatorio para db_ok):",
        "# DATABASE_URL=postgresql://postgres:SENHA@127.0.0.1:12345/whatsapp_ph",
        "",
        "# NUNCA colocar META_APP_SECRET nem META_ACCESS_TOKEN neste arquivo de cliente.",
        "",
    ]


def generate(force: bool = False) -> int:
    path = env_file().resolve()
    if path.exists() and not force:
        print(json.dumps({"codigo": "WHATSPH_CONFIGURACAO_EXISTENTE", "status": "SUCESSO", "arquivo": str(path)}))
        return 0
    root = phsftw_root_from(install_dir())
    phsftw = str(root) if root is not None else str(install_dir().parent)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(build_lines(phsftw)), encoding="utf-8", newline="\n")
    except OSError as exc:
        print(json.dumps({"codigo": "WHATSPH_CONFIGURACAO_FALHA", "status": "ERRO", "mensagem": str(exc)}))
        return 1
    print(json.dumps({"codigo": "WHATSPH_CONFIGURACAO_CRIADA", "status": "SUCESSO", "arquivo": str(path)}))
    return 0

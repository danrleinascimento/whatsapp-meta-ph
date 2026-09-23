# -*- coding: utf-8 -*-
"""Gera {app}/.env na primeira instalacao WHATSPH (sem secrets Meta de envio)."""
from __future__ import annotations

import argparse
import secrets
import uuid
from pathlib import Path


DEFAULT_HUB = "https://whatsapp-meta-ph-wzewk.ondigitalocean.app"
# Mesmo valor configurado no hub DO (fabrica PH Softwares).
DEFAULT_HUB_PULL = "GQ_Lg0ELY-drZriuqQvgzSqJ7sUhdb00AOOq5n0zKEo"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--app-dir", default=".", help="Pasta WHATSPH")
    p.add_argument("--database-url", default="", help="Opcional; senao deixa comentado")
    p.add_argument("--phsftw-root", default="", help="Ex: C:\\PHSFTW")
    p.add_argument("--force", action="store_true", help="Sobrescreve .env existente")
    args = p.parse_args()

    app = Path(args.app_dir).resolve()
    app.mkdir(parents=True, exist_ok=True)
    env_path = app / ".env"
    if env_path.exists() and not args.force:
        print("OK .env ja existe — nao sobrescrito:", env_path)
        return 0

    phsftw = args.phsftw_root.strip() or str(app.parent)
    db = args.database_url.strip()
    lines = [
        "APP_ROLE=agent",
        "APP_ENV=production",
        "LOG_LEVEL=INFO",
        "PORT=8765",
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
    ]
    if db:
        lines.append(f"DATABASE_URL={db}")
    else:
        lines.append(
            "# DATABASE_URL=postgresql://postgres:SENHA@127.0.0.1:12345/whatsapp_ph"
        )
    lines.extend(
        [
            "",
            "# NUNCA colocar META_APP_SECRET nem META_ACCESS_TOKEN neste arquivo de cliente.",
            "",
        ]
    )
    env_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("OK .env criado:", env_path)
    print("Ajuste DATABASE_URL e reinicie o servico PHWhatsMeta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

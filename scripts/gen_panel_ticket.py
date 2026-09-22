"""Gera ticket de painel (simula GEPH) e imprime URL."""

from __future__ import annotations

import os
import sys
from urllib.parse import quote

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.auth import create_panel_ticket
from app.config import get_settings


def main() -> int:
    usuario = sys.argv[1] if len(sys.argv) > 1 else "ADMIN"
    ticket = create_panel_ticket(usuario)
    port = get_settings().port
    print(ticket)
    print(f"http://127.0.0.1:{port}/?ticket={quote(ticket, safe='')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Caminhos do WHATSPH em desenvolvimento e no whatsph.exe (PyInstaller).

- Instalacao: pasta do whatsph.exe (.env, logs). Em desenvolvimento, a pasta atual.
- Recursos: sql/ e web/dist/ embutidos no exe (sys._MEIPASS). Em desenvolvimento, a raiz do repo.
"""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def install_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def resource_dir() -> Path:
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        return Path(bundle)
    return Path(__file__).resolve().parents[1]


def env_file() -> Path:
    if is_frozen():
        return install_dir() / ".env"
    return Path(".env")


def logs_dir() -> Path:
    return install_dir() / "logs"


def phsftw_root_from(start: Path) -> Path | None:
    for path in (start, *start.parents):
        if path.name.upper() == "PHSFTW":
            return path
    return None

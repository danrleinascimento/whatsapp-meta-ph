"""Validacao de path de PDF sob PHSFTW_ROOT (anti path-traversal)."""

from __future__ import annotations

from pathlib import Path

from app.config import get_settings


def resolve_allowed_pdf(
    file_path: str,
    extra_roots: list[str] | None = None,
) -> Path:
    settings = get_settings()
    roots: list[Path] = []
    if settings.phsftw_root:
        roots.append(Path(settings.phsftw_root).resolve())
    for r in extra_roots or []:
        if r:
            roots.append(Path(r).resolve())

    if not roots:
        raise ValueError("PHSFTW_ROOT nao configurado")

    candidate = Path(file_path).resolve()
    if candidate.suffix.lower() != ".pdf":
        raise ValueError("Apenas arquivos .pdf sao permitidos")
    if not candidate.is_file():
        raise ValueError("Arquivo PDF nao encontrado")

    for root in roots:
        try:
            candidate.relative_to(root)
            return candidate
        except ValueError:
            continue

    raise ValueError("Path do PDF fora das pastas permitidas (PHSFTW)")

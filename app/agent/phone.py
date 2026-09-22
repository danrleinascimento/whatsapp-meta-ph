"""Normalizacao de telefone BR para Cloud API (somente digitos)."""

from __future__ import annotations

import re


def normalize_wa_id(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        raise ValueError("Telefone vazio")
    if digits.startswith("55") and len(digits) >= 12:
        return digits
    if len(digits) in (10, 11):
        return "55" + digits
    return digits

"""Mensagens amigaveis para codigos de erro Meta WhatsApp Cloud API."""

from __future__ import annotations

from typing import Optional


def friendly_meta_error(error_code: Optional[str], message: str) -> str:
    """Enriquece mensagens com contexto da doc Meta / erros conhecidos."""
    code = str(error_code or "")
    if code == "132001":
        return (
            f"{message} — Use exatamente name+language de GET /{{WABA}}/message_templates "
            f"(status APPROVED). O nome do curl do painel Meta pode diferir do nome real."
        )
    if code == "131058":
        return (
            f"{message} — hello_world so pode ser enviado pelo Public Test Number da Meta; "
            f"em numero comercial use outro template APPROVED da WABA."
        )
    if code == "131047":
        return (
            f"{message} — Re-engagement: fora da janela 24h e obrigatorio template aprovado."
        )
    if code == "131026":
        return f"{message} — Destinatario invalido ou sem WhatsApp."
    return message

"""Schemas Pydantic das APIs do agente."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class SendTemplateRequest(BaseModel):
    to: str
    template_name: str
    # Opcional: se omitido, usa o language APPROVED retornado pela Meta para o nome
    language_code: Optional[str] = None
    components: Optional[list[dict[str, Any]]] = None
    sistema_origem: Optional[str] = "GEPH"
    usuario_geph: Optional[str] = None


class SendTextRequest(BaseModel):
    to: str
    body: str = Field(..., min_length=1, max_length=4096)
    sistema_origem: Optional[str] = "GEPH"
    usuario_geph: Optional[str] = None


class SendDocumentRequest(BaseModel):
    to: str
    file_path: str
    caption: Optional[str] = None
    diretorio_principal: Optional[str] = None
    diretorio_secundario: Optional[str] = None
    sistema_origem: Optional[str] = "GEPH"
    usuario_geph: Optional[str] = None


class BatchItem(BaseModel):
    type: str
    to: str
    body: Optional[str] = None
    template_name: Optional[str] = None
    language_code: Optional[str] = None
    components: Optional[list[dict[str, Any]]] = None
    file_path: Optional[str] = None
    caption: Optional[str] = None
    diretorio_principal: Optional[str] = None
    diretorio_secundario: Optional[str] = None
    sistema_origem: Optional[str] = "GEPH"
    usuario_geph: Optional[str] = None


class SendBatchRequest(BaseModel):
    items: list[BatchItem] = Field(..., min_length=1, max_length=500)


class TicketRequest(BaseModel):
    usuario_geph: str = Field(..., min_length=1, max_length=64)

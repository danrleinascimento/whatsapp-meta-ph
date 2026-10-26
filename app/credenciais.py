"""Senha padrao do PostgreSQL local PH (servico postgresPH), mesmo formato do HUPH.

DATABASE_URL do agente vai sem senha no .env; a conexao completa com esta credencial.
"""

from __future__ import annotations

import base64
import json
import zlib

_CREDENCIAIS = 'c$}+NN=nR2&R4QhQ1YrsHw+JqEHcO`DfjhD^j4|`0E`+5c>'


class CredencialError(RuntimeError):
    pass


def obter_senha_banco() -> str:
    try:
        senha = json.loads(zlib.decompress(base64.b85decode(_CREDENCIAIS)))["banco"]
    except (ValueError, KeyError, zlib.error):
        raise CredencialError("Credencial PH do banco invalida nesta entrega") from None
    if not isinstance(senha, str) or not senha:
        raise CredencialError("Credencial PH do banco ausente nesta entrega")
    return senha

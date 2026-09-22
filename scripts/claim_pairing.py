"""Claim de pairing no agente apos Embedded Signup no hub."""

from __future__ import annotations

import os
import sys

import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import get_settings
from app.crypto import encrypt_token
from app.db import repos


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python scripts/claim_pairing.py <pair_code>")
        return 1
    pair_code = sys.argv[1]
    s = get_settings()
    if not s.hub_base_url or not s.hub_pull_secret:
        print("ERRO: HUB_BASE_URL / HUB_PULL_SECRET ausentes")
        return 1

    url = s.hub_base_url.rstrip("/") + "/v1/hub/pairing/claim"
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            url,
            params={"pair_code": pair_code, "installation_id": s.installation_id},
            headers={"X-PH-Hub-Secret": s.hub_pull_secret},
        )
    if resp.status_code >= 400:
        print("FALHA", resp.status_code, resp.text)
        return 1
    data = resp.json()
    token = data.get("access_token")
    if not token:
        print("Sem access_token")
        return 1
    repos.upsert_config(
        s.installation_id,
        status="CONNECTED",
        waba_id=data.get("waba_id"),
        phone_number_id=data.get("phone_number_id"),
        display_phone=data.get("display_phone"),
        graph_api_version=data.get("graph_api_version") or s.graph_api_version,
        access_token_enc=encrypt_token(token),
        last_error=None,
    )
    print("OK — token claim e gravado cifrado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

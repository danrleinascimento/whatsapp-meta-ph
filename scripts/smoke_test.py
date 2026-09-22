"""Smoke test local do agente (health + status + path guard).

Nao envia mensagem real a menos que --send-template seja passado.
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import get_settings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8765")
    parser.add_argument("--send-template", action="store_true")
    parser.add_argument("--to", default="")
    parser.add_argument("--template", default="hello_world")
    parser.add_argument("--lang", default="en_US")
    args = parser.parse_args()

    s = get_settings()
    if not s.ph_api_key:
        print("ERRO: PH_API_KEY ausente")
        return 1
    headers = {"X-PH-Api-Key": s.ph_api_key}

    with httpx.Client(timeout=60.0) as client:
        r = client.get(f"{args.base}/health")
        print("GET /health", r.status_code, r.json())
        if r.status_code != 200 or not r.json().get("db_ok"):
            print("FALHA health/db")
            return 1

        r = client.get(f"{args.base}/v1/whatsapp/status", headers=headers)
        print("GET /v1/whatsapp/status", r.status_code, r.json())

        # Path fora da allowlist deve dar 400
        r = client.post(
            f"{args.base}/v1/whatsapp/send-document",
            headers=headers,
            json={
                "to": "5549999999999",
                "file_path": r"C:\Windows\notepad.exe",
                "usuario_geph": "SMOKE",
            },
        )
        print("POST send-document path ilegal", r.status_code, r.text[:200])
        if r.status_code != 400:
            print("AVISO: esperava 400 para path ilegal")

        if args.send_template:
            if not args.to:
                print("ERRO: --to obrigatorio com --send-template")
                return 1
            r = client.post(
                f"{args.base}/v1/whatsapp/send-template",
                headers=headers,
                json={
                    "to": args.to,
                    "template_name": args.template,
                    "language_code": args.lang,
                    "usuario_geph": "SMOKE",
                    "sistema_origem": "SMOKE",
                },
            )
            print("POST send-template", r.status_code, r.text[:500])

    print("OK smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Smoke test local do agente (health + status + path guard + template).

Usa a API oficial de templates da WABA para evitar erro Meta 132001.
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import get_settings
from app.crypto import decrypt_token
from app.db import repos
from app.graph import pick_smoke_template, resolve_template


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8765")
    parser.add_argument("--send-template", action="store_true")
    parser.add_argument("--to", default="")
    parser.add_argument(
        "--template",
        default="",
        help="Nome do template. Vazio = escolhe APPROVED automatico (exceto hello_world).",
    )
    parser.add_argument(
        "--lang",
        default="",
        help="Idioma exato (ex. en_US). Vazio = idioma APPROVED da Meta para o nome.",
    )
    args = parser.parse_args()

    s = get_settings()
    if not s.ph_api_key:
        print("ERRO: PH_API_KEY ausente")
        return 1
    headers = {"X-PH-Api-Key": s.ph_api_key}
    exit_code = 0

    with httpx.Client(timeout=90.0) as client:
        r = client.get(f"{args.base}/health")
        print("GET /health", r.status_code, r.json())
        if r.status_code != 200 or not r.json().get("db_ok"):
            print("FALHA health/db")
            return 1

        r = client.get(f"{args.base}/v1/whatsapp/status", headers=headers)
        print("GET /v1/whatsapp/status", r.status_code, r.json())

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
            exit_code = 1

        if args.send_template:
            if not args.to:
                print("ERRO: --to obrigatorio com --send-template")
                return 1

            cfg = repos.get_config(s.installation_id)
            if not cfg or not cfg.get("access_token_enc") or not cfg.get("waba_id"):
                print("ERRO: config/token ausente — rode seed_dev_config.py")
                return 1
            token = decrypt_token(cfg["access_token_enc"])
            waba = str(cfg["waba_id"])

            # Lista via HTTP do agente
            r = client.get(f"{args.base}/v1/whatsapp/templates", headers=headers)
            print("GET /v1/whatsapp/templates", r.status_code, r.text[:500])

            tpl_name = args.template.strip()
            tpl_lang = args.lang.strip() or None
            if not tpl_name:
                auto = pick_smoke_template(waba_id=waba, access_token=token)
                tpl_name = auto["name"]
                tpl_lang = auto["language"]
                print(f"AUTO template={tpl_name} lang={tpl_lang}")
            else:
                resolved = resolve_template(
                    waba_id=waba,
                    access_token=token,
                    template_name=tpl_name,
                    language_code=tpl_lang,
                )
                print(
                    f"RESOLVED template={resolved['name']} lang={resolved['language']}"
                    + (
                        f" (de {resolved['resolved_from']})"
                        if resolved.get("resolved_from")
                        else ""
                    )
                )
                tpl_name = resolved["name"]
                tpl_lang = resolved["language"]

            body = {
                "to": args.to,
                "template_name": tpl_name,
                "usuario_geph": "SMOKE",
                "sistema_origem": "SMOKE",
            }
            if tpl_lang:
                body["language_code"] = tpl_lang
            r = client.post(
                f"{args.base}/v1/whatsapp/send-template",
                headers=headers,
                json=body,
            )
            print("POST send-template", r.status_code, r.text[:800])
            data = r.json() if r.content else {}
            if r.status_code != 200 or not data.get("ok"):
                exit_code = 1

    print("OK smoke" if exit_code == 0 else "FALHA smoke")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

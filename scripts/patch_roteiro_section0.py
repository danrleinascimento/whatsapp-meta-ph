# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(r"C:\projetos\python\whatsmeta\ROTEIRO_PROXIMOS_PASSOS_WHATSPH.md")
t = p.read_text(encoding="utf-8")
start = t.index("## 0. Estado comprovado")
end = t.index("## Ordem obrigatória")
new = r"""## 0. Estado comprovado (22/09/2026 — revisao pos-prints Meta/DO)

| Item | Status |
|------|--------|
| Push GitHub (agente + hub + templates resolve) | **Feito** — ate `a2957f9` (+ painel React nesta sessao, push pendente) |
| Agente local `APP_ROLE=agent` `:8765` | **OK** |
| Seed token System User + `CONNECTED` | **OK** |
| Template APPROVED (`3p_direct_integration_test_template` / alias `lp_`) | **OK** |
| PDF `Orcamento-5822371.pdf` → WhatsApp | **OK** (`ACCEPTED`) |
| Painel ticket HMAC | **OK** |
| Painel **React + Vite + Tailwind** (`web/`) | **Feito** — `web/dist` servido pelo FastAPI |
| Meta App `PH_Softwares` / `META_APP_ID` | **Confirmado** `2053406131958490` |
| `META_EMBEDDED_SIGNUP_CONFIG_ID` | **Ainda nao criado** (N4) |
| DO `DATABASE_URL` | **OK** `${dev-db-085123.DATABASE_URL}` |
| DO `META_APP_SECRET` / `META_WEBHOOK_VERIFY_TOKEN` | **Encrypted OK** |
| DO `HUB_PULL_SECRET` | **VAZIO no DO** — colar o valor do `.env` local |
| DO `META_APP_ID` | **Adicionar** `2053406131958490` |
| SQL no Postgres DO (`001`/`002`) | **Pendente** (causa tipica de `db_ok:false`) |
| Codigo hub poller / events | **No repo** — validar apos secret + SQL |
| Embedded Signup live | **Scaffold so** |
| Instalador Windows | **Codigo Inno/NSSM** — `.exe` pendente |
| PHVCL / GEPH | **Em andamento** — falta Rebuild `PH.bpl` no BCB5 |

---

## Decisao N3 — Painel web moderno

**Pedido:** FastAPI + React Vite, moderno e bonito. **Feito.**

| Opcao | Status |
|-------|--------|
| Django + React | **Descartado** |
| **FastAPI + React Vite + Tailwind** | **Implementado** em `web/` |
| HTML legado | Fallback se `web/dist` ausente |

```powershell
cd C:\projetos\python\whatsmeta\web
npm install
npm run build
cd ..
uvicorn app.main:app --host 127.0.0.1 --port 8765
python scripts\gen_panel_ticket.py ADMIN
```

---

## Onde encontrar `META_APP_ID` e `config_id` (N4)

1. Meta Developers → App **PH_Softwares** → Configuracoes → Basico.
2. **ID do Aplicativo** = `META_APP_ID` = **`2053406131958490`** (confirmado print 22/09/2026).
3. `META_EMBEDDED_SIGNUP_CONFIG_ID`: criar Embedded Signup (ainda nao existe) e copiar Configuration ID.
4. OAuth Redirect: `https://whatsapp-meta-ph-wzewk.ondigitalocean.app`
5. DO: `META_APP_ID=2053406131958490` + config_id (N4) + App Secret Encrypted.
6. Codigo: `app/hub/routes.py` + `app/config.py`.

**Seguranca:** App Secret em print/chat → preferir Reset no Meta e atualizar so o DO. Nunca no Git/agente/C++.

---

## Onde encontrar `DATABASE_URL` e `HUB_PULL_SECRET` (N1 / DO)

### DigitalOcean (evidencia print 22/09/2026)

1. Apps → `whatsapp-meta-ph` → Settings → Environment Variables.
2. `DATABASE_URL` = `${dev-db-085123.DATABASE_URL}` (**ja correto**).
3. `HUB_PULL_SECRET` estava **vazio** → colar o valor do `.env` local do agente.
4. Checklist: `docs/CHECKLIST_HUB_DIGITALOCEAN.md`.
5. Aplicar SQL `001`+`002` no Postgres `dev-db-085123` → Redeploy → `/health` com `db_ok:true`.

### Agente local

```env
HUB_BASE_URL=https://whatsapp-meta-ph-wzewk.ondigitalocean.app
HUB_PULL_SECRET=<igual ao DO>
META_APP_ID=2053406131958490
DATABASE_URL=postgresql://...@127.0.0.1:12345/whatsapp_ph
```

---

"""
p.write_text(t[:start] + new + t[end:], encoding="utf-8")
print("OK")

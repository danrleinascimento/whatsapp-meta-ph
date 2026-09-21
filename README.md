# WhatsApp Meta Hub (PH Softwares)

Servico **central** (DigitalOcean App Platform) para:

- Webhook HTTPS da Meta WhatsApp Cloud API
- (proximas fases) Embedded Signup / pairing com o agente local

Codigo local: `C:\projetos\python\whatsmeta`  
Repo GitHub: https://github.com/danrleinascimento/whatsapp-meta-ph  
App DO alvo: `whatsapp-meta-ph` (novo — **nao** reutilizar `rtc-hub-ph`)

## Endpoints v0.1

| Metodo | Path | Funcao |
|--------|------|--------|
| GET | `/health` | Health check DO / monitoramento |
| GET | `/webhook/whatsapp` | Verificacao Meta (`hub.challenge`) |
| POST | `/webhook/whatsapp` | Eventos Meta (assinatura HMAC) |

Documentacao oficial Meta:

- https://developers.facebook.com/docs/graph-api/webhooks/getting-started
- https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks/

## Rodar local

```bash
cd C:\projetos\python\whatsmeta
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edite META_WEBHOOK_VERIFY_TOKEN no .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Teste challenge:

```bash
curl "http://127.0.0.1:8000/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=SEU_TOKEN&hub.challenge=12345"
```

Deve devolver corpo `12345` (texto puro).

## Segredos

Nunca committe `.env`. No DigitalOcean use Environment Variables criptografadas:

- `META_WEBHOOK_VERIFY_TOKEN`
- `META_APP_SECRET` (quando o App Meta existir)
- `APP_ENV=production`
- `LOG_LEVEL=INFO`

## Relacao com rtc-hub-ph

O app `rtc-hub-ph` / repo `MarcianoMendes/servico-rtc` e outro produto (RTC).  
WhatsApp Meta usa app e repo **separados**.

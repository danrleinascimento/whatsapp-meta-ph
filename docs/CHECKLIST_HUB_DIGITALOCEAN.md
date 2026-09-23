# Checklist operacional — Hub DigitalOcean (N1)
# Revisao: 22/09/2026 17:57
#
# Estado vivo /health hub:
#   version=0.2.3 db_ok=true schema_ok=false events_backend=memory
# Binding correto:
#   DATABASE_URL=${whatsapp-meta-db.DATABASE_URL}
# HUB_PULL_SECRET: alinhado (poller 200 OK)

## Feito
- [x] DATABASE_URL binding whatsapp-meta-db
- [x] HUB_PULL_SECRET no DO = mesmo do .env agente
- [x] Deploy ed859f2 / v0.2.3 (migrate + memory fallback)
- [x] Poller local 200 em /v1/hub/events

## Aberto
- [ ] schema_ok=true (Neon ou doadmin GRANT CREATE)
- [ ] Confirmar META_APP_ID + GRAPH_API_VERSION no Web Service env
- [ ] N2: mensagem nova ACCEPTED → DELIVERED no painel

## Producao Windows / GEPH
Ver ROTEIRO_PROXIMOS_PASSOS_WHATSPH.md secoes N5 e N6.

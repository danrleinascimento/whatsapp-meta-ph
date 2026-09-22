-- Hub / agente — pairing blobs (TTL curto) — PostgreSQL 9.5+
-- Aplicar no Postgres do DigitalOcean (DATABASE_URL do hub) e opcionalmente no local.

CREATE TABLE IF NOT EXISTS whatsapp_pairing_blob (
    pair_code        VARCHAR(64)  PRIMARY KEY,
    installation_id  VARCHAR(64)  NOT NULL,
    waba_id          VARCHAR(64),
    phone_number_id  VARCHAR(64),
    display_phone    VARCHAR(32),
    graph_api_version VARCHAR(16) NOT NULL DEFAULT 'v25.0',
    access_token     TEXT         NOT NULL,
    claimed          BOOLEAN      NOT NULL DEFAULT FALSE,
    expires_at       TIMESTAMP    NOT NULL,
    created_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_whatsapp_pairing_installation
    ON whatsapp_pairing_blob (installation_id);

CREATE INDEX IF NOT EXISTS ix_whatsapp_pairing_expires
    ON whatsapp_pairing_blob (expires_at);

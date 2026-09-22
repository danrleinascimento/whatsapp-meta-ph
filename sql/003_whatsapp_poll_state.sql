-- Poller cursor (agente local) — PostgreSQL 9.5+

CREATE TABLE IF NOT EXISTS whatsapp_poll_state (
    installation_id  VARCHAR(64)  PRIMARY KEY,
    since_id         BIGINT       NOT NULL DEFAULT 0,
    updated_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

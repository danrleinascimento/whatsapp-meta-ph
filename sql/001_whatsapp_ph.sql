-- whatsapp_ph — schema v1 (PostgreSQL 9.5+)
-- Database: whatsapp_ph
-- Sem FK para biph / outros projetos PH

CREATE TABLE IF NOT EXISTS whatsapp_local_auth (
    id              SERIAL PRIMARY KEY,
    installation_id VARCHAR(64)  NOT NULL,
    api_key_hash    VARCHAR(128) NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_whatsapp_local_auth_installation UNIQUE (installation_id)
);

CREATE TABLE IF NOT EXISTS whatsapp_config (
    id                 SERIAL PRIMARY KEY,
    installation_id    VARCHAR(64)  NOT NULL,
    status             VARCHAR(32)  NOT NULL DEFAULT 'DISCONNECTED',
    waba_id            VARCHAR(64),
    phone_number_id    VARCHAR(64),
    display_phone      VARCHAR(32),
    graph_api_version  VARCHAR(16)  NOT NULL DEFAULT 'v25.0',
    access_token_enc   TEXT,
    token_expires_at   TIMESTAMP,
    meta_business_id   VARCHAR(64),
    last_error         TEXT,
    connected_at       TIMESTAMP,
    created_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_whatsapp_config_installation UNIQUE (installation_id),
    CONSTRAINT ck_whatsapp_config_status CHECK (
        status IN ('DISCONNECTED', 'CONNECTED', 'ERROR')
    )
);

CREATE TABLE IF NOT EXISTS whatsapp_message (
    id                BIGSERIAL PRIMARY KEY,
    installation_id   VARCHAR(64)  NOT NULL,
    direction         VARCHAR(8)   NOT NULL DEFAULT 'OUT',
    msg_type          VARCHAR(32)  NOT NULL,
    to_wa_id          VARCHAR(32),
    template_name     VARCHAR(128),
    caption           TEXT,
    local_file_path   TEXT,
    media_id          VARCHAR(64),
    meta_message_id   VARCHAR(128),
    status            VARCHAR(32)  NOT NULL DEFAULT 'PENDING',
    http_status       INTEGER,
    error_code        VARCHAR(32),
    error_message     TEXT,
    sistema_origem    VARCHAR(32),
    usuario_geph      VARCHAR(64),
    empresa_id_ref    INTEGER,
    hostname          VARCHAR(128),
    created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_whatsapp_message_direction CHECK (direction IN ('IN', 'OUT'))
);

CREATE INDEX IF NOT EXISTS ix_whatsapp_message_meta_id
    ON whatsapp_message (meta_message_id);
CREATE INDEX IF NOT EXISTS ix_whatsapp_message_created
    ON whatsapp_message (created_at);
CREATE INDEX IF NOT EXISTS ix_whatsapp_message_to
    ON whatsapp_message (to_wa_id);
CREATE INDEX IF NOT EXISTS ix_whatsapp_message_installation
    ON whatsapp_message (installation_id);

CREATE TABLE IF NOT EXISTS whatsapp_webhook_event (
    id              BIGSERIAL PRIMARY KEY,
    waba_id         VARCHAR(64),
    field_name      VARCHAR(64),
    payload_json    TEXT         NOT NULL,
    received_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at    TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_whatsapp_webhook_event_waba
    ON whatsapp_webhook_event (waba_id);

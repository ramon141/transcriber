-- Cache de transcrições.
-- Cada arquivo é identificado pelo SHA-256 do seu conteúdo binário.

CREATE TABLE IF NOT EXISTS transcricoes (
    id                     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    hash_arquivo           TEXT        NOT NULL UNIQUE,
    nome_arquivo           TEXT        NOT NULL,
    transcricao_completa   TEXT,
    segmentos_com_falantes JSONB       NOT NULL DEFAULT '[]'::JSONB,
    resumo_falantes        JSONB       NOT NULL DEFAULT '{}'::JSONB,
    diarizacao_ativada     BOOLEAN     NOT NULL DEFAULT FALSE,
    modelo_whisper         TEXT,
    duracao_total          FLOAT,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transcricoes_hash ON transcricoes(hash_arquivo);

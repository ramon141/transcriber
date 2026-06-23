-- Configuração da aplicação (chave/valor).
-- Guarda segredos de integração (HF_TOKEN, NOTION_TOKEN, NOTION_PARENT_ID).
-- As credenciais de conexão (SUPABASE_URL/KEY, DATABASE_URL) NÃO ficam aqui:
-- elas são o bootstrap e moram em arquivo local, pois abrem este próprio banco.

CREATE TABLE IF NOT EXISTS app_config (
    chave         TEXT        PRIMARY KEY,
    valor         TEXT        NOT NULL,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

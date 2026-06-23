#!/usr/bin/env python3
"""
Integração com Supabase para cache de transcrições.

Fluxo:
- Upload do arquivo → gera SHA-256 do conteúdo
- Antes de processar → busca hash no Supabase (cache hit = pula processamento)
- Após processar → salva resultado com hash (upsert)

Tabela esperada no Supabase (crie via SQL Editor):

    CREATE TABLE transcricoes (
        id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
        hash_arquivo     TEXT        NOT NULL UNIQUE,
        nome_arquivo     TEXT        NOT NULL,
        transcricao_completa         TEXT,
        segmentos_com_falantes       JSONB DEFAULT '[]'::JSONB,
        resumo_falantes              JSONB DEFAULT '{}'::JSONB,
        diarizacao_ativada           BOOLEAN DEFAULT FALSE,
        modelo_whisper   TEXT,
        duracao_total    FLOAT,
        created_at       TIMESTAMPTZ DEFAULT NOW()
    );

Variáveis de ambiente necessárias no .env:
    SUPABASE_URL=https://...supabase.co
    SUPABASE_KEY=sb_publishable_...
"""

import hashlib
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

TABELA = "transcricoes"


def obter_url() -> Optional[str]:
    return os.getenv("SUPABASE_URL")


def obter_chave() -> Optional[str]:
    return os.getenv("SUPABASE_KEY")


def verificar_supabase_configurado() -> bool:
    return bool(obter_url()) and bool(obter_chave())


def _get_client():
    try:
        from supabase import create_client
    except ImportError:
        raise ImportError("supabase não instalado. Execute: pip install supabase")

    url = obter_url()
    key = obter_chave()
    if not url or not key:
        raise ValueError(
            "SUPABASE_URL e SUPABASE_KEY não configurados. "
            "Adicione-os ao arquivo .env na raiz do projeto."
        )
    return create_client(url, key)


def computar_hash(arquivo_bytes: bytes) -> str:
    return hashlib.sha256(arquivo_bytes).hexdigest()


def buscar_por_hash(hash_arquivo: str) -> Optional[dict]:
    client = _get_client()
    resp = (
        client.table(TABELA)
        .select("*")
        .eq("hash_arquivo", hash_arquivo)
        .limit(1)
        .execute()
    )
    data: list[dict] = resp.data
    return data[0] if data else None


def listar_transcricoes(limite: int = 100) -> list[dict]:
    client = _get_client()
    resp = (
        client.table(TABELA)
        .select("id,hash_arquivo,nome_arquivo,modelo_whisper,duracao_total,diarizacao_ativada,created_at,transcricao_completa,segmentos_com_falantes,resumo_falantes")
        .order("created_at", desc=True)
        .limit(limite)
        .execute()
    )
    return resp.data or []


def buscar_transcricoes(
    termo: str = "",
    modelo: str = "",
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
) -> list[dict]:
    client = _get_client()
    query = client.table(TABELA).select(
        "id,hash_arquivo,nome_arquivo,modelo_whisper,duracao_total,diarizacao_ativada,created_at,transcricao_completa,segmentos_com_falantes,resumo_falantes"
    )

    if termo:
        query = query.ilike("nome_arquivo", f"%{termo}%")
    if modelo:
        query = query.eq("modelo_whisper", modelo)
    if data_inicio:
        query = query.gte("created_at", f"{data_inicio}T00:00:00")
    if data_fim:
        query = query.lte("created_at", f"{data_fim}T23:59:59")

    resp = query.order("created_at", desc=True).limit(200).execute()
    return resp.data or []


def salvar_transcricao(
    hash_arquivo: str,
    nome_arquivo: str,
    transcricao_completa: str,
    segmentos_com_falantes: list[dict],
    resumo_falantes: dict,
    diarizacao_ativada: bool,
    modelo_whisper: str,
    duracao_total: float,
) -> dict:
    client = _get_client()
    payload: dict = {
        "hash_arquivo": hash_arquivo,
        "nome_arquivo": nome_arquivo,
        "transcricao_completa": transcricao_completa,
        "segmentos_com_falantes": segmentos_com_falantes,
        "resumo_falantes": resumo_falantes,
        "diarizacao_ativada": diarizacao_ativada,
        "modelo_whisper": modelo_whisper,
        "duracao_total": duracao_total,
    }
    resp = (
        client.table(TABELA)
        .upsert(payload, on_conflict="hash_arquivo")
        .execute()
    )
    data: list[dict] = resp.data
    return data[0] if data else {}

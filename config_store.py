#!/usr/bin/env python3
"""
Resolver central de configuração do Transcriber.

Duas camadas, com fallback para variáveis de ambiente (.env):

1. Conexão (bootstrap)  → arquivo local JSON
   SUPABASE_URL, SUPABASE_KEY, DATABASE_URL.
   Moram em arquivo porque abrem o próprio banco; não podem ficar nele.

2. Integrações          → tabela `app_config` no banco
   HF_TOKEN, NOTION_TOKEN, NOTION_PARENT_ID.

Ordem de leitura:
   conexão     → arquivo local → os.getenv
   integração  → tabela app_config → os.getenv
"""

import json
import os
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

ARQUIVO_CONFIG = Path.home() / ".split_audio" / "config.json"
TABELA_CONFIG = "app_config"


class ChaveConexao(str, Enum):
    SUPABASE_URL = "SUPABASE_URL"
    SUPABASE_KEY = "SUPABASE_KEY"
    DATABASE_URL = "DATABASE_URL"


class ChaveIntegracao(str, Enum):
    HF_TOKEN = "HF_TOKEN"
    NOTION_TOKEN = "NOTION_TOKEN"
    NOTION_PARENT_ID = "NOTION_PARENT_ID"


# Cache em processo das integrações lidas do banco; None = ainda não carregado.
_cache_integracoes: Optional[Dict[str, str]] = None


# ── Camada de conexão (arquivo local) ─────────────────────────────────────────
def _ler_arquivo() -> Dict[str, str]:
    if not ARQUIVO_CONFIG.exists():
        return {}

    try:
        bruto = json.loads(ARQUIVO_CONFIG.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(bruto, dict):
        return {}

    return {str(k): str(v) for k, v in bruto.items()}


def obter_conexao(chave: ChaveConexao) -> Optional[str]:
    valor = _ler_arquivo().get(chave.value)
    if valor:
        return valor

    return os.getenv(chave.value)


def conexao_configurada() -> bool:
    return all(obter_conexao(chave) for chave in ChaveConexao)


def salvar_conexao(supabase_url: str, supabase_key: str, database_url: str) -> None:
    ARQUIVO_CONFIG.parent.mkdir(parents=True, exist_ok=True)

    dados: Dict[str, str] = {
        ChaveConexao.SUPABASE_URL.value: supabase_url,
        ChaveConexao.SUPABASE_KEY.value: supabase_key,
        ChaveConexao.DATABASE_URL.value: database_url,
    }
    ARQUIVO_CONFIG.write_text(json.dumps(dados, indent=2), encoding="utf-8")


# ── Camada de integrações (banco) ─────────────────────────────────────────────
def _carregar_integracoes_db() -> Dict[str, str]:
    global _cache_integracoes
    if _cache_integracoes is not None:
        return _cache_integracoes

    try:
        from supabase_integration import _get_client

        client = _get_client()
        resp = client.table(TABELA_CONFIG).select("chave,valor").execute()
        linhas = resp.data or []

        resultado: Dict[str, str] = {}
        for linha in linhas:
            if not isinstance(linha, dict):
                continue
            chave = linha.get("chave")
            valor = linha.get("valor")
            if isinstance(chave, str) and isinstance(valor, str):
                resultado[chave] = valor

        _cache_integracoes = resultado
    except Exception:
        _cache_integracoes = {}

    return _cache_integracoes


def invalidar_cache() -> None:
    global _cache_integracoes
    _cache_integracoes = None


def obter_integracao(chave: ChaveIntegracao) -> Optional[str]:
    valor = _carregar_integracoes_db().get(chave.value)
    if valor:
        return valor

    return os.getenv(chave.value)


def salvar_integracoes(valores: Dict[ChaveIntegracao, str]) -> None:
    from supabase_integration import _get_client

    client = _get_client()
    payload = [
        {"chave": chave.value, "valor": valor}
        for chave, valor in valores.items()
        if valor
    ]
    if payload:
        client.table(TABELA_CONFIG).upsert(payload, on_conflict="chave").execute()

    invalidar_cache()


# ── Teste de credenciais de conexão ───────────────────────────────────────────
def _testar_database(database_url: str) -> Optional[str]:
    try:
        import psycopg2
    except ImportError:
        return "psycopg2-binary não instalado no backend."

    try:
        conn = psycopg2.connect(database_url)
        conn.close()
        return None
    except Exception as err:
        return f"DATABASE_URL inválida: {err}"


def _testar_supabase(supabase_url: str, supabase_key: str) -> Optional[str]:
    try:
        from supabase import create_client
    except ImportError:
        return "pacote supabase não instalado no backend."

    try:
        client = create_client(supabase_url, supabase_key)
        client.table(TABELA_CONFIG).select("chave").limit(1).execute()
        return None
    except Exception:
        return "Credenciais Supabase incorretas (SUPABASE_URL / SUPABASE_KEY)."


def testar_conexao(
    supabase_url: str, supabase_key: str, database_url: str
) -> Tuple[bool, str]:
    """
    Valida as credenciais e, se o banco conectar, aplica as migrations
    (criando as tabelas necessárias) antes de testar a chave Supabase.

    Retorna (sucesso, mensagem). Não persiste nada — só testa.
    """
    erro_db = _testar_database(database_url)
    if erro_db:
        return False, erro_db

    try:
        from migrate import rodar_migrations

        rodar_migrations(database_url)
    except Exception as err:
        return False, f"Falha ao aplicar migrations: {err}"

    erro_sb = _testar_supabase(supabase_url, supabase_key)
    if erro_sb:
        return False, erro_sb

    return True, "Conexão validada com sucesso."

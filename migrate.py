#!/usr/bin/env python3
"""
Runner de migrations para o banco Supabase/Postgres.

Uso:
    python migrate.py

Requer DATABASE_URL no .env.
Encontre em: Supabase Dashboard → Settings → Database
             → Connection string → Transaction pooler → URI

Formato:
    DATABASE_URL=postgresql://postgres.[ref]:[senha]@aws-0-[região].pooler.supabase.com:6543/postgres

Migrations aplicadas são registradas na tabela `schema_migrations`.
Cada arquivo .sql em migrations/ é aplicado UMA vez, em ordem alfabética.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

_CREATE_CONTROL_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     TEXT        PRIMARY KEY,
    aplicada_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def _obter_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        print("❌  DATABASE_URL não encontrada no .env\n")
        print("Adicione ao .env:")
        print(
            "  DATABASE_URL=postgresql://postgres.[ref]:[senha]"
            "@aws-0-[região].pooler.supabase.com:6543/postgres\n"
        )
        print("Encontre em:")
        print("  Supabase Dashboard → Settings → Database")
        print("  → Connection string → Transaction pooler → URI")
        sys.exit(1)
    return url


def _listar_arquivos() -> list[Path]:
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def _aplicadas(cursor) -> set[str]:
    cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
    return {row[0] for row in cursor.fetchall()}


def rodar_migrations(url: str) -> int:
    """
    Aplica migrations pendentes no banco indicado por `url`.

    Retorna a quantidade aplicada. Levanta exceção em caso de falha
    (não chama sys.exit), para poder ser usada de dentro da API.
    """
    import psycopg2

    arquivos = _listar_arquivos()
    if not arquivos:
        return 0

    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        cur.execute(_CREATE_CONTROL_TABLE)
        conn.commit()

        ja_aplicadas = _aplicadas(cur)
        pendentes = [f for f in arquivos if f.name not in ja_aplicadas]

        for path in pendentes:
            sql = path.read_text(encoding="utf-8")
            cur.execute(sql)
            cur.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (path.name,),
            )
            conn.commit()

        return len(pendentes)
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def main() -> None:
    try:
        import psycopg2  # noqa: F401
    except ImportError:
        print("❌  psycopg2-binary não instalado.")
        print("    Execute: pip install psycopg2-binary")
        sys.exit(1)

    url = _obter_url()
    print("Conectando ao banco de dados...", flush=True)

    try:
        aplicadas = rodar_migrations(url)
    except Exception as err:
        print("❌  ERRO ao aplicar migrations:")
        print(f"  {err}")
        sys.exit(1)

    if aplicadas == 0:
        print("✅  Nenhuma migration pendente. Nada a fazer.")
    else:
        print(f"\n✅  {aplicadas} migration(s) aplicada(s) com sucesso.")


if __name__ == "__main__":
    main()

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


def main() -> None:
    try:
        import psycopg2
    except ImportError:
        print("❌  psycopg2-binary não instalado.")
        print("    Execute: pip install psycopg2-binary")
        sys.exit(1)

    arquivos = _listar_arquivos()
    if not arquivos:
        print("Nenhum arquivo .sql em migrations/")
        return

    url = _obter_url()
    print("Conectando ao banco de dados...", flush=True)

    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor()

    # Garante tabela de controle
    cur.execute(_CREATE_CONTROL_TABLE)
    conn.commit()

    ja_aplicadas = _aplicadas(cur)
    pendentes = [f for f in arquivos if f.name not in ja_aplicadas]

    if not pendentes:
        total = len(arquivos)
        print(f"✅  Todas as {total} migration(s) já foram aplicadas. Nada a fazer.")
        cur.close()
        conn.close()
        return

    print(f"\nAplicando {len(pendentes)} migration(s) pendente(s):\n")

    for path in pendentes:
        print(f"  → {path.name} ...", end=" ", flush=True)
        sql = path.read_text(encoding="utf-8")
        try:
            cur.execute(sql)
            cur.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (path.name,),
            )
            conn.commit()
            print("✅")
        except Exception as err:
            conn.rollback()
            print("❌  ERRO")
            print(f"\nFalha em {path.name}:")
            print(f"  {err}")
            cur.close()
            conn.close()
            sys.exit(1)

    print(f"\n✅  {len(pendentes)} migration(s) aplicada(s) com sucesso.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()

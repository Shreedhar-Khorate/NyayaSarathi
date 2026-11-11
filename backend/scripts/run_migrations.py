"""
NyayaSarathi Database Migration Runner.
Executes SQL migration files against Supabase PostgreSQL.
Usage:
    python backend/scripts/run_migrations.py
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Ensure backend root is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

load_dotenv(os.path.join(backend_dir, ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
MIGRATIONS_DIR = os.path.join(backend_dir, "migrations")


def run_migrations():
    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL is not set in backend/.env")
        sys.exit(1)

    print("[*] Connecting to Supabase PostgreSQL for migration...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}")
        sys.exit(1)

    # Create schema migrations tracking table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public._schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
        );
        ALTER TABLE public._schema_migrations ENABLE ROW LEVEL SECURITY;
    """)

    migration_files = sorted(
        [f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql")]
    )

    print(f"[*] Found {len(migration_files)} migration(s) in {MIGRATIONS_DIR}")

    for filename in migration_files:
        version = filename.split("_")[0]
        cursor.execute("SELECT version FROM public._schema_migrations WHERE version = %s;", (version,))
        if cursor.fetchone():
            print(f"  [-] Migration {filename} already applied. Skipping.")
            continue

        filepath = os.path.join(MIGRATIONS_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            sql_content = f.read()

        print(f"  [>] Applying migration: {filename}...")
        try:
            cursor.execute(sql_content)
            cursor.execute(
                "INSERT INTO public._schema_migrations (version) VALUES (%s);",
                (version,)
            )
            print(f"  [OK] Applied {filename} successfully.")
        except Exception as e:
            print(f"  [FAIL] Error applying {filename}: {e}")
            cursor.close()
            conn.close()
            sys.exit(1)

    cursor.close()
    conn.close()
    print("[SUCCESS] All pending migrations executed successfully.")
    return True


if __name__ == "__main__":
    run_migrations()

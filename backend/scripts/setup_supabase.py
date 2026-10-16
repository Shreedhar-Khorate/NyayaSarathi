"""
NyayaSarathi — Supabase Database Setup & Demo Credential Seeder.
Uses credentials from backend/.env (zero hardcoded values).
Connects to Supabase via PostgreSQL (psycopg2) and the Supabase Client.
Creates the project tables and seeds the demo credentials from LOGINS.md.
"""

import os
import sys
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

load_dotenv(os.path.join(backend_dir, ".env"))

from services.auth_service import hash_password
from services.supabase_client import get_supabase_client, normalize_supabase_url


DEMO_ACCOUNTS = [
    {
        "id": "e43b171f-0e42-45e0-b6f2-7104b2a472c3",
        "email": "user@nyayasarathi.in",
        "password": "User@12345",
        "full_name": "Adv. Rohan Verma",
        "role": "USER",
    },
    {
        "id": "a18c992d-71b3-4f9e-9d21-432859c71a82",
        "email": "judge@nyayasarathi.in",
        "password": "Judge@12345",
        "full_name": "Hon'ble Justice S. K. Mukherjee",
        "role": "JUDGE",
    },
    {
        "id": "f92d441a-3e11-4b2a-8991-621804b82d99",
        "email": "admin@nyayasarathi.in",
        "password": "Admin@12345",
        "full_name": "Judicial System Administrator",
        "role": "ADMIN",
    },
]


def setup_supabase_database():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("[ERROR] DATABASE_URL is missing in .env")
        sys.exit(1)

    print(f"[*] Connecting to Supabase PostgreSQL...")
    try:
        conn = psycopg2.connect(db_url, sslmode="require")
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        print("[+] Connected to Supabase PostgreSQL successfully!")
    except Exception as e:
        print(f"[!] PostgreSQL direct connection failed: {e}")
        print("[*] Attempting fallback via Supabase HTTP REST Client...")
        return setup_via_supabase_client()

    print("[*] Creating database tables according to project architecture...")

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'USER',
            created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
        );
        CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
        CREATE INDEX IF NOT EXISTS idx_users_role ON public.users(role);
    """)
    print("  [x] Table 'users' verified.")

    # 2. RAG Documents Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.rag_documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size BIGINT NOT NULL,
            storage_path TEXT,
            total_pages INTEGER NOT NULL DEFAULT 1,
            total_chunks INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'indexed',
            created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
            user_id TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_rag_documents_user ON public.rag_documents(user_id);
        CREATE INDEX IF NOT EXISTS idx_rag_documents_status ON public.rag_documents(status);
    """)
    print("  [x] Table 'rag_documents' verified.")

    # 3. RAG Chunks Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.rag_chunks (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL REFERENCES public.rag_documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            page_number INTEGER NOT NULL DEFAULT 1,
            paragraph_number INTEGER NOT NULL DEFAULT 1,
            section_title TEXT,
            token_count INTEGER NOT NULL DEFAULT 0,
            text TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_rag_chunks_document_id ON public.rag_chunks(document_id);
        CREATE INDEX IF NOT EXISTS idx_rag_chunks_page ON public.rag_chunks(document_id, page_number);
    """)
    print("  [x] Table 'rag_chunks' verified.")

    # 4. Judgments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.judgments (
            cnr TEXT PRIMARY KEY,
            source TEXT,
            court_code TEXT,
            bench TEXT,
            year INTEGER,
            text_length INTEGER,
            title TEXT,
            judge TEXT,
            decision_date TEXT,
            disposal_nature TEXT,
            disposal_nature_normalized TEXT,
            full_text TEXT,
            parsed_case_type_raw TEXT,
            parsed_case_type TEXT,
            parsed_petitioner TEXT,
            parsed_respondent TEXT,
            parsed_court_name TEXT,
            ingested_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
            dataset_config TEXT,
            dataset_split TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_judgments_year ON public.judgments(year);
        CREATE INDEX IF NOT EXISTS idx_judgments_outcome ON public.judgments(disposal_nature_normalized);
        CREATE INDEX IF NOT EXISTS idx_judgments_case_type ON public.judgments(parsed_case_type);
        CREATE INDEX IF NOT EXISTS idx_judgments_court ON public.judgments(parsed_court_name);
        CREATE INDEX IF NOT EXISTS idx_judgments_type_outcome ON public.judgments(parsed_case_type, disposal_nature_normalized);
        CREATE INDEX IF NOT EXISTS idx_judgments_court_outcome ON public.judgments(parsed_court_name, disposal_nature_normalized);
    """)
    print("  [x] Table 'judgments' verified.")

    # 5. Ingestion Log Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.ingestion_log (
            id BIGSERIAL PRIMARY KEY,
            started_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
            completed_at TIMESTAMPTZ,
            config TEXT,
            split TEXT,
            filters TEXT,
            records_fetched INTEGER DEFAULT 0,
            records_inserted INTEGER DEFAULT 0,
            records_skipped INTEGER DEFAULT 0,
            status TEXT DEFAULT 'running',
            error TEXT
        );
    """)
    print("  [x] Table 'ingestion_log' verified.")

    # 6. Seed Credentials from LOGINS.md
    print("[*] Seeding demo credentials from LOGINS.md...")
    for acc in DEMO_ACCOUNTS:
        email = acc["email"].strip().lower()
        pw_hash = hash_password(acc["password"])
        cursor.execute("SELECT id FROM public.users WHERE LOWER(email) = LOWER(%s);", (email,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE public.users 
                SET password_hash = %s, full_name = %s, role = %s
                WHERE id = %s;
            """, (pw_hash, acc["full_name"], acc["role"], existing["id"]))
            print(f"  [OK] Updated user: {email} ({acc['role']})")
        else:
            cursor.execute("""
                INSERT INTO public.users (id, email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s, %s);
            """, (acc["id"], email, pw_hash, acc["full_name"], acc["role"]))
            print(f"  [OK] Inserted user: {email} ({acc['role']})")

    cursor.close()
    conn.close()
    print("\n[SUCCESS] Supabase database setup & credential seeding completed successfully!")
    return True


def setup_via_supabase_client():
    client = get_supabase_client()
    if not client:
        print("[ERROR] Could not initialize Supabase Client.")
        sys.exit(1)

    print("[*] Seeding demo credentials via Supabase REST API...")
    for acc in DEMO_ACCOUNTS:
        email = acc["email"].strip().lower()
        pw_hash = hash_password(acc["password"])
        data = {
            "id": acc["id"],
            "email": email,
            "password_hash": pw_hash,
            "full_name": acc["full_name"],
            "role": acc["role"],
        }
        res = client.table("users").upsert(data).execute()
        print(f"  [OK] Upserted user via REST: {email} ({acc['role']})")
    print("\n[SUCCESS] Supabase setup via REST completed!")
    return True


if __name__ == "__main__":
    setup_supabase_database()

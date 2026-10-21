-- ==============================================================================
-- 🏛️ NyayaSarathi — Supabase Schema & Migration Script
-- Run this script in the Supabase Dashboard SQL Editor (SQL Editor -> New Query)
-- ==============================================================================

-- 1. Enable Useful PostgreSQL Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector"; -- for pgvector semantic search if desired

-- ------------------------------------------------------------------------------
-- 2. Users Table (Authentication & Role-Based Access)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.users (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT, -- Nullable for Google OAuth users
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'USER', -- 'USER', 'ADVOCATE', 'ADMIN'
    avatar_url TEXT,
    organization TEXT,
    designation TEXT,
    profile_completed BOOLEAN NOT NULL DEFAULT FALSE,
    google_sub TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON public.users(role);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_sub ON public.users(google_sub) WHERE google_sub IS NOT NULL;

-- ------------------------------------------------------------------------------
-- PRODUCTION SECURITY NOTICE:
-- Do NOT insert hardcoded default passwords into production migrations.
-- Initial administrator accounts must be provisioned via the secure bootstrap CLI:
--   python backend/scripts/bootstrap_admin.py --email admin@domain.gov.in
-- ------------------------------------------------------------------------------

-- ------------------------------------------------------------------------------
-- 3. RAG Documents Table (Knowledge Base Documents)
-- ------------------------------------------------------------------------------
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

-- ------------------------------------------------------------------------------
-- 4. RAG Chunks Table (Paragraph-Level Retrieval Chunks)
-- ------------------------------------------------------------------------------
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

-- ------------------------------------------------------------------------------
-- 5. Judgments Table (High Court & Supreme Court Precedents)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.judgments (
    cnr TEXT PRIMARY KEY,
    source TEXT,                             -- 'sc' or 'hc'
    court_code TEXT,
    bench TEXT,
    year INTEGER,
    text_length INTEGER,
    title TEXT,
    judge TEXT,
    decision_date TEXT,
    disposal_nature TEXT,                     -- Raw outcome string
    disposal_nature_normalized TEXT,         -- Normalized outcome label (e.g. 'granted', 'dismissed')
    full_text TEXT,
    parsed_case_type_raw TEXT,
    parsed_case_type TEXT,
    parsed_petitioner TEXT,
    parsed_respondent TEXT,
    parsed_court_name TEXT,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    dataset_config TEXT,                     -- 'supreme_court' or 'high_courts'
    dataset_split TEXT                       -- 'train', 'validation', 'test'
);

-- B-Tree Indexes for fast candidate filtering
CREATE INDEX IF NOT EXISTS idx_judgments_year ON public.judgments(year);
CREATE INDEX IF NOT EXISTS idx_judgments_outcome ON public.judgments(disposal_nature_normalized);
CREATE INDEX IF NOT EXISTS idx_judgments_case_type ON public.judgments(parsed_case_type);
CREATE INDEX IF NOT EXISTS idx_judgments_court ON public.judgments(parsed_court_name);
CREATE INDEX IF NOT EXISTS idx_judgments_source ON public.judgments(source);
CREATE INDEX IF NOT EXISTS idx_judgments_type_outcome ON public.judgments(parsed_case_type, disposal_nature_normalized);
CREATE INDEX IF NOT EXISTS idx_judgments_court_outcome ON public.judgments(parsed_court_name, disposal_nature_normalized);

-- ------------------------------------------------------------------------------
-- 6. Ingestion Log Table (Dataset Batch Tracking)
-- ------------------------------------------------------------------------------
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

-- ------------------------------------------------------------------------------
-- 7. User Activity History Table (Persistent Research & Document Activity)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.user_activity_history (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    activity_type TEXT NOT NULL, -- 'LEGAL_RESEARCH', 'DOCUMENT_UPLOAD', 'OCR_ANALYSIS', 'PREDICTION'
    title TEXT NOT NULL,
    query_text TEXT,
    resource_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_activity_user_created ON public.user_activity_history(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_type ON public.user_activity_history(activity_type);

-- ------------------------------------------------------------------------------
-- 8. Row-Level Security (RLS) Policies
-- ------------------------------------------------------------------------------
-- Disable RLS by default on public read tables or configure service_role bypass:
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rag_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rag_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.judgments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingestion_log ENABLE ROW LEVEL SECURITY;

-- Allow service_role key full unrestricted access to all tables
CREATE POLICY "Service Role Full Access Users" ON public.users FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service Role Full Access Documents" ON public.rag_documents FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service Role Full Access Chunks" ON public.rag_chunks FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service Role Full Access Judgments" ON public.judgments FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service Role Full Access Logs" ON public.ingestion_log FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Allow public read access on verified judgments (public legal records)
CREATE POLICY "Public Read Judgments" ON public.judgments FOR SELECT TO anon, authenticated USING (true);

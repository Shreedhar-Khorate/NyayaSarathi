-- ==============================================================================
-- Migration 008: Enforce Row-Level Security (RLS) Across All Public Tables
-- NyayaSarathi Legal Intelligence Platform
-- ==============================================================================
-- Fixes Supabase Security Advisor critical alert: `rls_disabled_in_public`
-- and removes permissive `public`/`authenticated` `USING (true)` policies.
--
-- Architecture Note:
--   - Next.js frontend communicates exclusively through the FastAPI backend.
--   - FastAPI connects via privileged Postgres pooler (DATABASE_URL) or
--     SUPABASE_SERVICE_ROLE_KEY, both of which bypass RLS.
--   - Enabling RLS on all `public` tables with no permissive `anon` or
--     `authenticated` policies completely blocks unauthorized PostgREST access.
-- ==============================================================================

-- 1. Enable RLS on every public table
ALTER TABLE IF EXISTS public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.rag_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.rag_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.judgments ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.ingestion_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.user_activity_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.role_change_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.chat_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.chat_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.chat_participant_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public._schema_migrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public._supabase_keepalive ENABLE ROW LEVEL SECURITY;

-- 2. Remove overly permissive policies that exposed tables via anon/authenticated PostgREST
DROP POLICY IF EXISTS "Users can only read own history" ON public.user_activity_history;
DROP POLICY IF EXISTS "Authenticated Read Role Audit" ON public.role_change_audit;
DROP POLICY IF EXISTS "Public Read Judgments" ON public.judgments;

-- 3. Explicit service_role policies (PostgREST service_role access; anon/authenticated blocked)
DROP POLICY IF EXISTS "Service Role Full Access Users" ON public.users;
CREATE POLICY "Service Role Full Access Users" ON public.users
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service Role Full Access Documents" ON public.rag_documents;
CREATE POLICY "Service Role Full Access Documents" ON public.rag_documents
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service Role Full Access Chunks" ON public.rag_chunks;
CREATE POLICY "Service Role Full Access Chunks" ON public.rag_chunks
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service Role Full Access Judgments" ON public.judgments;
CREATE POLICY "Service Role Full Access Judgments" ON public.judgments
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service Role Full Access Logs" ON public.ingestion_log;
CREATE POLICY "Service Role Full Access Logs" ON public.ingestion_log
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service Role Full Access Activity History" ON public.user_activity_history;
CREATE POLICY "Service Role Full Access Activity History" ON public.user_activity_history
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service Role Full Access Role Audit" ON public.role_change_audit;
CREATE POLICY "Service Role Full Access Role Audit" ON public.role_change_audit
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service Role Full Access Chat Conversations" ON public.chat_conversations;
CREATE POLICY "Service Role Full Access Chat Conversations" ON public.chat_conversations
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service Role Full Access Chat Messages" ON public.chat_messages;
CREATE POLICY "Service Role Full Access Chat Messages" ON public.chat_messages
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service Role Full Access Chat Attachments" ON public.chat_attachments;
CREATE POLICY "Service Role Full Access Chat Attachments" ON public.chat_attachments
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service Role Full Access Chat Participant State" ON public.chat_participant_state;
CREATE POLICY "Service Role Full Access Chat Participant State" ON public.chat_participant_state
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service Role Full Access Schema Migrations" ON public._schema_migrations;
CREATE POLICY "Service Role Full Access Schema Migrations" ON public._schema_migrations
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service Role Full Access Supabase Keepalive" ON public._supabase_keepalive;
CREATE POLICY "Service Role Full Access Supabase Keepalive" ON public._supabase_keepalive
    FOR ALL TO service_role USING (true) WITH CHECK (true);


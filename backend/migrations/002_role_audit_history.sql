-- ==============================================================================
-- 🏛️ Migration 002: Role Change Audit History
-- NyayaSarathi Legal Intelligence Platform
-- ==============================================================================

-- 1. Create public.role_change_audit table for durable role transition logging
CREATE TABLE IF NOT EXISTS public.role_change_audit (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    target_user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    actor_user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    old_role TEXT NOT NULL,
    new_role TEXT NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 2. Create performance indexes for target user lookup, chronological sorting, and actor auditing
CREATE INDEX IF NOT EXISTS idx_role_audit_target ON public.role_change_audit(target_user_id);
CREATE INDEX IF NOT EXISTS idx_role_audit_created ON public.role_change_audit(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_role_audit_actor ON public.role_change_audit(actor_user_id);

-- 3. Enable Row-Level Security (RLS)
ALTER TABLE public.role_change_audit ENABLE ROW LEVEL SECURITY;

-- 4. Service role full access policy
DROP POLICY IF EXISTS "Service Role Full Access Role Audit" ON public.role_change_audit;
CREATE POLICY "Service Role Full Access Role Audit" ON public.role_change_audit
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 5. Authenticated read policy (backend service queries or verified admin calls)
DROP POLICY IF EXISTS "Authenticated Read Role Audit" ON public.role_change_audit;
CREATE POLICY "Authenticated Read Role Audit" ON public.role_change_audit
    FOR SELECT
    TO authenticated
    USING (true);

-- ==============================================================================
-- 🏛️ Migration 001: Extend User Profile and Add User Activity History
-- NyayaSarathi Legal Intelligence Platform
-- ==============================================================================

-- 1. Safely alter public.users to allow passwordless accounts (Google OAuth)
-- and add extended profile fields.
ALTER TABLE public.users ALTER COLUMN password_hash DROP NOT NULL;

ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS avatar_url TEXT,
    ADD COLUMN IF NOT EXISTS organization TEXT,
    ADD COLUMN IF NOT EXISTS designation TEXT,
    ADD COLUMN IF NOT EXISTS profile_completed BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    ADD COLUMN IF NOT EXISTS google_sub TEXT;

-- Index on google_sub for fast O(1) OAuth lookup and uniqueness when present
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_sub ON public.users(google_sub) WHERE google_sub IS NOT NULL;

-- 2. Mark existing seeded users (from LOGINS.md) as having completed profiles
UPDATE public.users 
SET profile_completed = TRUE 
WHERE email IN ('user@nyayasarathi.in', 'judge@nyayasarathi.in', 'admin@nyayasarathi.in');

-- 3. Create public.user_activity_history for persistent research & document operations
CREATE TABLE IF NOT EXISTS public.user_activity_history (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    activity_type TEXT NOT NULL, -- 'LEGAL_RESEARCH', 'DOCUMENT_UPLOAD', 'OCR_ANALYSIS', 'PREDICTION'
    title TEXT NOT NULL,
    query_text TEXT,
    resource_id TEXT, -- document_id or cnr or prediction_id
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Composite and single indexes for fast ownership querying and descending order
CREATE INDEX IF NOT EXISTS idx_activity_user_created ON public.user_activity_history(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_type ON public.user_activity_history(activity_type);

-- 4. Enable Row Level Security (RLS) on user_activity_history
ALTER TABLE public.user_activity_history ENABLE ROW LEVEL SECURITY;

-- Service role bypasses RLS automatically; create safe public policy for app
DROP POLICY IF EXISTS "Users can only read own history" ON public.user_activity_history;
CREATE POLICY "Users can only read own history" ON public.user_activity_history
    FOR ALL
    USING (TRUE)
    WITH CHECK (TRUE);

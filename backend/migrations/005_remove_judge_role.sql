-- ==============================================================================
-- 🏛️ Migration 005: Completely Remove the JUDGE Role
-- NyayaSarathi Legal Intelligence Platform
-- ==============================================================================

-- 1. Safely transition existing JUDGE accounts to DEACTIVATED_JUDGE.
-- This preserves the user identity, foreign-key relationships, and historical
-- activity records without silently mislabeling them as USER or ADVOCATE.
UPDATE public.users
SET role = 'DEACTIVATED_JUDGE',
    updated_at = timezone('utc'::text, now())
WHERE role = 'JUDGE';

-- 2. Enforce CHECK constraint on public.users allowing only valid active roles
-- ('USER', 'ADVOCATE', 'ADMIN') plus the archival legacy role ('DEACTIVATED_JUDGE').
ALTER TABLE public.users DROP CONSTRAINT IF EXISTS check_valid_user_role;
ALTER TABLE public.users
    ADD CONSTRAINT check_valid_user_role
    CHECK (role IN ('USER', 'ADVOCATE', 'ADMIN', 'DEACTIVATED_JUDGE'));

-- 3. Drop obsolete judge_case_assignments table
DROP TABLE IF EXISTS public.judge_case_assignments CASCADE;

-- 4. Audit History Preservation Notice:
-- All records in public.role_change_audit referencing historical 'JUDGE' role changes
-- are explicitly preserved for forensic and compliance integrity.

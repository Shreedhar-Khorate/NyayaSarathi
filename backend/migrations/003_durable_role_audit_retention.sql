-- ==============================================================================
-- 🏛️ Migration 003: Durable Role-Change Audit Retention
-- NyayaSarathi Legal Intelligence Platform
-- ==============================================================================

-- 1. Add immutable identity snapshots to role_change_audit
ALTER TABLE public.role_change_audit
    ADD COLUMN IF NOT EXISTS target_email TEXT,
    ADD COLUMN IF NOT EXISTS actor_email TEXT,
    ADD COLUMN IF NOT EXISTS actor_name TEXT;

-- 2. Backfill existing records with snapshots from public.users table
UPDATE public.role_change_audit a
SET 
    target_email = u_target.email
FROM public.users u_target
WHERE a.target_user_id = u_target.id AND a.target_email IS NULL;

UPDATE public.role_change_audit a
SET 
    actor_email = u_actor.email,
    actor_name = u_actor.full_name
FROM public.users u_actor
WHERE a.actor_user_id = u_actor.id AND a.actor_email IS NULL;

-- 3. Allow target_user_id and actor_user_id to be NULL when user accounts are removed
ALTER TABLE public.role_change_audit
    ALTER COLUMN target_user_id DROP NOT NULL,
    ALTER COLUMN actor_user_id DROP NOT NULL;

-- 4. Drop cascading foreign key constraints
ALTER TABLE public.role_change_audit
    DROP CONSTRAINT IF EXISTS role_change_audit_target_user_id_fkey,
    DROP CONSTRAINT IF EXISTS role_change_audit_actor_user_id_fkey;

-- 5. Re-add foreign key constraints with ON DELETE SET NULL to preserve audit trail permanently
ALTER TABLE public.role_change_audit
    ADD CONSTRAINT role_change_audit_target_user_id_fkey
    FOREIGN KEY (target_user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE public.role_change_audit
    ADD CONSTRAINT role_change_audit_actor_user_id_fkey
    FOREIGN KEY (actor_user_id) REFERENCES public.users(id) ON DELETE SET NULL;

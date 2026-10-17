-- ==============================================================================
-- 🏛️ Migration 004: Judge Case Assignments & Bench Docketing
-- NyayaSarathi Legal Intelligence Platform
-- ==============================================================================

-- 1. Create judge_case_assignments table for persistent bench matter tracking
CREATE TABLE IF NOT EXISTS public.judge_case_assignments (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    case_number TEXT NOT NULL,
    title TEXT NOT NULL,
    court_name TEXT NOT NULL,
    case_type TEXT NOT NULL DEFAULT 'Criminal',
    judge_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    assigned_by_id TEXT REFERENCES public.users(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'ASSIGNED', -- 'ASSIGNED', 'IN_REVIEW', 'HEARING_SCHEDULED', 'RESERVED', 'DISPOSED'
    priority TEXT NOT NULL DEFAULT 'REGULAR', -- 'URGENT', 'REGULAR', 'EXPEDITED'
    filing_date DATE,
    hearing_date DATE,
    petitioner TEXT,
    respondent TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 2. Indexes for docket queries, judge workload, and scheduling
CREATE INDEX IF NOT EXISTS idx_case_assign_judge ON public.judge_case_assignments(judge_id);
CREATE INDEX IF NOT EXISTS idx_case_assign_status ON public.judge_case_assignments(status);
CREATE INDEX IF NOT EXISTS idx_case_assign_case_num ON public.judge_case_assignments(case_number);
CREATE INDEX IF NOT EXISTS idx_case_assign_created ON public.judge_case_assignments(created_at DESC);

-- 3. Row-Level Security
ALTER TABLE public.judge_case_assignments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service Role Full Access Case Assignments" ON public.judge_case_assignments;
CREATE POLICY "Service Role Full Access Case Assignments" ON public.judge_case_assignments
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS "Authenticated Read Case Assignments" ON public.judge_case_assignments;
CREATE POLICY "Authenticated Read Case Assignments" ON public.judge_case_assignments
    FOR SELECT
    TO authenticated
    USING (true);

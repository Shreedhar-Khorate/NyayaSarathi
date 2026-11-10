-- ==============================================================================
-- Migration 007: Supabase Keep-Alive Dummy Table
-- NyayaSarathi Legal Intelligence Platform
-- ==============================================================================
-- Used by GET /supa to perform periodic INSERT + DELETE activity so Supabase
-- free-tier projects do not pause due to 7-day inactivity.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public._supabase_keepalive (
    id         TEXT PRIMARY KEY,
    pinged_at  TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);


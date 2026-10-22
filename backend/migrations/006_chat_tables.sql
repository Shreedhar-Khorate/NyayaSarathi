-- ==============================================================================
-- Migration 006: Real-Time User–Advocate Chat Tables
-- NyayaSarathi Legal Intelligence Platform
-- ==============================================================================
-- Applies to: PostgreSQL / Supabase (authoritative production database)
-- SQLite equivalent is applied automatically via init_chat_tables() on startup.
-- User IDs are TEXT to match public.users.id convention.
-- ==============================================================================

-- 1. chat_conversations: one private conversation per user/advocate pair
CREATE TABLE IF NOT EXISTS public.chat_conversations (
    id            TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    advocate_id   TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    status        TEXT NOT NULL DEFAULT 'active'
                      CHECK (status IN ('active', 'closed', 'archived')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    last_message_at TIMESTAMPTZ,
    -- Enforce one conversation per unique user/advocate pair
    CONSTRAINT uq_chat_conv_pair UNIQUE (user_id, advocate_id)
);

CREATE INDEX IF NOT EXISTS idx_chat_conv_user
    ON public.chat_conversations (user_id);
CREATE INDEX IF NOT EXISTS idx_chat_conv_advocate
    ON public.chat_conversations (advocate_id);
CREATE INDEX IF NOT EXISTS idx_chat_conv_last_msg
    ON public.chat_conversations (last_message_at DESC NULLS LAST);

-- 2. chat_messages: messages within a conversation
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES public.chat_conversations(id) ON DELETE CASCADE,
    sender_id       TEXT NOT NULL REFERENCES public.users(id),
    body            TEXT,          -- nullable only for attachment-only messages
    idempotency_key TEXT,          -- optional client-supplied key for dedup
    created_at      TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    -- idempotency: prevent duplicate sends with same key in same conversation
    CONSTRAINT uq_chat_msg_idempotency UNIQUE (conversation_id, idempotency_key),
    -- at least body or an attachment must exist (enforced in application layer)
    CONSTRAINT chk_msg_nonempty CHECK (
        body IS NOT NULL OR length(trim(coalesce(body, ''))) > 0
        -- real check: attachment link kept in chat_attachments; app validates
    )
);

-- Drop the over-restrictive inline check (application handles it properly)
ALTER TABLE public.chat_messages DROP CONSTRAINT IF EXISTS chk_msg_nonempty;

-- Composite index for paginated history
CREATE INDEX IF NOT EXISTS idx_chat_msg_conv_created
    ON public.chat_messages (conversation_id, created_at, id);
CREATE INDEX IF NOT EXISTS idx_chat_msg_idempotency
    ON public.chat_messages (conversation_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

-- 3. chat_attachments: file metadata linked to messages
CREATE TABLE IF NOT EXISTS public.chat_attachments (
    id              TEXT PRIMARY KEY,
    message_id      TEXT NOT NULL REFERENCES public.chat_messages(id) ON DELETE CASCADE,
    conversation_id TEXT NOT NULL REFERENCES public.chat_conversations(id) ON DELETE CASCADE,
    uploaded_by     TEXT NOT NULL REFERENCES public.users(id),
    storage_key     TEXT NOT NULL,          -- private bucket path (server-generated)
    original_filename TEXT NOT NULL,        -- safe display name
    content_type    TEXT,
    size_bytes      BIGINT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_chat_attach_msg
    ON public.chat_attachments (message_id);
CREATE INDEX IF NOT EXISTS idx_chat_attach_conv
    ON public.chat_attachments (conversation_id);

-- 4. chat_participant_state: read cursor per participant
CREATE TABLE IF NOT EXISTS public.chat_participant_state (
    conversation_id   TEXT NOT NULL REFERENCES public.chat_conversations(id) ON DELETE CASCADE,
    user_id           TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    last_read_message_id TEXT REFERENCES public.chat_messages(id) ON DELETE SET NULL,
    last_read_at      TIMESTAMPTZ,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    PRIMARY KEY (conversation_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_chat_state_user
    ON public.chat_participant_state (user_id);

-- ==============================================================================
-- Instructions:
-- Run this migration against your Supabase PostgreSQL project using:
--   psql $DATABASE_URL -f backend/migrations/006_chat_tables.sql
-- or via Supabase SQL editor.
-- SQLite tables are auto-created on backend startup via init_chat_tables().
-- ==============================================================================

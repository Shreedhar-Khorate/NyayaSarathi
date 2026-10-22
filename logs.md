# NyayaSarathi — Project Logs

---

## Real-Time User–Advocate Chat — 2026-10-22

### 1. Initial Inspection

**Files and patterns inspected:**
- `backend/main.py` — FastAPI entry point, router registration, startup hooks
- `backend/services/auth_dependencies.py` — JWT dependency (`get_current_user`), `require_role` factory
- `backend/services/auth_service.py` — JWT signing / decoding
- `backend/services/user_repository.py` — `is_postgres_authoritative()`, `get_pg_connection()`, `get_db_connection()` (SQLite), `init_user_table()`
- `backend/services/supabase_client.py` — `get_supabase_client()`, `is_supabase_configured()`
- `backend/services/war_room_repository.py` — Pattern reference for SQLite repo + `init_*_tables()`
- `backend/routers/advocate.py` — Advocate router pattern, `require_advocate_or_admin` usage
- `backend/migrations/005_remove_judge_role.sql` — Migration naming convention
- `nyayasarathi-app/src/lib/auth.ts` — `getToken()`, `getAuthHeaders()`, `getUser()`
- `nyayasarathi-app/src/lib/config.ts` — `API_BASE_URL = http://127.0.0.1:8001`
- `nyayasarathi-app/src/app/advocate/dashboard/page.tsx` — Design system colors, component patterns
- `nyayasarathi-app/src/components/layout/NavAndFooter.tsx` — Navigation structure

**Confirmed facts:**
- Frontend does NOT use `@supabase/supabase-js` in the browser. All DB ops go through FastAPI.
- User IDs are TEXT (not UUID). users.id is TEXT PRIMARY KEY.
- Dual-mode: PostgreSQL when `DATABASE_URL` set + psycopg2 available and `NYAYASARATHI_USE_SQLITE != 1`. SQLite otherwise.
- No existing user–advocate assignment/case relationship model. Chat uses a direct user+advocate pair with uniqueness constraint.
- Custom NyayaSarathi JWTs do NOT satisfy Supabase auth.uid() or RLS. Approach A (backend-mediated Realtime) was chosen.
- Supabase Realtime does NOT observe SQLite writes — polling fallback implemented for SQLite mode.
- Active roles: USER, ADVOCATE, ADMIN. JUDGE/DEACTIVATED_JUDGE rejected at auth dependency level.

---

### 2. Design Decisions

**Schema / uniqueness rule:**
- One conversation per (user_id, advocate_id) pair — UNIQUE constraint on both columns.
- No case_id needed: no existing case assignment model in the codebase.
- Tables: `chat_conversations`, `chat_messages`, `chat_attachments`, `chat_participant_state`.
- All IDs are TEXT (UUID strings). All timestamps UTC ISO-8601.
- Idempotency key: optional client-supplied `idempotency_key` TEXT with UNIQUE(conversation_id, idempotency_key) constraint.

**Authorization policy:**
- USER can only create/access conversations where `user_id == their own id`.
- ADVOCATE can only access conversations where `advocate_id == their own id`.
- ADMIN can read conversation metadata (no private message content exposed automatically — they have to request it explicitly via the API which is authorized but not log-dumped).
- Participant ID always derived from verified JWT, never from request body.
- 404 returned for unauthorized access (not 403) to avoid disclosing conversation existence.

**Realtime authorization (Approach A — Backend-mediated):**
- Backend publishes minimal event `{type, conversation_id, message_id, created_at}` to Supabase Realtime channel `chat:{conversation_id}` using server-held service role key.
- Event is published AFTER successful database commit (non-atomic but acceptable).
- Event publication failure is non-fatal — message is already persisted.
- Browser does NOT use Supabase JS SDK. Polling fallback (`createChatPoller`) provides 5s interval in SQLite mode or as reconnect recovery.
- On tab visibility restore, frontend re-fetches from the last cursor.

**Attachment storage:**
- Private Supabase Storage bucket `chat-attachments` (env: `CHAT_STORAGE_BUCKET`).
- Storage keys generated server-side: `{conv_id}/{user_id}/{uuid}/{safe_filename}`.
- Permanent public URLs are NEVER issued. Downloads use short-lived signed URLs (60s) in PostgreSQL mode, or local disk streaming in SQLite dev mode.
- Allowed: `.pdf`, `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.txt`, `.doc`, `.docx`. Max 10 MB.
- MIME type detected from extension (not trusted from browser). Browser-supplied content-type is cross-checked.
- Malware scanning is NOT available in this environment. This is documented as a known limitation.

**PostgreSQL vs SQLite behavior:**
- PostgreSQL: full feature — all endpoints + Supabase Realtime event publishing.
- SQLite: full feature EXCEPT Realtime push. Polling fallback active. Local disk file storage under `backend/data/chat_uploads/`.
- `is_postgres_authoritative()` is used consistently (no second config flag).

**Outbox:** Not implemented. Realtime events are best-effort, published after commit. Clients recover via polling/cursor on reconnect. This is documented as a limitation.

---

### 3. Files Changed

| Path | Change |
|---|---|
| `backend/migrations/006_chat_tables.sql` | **CREATED** — PostgreSQL migration: chat_conversations, chat_messages, chat_attachments, chat_participant_state with indexes and constraints |
| `backend/services/chat_repository.py` | **CREATED** — Dual-mode repository: conversation CRUD, paginated messages, attachments, read-state |
| `backend/routers/chat.py` | **CREATED** — FastAPI router with 9 endpoints: list/create/get conversations, paginated messages, send, read, upload attachment, download attachment, health |
| `backend/tests/test_chat.py` | **CREATED** — 26 pytest tests covering auth, persistence, pagination, idempotency, read-state, attachments |
| `backend/main.py` | **MODIFIED** — Import `chat` router + `init_chat_tables`, register `/api/chat`, call `init_chat_tables()` on startup |
| `nyayasarathi-app/src/lib/chat.ts` | **CREATED** — TypeScript chat API client with types, all API functions, polling fallback creator |
| `nyayasarathi-app/src/app/chat/page.tsx` | **CREATED** — Full chat UI: conversation list, message history, composer, attachments, read-state, polling, reconnect, mobile layout |
| `nyayasarathi-app/src/app/advocate/dashboard/page.tsx` | **MODIFIED** — Added "Client Chat" tool link to TOOLS array |
| `nyayasarathi-app/src/components/layout/NavAndFooter.tsx` | **MODIFIED** — Added "Chat" to main navigation links |

**Migration to apply (PostgreSQL):**
```
psql $DATABASE_URL -f backend/migrations/006_chat_tables.sql
```
SQLite tables are auto-created on startup via `init_chat_tables()`.

---

### 4. Configuration

**New / changed environment variables (names only — never values):**
- `CHAT_STORAGE_BUCKET` — Name of private Supabase Storage bucket for chat attachments (default: `chat-attachments`)
- `NYAYASARATHI_USE_SQLITE` — Existing; controls database mode for all features including chat
- `DATABASE_URL` — Existing; required for PostgreSQL mode
- `SUPABASE_URL` — Existing; required for Realtime publishing and storage
- `SUPABASE_SERVICE_ROLE_KEY` — Existing; required for backend-side Realtime/Storage operations

**Private bucket setup:**
1. Create a Supabase Storage bucket named `chat-attachments` (private, no public access).
2. Do NOT enable public URLs on this bucket.
3. The backend uses service-role key for uploads; signed URLs (60s expiry) for downloads.

**No additional background worker is required.** Realtime events are published synchronously after commit. Outbox pattern is not implemented (documented limitation).

---

### 5. Testing

**Commands executed:**

```
# 1. Backend repository unit tests
python "C:\...\scratch\test_chat_repo.py"
# Result: ALL CHAT REPO TESTS PASSED (exit 0)

# 2. Pytest suite (26 tests)
cd backend && python -m pytest tests/test_chat.py -v
# Result: 26 passed, 0 failures, 102 warnings (exit 0)

# 3. TypeScript type check
cd nyayasarathi-app && npx tsc --noEmit
# Result: exit 0 (no errors)

# 4. Next.js production build
cd nyayasarathi-app && npm run build
# Result: exit 0 — 18 routes compiled, /chat route included
```

**Test results summary:**
- `test_chat_repo.py` (script): 9 assertions — PASS
- `test_chat.py` (pytest): 26 tests across 5 classes — **26 passed, 0 failed**
  - `TestConversationAuth` (9 tests): user/advocate permission enforcement, idempotency, admin access, nonexistent conversation
  - `TestMessages` (8 tests): persistence, empty/whitespace/overlong rejection, idempotency key, chronological order, pagination
  - `TestReadState` (3 tests): unread increment, mark-read, own messages not counted
  - `TestConversationList` (3 tests): scoped list for USER/ADVOCATE
  - `TestAttachments` (3 tests): create/retrieve metadata, nonexistent lookup
- TypeScript: **0 errors**
- Next.js build: **exit 0, 18 routes, /chat confirmed**

**Tests not run:**
- Supabase Realtime end-to-end subscription: not runnable without live Supabase credentials and browser environment
- Supabase Storage upload/download integration: not runnable without live credentials
- HTTP endpoint integration tests (FastAPI TestClient for chat router): not run — would require full app startup fixtures; deferred to CI
- Multi-user concurrent conversation creation: not run in current test environment

**Manual verification (not performed — no browser session active):**
- UI rendering of chat page, message sending, attachment upload/download

---

### 6. Known Limitations and Risks

1. **Supabase Realtime (SQLite mode):** Not available. Frontend falls back to 5-second polling. This is documented and disclosed to the user via the `/api/chat/health` endpoint and a UI badge.
2. **Outbox pattern not implemented:** Realtime events are best-effort. If event publishing fails after a commit, the recipient will receive the message on next poll/reconnect — no message is lost from the database.
3. **User–Advocate assignment model:** No pre-existing assignment model. The chat pair is user-chosen. This means a USER can open a conversation with any ADVOCATE (not restricted to an assigned one). A future improvement would add an advocate-assignment table to restrict pairings.
4. **Malware scanning:** Not available in this environment. Uploaded files are validated by extension and MIME type, but not scanned. Documented limitation.
5. **ADMIN can read message content:** ADMINs can call `/api/chat/conversations/{id}/messages` if they know the conversation ID. This follows the existing policy (ADMIN = unrestricted access). Explicit message-level moderation audit trail is not yet implemented.
6. **Supabase Storage not set up:** The `chat-attachments` bucket must be manually created in Supabase. Without it, attachment uploads fail with 503 in PostgreSQL mode. SQLite mode uses local disk.
7. **Local file storage (SQLite dev mode):** Files stored under `backend/data/chat_uploads/` are not encrypted at rest. This is dev-only behavior.
8. **Pagination cursor stability:** In SQLite mode, the `(created_at, id)` cursor is implemented with `<` on timestamp + `<` on id. In rare cases of identical timestamps, ordering by id (TEXT) provides lexicographic stability — this is correct for UUIDs.

---

### 7. Next Steps

1. **Create `chat-attachments` private bucket in Supabase** and configure CHAT_STORAGE_BUCKET env var.
2. **Run PostgreSQL migration** `006_chat_tables.sql` against Supabase.
3. **Add advocate-assignment model** to restrict conversation pairings to assigned pairs.
4. **Implement FastAPI TestClient integration tests** for all 9 chat endpoints.
5. **Add Supabase Realtime subscription in frontend** using backend-issued subscription tokens (once Approach B is evaluated).
6. **Add ADMIN message moderation audit log** if privacy policy requires it.
7. **Add rate limiting** to message-send and attachment-upload endpoints.
8. **Implement cleanup job** for orphaned Supabase Storage objects after failed DB writes.

---

### 8. Final Status

**PASS WITH LIMITATIONS**

Core feature is implemented and all automated checks pass:
- ✅ Chat tables (SQLite + PostgreSQL migration)
- ✅ 9 FastAPI endpoints with participant authorization
- ✅ 26 pytest tests: 26/26 passed
- ✅ TypeScript: 0 errors
- ✅ Next.js production build: exit 0, /chat route compiled
- ✅ Message persistence, pagination, idempotency, read-state
- ✅ Attachment upload/download with server-side validation
- ✅ Polling fallback for SQLite mode
- ✅ Reconnect recovery via visibility change

Known gaps (non-blocking for core feature):
- ⚠️ Supabase Storage bucket not yet created (manual step)
- ⚠️ PostgreSQL migration not yet applied (manual step)  
- ⚠️ Supabase Realtime push not end-to-end tested (needs live credentials)
- ⚠️ No advocate-assignment enforcement (any user can open chat with any advocate)
- ⚠️ Malware scanning not available

---

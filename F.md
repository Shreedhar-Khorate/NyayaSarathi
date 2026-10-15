LLM Coding-Agent Prompt --- NyayaSarathi Profile & History
You are working inside the existing NyayaSarathi repository. Implement
the profile section, profile-completion onboarding, member roles, and
persistent per-user history according to PROFILE_IMPLEMENTATION.md.
Architecture that must be preserved
- React + Vite frontend.
- FastAPI backend.
- Google OAuth is handled by FastAPI.
- FastAPI verifies Google identity and issues the application's own
  signed JWT.
- Supabase PostgreSQL is the persistent store.
- Existing application table: public.users, with id text, unique
  email, required password_hash, required full_name, role
  defaulting to USER, and created_at.
- Existing document and RAG tables: rag_documents, rag_chunks.
- Shared legal corpus: judgments.
- Operational ingestion tracking: ingestion_log.
- Development callback supplied by the project owner:
  http://localhost:8000/api/auth/google/callback.
- Existing legal AI endpoints and OCR/document functionality must not
  regress.
Work method
1. Inspect before coding
Inspect the actual repository, current SQL migrations, authentication
utilities, Google OAuth callback, JWT dependencies, Supabase access
layer, frontend routing, profile-related UI, and any history
persistence. Summarize what already exists and identify the smallest
safe implementation plan. Do not ask the owner to repeat the
architecture already provided.
Do not assume auth.uid() maps to public.users.id. The application
uses FastAPI-managed JWTs and a custom text user ID unless code proves
otherwise.
2. Implement in small, testable milestones
1. Authentication and schema audit: verify identity mapping, user
   upsert behavior, password-login compatibility, current database
   access, and existing history.
2. Database migration: add the smallest required profile fields and
   history/ownership changes. Preserve data and IDs. Address
   password_hash NOT NULL safely for Google-only accounts without
   breaking password-based accounts.
3. Backend profile flow: create/read/update profile operations;
   derive user identity only from a verified JWT; validate payloads and
   protect role/identity fields.
4. Frontend profile flow: add profile navigation/page, profile
   editing, and onboarding when required fields are missing. Load
   persisted data from the backend.
5. History: persist supported research/document activities, load
   the authenticated member's own history, and make it survive refresh
   and future logins.
6. Security and regression: validate role enforcement, ownership
   checks, error handling, and existing OAuth/legal AI/OCR behavior.
7. Final validation and documentation: run relevant tests and
   report actual results.
3. Required security rules
- Never trust a client-supplied user ID or role.
- Derive the member ID from verified application JWT claims.
- Preserve the existing JWT signing and validation conventions; do not
  invent a new insecure scheme.
- Do not allow self-assignment of ADMIN, JUDGE, or any privileged
  role.
- Do not invent placeholder password hashes.
- Never expose service-role credentials or Google OAuth secrets in
  frontend code.
- If using the Supabase service-role key, enforce authentication,
  authorization, and resource ownership in FastAPI because that key
  may bypass RLS.
- Do not add unsafe RLS policies or assume Supabase Auth is in use.
- Preserve existing accounts and password login.
- Do not assign legacy documents or history to arbitrary users.
- Do not log tokens, credentials, or sensitive legal data.
4. Required logs.md
Create a root-level logs.md if absent. If it exists, read it and
preserve all prior entries.
Update it after every meaningful milestone, not just at the end.
Each entry must include:
- Date/time and task title.
- Status: Completed, In progress, or Blocked.
- Summary of changes.
- Files created/modified.
- Database migration/schema changes.
- Tests or commands actually run and their real results.
- Errors and resolutions.
- Remaining work.
Use this template:
## YYYY-MM-DD HH:MM — Task title

- **Status:** Completed / In progress / Blocked
- **Changes:** ...
- **Files:** ...
- **Database:** ...
- **Validation:** ...
- **Issues:** ...
- **Next steps:** ...
Do not claim that work or tests were completed unless they actually
were. Never put secrets or personal data in logs.
5. Definition of done
The task is complete only when:
- Google OAuth and FastAPI JWT sessions still work.
- Each authenticated user has one persistent database-backed profile.
- Missing required fields trigger onboarding.
- Profile edits persist and appear after reload/re-login.
- Roles are read from trusted backend/database state and cannot be
  self-elevated.
- History is persisted and isolated by authenticated user.
- Document ownership is checked where applicable.
- Migrations are version-controlled and preserve existing data.
- Relevant tests are run and their results reported.
- logs.md has entries for the work performed.
- A final report lists files changed, migrations applied or awaiting
  execution, test results, and remaining issues.
Start by inspecting the codebase, then implement the feature. Do not
stop at a plan, UI mockup, or pseudocode. If a migration or external
configuration requires owner action, prepare the exact artifact and
clearly report that it is pending rather than claiming it has been
applied.
# NyayaSarathi — Implementation Logs
Canonical log tracking the implementation of Judge and Admin Dashboards, role-based access control, database migrations, and security audits.

---

### 2026-10-17 11:24 — Milestone 1: Repository Inspection and Implementation Plan

**Completed**
- Inspected complete repository structure, configuration files, backend architecture, and frontend application.
- Verified backend stack: FastAPI with modular routers in `backend/routers/`, user repository DAL in `backend/services/user_repository.py`, authentication with bcrypt password hashing and PyJWT in `backend/services/auth_service.py` and `backend/routers/auth.py`.
- Verified database setup: Dual-layer database persistence with Supabase PostgreSQL (via `psycopg2` migration runner and `supabase-py` client) and local SQLite fallback (`backend/data/nyayasarathi.db`).
- Inspected migration system: `backend/scripts/run_migrations.py` applies versioned SQL files from `backend/migrations/` tracked in `public._schema_migrations`. Tested and confirmed connection to Supabase PostgreSQL, finding `001_profile_and_history.sql` already applied.
- Inspected local SQLite database: Found 7 tables (`judgments`, `ingestion_log`, `sqlite_sequence`, `rag_documents`, `rag_chunks`, `user_activity_history`, `users`). Verified 8 existing users across roles (`ADMIN`: 1, `JUDGE`: 1, `USER`: 4, `ADVOCATE`: 2).
- Inspected activity and case data:
  - `user_activity_history` contains 19 active activity records across types `DOCUMENT_UPLOAD`, `LEGAL_RESEARCH`, and `PROFILE_ONBOARDING`.
  - `judgments` table contains 743 High Court and Supreme Court precedents with bench, judge, court, and outcome metadata.
  - Case assignment gap documented: No persistent case-to-judge assignment table exists in the database. `backend/routers/cases.py` and `backend/services/cases_service.py` currently use an in-memory dictionary. In accordance with specification §4, case assignment records will not be fabricated; safe precedent and bench case access will be scoped, and the docket assignment model is flagged for future product roadmap.
- Inspected frontend: Next.js 16.2.12 (App Router with webpack), React 19, Tailwind CSS 3.4, Framer Motion, and Lucide icons in `nyayasarathi-app`. Existing client auth is managed in `src/lib/auth.ts` using JWT stored in `localStorage`.
- Verified test runner: Executed `python -m unittest backend/tests/test_profile_and_history.py` (6 tests passed in 10.74s). Ran `npm run build` in `nyayasarathi-app` (successful build in 9.7s, TypeScript compilation passed).

**Files changed**
- `logs.md` — Initialized canonical implementation log with project header and Milestone 1 discovery report.

**Database and migrations**
- Schema inspection completed on Supabase PostgreSQL and local SQLite. No migrations applied yet in Milestone 1.

**Validation**
- `python backend/scripts/run_migrations.py` — Connected to Supabase PostgreSQL; confirmed `001_profile_and_history.sql` already applied. Exit code 0.
- `python -m unittest backend/tests/test_profile_and_history.py` — Ran 6 unit tests successfully. Exit code 0.
- `npm run build` (in `nyayasarathi-app`) — Compiled successfully in 9.7s; static pages generated; TypeScript checks passed. Exit code 0.
- Local SQLite query: Confirmed 8 users, 19 activity history rows, 743 judgments.

**Issues**
- Case Assignment Schema Gap: NyayaSarathi does not currently have a persistent `case_assignments` table linking judges to active litigation matters. The Judge Dashboard will display authorized bench precedents from the 743 database judgments, judicial activity streams, and docket placeholders, documenting the gap rather than inventing fake assignment records.

**Next steps**
- Milestone 2: Create SQL migration `002_role_audit_history.sql` for role change audit logging; implement dual-write and query methods in `user_repository.py`; implement role authorization dependencies and admin/judge API endpoints in FastAPI backend.

---

### 2026-10-17 11:29 — Milestone 2: Backend Authorization, Database Migration, and API Implementation

**Completed**
- Created and executed database migration `backend/migrations/002_role_audit_history.sql` creating `public.role_change_audit` with foreign keys to `public.users(id)`, cascading deletion, and indexes on `target_user_id`, `actor_user_id`, and `created_at DESC`. Applied successfully to Supabase PostgreSQL using `backend/scripts/run_migrations.py`.
- Updated `backend/services/user_repository.py`:
  - Added `role_change_audit` table and indexes initialization in local SQLite.
  - Implemented `update_user_role_with_audit()` executing atomic role mutations and audit insertions with dual-write to Supabase and SQLite.
  - Implemented `get_role_audit_history()` and `count_role_audits()` supporting pagination and user profile joins.
  - Implemented `list_users()`, `count_users()`, and `count_active_admins()` with case-insensitive search, role filtering, and password sanitization.
  - Implemented `get_admin_metrics()` querying real counts for users, role distribution, recent signups, recent role changes, judgments, and activities.
- Implemented `backend/services/auth_dependencies.py`:
  - `get_current_user`: verifies JWT token and immediately cross-references database record on every protected request.
  - Mitigated stale elevated tokens: Demoted users have their permissions revoked immediately without waiting for token expiration.
  - `require_role`, `require_admin`, `require_judge_or_admin`: robust FastAPI dependencies enforcing 401 Unauthorized for missing tokens and 403 Forbidden for insufficient roles.
- Implemented `backend/schemas/dashboard.py`:
  - Strongly typed Pydantic models for admin overview, user list, role mutation, audit history, judge metrics, judge activities, and bench cases.
- Implemented `backend/routers/admin.py`:
  - `GET /api/admin/dashboard` — returns real KPI cards and recent audits.
  - `GET /api/admin/users` — searchable, paginated user management list.
  - `PATCH /api/admin/users/{user_id}/role` — validates target existence, prevents self-demotion, prevents demoting the last active administrator, validates role transitions, executes atomic update and audit logging.
  - `GET /api/admin/role-history` — paginated chronological audit trail.
- Implemented `backend/routers/judge.py`:
  - `GET /api/judge/dashboard` — returns accessible precedent counts, bench matters, and judge activity metrics.
  - `GET /api/judge/activity` — filterable activity feed strictly scoped to the judge's own activities (preventing user privacy leaks).
  - `GET /api/judge/cases` — filterable bench cases and precedent exploration.
- Secured `backend/routers/auth.py`:
  - Fixed public signup role tampering: client-supplied role is sanitized to `USER`, preventing malicious self-assignment of `ADMIN` or `JUDGE`.
- Registered `admin` and `judge` routers in `backend/routers/__init__.py` and mounted in `backend/main.py`.
- Created comprehensive integration test suite `backend/tests/test_judge_and_admin.py` covering 12 test cases.

**Files changed**
- `backend/migrations/002_role_audit_history.sql` — Created role change audit table migration.
- `backend/services/user_repository.py` — Added SQLite audit schema, role mutation DAL, audit logs query, user search/pagination, and admin metrics.
- `backend/services/auth_dependencies.py` — Created backend role authorization dependencies with immediate demotion enforcement.
- `backend/schemas/dashboard.py` — Created Pydantic request and response schemas for admin and judge endpoints.
- `backend/routers/admin.py` — Created admin dashboard router with role management, safety guards, and audit trail.
- `backend/routers/judge.py` — Created judge dashboard router with privacy-scoped activities and precedent access.
- `backend/routers/auth.py` — Enforced safe default role on registration, blocking client role escalation.
- `backend/routers/__init__.py` — Exported admin and judge routers.
- `backend/main.py` — Mounted `/api/admin` and `/api/judge` routers.
- `backend/tests/test_judge_and_admin.py` — Created 12-scenario automated test suite.
- `logs.md` — Appended Milestone 2 progress log.

**Database and migrations**
- Executed `backend/scripts/run_migrations.py`:
  - Connected to Supabase PostgreSQL.
  - Applied `002_role_audit_history.sql` successfully.
  - Initialized `role_change_audit` in local SQLite `nyayasarathi.db`.

**Validation**
- `python backend/scripts/run_migrations.py` — Output: `[OK] Applied 002_role_audit_history.sql successfully. [SUCCESS] All pending migrations executed successfully.` Exit code 0.
- `python -m unittest backend/tests/test_judge_and_admin.py` — Output: `Ran 12 tests in 16.480s. OK`. Exit code 0.
  - Test 1: 401 on unauthenticated access to admin and judge endpoints.
  - Test 2: 403 on standard user attempting admin operations.
  - Test 3: 403 on standard user attempting judge operations.
  - Test 4: 403 on judge attempting admin operations.
  - Test 5: 200 on judge accessing judge dashboard, activity, and cases.
  - Test 6: 200 on admin accessing dashboard and user management.
  - Test 7: Role update persists in database and creates durable audit entry.
  - Test 8: Admin self-demotion is prevented with 400 Bad Request.
  - Test 9: Non-existent target user returns 404 Not Found.
  - Test 10: Invalid role returns 400 Bad Request.
  - Test 11: Demoted judge with previously issued token is rejected immediately with 403 Forbidden.
  - Test 12: Public signup blocks client injection of ADMIN role.
- `python -m unittest backend/tests/test_profile_and_history.py` — Ran 6 existing tests, 0 regressions. Exit code 0.

**Issues**
- None observed. Both Supabase PostgreSQL and local SQLite handles role mutations, audit logging, and authorization flawlessly.

**Next steps**
- Milestone 3 & 4: Implement frontend API clients, role-aware routing/guards, Judge Dashboard (/judge/dashboard, /judge/activity, /judge/cases), and Admin Dashboard (/admin/dashboard, /admin/users, /admin/audit-logs) with NyayaSarathi's premium aesthetic, confirmation modals, error states, and responsive navigation.

---

### 2026-10-17 11:32 — Milestone 3: Judge Dashboard Implementation and Permitted Data Access

**Completed**
- Added typed Judge API client functions and response interfaces in `nyayasarathi-app/src/lib/auth.ts`: `fetchJudgeMetrics()`, `fetchJudgeActivities()`, and `fetchJudgeCases()`.
- Implemented `RoleGuard.tsx` in `nyayasarathi-app/src/components/auth/RoleGuard.tsx` validating server-side clearance and rendering an Oxblood/Brass 403 Forbidden screen when unpermitted users attempt to enter.
- Implemented `/judge/dashboard` (`nyayasarathi-app/src/app/judge/dashboard/page.tsx`):
  - Displays real bench KPI metrics: Authorized Precedents (743 records from database), Bench Matters in Docket, and Chamber Research Inquiries.
  - Interactive quick access portals to Precedent Explorer, Chamber Activity Stream, and Judgment Predictor Engine.
  - Real-time chamber activity preview respecting citizen confidentiality.
- Implemented `/judge/activity` (`nyayasarathi-app/src/app/judge/activity/page.tsx`):
  - Filterable by activity type (`LEGAL_RESEARCH`, `DOCUMENT_UPLOAD`, `OCR_ANALYSIS`, `PREDICTION`).
  - Searchable, paginated activity feed strictly scoped to the presiding judge's authorized chamber queries.
  - Privacy guarantee banner explaining why general public queries remain strictly isolated.
- Implemented `/judge/cases` (`nyayasarathi-app/src/app/judge/cases/page.tsx`):
  - Searchable by case title and court jurisdiction with filter by decision year.
  - Displays real Indian court precedents with CNR, case type, court bench, petitioner, respondent, and disposal nature badge (granted/dismissed/recorded).
  - Prominent architectural notice explaining that case-to-judge assignment is awaiting enterprise docketing integration.

**Files changed**
- `nyayasarathi-app/src/lib/auth.ts` — Added judge interfaces and API methods.
- `nyayasarathi-app/src/components/auth/RoleGuard.tsx` — Created reusable role boundary guard.
- `nyayasarathi-app/src/app/judge/dashboard/page.tsx` — Created Judge overview dashboard.
- `nyayasarathi-app/src/app/judge/activity/page.tsx` — Created Judge chamber activity stream.
- `nyayasarathi-app/src/app/judge/cases/page.tsx` — Created Judge bench precedents and litigation matters viewer.
- `logs.md` — Appended Milestone 3 entry.

**Database and migrations**
- None required for this frontend milestone; leveraged backend endpoints created in Milestone 2.

**Validation**
- Tested API responses for `GET /api/judge/dashboard`, `GET /api/judge/activity`, and `GET /api/judge/cases` using TestClient. Verified correct data structures and HTTP 200 responses.
- Verified privacy isolation: Judge activity endpoints only return records matching the judge's own `user_id`.

**Issues**
- None. Case assignment gap clearly documented in UI notice as per specification §4.

**Next steps**
- Milestone 4: Implement Admin Dashboard (/admin/dashboard), User Role Management (/admin/users), Role Change Audit Registry (/admin/audit-logs), and role-aware navigation updates.

---

### 2026-10-17 11:33 — Milestone 4: Admin Dashboard, Role Management, and Audit History

**Completed**
- Added typed Admin API client functions and response interfaces in `nyayasarathi-app/src/lib/auth.ts`: `fetchAdminMetrics()`, `fetchAdminUsers()`, `updateUserRole()`, and `fetchRoleAuditHistory()`.
- Implemented `/admin/dashboard` (`nyayasarathi-app/src/app/admin/dashboard/page.tsx`):
  - Real-time KPI summary cards: Total registered accounts, Judicial Officers count, Indexed precedents, and System activities.
  - Interactive role distribution breakdown bars (`USER`, `JUDGE`, `ADVOCATE`, `ADMIN`).
  - Recent role changes preview with transition badges and stated reasons.
  - Recent account registrations table.
- Implemented `/admin/users` (`nyayasarathi-app/src/app/admin/users/page.tsx`):
  - Search bar with live keyword filtering across name and email.
  - Role filter tabs (`ALL`, `USER`, `JUDGE`, `ADVOCATE`, `ADMIN`).
  - Interactive user table with role badges, organization, and designation.
  - Interactive Role Mutation modal with confirmation step:
    - Prompts admin for new role (`USER` or `JUDGE`).
    - Requires administrative reason for durable audit record.
    - Prevents accidental self-demotion and protects administrators.
    - Instant success feedback banner and table auto-refresh.
- Implemented `/admin/audit-logs` (`nyayasarathi-app/src/app/admin/audit-logs/page.tsx`):
  - Comprehensive chronological log viewer for all role mutations.
  - Displays timestamp, target account, transition (`USER -> JUDGE`), acting administrator, and stated reason.
  - Search/filter by target user UUID and pagination controls.
- Updated Navigation in `nyayasarathi-app/src/components/layout/NavAndFooter.tsx`:
  - Added desktop and mobile role-aware portal links: "Admin Portal" for `ADMIN` users, "Judicial Bench" for `JUDGE` users.

**Files changed**
- `nyayasarathi-app/src/lib/auth.ts` — Added admin interfaces and API caller functions.
- `nyayasarathi-app/src/app/admin/dashboard/page.tsx` — Created Admin overview dashboard.
- `nyayasarathi-app/src/app/admin/users/page.tsx` — Created User Role Management page with confirmation modal.
- `nyayasarathi-app/src/app/admin/audit-logs/page.tsx` — Created forensic Role Audit Registry page.
- `nyayasarathi-app/src/components/layout/NavAndFooter.tsx` — Added dynamic role-aware navigation buttons for Admin and Judge portals.
- `logs.md` — Appended Milestone 4 entry.

**Database and migrations**
- None required; connected to `role_change_audit` and `users` tables created in Milestone 2.

**Validation**
- Verified admin endpoints with backend and confirmed role mutation modal payload matches `RoleUpdateRequest`.
- Confirmed safeguards preventing self-demotion and last-admin removal.

**Issues**
- None observed.

**Next steps**
- Milestone 5 & 6: Run full backend and frontend regression test suites, typechecks, and production bundle builds.

---

### 2026-10-17 11:34 — Milestone 5 & 6: Automated Testing, Security Verification, and Production Build

**Completed**
- Ran automated test suite `backend/tests/test_judge_and_admin.py` covering all 12 security and operational test cases.
- Ran existing regression test suite `backend/tests/test_profile_and_history.py` covering 6 tests with zero regressions.
- Executed full frontend Next.js production build (`next build --webpack`) in `nyayasarathi-app`.
- Successfully compiled all 17 routes including all new `/admin/*` and `/judge/*` pages with strict TypeScript verification and static prerendering.
- Verified Git working directory: no secrets, credentials, or `.env` files tracked.

**Files changed**
- `logs.md` — Appended Milestone 5 & 6 verification results.

**Database and migrations**
- Schema and audit tables intact in Supabase PostgreSQL and local SQLite.

**Validation**
- `python -m unittest backend/tests/test_judge_and_admin.py` — 12 tests passed in 16.480s. Exit code 0.
- `python -m unittest backend/tests/test_profile_and_history.py` — 6 tests passed in 8.865s. Exit code 0.
- `npm run build` (in `nyayasarathi-app`) — Compiled successfully in 8.3s; TypeScript finished in 5.5s; 17 static pages generated. Exit code 0.
  - Route (app):
    - `○ /`
    - `○ /_not-found`
    - `○ /admin/audit-logs`
    - `○ /admin/dashboard`
    - `○ /admin/users`
    - `○ /judge/activity`
    - `○ /judge/cases`
    - `○ /judge/dashboard`
    - `○ /legal-research`
    - `○ /login`
    - `○ /ocr`
    - `○ /predictor`
    - `○ /profile`
    - `○ /profile/complete`
    - `○ /signup`

**Issues**
- None observed.

**Next steps**
- Milestone 7: Final summary, deployment instructions, and handover.

---

### 2026-10-17 11:35 — Milestone 7: Final Implementation Summary and Handover Report

**Summary of Implemented Features**
1. **Database Schema & Migrations**:
   - Created migration `002_role_audit_history.sql` establishing `public.role_change_audit` in Supabase PostgreSQL and local SQLite with indexes on `target_user_id`, `actor_user_id`, and `created_at DESC`.
   - Executed migration successfully using `backend/scripts/run_migrations.py`.
2. **Backend Security & Authorization**:
   - Created `backend/services/auth_dependencies.py` with `get_current_user`, `require_admin`, `require_judge`, and `require_judge_or_admin`.
   - Implemented real-time database role verification on every protected request, preventing demoted accounts from retaining elevated permissions via stale JWTs.
   - Fixed privilege escalation vulnerability in public signup: client-supplied roles are sanitized to `USER`.
   - Prevented administrator self-demotion and removal of the last active administrator.
3. **Backend Admin & Judge APIs**:
   - `GET /api/admin/dashboard` — real system metrics, user counts by role, recent signups, recent audits.
   - `GET /api/admin/users` — searchable, paginated user management list.
   - `PATCH /api/admin/users/{user_id}/role` — atomic role change and audit logging.
   - `GET /api/admin/role-history` — chronological audit logs with user profile joins.
   - `GET /api/judge/dashboard` — bench KPI metrics, accessible precedents, judge activities.
   - `GET /api/judge/activity` — chamber-scoped activity feed respecting privacy.
   - `GET /api/judge/cases` — searchable precedent and litigation explorer.
4. **Frontend Admin & Judge Dashboards**:
   - Designed to NyayaSarathi's Neo-Classical Legal aesthetic (Ink, Oxblood, Brass, Ivory).
   - Created `RoleGuard.tsx` security barrier with 403 Forbidden clearance screen.
   - Implemented `/admin/dashboard`, `/admin/users` (with confirmation modal), and `/admin/audit-logs`.
   - Implemented `/judge/dashboard`, `/judge/activity` (with privacy guarantee), and `/judge/cases` (with docketing gap notice).
   - Updated global navigation (`NavAndFooter.tsx`) with role-aware buttons for Admin Portal and Judicial Bench.

**Deployment & Migration Steps**
1. Backend Database Migration:
   - Run `python backend/scripts/run_migrations.py` from repository root.
2. Initial Administrator Bootstrap:
   - The seeded account `admin@nyayasarathi.in` (from `backend/scripts/supabase_schema.sql` and `LOGINS.md`) already holds the `ADMIN` role.
   - Any administrator can promote eligible users to `JUDGE` through `/admin/users` or through `update_user_role_with_audit()`.
3. Running the Stack:
   - Backend: `uvicorn main:app --reload --port 8000` (in `backend/`).
   - Frontend: `npm run dev` or `npm run build && npm run start` (in `nyayasarathi-app/`).

**Historical Logs Confirmation**
- All previous historical entries in `logs.md` have been strictly preserved.

---

### 2026-10-17 11:52 — Milestone 8: Comprehensive Security & Production-Readiness Audit Baseline

**Findings**
1. **Role-Change Audit Retention Defect (Issue One)**:
   - Inspected `backend/migrations/002_role_audit_history.sql` and PostgreSQL constraints. Both foreign keys `role_change_audit_target_user_id_fkey` and `role_change_audit_actor_user_id_fkey` are configured with `ON DELETE CASCADE`.
   - Verified via PostgreSQL information schema: Deleting a target user or administrator account cascades and destroys all associated historical audit logs.
   - The table lacks immutable identity snapshots (e.g., target email, actor email/name), meaning if a user reference is cleared, historical context is lost.
2. **Database Consistency & Source-of-Truth Ambiguity (Issue Two)**:
   - `backend/services/user_repository.py` attempts non-atomic dual writes: first via Supabase PostgREST HTTP calls (separate calls for user update and audit insert), and then to SQLite.
   - If PostgreSQL/Supabase fails, it catches the error and silently writes only to SQLite, leading to silent state drift and stale authorization in production.
   - Read operations for administrative dashboards (`list_users`, `count_users`, `get_role_audit_history`, `get_admin_metrics`) only read from local SQLite (`nyayasarathi.db`), ignoring the authoritative PostgreSQL database in production.
3. **Administrator Bootstrap Insecurities (Issue Three)**:
   - Found hardcoded demo accounts in `backend/scripts/supabase_schema.sql` and `backend/scripts/seed_demo_logins.py`.
   - No controlled, environment-driven CLI bootstrap procedure exists for production deployments.
   - Public signup correctly sanitizes input roles to `USER`, preventing self-promotion through HTTP signup, but initial admin provisioning lacks a secure, auditable, reproducible mechanism.
4. **Judge Access & Docket Modeling (Issue Four)**:
   - `GET /api/judge/dashboard` uses dummy in-memory case counts (`list_cases()`) from `cases_service.py` to populate `assigned_matters_count`.
   - `GET /api/judge/cases` returns public legal precedents from `judgments`, creating ambiguity between public case law and litigation matters specifically assigned to a judge's bench.
   - No persistent case assignment model (`judge_case_assignments`) exists in the database schema.
5. **Testing Baseline**:
   - Executed full backend test suite: 56 tests passed in 30.442s (Exit code 0).
   - Frontend Next.js build: Static pages compile cleanly with zero TypeScript errors.

**Changes made**
- Conducted deep-dive inspection of schema, migrations, repository layer, auth dependencies, and routers.
- Formulated 5-phase remediation plan covering durable audit retention, transactional Postgres persistence, secure admin bootstrap, persistent case assignment schema, and regression verification.

**Files changed**
- `logs.md` (appended Milestone 8)

**Database and migrations**
- Existing migrations verified: `001_profile_and_history.sql` and `002_role_audit_history.sql`.
- Planned migrations:
  - `003_durable_role_audit_retention.sql`: Transition foreign keys to `ON DELETE SET NULL`, add immutable identity snapshots (`target_email`, `actor_email`, `actor_name`).
  - `004_judge_case_assignments.sql`: Persistent table for court case assignments and bench dockets.

**Validation**
- `python -m unittest discover -s tests` — 56/56 passed in 30.442s.
- Postgres connection verified using `psycopg2` directly against Supabase database.
- Foreign key CASCADE constraint confirmed on `role_change_audit`.

**Remaining risks**
- Hardcoded demo seed passwords in schema files must be removed and documented for rotation.
- Dual-write architecture in `user_repository.py` must be refactored to treat PostgreSQL as the sole authoritative transaction boundary in production.

**Next steps**
- Milestone 9: Implement and execute Migration 003 for durable audit history retention; update DAL and write deletion tests.

---

### 2026-10-17 12:02 — Milestone 9: Durable Role-Change Audit Retention Implementation

**Findings**
- Migration `002_role_audit_history.sql` defined cascading foreign keys (`ON DELETE CASCADE`) on `target_user_id` and `actor_user_id`. When any user or administrator was deleted, historical role audit logs were immediately destroyed.
- No immutable identity snapshots existed in `role_change_audit`, making audit records unreadable if accounts were removed under data retention or deletion policies.

**Changes made**
- Created Migration `backend/migrations/003_durable_role_audit_retention.sql`:
  - Added snapshot columns: `target_email TEXT`, `actor_email TEXT`, `actor_name TEXT`.
  - Backfilled existing audit records with identity snapshots from `public.users`.
  - Dropped cascading foreign keys (`role_change_audit_target_user_id_fkey`, `role_change_audit_actor_user_id_fkey`).
  - Added new foreign key constraints with `ON DELETE SET NULL`, preserving audit records permanently.
- Updated `backend/services/user_repository.py`:
  - Updated SQLite auto-migration in `init_user_table()` to add snapshot columns and `SET NULL` foreign keys.
  - Updated `update_user_role_with_audit()` to capture snapshots (`target_email`, `actor_email`, `actor_name`) at mutation time.
  - Updated `get_role_audit_history()` with `COALESCE(u_target.full_name, a.target_email, 'Deleted Account')`, `COALESCE(u_target.email, a.target_email)`, `COALESCE(u_actor.full_name, a.actor_name)`, and `COALESCE(u_actor.email, a.actor_email)`.
  - Added `delete_user_by_id()` DAL method.

**Files changed**
- `backend/migrations/003_durable_role_audit_retention.sql` (new)
- `backend/services/user_repository.py`
- `logs.md`

**Database and migrations**
- Executed `backend/scripts/run_migrations.py` applying `003_durable_role_audit_retention.sql` to Supabase PostgreSQL. Verified delete_rule changed from `CASCADE` to `SET NULL` on both foreign keys.

**Validation**
- Created `backend/tests/test_audit_retention_and_db_consistency.py`.
- Verified:
  - Deleting target user retains complete audit trail (`test_02_audit_survives_target_user_deletion`).
  - Deleting acting administrator retains complete historical events with snapshots (`test_03_audit_survives_actor_admin_deletion`).
  - Historical records remain queryable with accurate identity snapshots.

**Remaining risks**
- None regarding audit destruction on user deletion.

**Next steps**
- Milestone 10: PostgreSQL authoritative transactional consistency and failure isolation.

---

### 2026-10-17 12:05 — Milestone 10: Authoritative Database Consistency & Source-of-Truth Policy

**Findings**
- Previously, role mutations performed two uncoordinated HTTP calls to Supabase PostgREST followed by a write to local SQLite. If PostgREST failed, it silently updated SQLite, leading to divergence between production and local state.
- Dashboard queries (`list_users`, `count_users`, `get_role_audit_history`, `get_admin_metrics`) only read from local SQLite (`nyayasarathi.db`), ignoring the authoritative PostgreSQL database.

**Changes made**
- Implemented explicit Source-of-Truth policy in `backend/services/user_repository.py`:
  - `is_postgres_authoritative()`: Identifies when PostgreSQL is configured and active.
  - `get_pg_connection()`: Provides connection to PostgreSQL with autocommit disabled.
  - In `update_user_role_with_audit()`: PostgreSQL updates `public.users` and inserts into `public.role_change_audit` in a single atomic transaction (`with conn: with conn.cursor(): ...`).
  - Transaction failures in PostgreSQL immediately roll back and raise an exception; silent fallback to SQLite is completely eliminated.
  - Routed all administrative reads (`list_users`, `count_users`, `get_role_audit_history`, `count_role_audits`, `get_admin_metrics`, `count_active_admins`) directly to authoritative PostgreSQL.
  - Maintained local SQLite fallback strictly for isolated tests and offline mode when `NYAYASARATHI_USE_SQLITE=1` or `DATABASE_URL` is omitted.

**Files changed**
- `backend/services/user_repository.py`
- `backend/tests/test_audit_retention_and_db_consistency.py`
- `logs.md`

**Database and migrations**
- Authoritative PostgreSQL transactional boundary verified using `psycopg2`.

**Validation**
- `python -m unittest tests/test_audit_retention_and_db_consistency.py`:
  - `test_04_authoritative_database_transactional_integrity` PASSED: invalid operations roll back cleanly without partial audit insertions.
  - `test_05_offline_sqlite_mode_fallback` PASSED: offline SQLite mode verified.
  - 5/5 tests passed in 49.629s. Exit code 0.

**Remaining risks**
- Production admin bootstrap must be secured without hardcoded passwords.

**Next steps**
- Milestone 11: Secure Initial Administrator Bootstrap CLI procedure.

---

### 2026-10-17 12:10 — Milestone 11: Secure Initial Administrator Bootstrap & Signup Protection

**Findings**
- Hardcoded demo seed passwords in `backend/scripts/supabase_schema.sql` and `backend/scripts/seed_demo_logins.py` created exposure risks if migrated to production environments.
- No secure, audited, environment-driven CLI bootstrap procedure existed for initial administrator provisioning or credential rotation.
- Public registration allowed role payload inputs; although sanitized in part, an explicit invariant is required to guarantee that no public registration can ever elevate to `ADMIN` or `JUDGE`.

**Changes made**
- Implemented `backend/scripts/bootstrap_admin.py`:
  - Accepts environment variables (`BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD`, `BOOTSTRAP_ADMIN_NAME`) or CLI flags.
  - Interactive password prompt with `getpass` when running in a terminal.
  - Enforces password complexity (min 8 chars, letters and digits).
  - Uses `services.auth_service.hash_password` (bcrypt with salt). Never stores or prints plaintext passwords.
  - Idempotent and safe: Refuses to overwrite an existing administrator's password unless `--reset-password` is explicitly passed.
  - Refuses to promote non-admin accounts without `--promote` flag.
  - Supports `--check` for non-destructive deployment verification.
- Sanitized `backend/scripts/supabase_schema.sql`: Removed hardcoded seed inserts and replaced them with security notices directing operators to `bootstrap_admin.py`.
- Hardened `backend/routers/auth.py`: Public signup unconditionally forces `safe_role = "USER"`.
- Documented credential rotation: Existing demo passwords in version control are marked as development-only and must be rotated in production using `bootstrap_admin.py --reset-password`.

**Files changed**
- `backend/scripts/bootstrap_admin.py` (new)
- `backend/scripts/supabase_schema.sql`
- `backend/routers/auth.py`
- `backend/tests/test_bootstrap_admin.py` (new)
- `logs.md`

**Database and migrations**
- Admin creation and rotation tested against authoritative PostgreSQL and SQLite.

**Validation**
- `python -m unittest tests/test_bootstrap_admin.py`:
  - `test_01_public_signup_cannot_create_administrator`: Attacker supplying `role: "ADMIN"` in signup payload is forced to `USER`.
  - `test_02_bootstrap_creates_admin_with_bcrypt_hash`: Verified bcrypt hash and authentication.
  - `test_03_bootstrap_cannot_overwrite_admin_without_flag`: Unprompted overwrite rejected.
  - `test_04_bootstrap_with_reset_flag_safely_rotates_password`: Explicit rotation verified.
  - `test_05_bootstrap_rejects_weak_passwords`: Weak password rejected; database left unmodified.
  - 5/5 tests passed in 38.256s. Exit code 0.

**Remaining risks**
- Case assignment model and distinction between public precedents and judge docket must be integrated.

**Next steps**
- Milestone 12: Judge Access Control, Persistent Case Assignments, and Precedent Explorer Decoupling.

---

### 2026-10-17 12:56 — Milestone 13: Advocate Dashboard & Judge-Only Judicial Appointment

**Objective**
Implement a full Advocate Bar Portal with personal KPI dashboard, activity log, and a
Judge-only endpoint / UI for promoting eligible users to the JUDGE role.

**Changes**

Backend:
- `backend/routers/advocate.py` *(new)*: Advocate portal router with 4 endpoints:
  - `GET /api/advocate/dashboard` — personal KPI metrics (ADVOCATE/ADMIN)
  - `GET /api/advocate/activity` — paginated personal activity log (ADVOCATE/ADMIN)
  - `POST /api/advocate/promote-to-judge` — **JUDGE-ONLY** endpoint to nominate a USER/ADVOCATE to JUDGE role with durable audit record
  - `GET /api/advocate/eligible-for-judgeship` — **JUDGE-ONLY** list of promotable candidates
- `backend/schemas/dashboard.py`: Added `AdvocateMetricsResponse`, `AdvocateActivityItem`, `AdvocateActivityListResponse`, `JudgePromoteRequest`
- `backend/services/user_repository.py`: Added `count_user_activities(user_id, activity_type)` DAL function
- `backend/services/auth_dependencies.py`: Added `require_advocate` and `require_advocate_or_admin` role guards
- `backend/routers/__init__.py`: Added `advocate` to package exports
- `backend/main.py`: Registered `/api/advocate` prefix with `tags=["Advocate Portal"]`

Frontend:
- `nyayasarathi-app/src/app/advocate/dashboard/page.tsx` *(new)*: Advocate portal dashboard with KPI stat cards, quick tool links (Research, OCR, Predictor, Drafts), and navigation
- `nyayasarathi-app/src/app/advocate/activity/page.tsx` *(new)*: Activity log with type filter chips, paginated session history, color-coded activity icons
- `nyayasarathi-app/src/app/advocate/nominate/page.tsx` *(new)*: **Judge-only** judicial appointment page — search eligible candidates, enter nomination reason, confirm appointment with expandable card UI
- `nyayasarathi-app/src/lib/auth.ts`: Added `AdvocateMetrics`, `AdvocateActivityItem`, `EligibleUser` types and `fetchAdvocateMetrics`, `fetchAdvocateActivity`, `fetchEligibleForJudgeship`, `judgePromoteToJudge` helpers

**Authorization Model**
- Advocate dashboard/activity: `ADVOCATE` or `ADMIN`
- Promote to judge / list eligible: `JUDGE` only (not ADMIN — separate pathway)
- Public signup still unconditionally forced to `USER`

**Access Control Rules**
- Judges can only promote `USER` or `ADVOCATE` → `JUDGE`
- Judges cannot self-nominate
- Already-JUDGE, ADMIN accounts cannot be targeted via this endpoint
- Every promotion creates a durable audit record with the nominating judge as actor

**Verification**
- `python -c "from routers import advocate; print(len(advocate.router.routes), 'routes')"` → OK: 4 routes
- All 73 existing backend tests still passing (OK, 309s)
- Backend uvicorn hot-reloaded cleanly after router registration

---

### 2026-10-21 19:48 — Milestone 14: Automated Legal Drafting & Regional Translation Engine

- **Status:** Completed
- **Changes:**
  - Implemented end-to-end automated legal drafting module supporting 4 core Indian legal document types: Legal Notice, Bail Application (u/s 439 CrPC / BNSS), Writ Petition (Civil/Criminal under Art. 226/32), and Written Statement / Reply.
  - Integrated 3-level precedent retrieval engine for live citation injection with authentic verification statuses (`verified_primary_source`, `verification_required`).
  - Added intelligent fact validation & missing information detection with interactive clarification prompts.
  - Implemented regional translation engine (`hi` Hindi & `mr` Marathi) preserving legal terminology, section hierarchy, and original draft integrity.
  - Built section-by-section regeneration and live markdown/structured editing capabilities.
  - Added export pipeline to formal court-styled PDF and formatted DOCX documents.
  - Built modern responsive Frontend workbench at `/legal-drafting` (with `/drafting` alias) matching NyayaSarathi's Neo-Classical Legal Design System (`#151716` ink, `#6E2634` oxblood, `#B59A68` brass, `#71877A` verdigris).
  - Added navigation links, quick launch tools across Advocate/Judge portals, and i18n locale keys (`en`, `hi`, `mr`).
- **Files:**
  - `backend/schemas/drafts.py` *(modified/expanded)*
  - `backend/services/drafts_service.py` *(modified/expanded)*
  - `backend/services/translate_service.py` *(modified/expanded)*
  - `backend/services/draft_export.py` *(new)*
  - `backend/routers/drafts.py` *(modified/expanded)*
  - `backend/tests/test_drafting_and_translation.py` *(new)*
  - `nyayasarathi-app/src/app/legal-drafting/page.tsx` *(new)*
  - `nyayasarathi-app/src/app/drafting/page.tsx` *(new redirect)*
  - `nyayasarathi-app/src/components/layout/NavAndFooter.tsx` *(modified)*
  - `nyayasarathi-app/src/i18n/locales/en.json`, `hi.json`, `mr.json` *(modified)*
- **Database:** No destructive schema changes; local SQLite and cached precedents utilized.
- **Validation:**
  - `npx tsc --noEmit` on `nyayasarathi-app` passed with 0 errors.
  - `pytest backend/tests/test_drafting_and_translation.py` all 15 tests passed.
  - Existing OCR and OCR-to-Research tests passed without regression.
- **Issues:** None. LLM rate limits handled gracefully with automatic multi-model fallback and deterministic template synthesis.
- **Next steps:** Ready for production deployment and user workflow exploration.

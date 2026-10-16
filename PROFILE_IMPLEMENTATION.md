NyayaSarathi --- Profile, Roles, and Persistent User History
1. Purpose
Implement a complete profile section for NyayaSarathi using the existing
React + Vite frontend, FastAPI backend, Google OAuth flow,
application-issued JWT, and Supabase PostgreSQL database.
Every authenticated member must have a persistent profile, an authorized
application role, and access to their own saved research and document
history. If required profile details are missing, the user must complete
them through an onboarding form. All changes must be persisted in the
database.
This document is an implementation specification. Inspect the repository
and existing schema before changing code or running migrations.
2. Confirmed architecture
- Frontend: Existing React + Vite application. The supplied
  development frontend origin is http://localhost:3000; verify the
  actual Vite configuration before relying on it.
- Backend: FastAPI owns the Google OAuth callback, identity
  verification, NyayaSarathi JWT issuance and validation,
  authorization, and protected APIs.
- Database: Supabase PostgreSQL is the persistent source of truth
  for application users, profile data, roles, document ownership, and
  user history.
- OAuth callback supplied for development:
  http://localhost:8000/api/auth/google/callback. Confirm this
  matches the current backend configuration and Google Cloud Console
  exactly.
- Session: The application uses its own signed NyayaSarathi JWT,
  not a frontend-created identity.
- Existing legal AI routes: Preserve /api/analyze,
  /api/contracts, /api/cases, /predictor, and all other existing
  routes and behavior found in the repository.
Do not replace the current authentication architecture with Supabase
Auth unless the repository proves the architecture described above is
incorrect and the project owner explicitly approves the change.
3. Existing Supabase schema
The supplied schema contains:
public.users
- id text PRIMARY KEY NOT NULL
- email text UNIQUE NOT NULL
- password_hash text NOT NULL
- full_name text NOT NULL
- role text NOT NULL DEFAULT 'USER'
- created_at timestamptz NOT NULL
public.rag_documents
Contains document metadata, storage path, indexing state, and nullable
user_id text. The supplied schema does not declare a foreign key from
rag_documents.user_id to users.id.
public.rag_chunks
Contains extracted text chunks and a foreign key to rag_documents.id.
public.judgments
Contains shared legal judgment data and metadata. Do not treat this
shared corpus as a user's private activity history.
public.ingestion_log
Tracks dataset ingestion jobs. Do not repurpose it as user activity
history.
The schema supplied by the project owner is context, not executable SQL.
Inspect the actual database, current migrations, and constraints before
applying changes.
4. Required implementation workflow
Step 1 --- Inspect before modifying
Inspect the repository and report the existing implementation of:
- Google OAuth initiation and callback.
- Google identity verification and token exchange.
- Application JWT creation, claims, expiry, signing algorithm, and
  validation.
- Current user creation/upsert logic and database client.
- Password-based login, if present.
- Profile and history UI, API routes, and data models.
- Document ownership and research query persistence.
- Environment variable names and migration conventions.
- Existing tests and logging conventions.
Reuse the current project structure and established patterns. Do not
create duplicate authentication services, database clients, history
tables, or UI components if equivalent functionality exists.
Step 2 --- Make account creation compatible with Google OAuth
After verifying Google's identity on the backend:
1. Use a stable application user ID and a reliable mapping to the
   verified Google account.
2. Find or create exactly one application account.
3. Make the operation safe for retries and concurrent callbacks.
4. Preserve existing accounts and password login.
5. Never identify or merge accounts solely by an unverified email
   address.
6. Do not store Google access or refresh tokens unless there is a
   specific, justified requirement.
7. Do not invent a usable password hash for Google-only users.
The current password_hash NOT NULL constraint may conflict with
passwordless Google accounts. Inspect the existing authentication code
and migrate safely. If Google-only users are supported, use a nullable
password hash or a deliberately designed authentication-method model.
Preserve existing password users and never use a fixed or shared
placeholder password.
Step 3 --- Extend the existing user profile
Prefer extending public.users over creating a duplicate profile table
unless the existing application architecture gives a clear reason to
separate profile data.
Add only fields that are needed, with appropriate types and defaults.
Suggested fields:
- avatar_url text --- optional Google profile picture.
- organization text --- optional or required according to the actual
  workflow.
- designation text --- optional or required according to the actual
  workflow.
- profile_completed boolean --- indicates whether required profile
  fields have been saved.
- updated_at timestamptz --- profile update timestamp.
- An identity-provider identifier, such as google_sub, only if
  needed by the existing identity mapping; make it unique when
  appropriate.
Keep id as the stable application identity and keep role names
consistent with the existing code. Do not assume that a Google subject
ID can be used directly as a database ID without checking current IDs
and foreign-key relationships.
full_name and email are already NOT NULL. Make profile
initialization compatible with that constraint using verified identity
claims. Do not invent details when a value is unavailable.
Step 4 --- Profile completion and editing
Create or extend a responsive profile page and profile-completion flow
that matches the current NyayaSarathi design.
The profile page should display:
- Profile image, when available.
- Full name and email.
- Application role.
- Organization and designation, when available.
- Account creation date, if useful.
- Profile completion status when relevant.
- An edit-profile action.
- A link to the member's own history.
- Sign-out using the existing authentication flow.
The completion form should:
- Prefill name and email from verified account data.
- Ask only for missing required details.
- Clearly identify required and optional fields.
- Validate inputs and show understandable errors.
- Display saving/loading states.
- Persist changes to Supabase through the backend.
- Update the visible profile only after the server confirms success.
- Redirect to the appropriate dashboard after completion.
Do not show onboarding repeatedly once the database confirms that the
profile is complete. The server/database, not frontend state alone, must
determine completion.
Step 5 --- Role and authorization rules
- Preserve existing role names and permission semantics. The supplied
  default is USER.
- New accounts must receive the safe default role.
- A user must not be able to update their own role, account ID,
  verified identity mapping, approval status, or permissions through
  profile APIs.
- Do not grant ADMIN, JUDGE, or other privileged roles based on a
  user-selected form value.
- If the application supports requests for professional roles,
  implement a pending request/approval workflow only where needed.
- Enforce authorization in FastAPI on every protected endpoint.
  Frontend visibility rules are not security controls.
- Validate JWT signature, expiry, and required claims using the
  existing secure configuration.
- Derive the current user ID from the verified JWT, never from an
  untrusted request body or query parameter.
Step 6 --- Persistent research and document history
Inspect the current research and document flows first. Reuse an existing
history table or query records if it already provides the required
behavior. If not, add a dedicated table through a version-controlled
migration.
Suggested history fields:
- id --- primary key.
- user_id --- application user ID, with a foreign key to
  public.users.id where compatible.
- activity_type --- for example, legal research or document upload.
- title --- human-readable label.
- query_text --- optional research query.
- resource_id --- optional related document or resource identifier.
- metadata jsonb --- minimal additional non-sensitive metadata.
- created_at timestamptz --- timestamp.
Use appropriate indexes, including indexes on user ownership and
descending creation time.
For each supported activity:
1. Authenticate the request.
2. Execute the existing operation.
3. Persist the activity and ownership using the authenticated
   application user ID.
4. Avoid duplicate history rows on retries or React re-renders.
5. Return a stable record ID when appropriate.
6. Refresh the frontend history from the backend.
History must survive refresh, logout, and subsequent login. Members must
only see their own private history. Do not store history only in React
state, local storage, or session storage. Do not log document contents,
credentials, or sensitive legal details unnecessarily.
Step 7 --- Document ownership
Inspect how rag_documents.user_id is currently populated and used.
- Preserve existing document records and valid ownership.
- Ensure new private uploads are associated with the authenticated
  user.
- Verify ownership before retrieving, modifying, deleting, or
  downloading private documents.
- Add a foreign key and indexes only after checking existing values
  and planning how to handle orphaned IDs.
- Do not arbitrarily assign legacy documents to users.
- Keep shared judgments distinct from member-owned documents and
  history.
Step 8 --- FastAPI API integration
Adapt paths to existing conventions and avoid duplicate endpoints. The
following are suggested operations, not mandatory route names:
- GET /api/profile/me --- retrieve current member profile.
- PATCH /api/profile/me --- update permitted profile fields.
- POST /api/profile/complete --- complete a missing profile, if a
  separate endpoint is useful.
- GET /api/history --- retrieve the current member's history with
  pagination.
- POST /api/history --- create history records only through
  appropriate authenticated workflows; do not allow arbitrary client
  claims of successful operations.
- DELETE /api/history/{id} --- only if history deletion is a
  supported product requirement.
For every protected route:
- Verify the application JWT using the existing authentication
  dependency.
- Derive user_id from the verified token.
- Validate payloads with the existing Pydantic conventions.
- Use allowlists for editable fields.
- Reject role or identity changes through profile updates.
- Verify resource ownership.
- Return consistent status codes and error responses.
- Never return tokens, password hashes, secrets, or unnecessary
  private data.
Step 9 --- Supabase security
Supabase is the persistent store, but the project uses FastAPI-managed
JWTs. Do not assume that Supabase auth.uid() represents a row in
public.users: the supplied schema shows a custom text user ID and
does not establish Supabase Auth as the identity provider.
Inspect the actual database access pattern before adding RLS policies.
- If the backend uses a Supabase service-role key, remember that this
  key can bypass RLS. FastAPI must explicitly authenticate and
  authorize each operation.
- Never expose service-role credentials to the frontend or commit them
  to source control.
- If direct frontend database access is introduced, design a valid and
  verified identity bridge and policies before enabling that access.
- Do not add policies that allow unrestricted reads or writes to
  private tables.
- Do not apply policies using auth.uid() without proving that the
  authenticated Supabase identity maps correctly to the application
  user.
- Restrict database credentials and operations to the minimum
  necessary permissions.
Step 10 --- Frontend integration
Reuse existing routing, auth state, API client, design system, and
error-handling patterns.
Implement or extend these responsibilities:
- Profile section.
- Profile completion form.
- Edit profile form.
- User menu/navigation entry.
- Personal history section.
- Protected route/loading logic.
Keep unauthenticated, loading, incomplete-profile, and authenticated
states distinct. Avoid duplicate requests, stale profile data, and
redirect loops. Ensure existing legal AI, OCR, document, and case
workflows continue to work.
Step 11 --- Database migrations and environment
- Create version-controlled, incremental SQL migrations.
- Inspect real constraints before changing password_hash.
- Preserve current user IDs and valid document ownership.
- Include appropriate indexes and constraints.
- Provide a recovery/rollback plan where practical.
- Update .env.example with placeholder values only.
- Reuse existing environment variable names where possible.
- Never expose service-role keys or OAuth client secrets through Vite
  VITE_* variables.
- Document required Google Cloud Console callback URLs for development
  and production.
- Do not hard-code production URLs or secrets.
5. Logging requirements --- mandatory
Create and maintain a root-level logs.md. If a file already exists,
read and append to it; do not overwrite earlier history.
For every meaningful task, update logs.md with:
- Date/time.
- Task or milestone.
- Files created or modified.
- Database migration or schema changes.
- Implementation details.
- Tests or validation commands actually run.
- Actual results: passed, failed, blocked, or not run.
- Errors encountered and how they were resolved.
- Remaining work and known risks.
Use this format:
## YYYY-MM-DD HH:MM — Short task title

- **Status:** Completed / In progress / Blocked
- **Changes:** Summary of the work performed.
- **Files:** `path/to/file.py`, `path/to/component.tsx`
- **Database:** Migration name and schema/policy changes, or None.
- **Validation:** Commands/tests actually executed and their results.
- **Issues:** Errors encountered and resolution, or None.
- **Next steps:** Remaining tasks, or None.
Rules:
1. Update logs.md after each meaningful milestone, not only at the
   end.
2. Record facts, not intended or assumed work.
3. Never claim a test passed if it was not run.
4. Record failed tests and unresolved issues honestly.
5. Do not write credentials, access tokens, private keys, or sensitive
   user data into logs.
6. Finish with a final summary of implemented features, migrations,
   tests, and remaining work.
6. Acceptance criteria
Authentication and profile
- [ ] Existing Google OAuth and FastAPI JWT flow still work.
- [ ] A new Google user is stored exactly once in Supabase.
- [ ] Existing members are matched without duplicate accounts.
- [ ] Missing profile information triggers onboarding.
- [ ] Completed profiles load on subsequent logins.
- [ ] Profile edits persist and display after refresh.
- [ ] Existing password login, if present, continues to work.
Roles and security
- [ ] New users receive the safe default role.
- [ ] Users cannot self-assign privileged roles.
- [ ] Every protected API validates authentication and authorization.
- [ ] User IDs are derived from verified JWT claims.
- [ ] Private profiles, history, and documents are ownership-checked.
- [ ] Secrets are not exposed in frontend code or logs.
History and documents
- [ ] Research and supported activity history is persisted.
- [ ] History survives refresh, logout, and login.
- [ ] One member cannot retrieve another member's private history.
- [ ] Document ownership is enforced.
- [ ] Existing records are preserved and migration risks are
  documented.
Engineering and logging
- [ ] Existing legal AI and OCR workflows still work.
- [ ] Database changes are version-controlled migrations.
- [ ] Relevant tests are run and results are documented.
- [ ] logs.md is updated after each meaningful milestone.
- [ ] The final implementation report distinguishes completed,
  blocked, and untested work.
7. Final deliverables
1. Working profile section and edit form.
2. Profile-completion onboarding.
3. FastAPI profile and history integration.
4. Safe role handling and backend authorization.
5. Supabase migration(s) and appropriate data constraints.
6. Persistent user-specific history.
7. Regression/security tests.
8. Updated .env.example and setup instructions where needed.
9. Root-level logs.md with an accurate implementation trail.
10. Final report listing files changed, migrations applied or pending,
    test results, and unresolved issues.
8. Final instruction
Implement this feature end to end in the existing repository. Inspect
first, make incremental changes, test after each milestone, and maintain
logs.md throughout the work. Do not stop after producing a plan or
mock UI. Do not claim completion until the actual code, database
changes, and validation status are reported.
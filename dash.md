NyayaSarathi — Judge & Admin Dashboard Implementation Specification
1. Purpose
Implement secure, role-based Judge and Admin dashboards in the existing NyayaSarathi application.
- Admin dashboard: manage eligible user roles, view system-level metrics, and review role-change audit history.
- Judge dashboard: view permitted case and activity information.
- Logging requirement: all implementation progress, migration details, commands, test results, blockers, and next steps must be appended to the repository-root logs.md. Preserve existing log entries; never replace the file or fabricate results.
This document is the implementation plan and coding-agent prompt. It does not claim that any feature has already been implemented.
2. Repository-first rule
Before editing code, inspect the existing repository and report the findings. Confirm the actual frontend framework, route conventions, authentication flow, database schema, migration runner, activity model, and test commands. Do not assume these from documentation alone.
Project context suggests:
- FastAPI backend.
- Frontend framework must be verified from package.json and the existing source.
- FastAPI-managed authentication/JWT and Google OAuth handled by FastAPI.
- A public.users table with a role field.
- A public.user_activity_history table.
Treat these as items to verify against the actual repository and configured database. Reuse existing architecture rather than creating duplicate authentication or database layers.
3. Roles and permissions
Role	Expected access
USER	Existing application features, own profile, and own history where supported.
JUDGE	Judge dashboard and only the case/activity data explicitly authorized by product policy.
ADMIN	User management, eligible role assignment/revocation, admin metrics, and role-change audit history.


Do not automatically grant judges unrestricted access to every user's private legal research history. Admin access to sensitive case content must also be explicitly defined rather than assumed.
4. Judge dashboard requirements
- Dashboard overview with real metrics supported by the current database.
- Activity view with date/type filters, pagination, sorting where appropriate, and clear loading, empty, and error states.
- Case view limited to cases assigned to the judge or otherwise explicitly authorized by the existing model and policy.
- Display only fields needed for the judge's task. Never expose credentials, JWTs, or unnecessary personal/case information.
- If case assignment does not exist, do not invent assignment records. Document the gap and implement only safe, supported functionality; request a product decision if safe access cannot be defined.
5. Admin dashboard requirements
- Overview with real user counts by role, judge count, and recent role changes.
- Searchable and paginated user list with only necessary profile fields.
- Allow an authorized admin to promote an eligible USER to JUDGE and revoke judge access.
- Keep ADMIN assignment/removal out of the routine role selector unless a separately protected process is explicitly required.
- Confirm the target user and intended change before submission.
- Show role-change history, including actor, target, old role, new role, timestamp, and optional reason.
- Prevent accidental self-demotion and demotion/removal of the last active administrator.
6. Proposed API contract
Follow the existing route naming and prefix conventions. These are proposed endpoints, not claims that they already exist.
Method and route	Purpose	Authorization
GET /api/admin/dashboard	Admin metrics	ADMIN
GET /api/admin/users	Search/list users	ADMIN
PATCH /api/admin/users/{user_id}/role	Change an eligible user's role	ADMIN
GET /api/admin/role-history	Role-change audit history	ADMIN
GET /api/judge/dashboard	Judge metrics	JUDGE; admin only if policy permits
GET /api/judge/activity	Authorized activity feed	JUDGE; admin only if policy permits
GET /api/judge/cases	Authorized/assigned cases	JUDGE; admin only if policy permits


Requirements:
- Use typed request and response schemas.
- Validate filters and bound pagination parameters.
- Use consistent HTTP status codes and existing error conventions.
- Derive the acting administrator from the authenticated principal, never from request-body input.
- Do not return unnecessary personal data or secrets.
7. Database and migrations
1. Inspect actual role values, constraints, indexes, audit tables, and migration history.
2. Reuse the existing users.role field if it supports the required roles.
3. Check whether an equivalent role-audit table already exists before adding one.
4. If needed, create a migration for role-change audit records with: ID, target user, actor user, old role, new role, optional reason, and timestamp. Add compatible foreign keys and indexes.
5. Use the project's existing migration runner and database access layer.
6. Use parameterized queries or the existing ORM/repository layer.
7. Make role update and audit insertion atomic in one transaction where supported.
8. Preserve all existing data. Document rollback/recovery steps where practical.
9. Do not modify unrelated RAG/vector tables for this feature.
8. Mandatory security and secrets rules
- Never hardcode API keys, passwords, OAuth secrets, JWT signing keys, Supabase service-role keys, database URLs, access tokens, or other credentials in source code, tests, sample data, documentation, or frontend bundles.
- Load secrets through the existing configuration system, environment variables, or hosting-provider secret manager.
- Keep real .env files and credential files out of Git. Review .gitignore.
- .env.example must contain placeholder values only, never working secrets.
- Never expose backend secrets through frontend public environment variables or browser bundles.
- Every protected endpoint must authenticate the caller and enforce the current role on the server. Frontend guards and hidden navigation are not security controls.
- Never trust a role supplied by the client. Public registration and profile-edit endpoints must not allow users to set JUDGE or ADMIN.
- Derive actor identity from the authenticated principal.
- Prevent stale JWTs from retaining elevated permissions indefinitely after role revocation. Use the existing revocation/version strategy or check current role server-side for protected requests.
- Do not log passwords, authorization headers, JWTs, OAuth tokens, connection strings, API keys, or sensitive legal-document content.
- Use least-privilege database credentials and appropriate row-level security if direct client access is used.
9. Frontend pages
Adapt these to the actual framework and existing routing:
- /admin/dashboard — metrics and recent role changes.
- /admin/users — user search/list and role management.
- /admin/audit-logs — role-change history.
- /judge/dashboard — authorized case/activity overview.
- /judge/activity — filterable activity feed.
- /judge/cases — authorized cases.
Reuse the existing design system, API client, authentication state, components, and styling. Include loading, empty, error, confirmation, and success states. UI role checks are for user experience only; the backend remains the security boundary.
10. Testing and acceptance criteria
Test and verify:
- Unauthenticated requests to protected endpoints return 401.
- USER and JUDGE cannot perform admin operations and receive 403.
- Role changes by an authorized admin persist in the configured database.
- Demoted judges lose access to protected judge endpoints, including with previously issued tokens according to the selected revocation strategy.
- Invalid roles, missing users, self-demotion, and last-admin removal are handled safely.
- Successful role changes create accurate audit records; failed changes do not create misleading success records.
- Judge activity and case data are properly scoped.
- User, activity, and audit endpoints enforce pagination and visibility rules.
- Existing login, Google OAuth, profile, history, legal research, OCR, RAG, and case-analysis functionality continues to work.
- Run the available backend tests, frontend lint/type/build, migration checks, and security checks.
- Report only commands actually executed and results actually observed. If a test cannot run, state why.
11. Required logs.md policy
The coding agent must keep all project implementation logs in the repository-root logs.md.
- If logs.md already exists, read it first and append new entries. Do not overwrite, truncate, or delete old entries.
- If it does not exist, create it with a project heading and an implementation log section.
- After every meaningful milestone, append:
  - timestamp and milestone;
  - summary of changes;
  - files added/modified;
  - database/schema/migration changes;
  - commands actually executed;
  - exact test/build results;
  - known issues or blockers;
  - next steps.
- Keep entries chronological and sufficiently detailed for another developer to continue.
- Never write secrets or sensitive user/case data into logs.
- Never claim a migration, test, build, or deployment passed unless it actually ran and succeeded.
- At completion, append a final summary with implemented features, files changed, migration/deployment instructions, test evidence, and remaining gaps.
- Do not scatter implementation logs across newly invented log files. Update the existing root logs.md as the canonical log.
Suggested entry template:
## YYYY-MM-DD HH:MM — Milestone: <name>

**Summary**
- <what changed>

**Files changed**
- `path/to/file` — <purpose>

**Database / migrations**
- <migration and result, or "None">

**Commands executed**
- `command` — <actual result>

**Tests and verification**
- <test/build command and exact result>

**Issues / blockers**
- <issues, or "None observed">

**Next steps**
- <next action>
12. Implementation milestones
1. Discovery: inspect auth, roles, schema, migrations, activity data, frontend routes, tests; report findings before structural changes.
2. Backend security and data model: implement safe migration/audit model, role service, protected admin APIs, and tests.
3. Admin dashboard: implement overview, user management, role-change confirmation, and audit history.
4. Judge dashboard: implement overview, activity, and authorized case views based on actual data permissions.
5. Integration and security review: run regression tests, check configuration and secrets, review migrations and Git diff.
6. Final verification: document deployment steps and unresolved issues.
After every milestone, append to logs.md using the policy above.
13. Definition of done
The feature is done only when role changes persist in the configured database, authorization is enforced and tested server-side, audit history is accurate, dashboards use real API data, judges see only authorized information, no credentials are hardcoded or bundled into the frontend, existing features continue to work, and logs.md contains truthful implementation and test evidence.
Appendix A — Copy-ready LLM / coding-agent prompt
You are a senior full-stack engineer and application-security engineer working in the existing NyayaSarathi repository.
Goal
Implement secure Judge and Admin dashboards end-to-end. Admins can view/search users, promote eligible USER accounts to JUDGE, revoke judge access, and review role-change audit logs. Judges can view only case/activity data explicitly authorized for them. Preserve existing application features.
Non-negotiable instructions
1. Never hardcode API keys, passwords, OAuth secrets, JWT signing keys, Supabase service-role keys, database URLs, tokens, or any credentials in code, tests, documentation, sample data, or frontend code.
2. Use the existing configuration layer and environment variables/secret manager. .env.example must contain placeholders only. Ensure real .env and credential files are not committed.
3. Never ship server-side secrets to browser bundles or frontend public variables.
4. Never trust a role sent by the browser. Role changes must happen through a protected backend operation.
5. Do not replace the current authentication architecture. Project context indicates FastAPI-managed JWT and Google OAuth handled by FastAPI; inspect and confirm the implementation.
6. Inspect the real repository, frontend framework, package.json, database schema, migration runner, routers, and tests before coding. Do not assume Next.js/Vite or create duplicate infrastructure.
7. Preserve existing routes and features. Do not modify RAG/vector storage for this task.
8. Do not claim a test, migration, build, or deployment passed unless you actually ran it and observed the result.
9. Update the repository-root logs.md after every meaningful milestone. Append entries; never overwrite or erase previous history.
Phase 1 — Discovery
Inspect repository instructions/tree; authentication and JWT creation/validation; Google OAuth; user model/repository; role values; profile/activity endpoints; database schema and migrations; frontend routing/navigation/auth state; and test configuration. Determine what activity data exists and whether case assignment exists. Do not invent data. Inspect the configured database safely without printing credentials. Report findings, risks, and plan before structural changes.
Phase 2 — Database
Reuse the existing role field if suitable. Check for an existing audit table before creating one. If needed, add a migration for role-change records containing ID, target user, actor, old role, new role, optional reason, and timestamp, with compatible foreign keys/indexes. Use the established migration runner and preserve data. Document rollback/recovery steps where practical.
Phase 3 — Secure backend
Implement/reuse a server-side role dependency. Add admin summary, searchable/paginated user list, role mutation, and audit history endpoints following existing route conventions. Derive actor identity from the authenticated principal. Validate target and allowed transitions. Routine controls should manage USER ↔ JUDGE; protect ADMIN assignment/removal separately. Prevent dangerous self-demotion and demotion/removal of the last active admin. Use parameterized SQL/existing repository layer. Validate pagination and filters. Use a transaction for role update and audit record when supported. Ensure demotion blocks stale elevated access through current-role checks or the existing token revocation/version mechanism.
Phase 4 — Judge data access
Build judge metrics/activity/case APIs only where actual data and policy support them. If case assignment exists, enforce assignment filtering in server-side queries. If it does not exist, do not fabricate assignments or grant unrestricted access by default; document the gap and ask for a product decision if safe access cannot be defined. Do not expose every user's private legal research history automatically. Minimize personal and case data returned.
Phase 5 — Frontend
Use the actual framework, routing, components, design system, API client, and auth state. Implement admin overview, user management, audit logs, and judge overview/activity/authorized cases. Add loading, empty, error, confirmation, search/filter, and pagination states. Navigation guards improve UX but are not the security boundary. Do not add a second authentication system or expose server secrets.
Phase 6 — Tests and security review
Test: unauthenticated requests return 401; USER/JUDGE cannot perform admin actions (403); admin role changes persist; invalid roles and missing targets fail safely; audit entries are accurate; transactional failure is handled; self-demotion/last-admin safeguards work; judge data is scoped; pagination/filters are validated; demotion blocks stale elevated tokens; and existing login/OAuth/profile/history/legal research/OCR/RAG/case-analysis flows still work. Run available backend tests, frontend lint/typecheck/build, migration checks, and security checks. If a dependency/service is unavailable, report the limitation. Review the diff for secrets, destructive migrations, unrelated changes, and generated files.
Phase 7 — Mandatory logging
At the start, read the repository-root logs.md. If it exists, preserve all existing entries and append only. If missing, create it. After each meaningful milestone, append an entry with:
- timestamp and milestone;
- summary;
- files added/modified;
- migration/schema details;
- commands actually executed;
- exact test/build results;
- blockers and next steps.
Never log secrets or sensitive legal data. Never fabricate test results. Do not create another log file as a substitute for root logs.md.
Final report and acceptance
Role changes persist; only admins manage roles and admin audit logs; users cannot call protected judge/admin APIs; judges see only authorized data; role changes are auditable; no credentials are hardcoded or shipped to the frontend; existing features work; and logs.md contains truthful evidence. Separate implemented work from blocked/unverified items and provide migration/deployment steps.
Start with Phase 1 repository discovery. Do not blindly overwrite files or create duplicate authentication/database abstractions.
# TASK: Completely Remove the JUDGE Role from NyayaSarathi

## 1. Project Context

You are working on **NyayaSarathi**, an AI-powered legal-tech platform built with:

- **Frontend:** React.js + Vite
- **Backend:** FastAPI + Python
- **Database:** Inspect the existing configuration and identify whether the application uses SQLite, PostgreSQL, SQLAlchemy, or another persistence layer.
- **Authentication:** Role-based authentication and authorization.
- **Documentation:** Maintain a root-level `logs.md` file recording all changes.

The application currently has four roles:

1. `USER`
2. `ADVOCATE`
3. `JUDGE`
4. `ADMIN`

We have decided to remove the `JUDGE` role completely. After this change, the only supported roles must be:

- `USER`
- `ADVOCATE`
- `ADMIN`

Your responsibility is to implement this change across the entire repository, including the frontend, backend, authentication, authorization, database schema and records, API routes, dashboards, navigation, configuration, seed data, and tests.

**Do not merely hide the Judge dashboard. Remove the Judge role as an active application capability while preserving all existing functionality for USER, ADVOCATE, and ADMIN.**

---

## 2. Mandatory Rules

Follow these rules throughout the implementation:

1. Inspect the repository before modifying files.
2. Identify the actual frontend, backend, database, authentication, and routing architecture. Do not assume paths or filenames exist.
3. Search the entire project for `JUDGE`, `Judge`, `judge`, and related judge-specific identifiers.
4. Trace each reference to determine whether it is role-specific or shared functionality.
5. Remove obsolete judge-specific code without deleting unrelated legal functionality.
6. Preserve existing USER, ADVOCATE, and ADMIN features, permissions, dashboards, and workflows.
7. Do not rewrite the entire authentication system or introduce a new architecture unnecessarily.
8. Do not replace the current database, ORM, framework, or authentication library.
9. Do not create duplicate files, duplicate routes, or redundant authentication logic.
10. Do not hardcode credentials, secrets, passwords, or database connection strings.
11. Do not claim that tests passed unless you actually ran them and verified the results.
12. Do not erase the database, reset production data, or perform destructive migrations without a safe migration strategy.
13. Preserve existing audit history and unrelated legal records.
14. Maintain a detailed root-level `logs.md` file throughout the task.
15. Complete the implementation, not just a plan or a list of suggested changes.

If an operation risks losing user data or breaking an existing deployment, implement a safe migration or document the specific blocker rather than performing an unsafe deletion.

---

## 3. Phase One: Repository Audit

Before making changes, inspect the project structure and identify:

- Frontend source directory.
- Backend source directory.
- Authentication and authorization modules.
- User, role, and permission models.
- Database models and schema definitions.
- Database migration files.
- Login, registration, and token-generation logic.
- Frontend route definitions and route guards.
- Role-specific layouts, navigation, and dashboards.
- Judge-specific API endpoints and service modules.
- Database initialization, bootstrap, seed, and demo-account scripts.
- Tests and test fixtures.
- Environment variables and configuration.
- Documentation mentioning the Judge role.

Search all relevant source files, not just files with `judge` in their names. A Judge role may be referenced inside shared files such as `auth.py`, `models.py`, `main.py`, `App.jsx`, route configuration, or database initialization scripts.

Create a temporary internal checklist of every identified dependency before modifying the code.

Also inspect Git status and existing user changes. **Do not overwrite, revert, or discard unrelated work.**

Update `logs.md` with an initial entry describing the task, the starting architecture, and the scope of the audit.

---

## 4. Phase Two: Remove Judge Authentication and Role Assignment

Inspect all authentication and user-management code.

### Backend requirements

- Remove `JUDGE` from the application's supported role definitions and enumerations.
- Update role validation and serialization.
- Remove Judge-specific login handling, if it exists separately.
- Remove Judge registration or account-creation options.
- Remove Judge role assignment from registration, admin user-management forms, bootstrap scripts, and seed data.
- Remove judge-specific account creation and judge-role elevation workflows.
- Update role validation so new users cannot register or be assigned the removed role.
- Preserve the existing authentication mechanism, password hashing, session/token handling, and login behavior for the remaining three roles.
- Ensure role values are validated on the backend rather than trusting a role supplied by the frontend.
- Inspect JWT claims, token refresh, current-user responses, dependencies, decorators, and permission checks for Judge-specific logic.
- Ensure unsupported or legacy Judge accounts cannot continue using privileged Judge endpoints through an existing token.

If authentication uses a shared role-based login flow, preserve that flow and remove only the Judge-specific branches.

### Frontend requirements

- Remove Judge from role selectors, registration forms, login options, onboarding screens, and account-management forms.
- Remove Judge-specific redirects and dashboard routing logic.
- Remove Judge-only UI conditions and role-selection labels.
- Preserve login and registration for USER, ADVOCATE, and ADMIN.
- Make sure no Judge role is assigned by frontend defaults, cached state, or fallback logic.

Do not create a separate login implementation for the remaining roles unless the current architecture already requires it.

---

## 5. Phase Three: Remove Judge Dashboards, Pages, and Components

Search for every Judge-specific frontend page, component, layout, hook, context, and supporting asset.

Examples of possible filenames or routes include:

- `JudgeDashboard`
- `JudgeLayout`
- `JudgeCases`
- `JudgeCaseDetails`
- `JudgeHearingSchedule`
- `JudgePrivateNotes`
- `JudgePrecedents`
- `/judge/dashboard`
- `/judge/cases`
- `/judge/*`

These are examples only. Discover the actual files and routes before acting.

### Required actions

1. Remove Judge-specific page components that have no remaining legitimate use.
2. Remove Judge-only layouts, sidebars, navigation menus, widgets, and dashboard cards.
3. Remove imports and exports that reference deleted files.
4. Remove Judge-specific frontend routes.
5. Remove Judge-only route guards and redirect branches.
6. Remove Judge-specific API client functions and hooks when they are no longer used.
7. Remove Judge-only state management and menu configuration.
8. Remove Judge-specific links from shared navigation and dashboards.
9. Remove unused Judge-specific assets if they have no other references.
10. Update frontend tests and route configuration tests.

Check for broken imports, stale lazy-loaded routes, dead navigation links, and references to deleted components.

**Important:** Do not delete shared legal research, case search, precedent lookup, OCR, contract analysis, news, or other general legal tools simply because they were accessible from the Judge dashboard.

If a component contains both shared and Judge-specific functionality, extract or preserve the shared functionality before removing the Judge-specific parts.

---

## 6. Phase Four: Remove Judge Backend Routes, Services, and Permissions

Inspect all FastAPI routers, endpoints, services, dependencies, schemas, and authorization checks.

Possible examples include:

- `judge.py`
- `judge_router.py`
- `judge_service.py`
- Judge dashboard APIs.
- Assigned-docket APIs.
- Judge-only case-management endpoints.
- Hearing scheduling endpoints.
- Private judicial notes endpoints.
- Judge-only precedent-management endpoints.

Again, these names are illustrative; inspect the real repository.

### Required actions

- Remove Judge-only routers from the FastAPI application.
- Remove their `include_router()` registrations.
- Remove Judge-specific endpoints and their associated service code if no longer needed.
- Remove Judge-only request and response schemas when unused.
- Remove Judge-only permission dependencies.
- Remove Judge-specific authorization branches from shared APIs where they are no longer relevant.
- Remove Judge-only WebSocket handlers, event subscriptions, background tasks, or notifications if present.
- Remove frontend and backend references to obsolete endpoint paths.
- Update OpenAPI documentation automatically through the existing FastAPI configuration.
- Update tests that expect Judge routes or permissions.

### Authorization safety

Do not assume that deleting the frontend route makes the API inaccessible.

Verify that every remaining endpoint still enforces the appropriate role permissions. USER must not gain ADVOCATE or ADMIN permissions because a Judge permission branch was removed.

If an endpoint is shared by multiple roles, retain it and adjust its authorization rules deliberately.

If a Judge-specific endpoint is removed, verify that it no longer appears in the registered application routes and that direct requests to its former URL do not execute the old functionality.

Do not leave obsolete endpoints accessible just because their frontend pages have been deleted.

---

## 7. Phase Five: Database Cleanup and Migration

This phase requires special care.

First, identify the actual database engine, ORM, schema, migrations, and current role representation. Determine whether roles are stored as strings, database enums, check constraints, separate role tables, or a combination of these.

### A. Remove Judge from the supported schema

Update the appropriate schema definitions to allow only:

- `USER`
- `ADVOCATE`
- `ADMIN`

Inspect and update, where applicable:

- Python enums and constants.
- SQLAlchemy models.
- Database enum types.
- CHECK constraints.
- Role lookup tables.
- Pydantic validation schemas.
- Database initialization scripts.
- Migration files.
- Test fixtures and factories.
- Seed and demo data.

Do not create a new schema or replace the current database merely to remove a role.

### B. Inspect existing Judge records

Identify all database records associated with the Judge role and determine whether they are:

- Demo accounts.
- Test fixtures.
- Real user accounts.
- Related case assignments or other domain records.
- Audit history or historical events.

Do not automatically delete every row containing `JUDGE`.

### C. Apply a safe migration

Create a migration compatible with the existing migration framework.

The migration must:

1. Preserve all USER, ADVOCATE, and ADMIN records.
2. Preserve unrelated legal documents, cases, and research data.
3. Preserve audit logs and historical records.
4. Prevent future assignment of the removed Judge role.
5. Handle existing Judge accounts explicitly.
6. Update database constraints and enum definitions safely.
7. Avoid orphaned records and broken foreign-key relationships.
8. Support the database engine actually used by the project.
9. Have a documented rollback or recovery strategy wherever feasible.

If the database contains Judge accounts, do not automatically promote them to ADMIN or ADVOCATE.

Use a safe, explicit strategy appropriate to the application. For example, deactivate legacy Judge accounts or require a reviewed account migration, preserving their identity and historical records. If accounts must be removed, first verify the relationship and retention requirements for their associated records.

If the project has no migration framework, introduce only the smallest safe migration mechanism appropriate to the existing architecture.

### D. Validate the migration

After applying the migration in an appropriate development or test environment, verify:

- No active account can authenticate with the removed Judge role.
- The supported role schema accepts USER, ADVOCATE, and ADMIN.
- Invalid role assignment is rejected.
- Existing non-Judge users remain intact.
- Foreign keys remain valid.
- Historical audit data remains available.
- Application startup works against the migrated schema.

Do not delete or recreate the production database to achieve this.

---

## 8. Phase Six: Admin and User Management

Inspect the Admin dashboard and all user-management workflows.

Update them to support exactly three active roles:

- USER
- ADVOCATE
- ADMIN

Remove:

- Judge role options.
- Judge account creation.
- Judge role assignment and promotion.
- Judge-specific filters or status labels that are no longer meaningful.
- Judge-only account-management actions.
- Judge-only dashboard statistics and navigation.

Preserve unrelated Admin functionality, including user management, security controls, audit logs, and system monitoring.

If existing Judge accounts remain in the database as disabled legacy records, handle them consistently in Admin interfaces. Do not silently mislabel them as USER or ADVOCATE.

Ensure that ordinary users cannot assign themselves ADMIN or ADVOCATE permissions, and that role changes continue to be protected by the existing authorization system.

---

## 9. Phase Seven: Database and Business Logic Reference Audit

Perform a second repository-wide search after the implementation.

Search for variations including:

- `JUDGE`
- `Judge`
- `judge`
- `judge_id`
- `judgeId`
- `judge_role`
- `judge_dashboard`
- `/judge`
- `assigned_judge`
- Judge-specific table names and foreign keys.
- Judge-specific environment variables and feature flags.
- Judge-specific tests, seed data, and documentation.

For every remaining match, classify it as one of the following:

1. Obsolete code that must be removed.
2. Historical data or migration logic that must remain.
3. Shared functionality that must remain.
4. Documentation that must be updated.
5. An unrelated reference that does not need changing.

Do not blindly replace every occurrence of the word `judge`. A historical audit entry, legal case document, or ordinary legal-domain reference must not be deleted merely because it contains that word.

Remove obsolete code and update relevant documentation. Retain any necessary legacy migration logic and historical data handling, and explain these remaining references in `logs.md`.

---

## 10. Phase Eight: Tests and Verification

Run the project's existing tests and available static checks. Inspect the package scripts, Python dependency setup, and test configuration to determine the correct commands.

Add or update tests for the following.

### Authentication tests

- USER login continues to work.
- ADVOCATE login continues to work.
- ADMIN login continues to work.
- The system rejects new assignment of the JUDGE role.
- Unsupported role values are rejected.
- Legacy Judge tokens cannot access removed or privileged endpoints.
- Existing authorization behavior for the remaining roles is preserved.

### Route tests

- The frontend no longer registers Judge-only routes.
- The backend no longer registers Judge-only routers or endpoints.
- USER, ADVOCATE, and ADMIN routes remain available.
- Direct API requests cannot bypass authorization.

### Database tests

- The migration completes successfully in a disposable test database.
- Existing USER, ADVOCATE, and ADMIN records are preserved.
- Legacy Judge accounts are handled according to the chosen migration policy.
- Audit history and unrelated legal records remain intact.
- The schema rejects unsupported role assignments.

### Regression tests

Verify the main workflows relevant to the existing application, including as applicable:

- Login and logout.
- User registration.
- Role-based dashboard access.
- Legal research.
- OCR and document extraction.
- Contract analysis.
- War Room.
- Outcome Predictor.
- Legal news.
- Advocate-specific features.
- Admin user management and audit logs.

Do not create fake test results or disable failing tests merely to make the suite pass.

If a test cannot run because of missing environment variables, unavailable services, or absent dependencies, document the exact limitation.

---

## 11. Phase Nine: Update `logs.md`

Create or update a file named `logs.md` in the project root.

If `logs.md` already exists, append a new dated section. Do not erase earlier development history.

Maintain the log during the task, not just at the end.

Use this structure:

# NyayaSarathi Development Logs

## [Current Date] — Removal of JUDGE Role

### 1. Objective
Describe the decision to reduce the supported roles from USER, ADVOCATE, JUDGE, and ADMIN to USER, ADVOCATE, and ADMIN.

### 2. Initial Audit
Record the actual files, modules, routes, models, and database components discovered.

### 3. Files Modified
For each file, record:
- File path.
- What changed.
- Why the change was required.

### 4. Files Deleted
For each deleted file, record:
- File path.
- Purpose of the file.
- Why it was safe to remove.

### 5. Authentication and Authorization
Document changes to role definitions, login, registration, token validation, route guards, and permissions.

### 6. Frontend Changes
Document removed dashboards, pages, navigation entries, components, and routes.

### 7. Backend Changes
Document removed routers, endpoints, services, schemas, and permission checks.

### 8. Database Changes
Document:
- Database engine and migration framework.
- Migration filename.
- Schema and constraint changes.
- How existing Judge accounts were handled.
- How related records and audit history were preserved.
- Backup and rollback or recovery instructions.
- Whether the migration was actually executed.

Do not include passwords, tokens, secrets, or sensitive user information in the logs.

### 9. Tests and Verification
For each check, record:
- Command executed.
- Actual result.
- Pass/fail status.
- Any limitations or skipped checks.

### 10. Remaining References
List any remaining Judge-related references and explain why they must remain, such as historical migration logic or preserved audit records.

### 11. Known Issues
Record unresolved problems, environmental blockers, and any migration steps that still require manual execution.

### 12. Final Status
Summarize the implementation and distinguish between:
- Completed and verified.
- Implemented but not verified.
- Pending manual action.

Include a final checklist confirming the three supported roles and the regression checks performed.

Use actual filenames, actual commands, and actual results. Never invent a file path or claim a successful migration without evidence.

---

## 12. Phase Ten: Final Acceptance Criteria

The task is complete only when all applicable requirements below are satisfied.

### Role architecture
- [ ] USER remains supported.
- [ ] ADVOCATE remains supported.
- [ ] ADMIN remains supported.
- [ ] JUDGE is no longer a supported active role.
- [ ] New users cannot register or be assigned the JUDGE role.
- [ ] Legacy Judge authentication cannot grant access to protected functionality.

### Frontend
- [ ] Judge login and registration options are removed.
- [ ] Judge dashboard and Judge-only pages are removed.
- [ ] Judge frontend routes and navigation entries are removed.
- [ ] Broken imports and dead links are eliminated.
- [ ] Remaining dashboards and shared legal tools still work.

### Backend
- [ ] Judge-only routers and endpoints are removed or safely disabled.
- [ ] Router registration and authorization checks are updated.
- [ ] Remaining API permissions are correct.
- [ ] Obsolete Judge services and schemas are removed where safe.
- [ ] No hidden Judge-only endpoint remains accessible.

### Database
- [ ] Schema definitions no longer allow new JUDGE role assignments.
- [ ] A safe migration exists where required.
- [ ] Existing non-Judge accounts and unrelated records are preserved.
- [ ] Legacy Judge records are handled explicitly.
- [ ] Audit history is preserved.
- [ ] Migration and recovery instructions are documented.

### Verification and documentation
- [ ] Repository-wide reference audit is complete.
- [ ] Relevant tests and checks are executed.
- [ ] Failed and skipped checks are documented honestly.
- [ ] Root-level `logs.md` is updated with detailed changes.
- [ ] Final response lists modified and deleted files, migration details, test results, and remaining manual steps.

---

## 13. Execution Instructions

Work in this order:

1. Inspect the repository and Git status.
2. Audit every Judge-related dependency.
3. Write the initial `logs.md` entry.
4. Implement the smallest coherent set of code changes.
5. Create and validate the database migration if necessary.
6. Remove obsolete frontend and backend code.
7. Update tests, fixtures, seed data, and documentation.
8. Run the repository-wide reference search again.
9. Run available tests and startup/build checks.
10. Update `logs.md` with actual results.
11. Review the final diff for accidental changes to unrelated functionality.

Do not stop after producing a plan. Proceed with implementation and verification unless a genuine blocker requires clarification.

If a destructive database operation, irreversible data loss, or production migration requires additional authorization, stop before that operation and explain the blocker. Continue with safe, non-destructive work wherever possible.

## 14. Required Final Response

When finished, provide a concise implementation report containing:

1. Summary of the changes.
2. Important files modified.
3. Files deleted.
4. Database migration details and how existing Judge accounts were handled.
5. Authentication and authorization changes.
6. Tests executed and their actual outcomes.
7. Any remaining Judge references and why they remain.
8. Known issues or manual steps.
9. Confirmation that `logs.md` was updated, including its exact path.

**Priority:** Keep NyayaSarathi stable. Remove the Judge role thoroughly, preserve USER, ADVOCATE, and ADMIN, protect existing data, and avoid unnecessary refactoring or new features.
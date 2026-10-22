NyayaSarathi — Real-Time User–Advocate Chat Implementation Specification
Purpose: Give a coding agent a detailed, repository-aware plan to implement secure one-to-one real-time messaging between USER and ADVOCATE, including document sharing, and require all implementation progress and results to be recorded in the project's root logs.md.

Important: This document is an implementation specification, not evidence that the feature has already been implemented. The agent must inspect the actual repository, implement the feature, run the available checks, and record truthful results in logs.md.

1. Objective
Implement a production-minded chat feature inside the existing NyayaSarathi application so that an authorized USER and their assigned ADVOCATE can:
- Create or open an authorized conversation.
- Send and receive text messages in real time.
- Load older messages using pagination.
- Share documents and other explicitly permitted attachments securely.
- See message timestamps, delivery/read status where supported, and unread-message counts.
- Recover correctly after a network interruption, tab suspension, or reconnect.
- Use the feature from the existing USER and ADVOCATE dashboards.
Keep the current architecture and existing features intact. Do not rewrite authentication, role-based access control, legal research/RAG, OCR, War Room, user profiles, or audit functionality as part of this task.
2. Existing Architecture — Inspect and Preserve
The repository has the following known architecture. Verify these details against the current code before making changes.
Frontend
- Project folder: nyayasarathi-app.
- Stack: Next.js / React.
- Frontend API requests go through the existing API client and API_BASE_URL, currently configured as http://127.0.0.1:8001 in config.ts.
- The browser currently does not use @supabase/supabase-js for direct database access.
- Continue to use FastAPI for authenticated application APIs. Do not add browser-side access to the database or expose privileged Supabase credentials.
Backend
- FastAPI backend with custom JWT authentication and role-based authorization.
- Current roles: USER, ADVOCATE, ADMIN.
- Existing Supabase client: backend/services/supabase_client.py.
- Existing user repository: backend/services/user_repository.py.
- User IDs are TEXT, not UUID. Use the existing user ID format and foreign-key types.
- The user repository supports two database modes:
  - PostgreSQL/Supabase is authoritative when the repository's existing conditions allow it.
  - Local SQLite is used when NYAYASARATHI_USE_SQLITE=1, PostgreSQL driver/configuration is unavailable, or the configured database URL is missing or a placeholder.
- Other existing components may be SQLite-only. Do not assume every part of the application shares one database connection or transaction.
- The Supabase Python client and direct psycopg2 connection via DATABASE_URL are separate paths. Do not assume they share transactions.
Existing user schema
The current public.users table includes a text primary key id, unique email, full_name, role, profile fields, and timestamps. It permits USER, ADVOCATE, ADMIN, and the legacy DEACTIVATED_JUDGE sentinel. Do not change this role model for chat. Do not reactivate or introduce a JUDGE role.
3. Required Repository Reconnaissance
Before coding, inspect and document:
1. Backend folder layout, application entry point, router registration, dependency injection, and error-response conventions.
2. JWT authentication dependencies and how the current user ID and role are obtained from a verified token.
3. Existing user/advocate assignment or case relationship models, if any. Use the existing authoritative relationship if it exists.
4. Existing database migration approach, table naming conventions, timestamp conventions, and transaction helpers.
5. Existing user_repository.py behavior for PostgreSQL and SQLite, including how database mode is selected.
6. Existing Supabase Storage and Realtime configuration, if any.
7. Frontend API client, route structure, dashboard navigation, design system, and notification patterns.
8. Root logs.md (or existing log file naming). Append to the existing log; do not replace prior entries.
9. Existing tests, lint commands, formatters, and test fixtures.
Do not guess filenames, table names, or APIs. Reuse existing conventions where appropriate. If an assignment relationship does not exist, do not invent a claim that an advocate is assigned; define a minimal, explicit assignment mechanism only after documenting the gap and its impact.
4. Functional Requirements
4.1 Conversation access
- Support a private one-to-one conversation between a USER and an authorized ADVOCATE.
- A conversation must be linked to the correct user and advocate.
- Only those authorized participants can read, send messages to, upload attachments for, or download attachments from that conversation.
- ADMIN access must follow the application's existing administrative policy. Do not silently grant administrators access to private message contents merely because they are administrators. If admin moderation/access is required, it must be explicit, justified, audited, and consistent with current policy.
- A client must not be able to choose an arbitrary sender ID, user ID, advocate ID, or participant list and thereby gain access.
- Prevent duplicate conversations for the same intended pair or case, according to the application's actual relationship model.
- Do not allow a user to message an unrelated advocate unless the existing product rules explicitly allow it.
4.2 Messages
Each message should support, at minimum:
- Stable message ID.
- Conversation ID.
- Sender user ID.
- Message text.
- Created timestamp stored consistently (prefer UTC in storage; format for the user's locale in the UI).
- Optional edit/delete metadata only if supported by existing product requirements; do not add these operations casually.
- Optional attachment references.
- Read state or read receipts where supported by the chosen schema.
Validate message text on the server. Reject empty messages that contain neither text nor a valid attachment. Enforce a documented maximum message length. Normalize or trim surrounding whitespace without altering meaningful message content.
4.3 Message history
- Provide newest/older message pagination; do not load an unbounded conversation in one request.
- Use a stable cursor based on timestamp plus a unique ID, or another repository-consistent cursor strategy that avoids skipped/duplicated messages when timestamps match.
- Return messages in a consistent order.
- Fetch persisted history from the database on initial load and after reconnect. Realtime events are notifications, not the source of truth.
- Avoid duplicate messages when an API response and a Realtime event contain the same message.
4.4 Real-time behavior
- A recipient should see new messages while connected without manually refreshing.
- Realtime must not bypass backend authorization.
- Publish the event only after the message has been successfully persisted.
- Use private channels or another explicitly authorized subscription strategy.
- Reconnect gracefully after a transient disconnect and refetch messages missed while offline.
- Do not send document bytes, secrets, full legal documents, or unnecessary personal data in Realtime payloads. Prefer a minimal event containing an event type, conversation ID, message ID, and timestamp.
- The UI should show a useful connection state and should not imply a message was delivered if the server did not confirm persistence.
- Realtime delivery is not guaranteed to be durable. The database remains the source of truth.
4.5 Document and attachment sharing
- Store actual file bytes in a private storage bucket or the repository's existing secure file-storage abstraction.
- Store only attachment metadata and a storage object key/path in the chat database.
- Do not store large binary files directly in the messages table.
- Do not expose public object URLs for private legal documents.
- Downloads must pass authorization for the conversation and attachment before the server streams the file or issues a short-lived signed URL.
- Validate allowed extensions and MIME types on the server; do not trust browser-supplied MIME type alone.
- Enforce configurable maximum file size and reasonable per-message attachment limits.
- Generate storage object paths server-side. Prevent path traversal and object-key guessing from granting access.
- Use safe filenames for display and Content-Disposition.
- If malware scanning is available in the project environment, integrate it. If it is not available, document this limitation rather than claiming files are scanned.
- Clean up abandoned uploads and orphaned storage objects where feasible.
- Avoid logging document contents, access tokens, signed URLs, passwords, or other secrets.
4.6 Read state and unread counts
- Implement a read cursor or receipt design that fits the existing schema and product requirements.
- Update read state only for the authenticated participant and only for messages in a conversation they can access.
- Unread counts must be calculated without fetching every message into the browser.
- Avoid N+1 queries when listing conversations and unread counts.
- If full delivery receipts are not required, start with a last_read_at or last-read message cursor per participant instead of adding unnecessary per-message receipt rows.
4.7 Frontend experience
Integrate with the existing dashboard styling and navigation. At minimum provide:
- Conversation list.
- Message history panel.
- Message composer and send action.
- Attachment selection/upload and download/open action.
- Loading, empty, and error states.
- Unread indicator.
- Read status if implemented.
- Connection/reconnecting indicator.
- Retry handling for transient failures without accidentally duplicating messages.
- Keyboard-accessible controls and reasonable responsive layout.
- Clear errors for unauthorized access, unsupported file types, size limits, and network failures.
Do not introduce a separate design system or break existing dashboard routes.
5. Suggested Data Model
Adapt this model to the actual migration and repository conventions. The final schema must use TEXT user IDs to match public.users.id.
5.1 chat_conversations
Suggested fields:
- id TEXT PRIMARY KEY
- user_id TEXT NOT NULL REFERENCES users(id)
- advocate_id TEXT NOT NULL REFERENCES users(id)
- Optional case_id TEXT or equivalent only if an existing case relationship is available and appropriate
- created_at
- updated_at
- Optional last_message_at
- Optional status if the product needs active/closed conversations
Requirements:
- Add indexes for user_id, advocate_id, and last_message_at as appropriate.
- Add a uniqueness constraint matching the real product rule, such as one conversation per user/advocate pair or one per user/advocate/case. Do not choose the uniqueness rule without inspecting current assignment and case semantics.
- Enforce valid role pairing in application logic and, where practical, database constraints.
5.2 chat_messages
Suggested fields:
- id TEXT PRIMARY KEY
- conversation_id TEXT NOT NULL REFERENCES chat_conversations(id)
- sender_id TEXT NOT NULL REFERENCES users(id)
- body TEXT (nullable only if attachment-only messages are allowed)
- created_at
- Optional edited_at, deleted_at, or equivalent only if required
- Optional client idempotency key if needed to prevent duplicate sends
Requirements:
- Index (conversation_id, created_at, id) for paginated history.
- Index sender or other fields only where query patterns justify them.
- Validate that the sender is one of the authorized conversation participants before inserting a message.
- Use a transaction for the message insert and conversation's last_message_at update.
- Add a unique idempotency constraint if the implementation supports client-generated request keys.
5.3 chat_attachments
Suggested fields:
- id TEXT PRIMARY KEY
- message_id TEXT NOT NULL REFERENCES chat_messages(id)
- conversation_id TEXT NOT NULL REFERENCES chat_conversations(id) if useful for efficient authorization
- uploaded_by TEXT NOT NULL REFERENCES users(id)
- storage_key TEXT NOT NULL
- original_filename TEXT NOT NULL
- content_type TEXT
- size_bytes BIGINT in PostgreSQL and a compatible integer type in SQLite
- created_at
Requirements:
- Keep the bucket private.
- Never store permanent public URLs for private documents.
- Add indexes to support attachment lookup and authorization.
- Define whether deleting a message deletes metadata and storage objects, and implement cleanup consistently.
5.4 Read state
Prefer a small participant-state table or equivalent if needed, for example chat_participant_state with conversation_id, user_id, last_read_message_id or last_read_at, and updated_at. Add a uniqueness constraint on (conversation_id, user_id). Ensure the user is a participant before allowing state updates.
5.5 Transactional outbox (recommended for PostgreSQL mode)
If reliable event publication is in scope, add an outbox table containing an event ID, conversation ID, message ID, event type, creation time, and processing status/attempt count. Insert the message and outbox event in the same PostgreSQL transaction. A publisher can retry unprocessed events and mark them processed after successful publication.

Important limitations:
- A transaction that writes through psycopg2 and a separate Supabase REST client call are not one transaction.
- Do not claim atomic delivery unless the message and outbox row are written in the same database transaction.
- An outbox reduces the risk of lost notifications but does not make client delivery durable. Clients must still fetch history on reconnect.
- If no publisher/worker mechanism exists, implement a minimal repository-consistent background/polling process only if it can be run and tested safely. Document operational requirements.
6. API Design
Use the project's existing route prefixes, dependency patterns, response envelopes, and error conventions. The following are logical operations, not mandatory literal paths.
Conversation operations
- GET /chat/conversations
  - Return only conversations the authenticated participant may access.
  - Include safe conversation summary, last-message preview if permitted, last-message timestamp, and unread count.
  - Paginate if the number of conversations can grow.
- POST /chat/conversations
  - Create or retrieve the authorized conversation.
  - Validate role pairing and assignment/case relationship server-side.
  - Make the operation idempotent according to the chosen uniqueness rule.
- GET /chat/conversations/{conversation_id}
  - Return conversation metadata only after participant authorization.
Message operations
- GET /chat/conversations/{conversation_id}/messages
  - Return paginated messages in a stable order.
  - Verify participation before querying content.
- POST /chat/conversations/{conversation_id}/messages
  - Derive sender ID from verified authentication context.
  - Validate text and attachments.
  - Persist the message transactionally.
  - Publish/queue a minimal Realtime event only after successful persistence.
  - Return the persisted message representation.
- POST /chat/conversations/{conversation_id}/read
  - Update the authenticated participant's read cursor/state.
- Optional POST /chat/conversations/{conversation_id}/typing
  - Add only if typing indicators are genuinely needed. Do not persist every typing event.
- Optional POST /chat/conversations/{conversation_id}/attachments
  - Upload file, validate it, store it privately, and create authorized metadata.
- GET /chat/attachments/{attachment_id} or equivalent
  - Verify current participant access and stream the file or issue a short-lived signed URL.
Use the application's established status codes and error response format. Return 401 for missing/invalid authentication, 403 for authenticated users without permission, 404 where the app intentionally avoids disclosing the existence of unauthorized resources, 413 for oversized uploads, and 422 for invalid input, consistent with existing conventions.
7. Authentication and Authorization
This section is security-critical.
1. Reuse the existing verified JWT dependency. Do not build a second authentication system.
2. Get the authenticated user ID and role from the verified token/dependency, not from request body fields.
3. For every conversation, message, read-state, attachment upload, and attachment download operation, verify that the caller is an authorized participant.
4. Validate the user/advocate relationship using the authoritative assignment or case data model.
5. Reject requests that supply a forged sender_id, change participant IDs, or access another conversation by guessing its ID.
6. Keep service-role credentials and JWT signing secrets on the backend only.
7. Never return database connection strings, stack traces, secrets, or privileged Supabase configuration to the frontend.
8. Add rate limiting or a documented abuse-control plan for message sends and uploads, following existing infrastructure.
9. Keep audit logs useful but privacy-conscious: log identifiers, operation outcome, and error category; do not log message bodies or file contents by default.
10. Ensure ADMIN cannot read private chat content unless explicit existing policy authorizes it.
8. Supabase Realtime Integration
First inspect whether the current custom JWT can be used by the desired Supabase Realtime authorization method. Do not assume a custom NyayaSarathi JWT automatically satisfies Supabase's auth.uid() or RLS requirements.

Choose and document one secure approach:
Approach A — Backend-mediated Realtime publishing
- Browser uses FastAPI for all privileged operations.
- Backend verifies the NyayaSarathi JWT and participant access.
- Backend publishes a minimal event to the correct private channel using server-held credentials.
- Browser subscription must still be protected; do not assume private channel names are secret authorization.
- If the frontend cannot securely authorize subscriptions without exposing secrets, add a safe subscription-token or backend-mediated event mechanism supported by the existing stack.
Approach B — Supabase-compatible subscriber token
- Only if the existing architecture can safely issue a short-lived Supabase-compatible JWT with appropriate claims and authorization.
- Define the exact claims, signing key custody, expiry, audience, and private-channel/RLS policy.
- Do not expose the signing secret.
- Test that a participant can subscribe to their own conversation and cannot subscribe to another conversation.
For either approach:
- Use private conversation-specific channels, with opaque IDs where appropriate.
- Event payload should be minimal, such as {type, conversation_id, message_id, created_at}.
- The recipient fetches the persisted message from FastAPI or receives the API response only after authorization.
- Deduplicate event/API delivery by stable message ID.
- Reconnect and refetch history from a known cursor.
- Never publish message events before the database commit succeeds.
- Document local development behavior and required environment variables.
9. PostgreSQL and SQLite Compatibility
The feature must explicitly support the repository's two database modes or clearly report a tested limitation.
PostgreSQL authoritative mode
- Use existing connection and transaction conventions where possible.
- Create migrations using the project's existing migration system.
- Use database constraints and indexes for integrity and query performance.
- If using an outbox, write the message and outbox row in the same PostgreSQL transaction.
- Avoid N+1 queries for conversations, previews, and unread counts.
SQLite fallback mode
- Provide a compatible schema/migration and repository implementation if the app is expected to support chat in SQLite mode.
- Use SQLite-compatible data types, placeholders, transaction handling, and indexes.
- Do not use PostgreSQL-only SQL in a shared query without a clear dialect abstraction.
- Supabase Realtime does not automatically observe writes to local SQLite. Implement a working local notification/polling fallback, or clearly disable live updates in SQLite mode while ensuring manual refresh/history remains functional.
- Do not claim that SQLite-mode real-time delivery works unless it is actually implemented and tested.
- Avoid creating a hidden third source of truth or silently syncing SQLite messages to Supabase without a designed synchronization mechanism.
Mode selection and errors
- Follow the existing is_postgres_authoritative() decision rather than creating a conflicting configuration rule.
- Make logs and health/debug information clear about which mode is active, without leaking secrets.
- If required storage or Realtime configuration is missing, return a clear, safe error and document the degraded behavior.
10. Storage and Upload Flow
Recommended upload flow:
1. Frontend requests an upload through FastAPI.
2. Backend authenticates the caller and checks conversation participation.
3. Backend validates size, extension, content type, and any available file-signature checks.
4. Backend generates a safe, non-guessable storage key under the conversation's namespace.
5. File is stored in a private bucket or approved private storage service.
6. Metadata is recorded in the database and associated with the message/conversation.
7. The message is persisted and a minimal Realtime event is published/queued after commit.
8. On download, backend rechecks authorization and streams the object or generates a short-lived signed URL.
9. Failed database writes after upload trigger cleanup of the orphaned object where possible.
10. Periodic cleanup can remove abandoned temporary uploads if a background-job mechanism already exists.
Document bucket name, allowed file types, size limits, and setup steps in the repository's environment documentation. Never hardcode credentials.
11. Frontend Implementation Plan
1. Add a chat API module that uses the existing API client and auth mechanism.
2. Add types/interfaces for conversation, message, attachment metadata, pagination cursor, and connection status.
3. Add a conversation list view to the appropriate USER and ADVOCATE dashboards.
4. Add a conversation view with paginated history and stable message ordering.
5. Add send-message behavior with pending/success/failure states.
6. Add attachment upload and authorized download/open controls.
7. Add unread count and read-state updates.
8. Subscribe to authorized Realtime events using the chosen security approach.
9. Deduplicate events and API responses by message ID.
10. On reconnect or tab visibility restoration, refetch messages from the last known cursor.
11. Handle expired JWTs using the existing auth refresh/logout behavior; never log the token.
12. Add accessible labels, keyboard support, mobile layout, and explicit error states.
13. Avoid polling at an unnecessarily high frequency. If polling is the SQLite fallback, use a conservative configurable interval and stop/reduce polling when the view is inactive.
12. Testing Requirements
Add tests using the project's existing test framework and fixtures. Do not merely describe tests; execute the tests that are feasible in the environment.
Authorization tests
- Unauthenticated caller cannot list or access conversations.
- USER can access their own authorized conversation.
- USER cannot access another user's conversation.
- ADVOCATE can access only conversations assigned to them.
- ADVOCATE cannot impersonate a USER or another advocate.
- ADMIN access follows explicit policy; private messages are not automatically exposed.
- Forged sender_id, participant IDs, and conversation IDs are rejected.
- Attachment download is denied to nonparticipants.
Persistence and correctness tests
- Valid message persists and is returned.
- Empty message is rejected unless a valid attachment is present.
- Invalid or overlong text is rejected.
- Pagination has stable ordering and no duplicates across pages.
- Concurrent creation does not create duplicate conversations under the selected uniqueness rule.
- Idempotency key prevents duplicate sends if implemented.
- Message and conversation last-message timestamp remain consistent.
- Read state and unread counts are correct.
- A database failure does not publish a success event.
Realtime and recovery tests
- Authorized recipient receives a minimal event in PostgreSQL mode.
- Unauthorized user cannot subscribe to another conversation.
- Realtime event and API response do not duplicate the displayed message.
- Disconnect/reconnect causes history recovery.
- Missed events are recovered from persisted history.
- SQLite mode does not falsely report Supabase Realtime as active.
- Outbox retries pending events if an outbox is implemented.
Attachment tests
- Valid file uploads to private storage.
- Disallowed type and oversized file are rejected.
- Filename and storage path are safely handled.
- Failed metadata insertion attempts cleanup.
- Unauthorized download fails.
- Private files are not served through permanent public URLs.
Quality checks
Run relevant backend tests, frontend lint/type checks, and build commands identified during reconnaissance. Record exact commands and exit results. Do not claim a test passed if it was not run.
13. Performance and Data Growth
- Always paginate message history.
- Add indexes for the actual conversation-list, message-history, and unread-count queries.
- Do not load every message or all attachments to compute unread counts.
- Store files in private object storage, not in database rows.
- Use configurable upload limits.
- Consider retention/archive policy only after clarifying legal and product requirements; do not automatically delete legal communications.
- Do not add Redis, MongoDB, Socket.IO, or another service unless the existing infrastructure demonstrably requires it.
- Monitor database size, storage usage, message volume, and Realtime usage through available project metrics.
- Avoid sending entire message history or document text through Realtime.
14. Environment and Setup Documentation
Inspect existing environment-variable names first and reuse them. Add only variables that are genuinely required. Document:
- Which database mode is active and how the existing mode selector chooses it.
- Required PostgreSQL connection configuration, without publishing its value.
- Supabase URL and backend-only credentials required for private storage and event publishing.
- Private storage bucket name and setup procedure.
- Realtime channel authorization approach and any required policies.
- Maximum upload size and allowed file types.
- Any background worker or outbox publisher command, how it runs, and how it is monitored.
- Local SQLite fallback behavior and its real-time limitations.
- Frontend configuration only for non-secret API base URL and non-sensitive settings.
- How to run migrations, tests, and the application.
Never put real secrets in .md files, source code, test fixtures, logs, or frontend environment variables.
15. Mandatory logs.md Requirement
The coding agent MUST update the existing project-root logs.md throughout implementation and before finishing. If a root logs.md already exists, append to it and preserve every existing entry. Do not create a replacement log under another directory unless the project convention requires it.

Create a dated implementation section, for example:

## Real-Time User–Advocate Chat — YYYY-MM-DD

Record the following:
1. Initial inspection
   - Relevant files and patterns inspected.
   - Existing authentication, assignment, database-mode, storage, and Realtime behavior discovered.
   - Any assumptions that were confirmed or disproved.
2. Design decisions
   - Tables/migrations and uniqueness rules.
   - Authorization policy and how advocate assignment is verified.
   - Realtime authorization method, payload design, and reconnect recovery.
   - Attachment storage and download authorization.
   - PostgreSQL and SQLite behavior, including limitations.
   - Whether an outbox was implemented and why.
3. Files changed
   - Exact paths of every created, modified, or removed file.
   - One-line summary of the change in each file.
   - Migration filenames and how to apply them.
4. Configuration
   - Names of new or changed environment variables only; never record their values.
   - Private bucket/policy setup and any deployment requirements.
   - Any worker/background process required.
5. Testing
   - Exact commands executed.
   - Actual pass/fail counts or exit status.
   - Tests not run and why.
   - Any manual verification performed, with steps and observed outcome.
   - Clearly separate automated results from manual checks.
6. Known limitations and risks
   - Realtime or SQLite fallback limitations.
   - Any missing assignment model, storage configuration, malware scanning, or deployment setup.
   - Any unresolved security, performance, or migration concerns.
7. Next steps
   - Concrete follow-up tasks, only if work remains.
8. Final status
   - Use exactly one of:
     - PASS — core feature implemented and required checks passed.
     - PASS WITH LIMITATIONS — feature works but known gaps remain.
     - FAIL — core functionality is not complete or critical checks failed.
   - Explain the evidence for the status.
Log integrity rules
- Update logs.md as meaningful milestones are completed, not just at the end.
- Preserve existing log content.
- Never fabricate file changes, commands, test results, or successful deployment.
- Never write secrets, JWTs, database URLs, service-role keys, private message bodies, or document contents to logs.
- If the repository's log is named log.md or logs.mg instead, inspect the actual files and use the established root log file. The user specifically requests logs.md; create it at the project root if it does not exist, unless repository conventions clearly establish a different canonical log. If a differently named file is used, explain that in logs.md.
- Before completion, verify that the updated root logs.md exists and contains the implementation section.
16. Recommended Implementation Order
1. Inspect repository and append initial findings to root logs.md.
2. Confirm participant/advocate assignment model and database-mode conventions.
3. Design and implement migrations for PostgreSQL and SQLite as applicable.
4. Implement repositories and transactional message persistence.
5. Implement conversation, message, read-state, and attachment FastAPI endpoints.
6. Implement participant authorization and negative security tests.
7. Configure private storage and attachment authorization.
8. Implement Realtime publishing/subscription authorization and reconnect recovery.
9. Implement a SQLite fallback or explicitly document its supported behavior.
10. Integrate USER and ADVOCATE dashboard UI.
11. Run tests, lint/type checks, and build.
12. Fix failures and update logs.md after each meaningful milestone.
13. Review secrets, logs, object access, query performance, and migration safety.
14. Verify the final root logs.md entry and report the final status honestly.
17. Definition of Done
The task is complete only when all applicable items below are satisfied:
- [ ] Existing authentication and RBAC remain intact.
- [ ] Authorized USER and ADVOCATE can open the correct conversation.
- [ ] Unauthorized cross-conversation access is blocked by the backend.
- [ ] Messages persist and history is paginated.
- [ ] Realtime notifications work in the supported database mode.
- [ ] Reconnect fetches missed messages from persistent history.
- [ ] Realtime subscription authorization is tested and documented.
- [ ] Documents are stored privately and downloads are authorized.
- [ ] Unread/read state works if included in the agreed scope.
- [ ] PostgreSQL and SQLite behavior is implemented or limitations are explicit and tested.
- [ ] Existing application routes and features continue to work.
- [ ] Relevant tests and frontend checks have been run.
- [ ] Setup/configuration instructions are documented without secrets.
- [ ] Root logs.md contains changed files, migration details, commands, actual results, limitations, and final status.
- [ ] The final response summarizes what changed, how to run it, which checks passed/failed, and what remains.
18. Final Instructions to the Coding Agent
Implement the feature in the existing repository; do not stop after producing a plan. Inspect before editing, follow existing conventions, make the smallest maintainable set of changes, and test each milestone. Do not expose private legal communications or privileged credentials. Do not claim Supabase Realtime can observe local SQLite writes. Do not claim notification delivery is durable without recovery logic. Keep logs.md updated throughout the work and verify it exists at the repository root before reporting completion.

At the end, report:
1. What was implemented.
2. Exact files changed.
3. Migrations and setup steps.
4. Exact tests/commands run and their real results.
5. Known limitations.
6. The final logs.md section and status (PASS, PASS WITH LIMITATIONS, or FAIL).
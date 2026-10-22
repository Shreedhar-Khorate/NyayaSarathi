# NyayaSarathi — Complete USER–ADVOCATE Chat UI Implementation

## Project Objective

Implement the complete, functional USER–ADVOCATE messaging workflow in the existing NyayaSarathi application.

The chat database tables, FastAPI backend functionality, private attachment storage, and initial backend tests have already been implemented. However, the application currently has no clear, visible options for users to find advocates and initiate conversations, or for advocates to access and respond to incoming messages.

The objective is to connect the existing backend functionality to a complete, user-friendly frontend experience without unnecessarily rewriting working components.

**The implementation must follow the milestones below in order. Do not skip milestones, claim incomplete work is finished, or move forward while a critical issue from an earlier milestone remains unresolved.**

---

# Global Instructions — Follow Throughout Every Milestone

### 1. Inspect Before Modifying

Before writing code, inspect the existing project structure and understand:

- The Next.js frontend in `nyayasarathi-app`.
- The FastAPI backend and its router organization.
- Existing authentication, JWT handling, and role-based authorization.
- USER and ADVOCATE dashboard layouts and navigation.
- Existing chat pages, components, API clients, repositories, and endpoints.
- Current conversation creation, message sending, attachment handling, read/unread state, and real-time or polling functionality.
- Existing PostgreSQL/Supabase and SQLite compatibility logic.
- Current tests, project conventions, and root-level `logs.md`.

Use the actual implementation to determine endpoint URLs, request bodies, response schemas, component locations, and authentication requirements. Do not invent duplicate endpoints or assume that an existing function behaves a certain way without inspecting its code.

### 2. Preserve Existing Architecture

- Frontend API requests must go through the existing FastAPI API client and `API_BASE_URL`.
- Do not introduce direct browser access to Supabase PostgreSQL.
- Do not expose Supabase service-role keys, database credentials, JWT signing secrets, or other backend secrets to the frontend.
- Reuse existing chat tables, repositories, endpoints, authentication, and components wherever possible.
- Do not recreate chat tables or introduce unnecessary database migrations.
- Preserve existing legal research, OCR, document extraction, dashboard, and authentication functionality.
- Preserve the existing roles: `USER`, `ADVOCATE`, and `ADMIN`.
- Do not reintroduce the removed `JUDGE` role.
- Do not use Flask; preserve the existing FastAPI backend.
- Avoid unrelated refactoring, dependency changes, and redesigns.

### 3. Mandatory Logging Policy

The existing root-level `logs.md` is the permanent development log.

**Append new entries to `logs.md`. Never overwrite, truncate, replace, or delete existing entries.**

Every milestone must end with a dated log entry containing:

1. Milestone number and title.
2. Objective.
3. Files inspected.
4. Files created, modified, or deleted.
5. Backend endpoints reused or introduced.
6. Frontend routes and components implemented.
7. Authentication and authorization changes.
8. Database or storage changes, if any.
9. Tests and commands executed.
10. Actual test results, including passed and failed counts when available.
11. Bugs encountered and their resolutions.
12. Remaining issues and known limitations.
13. Confirmation of whether the milestone acceptance criteria passed.

Use the actual date at execution time. Never invent test results, endpoints, file names, or successful operations.

If a milestone cannot be completed, document the exact blocker and continue only where doing so is safe.

---

# Milestone 0 — Repository Inspection and Baseline

## Objective

Establish the current state of the project before implementing the missing UI.

## Tasks

1. Inspect the repository tree and identify the frontend and backend entry points.
2. Locate the USER and ADVOCATE dashboards and navigation components.
3. Locate existing chat pages, chat-related hooks, API clients, types, and components.
4. Inspect the FastAPI chat router and all relevant endpoints.
5. Inspect the chat repository and authorization checks.
6. Inspect the existing migration `006_chat_tables.sql` and current chat schema references without recreating or reapplying migrations.
7. Verify the existence and intended use of:
   - `chat_conversations`
   - `chat_messages`
   - `chat_attachments`
   - `chat_participant_state`
8. Inspect the existing private `chat-attachments` storage integration.
9. Identify how the frontend stores and supplies authentication tokens.
10. Determine whether advocate directory and conversation-list endpoints already exist.
11. Run relevant baseline tests and the frontend typecheck before modifications.
12. Review the existing root `logs.md` so new entries follow its established format.

## Required Deliverable

Produce a concise internal implementation checklist based on actual findings, then append a baseline entry to `logs.md`.

Record existing failures separately from any failures introduced by subsequent work.

## Acceptance Criteria

- The existing implementation is understood before changes begin.
- Existing API routes and schemas have been identified.
- The precise reason the chat option is missing has been established.
- Baseline test results are recorded accurately.
- Existing logs remain intact.

---

# Milestone 1 — Backend API Readiness

## Objective

Ensure the existing backend exposes all functionality needed by the frontend, implementing only genuinely missing endpoints.

## Tasks

### 1. Advocate Directory

Inspect whether a secure advocate directory endpoint already exists.

If missing, implement the smallest appropriate FastAPI endpoint that allows an authenticated USER to retrieve eligible advocates.

Return only fields intended for public profile display, such as:

- Advocate's public display name.
- Public profile image, if available.
- Professional designation or specialization, if available.
- Organization or professional affiliation, if available.
- Other explicitly approved public profile fields already supported by the application.

Do not expose password hashes, authentication tokens, private user details, administrative metadata, or sensitive account fields.

Use the existing user repository and database mode selection rather than creating a separate database access architecture.

If no eligible advocates exist, return a valid empty result.

### 2. Conversation Creation and Reopening

Inspect the existing conversation creation endpoint.

Ensure an authenticated USER can start or reopen a conversation with an eligible ADVOCATE.

- Derive the USER identity from the authenticated request context.
- Validate that the selected recipient is an eligible ADVOCATE.
- Prevent unauthorized participant combinations.
- Reuse the existing uniqueness rule and conversation repository.
- Return the existing conversation when one already exists, rather than creating duplicates.
- Handle concurrent creation safely using the existing database constraints and appropriate conflict handling.

Do not allow the client to impersonate a sender by supplying an arbitrary user ID.

### 3. Conversation Lists

Verify that authenticated users can retrieve their own authorized conversations.

For USER accounts, return only conversations in which the authenticated USER is a participant.

For ADVOCATE accounts, return only conversations belonging to the authenticated ADVOCATE.

Include available information useful for the conversation list, such as:

- Conversation ID.
- Other participant's safe display information.
- Latest message preview.
- Latest message timestamp.
- Unread count or read state, if supported.
- Any existing conversation status.

If a required list endpoint is missing, implement it using existing repository patterns.

### 4. Message and Attachment API Verification

Verify that the existing backend supports:

- Sending messages.
- Retrieving paginated message history.
- Marking conversations or messages as read.
- Uploading supported attachments.
- Retrieving attachment metadata.
- Authorizing attachment downloads.
- Returning appropriate errors for unauthorized requests.

Reuse existing implementations. Fix only issues that block the intended workflow.

### 5. Authorization

Enforce participant authorization server-side for every conversation and message operation.

An authenticated user must not be able to access another user's conversation by changing a conversation ID or attachment ID.

Do not grant ADMIN automatic access to private conversations unless an explicit, documented policy already authorizes that access.

## Testing

Add or update backend tests for:

- Advocate directory authorization.
- Safe directory response fields.
- Empty advocate directory.
- Conversation creation.
- Existing conversation reuse.
- Duplicate prevention.
- USER conversation-list isolation.
- ADVOCATE conversation-list isolation.
- Unauthorized message access.
- Unauthorized attachment access.
- Invalid participant and role combinations.

## Acceptance Criteria

- Every required backend operation exists or has been verified.
- Existing endpoints are reused where appropriate.
- Authorization is enforced server-side.
- No database migration is added merely to implement frontend navigation.
- Backend tests pass, or outstanding failures are documented precisely.

Append the milestone results to `logs.md`.

---

# Milestone 2 — USER Dashboard Navigation

## Objective

Make the chat workflow discoverable to ordinary users.

## Required Navigation

Add clearly visible navigation entries to the existing USER dashboard:

1. **Find an Advocate**
2. **Messages**

Use the existing sidebar, navigation bar, or dashboard menu conventions.

Do not replace the dashboard or introduce an unrelated design system.

### Find an Advocate

The navigation entry must open the advocate directory implemented or verified in Milestone 1.

### Messages

The navigation entry must open the USER's conversation list and allow access to existing conversations.

### UI Requirements

- Match the application's existing visual design.
- Use consistent labels, spacing, icons, and active-navigation states.
- Support the application's responsive layouts.
- Ensure the links work with direct URL navigation and browser refresh.
- Preserve existing dashboard navigation and functionality.
- Do not show broken or nonfunctional menu items.

## Acceptance Criteria

- An authenticated USER can clearly see both options.
- Both routes open successfully.
- Navigation remains functional on desktop and mobile layouts.
- Unauthenticated users cannot access protected routes.

Append the implementation and test results to `logs.md`.

---

# Milestone 3 — Find an Advocate Page

## Objective

Allow a USER to find an eligible advocate and initiate a private conversation.

## Tasks

### 1. Advocate Listing

Fetch the directory through the existing FastAPI API client.

Render available safe public information for each advocate.

Include:

- Loading state while the directory is being fetched.
- Empty state when no advocates are available.
- Error state with a clear retry option.
- Appropriate handling of expired sessions and authorization errors.
- A useful empty state when optional profile information is unavailable.

Do not hardcode advocate records or use mock data as production data.

### 2. Search and Filtering

If supported by the available advocate data, implement lightweight client-side search or filtering by advocate name and specialization.

Do not add a complex search engine or unnecessary database functionality for this feature.

Search must not expose private information.

### 3. Start Chat Button

Every eligible advocate entry must provide a clearly visible **Chat** action.

When clicked:

1. Prevent duplicate clicks while the request is in progress.
2. Call the existing conversation creation or reopen endpoint.
3. Handle the existing-conversation case correctly.
4. Handle authorization, network, and server errors.
5. Use the returned conversation ID.
6. Navigate to the shared chat page for that conversation.
7. Load the conversation's existing history.

Do not create a local-only conversation that is not persisted by the backend.

### 4. Duplicate Prevention

Ensure repeated clicks, page refreshes, and reopening a conversation do not create duplicate USER–ADVOCATE conversations.

Rely on backend validation and database uniqueness for correctness; frontend button disabling is only a usability safeguard.

## Acceptance Criteria

- The directory displays real eligible advocates from the backend.
- The USER can open a chat with a selected advocate.
- Existing conversations are reopened.
- Duplicate conversations are not created.
- Loading, empty, and error states work correctly.
- Unauthorized recipients cannot be selected successfully.

Add relevant tests and append results to `logs.md`.

---

# Milestone 4 — USER Messages Page

## Objective

Provide a central location where a USER can see and reopen all authorized conversations.

## Tasks

1. Fetch conversations belonging to the authenticated USER.
2. Display the other participant's safe profile information.
3. Show the latest message preview where available.
4. Show the latest message timestamp where available.
5. Show unread counts or read indicators when supported by the backend.
6. Provide an appropriate empty state when the USER has not started a conversation.
7. Include loading and recoverable error states.
8. Allow the USER to open a conversation.
9. Refresh conversation data after sending or receiving messages using existing mechanisms.
10. Prevent duplicate conversations from being created when the user opens an existing conversation.

If the USER has no conversations, provide a direct link to **Find an Advocate**.

Use pagination or another existing scalable approach where supported. Do not fetch an unlimited message history merely to render the conversation list.

## Acceptance Criteria

- Only the authenticated USER's conversations appear.
- Clicking an entry opens the correct conversation.
- Unread information is accurate according to the existing backend.
- Empty, loading, and error states are usable.
- The page does not expose unrelated users' private conversations.

Append implementation and test results to `logs.md`.

---

# Milestone 5 — ADVOCATE Messages Page

## Objective

Give advocates a visible inbox for incoming USER conversations.

## Tasks

1. Add a **Messages** navigation entry to the ADVOCATE dashboard.
2. Fetch the authenticated ADVOCATE's conversations through FastAPI.
3. Display the USER's permitted profile information.
4. Display the latest message preview and timestamp when available.
5. Display unread information when supported.
6. Allow the ADVOCATE to open a conversation.
7. Allow the ADVOCATE to reply through the existing message API.
8. Show loading, empty, error, and session-expiration states.
9. Ensure new conversations become visible through the existing refresh, polling, or real-time mechanism.
10. Provide a clear empty state when the advocate has not received messages.

### Security Requirements

- An advocate must not access another advocate's inbox.
- Changing a conversation ID must not bypass authorization.
- The backend must determine the authenticated sender.
- An ADVOCATE must not initiate unauthorized conversations with arbitrary users if the intended policy permits only USER-initiated conversations.

Do not rely on hiding unauthorized entries in the frontend as the security mechanism.

## Acceptance Criteria

- ADVOCATE accounts have a visible Messages option.
- Incoming conversations appear in the inbox.
- The advocate can open and respond to authorized conversations.
- Unauthorized conversations remain inaccessible.
- Existing ADVOCATE dashboard functionality remains intact.

Append implementation and test results to `logs.md`.

---

# Milestone 6 — Shared Chat Interface

## Objective

Provide a complete conversation interface that both USER and ADVOCATE can use.

## Tasks

### 1. Conversation Header

Display appropriate information about the other participant, using only permitted profile fields.

Include a back-navigation action to the relevant Messages page.

### 2. Message History

- Load the correct conversation history from FastAPI.
- Render messages in chronological order.
- Visually distinguish messages sent by the authenticated participant from messages received.
- Display message content, timestamp, and available delivery or read information.
- Support pagination or incremental history loading if available.
- Provide a useful empty state for new conversations.

Do not download every historical message at once if pagination is supported.

### 3. Send Message

- Provide a message composer and Send action.
- Disable submission for empty or whitespace-only messages when the backend does not accept them.
- Display sending, success, and failure states.
- Prevent accidental duplicate submissions.
- Clear the composer only when the message has been accepted successfully.
- Refresh the conversation list after sending if necessary.
- Preserve the draft when a request fails, where practical.

### 4. Read and Unread State

Use the existing read-state endpoints and data model.

- Mark messages as read at the appropriate time.
- Update unread counts after reading.
- Avoid marking messages as read merely because a conversation list item is rendered.
- Avoid excessive repeated read-state requests.

### 5. Receiving Messages and Recovery

Inspect the existing real-time implementation before choosing how to receive messages.

- Reuse the existing real-time broadcast/subscription mechanism if functional.
- Preserve the existing polling fallback.
- Recover after browser tab visibility changes or temporary network interruptions.
- Prevent duplicate message rendering when a real-time event and polling response deliver the same message.
- Clean up subscriptions, event listeners, and polling resources when components unmount.
- Avoid unbounded polling or unnecessary network requests.

Do not claim real-time delivery has been verified merely because a server endpoint returns a successful HTTP status. Test actual browser behavior if the environment allows it and document any remaining limitation.

### 6. Responsive UI and Accessibility

Ensure:

- The message list and composer work on mobile and desktop.
- The message composer is keyboard accessible.
- Buttons have meaningful labels.
- Loading and error states are understandable.
- Long messages and filenames do not break the layout.
- Focus and navigation remain usable.

## Acceptance Criteria

- USER and ADVOCATE can exchange messages in an authorized conversation.
- Message history persists across refreshes.
- Sending and receiving states are handled correctly.
- Read/unread state follows backend behavior.
- Polling or real-time recovery works according to the existing architecture.
- No duplicate messages appear due to repeated events.

Append the milestone implementation and test results to `logs.md`.

---

# Milestone 7 — Document and Attachment Sharing

## Objective

Allow USER and ADVOCATE participants to exchange supported documents privately.

## Tasks

### 1. Upload UI

Implement or connect the attachment picker to the existing FastAPI upload workflow.

- Display the selected filename and file size.
- Validate file type and size against the backend's actual permitted limits.
- Display upload progress if supported by the current client.
- Prevent duplicate submissions.
- Display upload errors clearly.
- Send attachment metadata through the existing message workflow.
- Show the attachment in the conversation after successful upload.

Do not invent file-size limits or supported file types. Inspect and reuse the backend configuration.

### 2. Secure Storage

- Keep the existing `chat-attachments` bucket private.
- Upload through the authorized backend workflow already in use.
- Do not make the bucket public to simplify downloading.
- Do not expose service-role credentials in browser code.
- Store only necessary attachment metadata in PostgreSQL.
- Follow the existing storage-key and ownership conventions.

### 3. Download UI

- Display permitted filename, file type, size, and timestamp where available.
- Provide a Download or Open action appropriate to the supported file type.
- Request access through the authorized backend endpoint.
- Verify that the authenticated participant belongs to the conversation before allowing a download.
- Handle expired signed URLs and failed downloads appropriately.
- Avoid exposing permanent public object URLs.

### 4. Document Security

Ensure the backend validates:

- Authenticated participant identity.
- Conversation membership.
- Attachment-to-conversation association.
- File type and size.
- Access to the underlying private storage object.

Do not trust a frontend-provided attachment ID or storage path without server-side validation.

## Acceptance Criteria

- USER can upload and share a supported document.
- ADVOCATE can retrieve it only when authorized.
- ADVOCATE can upload and share a supported document.
- USER can retrieve it only when authorized.
- Unrelated users cannot download attachments by guessing IDs.
- Files remain private in storage.
- Upload and download failures are handled gracefully.

Append implementation and test results to `logs.md`.

---

# Milestone 8 — Frontend and Backend Integration Testing

## Objective

Verify the full workflow rather than relying only on isolated unit tests.

## Backend Tests

Run the existing chat test suites, including the project's equivalents of:

- `tests/test_chat.py`
- `tests/test_chat_api.py`

Add or update tests for missing functionality.

Test at least:

1. USER directory access.
2. ADVOCATE directory behavior according to the access policy.
3. USER creates a conversation.
4. USER reopens the same conversation.
5. Duplicate conversation prevention.
6. ADVOCATE sees only their own conversations.
7. USER sees only their own conversations.
8. Both participants can send and retrieve messages.
9. Unrelated participants cannot read messages.
10. Unrelated participants cannot download attachments.
11. Read/unread state changes correctly.
12. Empty directory and empty inbox behavior.
13. Invalid tokens and expired sessions.
14. Invalid request bodies and unsupported file uploads.

Use isolated test data and clean up test records safely.

## Frontend Tests and Checks

Run the project's existing checks, including:

- Frontend TypeScript typecheck, such as `npx tsc --noEmit`, if applicable.
- Existing lint and build commands where configured.
- Relevant component or integration tests.
- Existing regression tests for dashboard and authentication behavior.

Do not claim a command passed unless it was actually executed and its exit status verified.

## Two-Session End-to-End Test

Where the environment permits, test with two independent authenticated browser sessions:

**Session A — USER**
1. Sign in as USER.
2. Open Find an Advocate.
3. Select an ADVOCATE.
4. Start or reopen the conversation.
5. Send a text message.
6. Upload a supported document.
7. Open Messages and verify the conversation appears.

**Session B — ADVOCATE**
1. Sign in as the corresponding ADVOCATE.
2. Open Messages.
3. Verify the conversation appears.
4. Open the conversation.
5. Reply to the USER.
6. Download the shared document.

Return to Session A and verify that the reply appears and the document remains accessible.

### Negative Authorization Tests

Where possible, attempt to access a conversation and attachment belonging to unrelated participants. Verify that the backend rejects the requests.

If a live browser test cannot be run, state that explicitly and distinguish unit-tested functionality from functionality verified end-to-end.

## Acceptance Criteria

- Existing tests remain passing, apart from previously documented baseline failures.
- New functionality has relevant automated coverage.
- Typecheck and configured build checks pass.
- Live end-to-end results are recorded honestly.
- Authorization failures are verified.

Append all actual test commands and results to `logs.md`.

---

# Milestone 9 — Security, Regression, and Code Quality Review

## Objective

Ensure the feature is secure, maintainable, and compatible with the existing application.

## Tasks

Review:

- Authentication and role checks on every chat endpoint.
- Conversation ownership and participant authorization.
- Advocate directory data exposure.
- Message sender identity enforcement.
- Attachment upload and download authorization.
- Private storage configuration.
- Token and secret exposure in frontend code.
- Duplicate message handling and idempotency.
- Polling and subscription cleanup.
- Pagination and excessive database requests.
- Error handling and accidental disclosure of internal exceptions.
- PostgreSQL-authoritative and SQLite fallback compatibility.
- Existing dashboard navigation and authentication regressions.

Do not broaden the scope into an unrelated security overhaul. If an unrelated issue is discovered, document it separately and only change it if it blocks or directly compromises the chat feature.

Do not automatically change unrelated RLS policies, database permissions, or existing legal application behavior as part of this UI task.

## Acceptance Criteria

- No new credentials or secrets are exposed.
- No unauthorized conversation or attachment access is introduced.
- Existing application features remain functional.
- Relevant lint, typecheck, tests, and build checks are completed where available.
- Remaining security concerns are documented.

Append the review findings to `logs.md`.

---

# Milestone 10 — Final Verification and Handover

## Objective

Deliver a working chat workflow and a verifiable implementation report.

## Tasks

1. Verify the complete USER–ADVOCATE workflow from the frontend.
2. Verify that all required navigation entries are visible.
3. Confirm that the shared chat interface uses existing FastAPI APIs.
4. Confirm that attachment sharing respects private storage.
5. Re-run relevant tests after the final changes.
6. Review the Git diff for accidental deletions, unrelated changes, credentials, or generated files.
7. Confirm that previous `logs.md` entries remain unchanged and new milestone entries are appended.
8. Record the final status of every milestone.
9. List any incomplete work and the exact steps needed to finish it.

## Required Final Report

Provide:

- A milestone-by-milestone completion table.
- Files created and modified.
- New and reused API endpoints.
- Frontend routes added or connected.
- Backend and frontend test commands with actual results.
- End-to-end verification status.
- Security checks completed.
- Known limitations and unresolved blockers.
- Confirmation that `logs.md` was appended to, not overwritten.

Use statuses such as `PASS`, `PARTIAL`, `BLOCKED`, or `NOT RUN`. Do not label untested functionality as verified.

---

# Final Definition of Done

The feature is complete only when:

- A USER can visibly find an advocate.
- A USER can start or reopen a conversation.
- A USER has a Messages page listing their conversations.
- An ADVOCATE has a Messages page listing their incoming conversations.
- Both authorized participants can exchange persistent messages.
- Both can share and retrieve supported documents securely.
- Unauthorized users cannot access conversations or attachments.
- Existing application functionality is preserved.
- Relevant automated checks have been executed.
- The final implementation and every milestone are documented in the existing root `logs.md`.

**Start with Milestone 0. Inspect the actual code, record the baseline, and proceed sequentially. Do not skip directly to UI coding without verifying the existing APIs.**
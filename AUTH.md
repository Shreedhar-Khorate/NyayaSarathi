# Pull Request: Authentication, Supabase Persistence & User Profile Infrastructure

## PR Title
`feat(auth): Supabase Database Migration, Google OAuth, User Profiles, and RBAC Infrastructure`

---

## 📌 Summary of Changes

This Pull Request delivers a comprehensive, production-grade identity and user persistence system for **NyayaSarathi**. It transitions authentication from ephemeral/local SQLite user storage to **Supabase PostgreSQL**, adds **Google OAuth 2.0 (PKCE) authentication**, introduces **Role-Based Access Control (RBAC)** across `USER`, `JUDGE`, and `ADMIN` personas, and provides complete user profile management along with an activity history feed.

---

## 🚀 Key Features & Architectural Additions

### 1. Database & Persistence Layer (Supabase PostgreSQL)
- **Supabase Client Integration**: Introduced a singleton service layer ([`backend/services/supabase_client.py`](file:///c:/Users/Shreedhar%20Khorate/Desktop/NyayaSarathi/backend/services/supabase_client.py)) handling connection failover, schema validation, and health checks.
- **Relational User Schema**:
  - `public.users`: Holds credentials, Google OAuth linkage (`google_sub`), verified full name, avatar, organization, designation, profile completion flag, and role enum (`USER`, `JUDGE`, `ADMIN`).
  - `public.user_activity_history`: Audit trail for queries, document uploads, predictions, and onboarding milestones.
- **Migration & Seeding Tooling**:
  - [`backend/scripts/supabase_schema.sql`](file:///c:/Users/Shreedhar%20Khorate/Desktop/NyayaSarathi/backend/scripts/supabase_schema.sql): Complete SQL DDL with indexing and RLS compatibility.
  - [`backend/scripts/setup_supabase.py`](file:///c:/Users/Shreedhar%20Khorate/Desktop/NyayaSarathi/backend/scripts/setup_supabase.py): Interactive/automated database initializer.
  - [`backend/scripts/migrate_sqlite_users.py`](file:///c:/Users/Shreedhar%20Khorate/Desktop/NyayaSarathi/backend/scripts/migrate_sqlite_users.py): Seamless data migration utility from legacy SQLite to Supabase.
  - [`backend/scripts/seed_demo_logins.py`](file:///c:/Users/Shreedhar%20Khorate/Desktop/NyayaSarathi/backend/scripts/seed_demo_logins.py): Automated seeding for demo user, judge, and admin credentials.

### 2. Multi-Role RBAC & Security
- **Role Hierarchy**:
  - `USER`: Advocates, litigators, and citizens.
  - `JUDGE`: Judicial officers with bench-level privileges.
  - `ADMIN`: Platform administration and governance.
- **Privilege Escalation Prevention**: Profile updates restrict self-editing of `role` fields via Pydantic schemas; role elevation requires direct administrative or database updates.
- **Default Seed Accounts**:
  - **User**: `user@nyayasarathi.in` / `User@12345`
  - **Judge**: `judge@nyayasarathi.in` / `Judge@12345`
  - **Admin**: `admin@nyayasarathi.in` / `Admin@12345`

### 3. Google OAuth 2.0 Integration
- **Direct & Secure Flow**: Implemented Google Identity Services OAuth callback handler ([`backend/routers/google_oauth.py`](file:///c:/Users/Shreedhar%20Khorate/Desktop/NyayaSarathi/backend/routers/google_oauth.py)) verifying Google JWT ID tokens.
- **Account Linking & Provisioning**: Automatically detects existing users by verified email, links `google_sub`, or provisions new verified accounts.
- **Frontend Components**:
  - [`GoogleAuthButton.tsx`](file:///c:/Users/Shreedhar%20Khorate/Desktop/NyayaSarathi/nyayasarathi-app/src/components/auth/GoogleAuthButton.tsx): One-click Google sign-in button.
  - [`useGoogleAuth.ts`](file:///c:/Users/Shreedhar%20Khorate/Desktop/NyayaSarathi/nyayasarathi-app/src/lib/useGoogleAuth.ts): Client hook managing token handoff and session initialization.

### 4. User Profile, Onboarding & Activity History
- **Profile Hub ([`nyayasarathi-app/src/app/profile/page.tsx`](file:///c:/Users/Shreedhar%20Khorate/Desktop/NyayaSarathi/nyayasarathi-app/src/app/profile/page.tsx))**:
  - Live profile editing (name, organization, designation, avatar).
  - Judicial/Advocate badge indicators matching user role.
  - Chronological activity log feed with pagination and milestone tracking.
- **Onboarding Flow ([`nyayasarathi-app/src/app/profile/complete/page.tsx`](file:///c:/Users/Shreedhar%20Khorate/Desktop/NyayaSarathi/nyayasarathi-app/src/app/profile/complete/page.tsx))**:
  - Guides new signups to complete credentials and professional details before navigating judicial tools.
- **Avatar & Navigation**:
  - [`UserAvatar.tsx`](file:///c:/Users/Shreedhar%20Khorate/Desktop/NyayaSarathi/nyayasarathi-app/src/components/ui/UserAvatar.tsx): Dynamic avatar dropdown showing role badges (`JUDGE`, `ADMIN`), account status, quick profile links, and secure logout.
  - [`NavAndFooter.tsx`](file:///c:/Users/Shreedhar%20Khorate/Desktop/NyayaSarathi/nyayasarathi-app/src/components/layout/NavAndFooter.tsx): Integrated session awareness and login/logout state switching.

---

## 🛠️ API Surface Additions

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/google` | Google OAuth token verification and account linking |
| `GET` | `/api/profile` | Retrieve authenticated user profile and details |
| `PUT` | `/api/profile` | Update profile information (name, organization, designation, avatar) |
| `POST` | `/api/profile/complete` | Complete mandatory user onboarding |
| `GET` | `/api/profile/history` | Paginated activity history feed for current user |

---

## 🧪 Test Verification & Quality Assurance

| Test Suite | Command | Result |
| :--- | :--- | :--- |
| **Supabase Configuration & Connectivity** | `python -m unittest tests/test_supabase_config.py` | ✅ **PASS** |
| **Profile, RBAC & Activity History** | `python -m unittest tests/test_profile_and_history.py` | ✅ **PASS** |
| • Privilege Escalation Guard | Verify user cannot modify role to ADMIN or JUDGE | ✅ PASS |
| • Profile Onboarding Flow | Verify complete profile milestone and history | ✅ PASS |
| • Activity Logging | Verify audit log generation on platform events | ✅ PASS |
| **Complete Backend Test Suite** | `python -m unittest discover tests` | ✅ **All Tests Passing** |
| **Frontend Production Build** | `npm run build` | ✅ **Build successful with zero type or lint errors** |

---

## 📁 Key Files Touched

### Backend
- `backend/services/supabase_client.py` — Supabase database client and connectivity checks
- `backend/services/user_repository.py` — Database queries and data access layer for users and activity
- `backend/routers/google_oauth.py` — Google OAuth authentication endpoints
- `backend/routers/profile.py` — User profile, onboarding, and activity history endpoints
- `backend/schemas/auth.py` — Authentication and profile request/response models
- `backend/scripts/supabase_schema.sql` — PostgreSQL DDL and initial demo data
- `backend/scripts/setup_supabase.py` — Supabase database initialization script
- `backend/scripts/seed_demo_logins.py` — Demo logins seeding script
- `backend/scripts/migrate_sqlite_users.py` — SQLite to Supabase data migration script
- `backend/tests/test_profile_and_history.py` — Unit tests for profile and RBAC
- `backend/tests/test_supabase_config.py` — Configuration tests for database

### Frontend
- `nyayasarathi-app/src/app/profile/page.tsx` — Full user profile management and activity timeline
- `nyayasarathi-app/src/app/profile/complete/page.tsx` — Profile completion onboarding screen
- `nyayasarathi-app/src/components/ui/UserAvatar.tsx` — User avatar dropdown with role indicators
- `nyayasarathi-app/src/components/auth/GoogleAuthButton.tsx` — Google Sign-In button component
- `nyayasarathi-app/src/components/layout/NavAndFooter.tsx` — Nav updates with authenticated user menu
- `nyayasarathi-app/src/lib/auth.ts` — Authentication client helper and token storage
- `nyayasarathi-app/src/lib/useGoogleAuth.ts` — Google OAuth React hook

---

## 🔒 Security Considerations
- **Password Hashing**: BCrypt hashing with configurable rounds (`$2b$12$`).
- **Token Security**: HS256 JWT tokens with user id, email, and role claims.
- **SQL Injection Prevention**: Parameterized queries via Supabase PostgREST client.
- **Self-Escalation Protection**: Explicit server-side validation ensuring users cannot modify their own `role`.

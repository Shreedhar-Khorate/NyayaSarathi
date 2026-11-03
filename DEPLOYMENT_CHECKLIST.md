# NyayaSarathi — Production Deployment Checklist

Step-by-step pre-flight checklist for deploying NyayaSarathi across **Supabase**, **Render**, and **Vercel**.

---

## Phase 1: Supabase Configuration & Database Initialization

- [ ] **1.1. Create a Fresh Supabase Project**
  - Navigate to Supabase Dashboard and create a new project in the target region (e.g., `ap-south-1` Mumbai).
  - Copy and record configuration keys into your secure vault (all production credentials must remain redacted from documentation):
    - Project Reference ID: `[REDACTED]`
    - PostgreSQL Connection String (Transaction Pooler - port `6543`, `Transaction` mode): `[REDACTED]`
    - Project URL (`https://[PROJECT_REF].supabase.co`): `[REDACTED]`
    - `anon` Public API Key: `[REDACTED]`
    - `service_role` Secret Key: `[REDACTED]`

- [ ] **1.2. Execute Database Migrations in Correct Sequence**
  - Open Supabase SQL Editor and run the DDL scripts in this strict order:
    1. Base Tables (`backend/scripts/setup_supabase.py` DDL block: `users`, `rag_documents`, `rag_chunks`, `judgments`, `ingestion_log`).
    2. `backend/migrations/001_profile_and_history.sql` (`user_profiles`, `user_activity_history`).
    3. `backend/migrations/002_role_audit_history.sql`.
    4. `backend/migrations/003_durable_role_audit_retention.sql`.
    5. `backend/migrations/004_judge_case_assignments.sql`.
    6. `backend/migrations/005_remove_judge_role.sql`.
    7. `backend/migrations/006_chat_tables.sql` (`chat_conversations`, `chat_messages`, `chat_attachments`, `chat_read_states`).

- [ ] **1.3. Configure Supabase Storage Buckets**
  - In Supabase Dashboard -> Storage:
    - Create a **Private** bucket named: `chat-attachments`
    - Create a **Private** bucket named: `document-uploads` (for OCR & RAG files)
    - Verify RLS policies: Service role has full access; direct public access is denied.

- [ ] **1.4. Enable Supabase Realtime**
  - In Supabase Dashboard -> Database -> Publications:
    - Ensure `supabase_realtime` publication includes `chat_messages` or verify broadcast endpoint access is active.

---

## Phase 2: Backend Deployment (Render)

- [ ] **2.1. Update `backend/requirements.txt`**
  - Add `psycopg2-binary>=2.9.9` to `requirements.txt`.
  - Ensure lightweight headless OpenCV is specified: `opencv-python-headless>=4.10.0` (avoids missing X11/GL system library crashes).

- [ ] **2.2. Fix CORS Origins in `backend/main.py`**
  - Replace `allow_origin_regex=r"https?://.*"` with dynamic origin parsing from `CORS_ORIGINS` environment variable.
  - Set production Vercel frontend URL in `CORS_ORIGINS`.

- [ ] **2.3. Create Render Web Service**
  - **Type:** Web Service
  - **Environment:** Python 3.12 (or Docker if PaddleOCR binaries require native Debian packages)
  - **Root Directory:** `backend`
  - **Build Command:** `pip install --no-cache-dir -r requirements.txt`
  - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2`
  - **Plan Size:** Minimum **Standard (2GB RAM)** recommended if running PaddleOCR.

- [ ] **2.4. Configure Render Environment Variables**
  - Set `APP_NAME="NyayaSarathi API"`
  - Set `DEBUG="false"`
  - Set `DATABASE_URL` = `[REDACTED]` (Supabase transaction pooler URL with `sslmode=require`)
  - Set `SUPABASE_URL` = `[REDACTED]`
  - Set `SUPABASE_SERVICE_ROLE_KEY` = `[REDACTED]`
  - Set `SUPABASE_ANON_KEY` = `[REDACTED]`
  - Set `JWT_SECRET_KEY` = `[REDACTED]` (Strong 64-character random hex: `openssl rand -hex 32`)
  - Set `CORS_ORIGINS` (e.g. `["https://[YOUR_APP].vercel.app"]`)
  - Set `FRONTEND_BASE_URL` (`https://[YOUR_APP].vercel.app`)
  - Set LLM API keys (`GEMINI_API_KEY`, `GROQ_API_KEY`, etc.) = `[REDACTED]`

- [ ] **2.5. Health Check Verification**
  - Verify `GET https://[YOUR_BACKEND].onrender.com/health` returns `200 OK`.
  - Verify `GET https://[YOUR_BACKEND].onrender.com/api/chat/status` reports `"mode": "postgresql"`.

---

## Phase 3: Frontend Deployment (Vercel)

- [ ] **3.1. Create Vercel Project**
  - Connect your Git repository.
  - **Framework Preset:** Next.js
  - **Root Directory:** `nyayasarathi-app`
  - **Build Command:** `next build`
  - **Output Directory:** `.next`

- [ ] **3.2. Configure Vercel Environment Variables**
  - `NEXT_PUBLIC_API_URL`: `https://[YOUR_BACKEND].onrender.com`

- [ ] **3.3. Verify OAuth & Callback Redirects**
  - In Google Cloud Console -> Credentials:
    - Add Authorized Javascript Origin: `https://[YOUR_APP].vercel.app`
    - Add Authorized Redirect URI: `https://[YOUR_BACKEND].onrender.com/api/auth/google/callback`

---

## Phase 4: Production Smoke Testing

- [ ] **4.1. Account Registration & Auth Flow**
  - Register a new user at `https://[YOUR_APP].vercel.app/signup`.
  - Check Supabase `public.users` table to verify user is inserted into PostgreSQL.
  - Complete profile onboarding and verify record in `public.user_profiles`.

- [ ] **4.2. Chat & Realtime Test**
  - Log in with two different accounts (one USER, one ADVOCATE).
  - Open a conversation and send a message.
  - Verify message is inserted into `public.chat_messages`.
  - Upload an attachment and confirm storage in Supabase bucket `chat-attachments`.

- [ ] **4.3. Restart Resilience Verification**
  - Trigger a manual redeploy/restart of the Render backend.
  - Refresh the frontend and confirm users, conversations, and sessions persist without data loss.


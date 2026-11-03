# NyayaSarathi — Production Deployment Fixes Guide

This document catalogs every critical and high-severity issue identified during the deployment audit, complete with exact code paths, explanations, and implementation steps. All secret values and sensitive connection strings are strictly redacted.

---

### Issue 1: Missing `psycopg2-binary` in `requirements.txt`
- **Severity:** **CRITICAL**
- **File:** `backend/requirements.txt`
- **Problem:** Authoritative PostgreSQL connections and repository operations import `psycopg2`. However, `psycopg2` or `psycopg2-binary` is completely absent from `backend/requirements.txt`.
- **Why it matters:** On Render, `pip install -r requirements.txt` will succeed, but the app will find `PSYCOPG2_AVAILABLE = False` and fall back to SQLite, causing all production data to be stored on ephemeral local disk and erased on restart.
- **Recommended Solution:** Add `psycopg2-binary>=2.9.9` to `backend/requirements.txt`.
- **Implementation Steps:**
  Append to `backend/requirements.txt`:
  ```text
  psycopg2-binary>=2.9.9
  ```

---

### Issue 2: Broken / Dormant Supabase Project Credentials
- **Severity:** **CRITICAL**
- **File:** `backend/.env` (and cloud deployment environment variables)
- **Problem:** Credentials in `backend/.env` reference a Supabase project reference that fails DNS lookups and transaction pooler handshakes (`FATAL: tenant/user not found`).
- **Why it matters:** The backend cannot connect to Supabase PostgreSQL or REST endpoints in production.
- **Recommended Solution:** Provision an active Supabase project and update `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and `DATABASE_URL` in the deployment settings.
- **Implementation Steps:**
  Update Render and local `.env` with the active Supabase connection string and project URL.

---

### Issue 3: Insecure Wildcard Regex in CORS Configuration
- **Severity:** **CRITICAL**
- **File:** `backend/main.py` (lines 43–55)
- **Problem:**
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=[...],
      allow_origin_regex=r"https?://.*",
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- **Why it matters:** `allow_origin_regex=r"https?://.*"` allows **any website** on the internet to send credentialed requests to your API. An attacker hosting a malicious site can make authenticated calls to `/api/admin/users`, steal profile data, or perform CSRF-like attacks.
- **Recommended Solution:** Remove `allow_origin_regex` and parse `CORS_ORIGINS` from the environment.
- **Implementation Steps:**
  In `backend/main.py`:
  ```python
  import json
  cors_env = os.getenv("CORS_ORIGINS")
  if cors_env:
      try:
          allowed_origins = json.loads(cors_env)
      except Exception:
          allowed_origins = [o.strip() for o in cors_env.split(",") if o.strip()]
  else:
      allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

  app.add_middleware(
      CORSMiddleware,
      allow_origins=allowed_origins,
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

---

### Issue 4: Base Database Tables Missing from Migration Folder
- **Severity:** **HIGH**
- **File:** `backend/migrations/`
- **Problem:** Tables `users`, `rag_documents`, `rag_chunks`, `judgments`, and `ingestion_log` are defined inside `backend/scripts/setup_supabase.py` rather than as `000_base_tables.sql` in the migrations folder.
- **Why it matters:** Running migration scripts (`backend/scripts/run_migrations.py`) on a fresh Supabase database fails immediately because `001_profile_and_history.sql` attempts to add foreign keys to `public.users`, which does not exist yet.
- **Recommended Solution:** Create `backend/migrations/000_base_tables.sql` containing the core DDL.
- **Implementation Steps:**
  Create `backend/migrations/000_base_tables.sql` with:
  ```sql
  CREATE TABLE IF NOT EXISTS public.users (
      id TEXT PRIMARY KEY,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      full_name TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'USER',
      created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
  );
  CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
  CREATE INDEX IF NOT EXISTS idx_users_role ON public.users(role);

  CREATE TABLE IF NOT EXISTS public.rag_documents (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      filename TEXT NOT NULL,
      file_type TEXT NOT NULL,
      file_size BIGINT NOT NULL,
      storage_path TEXT,
      total_pages INTEGER NOT NULL DEFAULT 1,
      total_chunks INTEGER NOT NULL DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'indexed',
      created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
      user_id TEXT
  );

  CREATE TABLE IF NOT EXISTS public.rag_chunks (
      id TEXT PRIMARY KEY,
      document_id TEXT NOT NULL REFERENCES public.rag_documents(id) ON DELETE CASCADE,
      chunk_index INTEGER NOT NULL,
      page_number INTEGER NOT NULL DEFAULT 1,
      paragraph_number INTEGER NOT NULL DEFAULT 1,
      section_title TEXT,
      token_count INTEGER NOT NULL DEFAULT 0,
      text TEXT NOT NULL
  );
  ```

---

### Issue 5: Ephemeral File Storage for OCR & Document RAG
- **Severity:** **HIGH**
- **File:** `backend/routers/ocr.py`, `backend/services/document_processor.py`
- **Problem:** OCR uploads write directly to local disk (`backend/data/uploads`). When a document is indexed for RAG, the system looks for the file on disk.
- **Why it matters:** On Render, files written to local disk are wiped whenever the service restarts, scales, or redeploys. Subsequent attempts to re-read or download original legal PDFs will fail.
- **Recommended Solution:** Upload files to a Supabase Storage bucket (`document-uploads`) and store the storage key in `rag_documents.storage_path`.
- **Implementation Steps:**
  Mirror the storage bucket logic already implemented in `backend/routers/chat.py` for chat attachments.

---

### Issue 6: Heavy Native Dependencies in Free-Tier Cloud Deployments
- **Severity:** **HIGH**
- **File:** `backend/requirements.txt` (`paddlepaddle==2.6.2`, `paddleocr==2.8.1`, `opencv-python`)
- **Problem:** PaddleOCR and OpenCV load heavy shared C libraries and consume >1GB RAM during model inference.
- **Why it matters:** Free or starter instances on Render (512MB RAM) will crash with `Error: Container killed (OOM)` upon receiving the first OCR request.
- **Recommended Solution:**
  1. Replace `opencv-python` with `opencv-python-headless` in `requirements.txt`.
  2. Use a Render plan with at least 2GB RAM, or deploy the OCR workload as a standalone serverless microservice.

---

### Issue 7: Unauthenticated Document Upload Endpoint
- **Severity:** **MEDIUM**
- **File:** `backend/routers/ocr.py` (lines 44–110)
- **Problem:** `POST /api/ocr/upload` allows anonymous uploads (`user_id = Depends(get_optional_user_id)`).
- **Why it matters:** Anonymous callers can flood the API with multi-megabyte PDF uploads, exhausting server memory and compute.
- **Recommended Solution:** Require `current_user: Dict[str, Any] = Depends(get_current_user)` on all document processing endpoints.

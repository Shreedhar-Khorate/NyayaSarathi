<div align="center">

# ⚖️ NyayaSarathi
### AI-Powered Judicial Case Intelligence & Decision Support System

[![License: MIT](https://img.shields.io/badge/License-MIT-gold.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

[![Render](https://img.shields.io/badge/Render-FastAPI%20Backend-46E3B7?style=flat-square&logo=render&logoColor=black)](https://render.com)
[![Vercel](https://img.shields.io/badge/Vercel-Next.js%20Frontend-000000?style=flat-square&logo=vercel&logoColor=white)](https://vercel.com)
[![Tests Passing](https://img.shields.io/badge/Tests-264%20Passed-success?style=flat-square&logo=pytest&logoColor=white)](backend/tests/)
[![KeepAlive Architecture](https://img.shields.io/badge/KeepAlive%20Bots-Active%2024%2F7-blueviolet?style=flat-square&logo=uptimerobot&logoColor=white)](#-dual-keep-alive-bots-infrastructure)

<p align="center">
  <strong>Empowering Indian Advocates, Judicial Researchers, and Litigants with Explainable Legal AI</strong>
</p>

<p align="center">
  <a href="#-executive-overview">📌 Overview</a> •
  <a href="#-core-capabilities">✨ Capabilities</a> •
  <a href="#-dual-keep-alive-bots-infrastructure">🤖 Keep-Alive Architecture</a> •
  <a href="#-quickstart--installation">⚡ Quickstart</a> •
  <a href="#-api-endpoint-reference">📡 API Reference</a>
</p>

---

</div>

## 📌 Executive Overview

**NyayaSarathi** is a next-generation judicial intelligence and legal assistance platform engineered specifically for the Indian legal framework. By combining **Retrieval-Augmented Generation (RAG)**, **Bayesian Dirichlet probability calibration**, **Reciprocal Rank Fusion (RRF)**, and **Multi-Agent Adversarial Bench Simulation**, NyayaSarathi delivers verifiable, hallucination-resistant legal decision support.

The system features dedicated workflows for **Citizens (Litigants)**, **Advocates**, and **Administrators**, underpinned by enterprise-grade **Row-Level Security (RLS)** in Supabase PostgreSQL.

---

## 🏛️ System Architecture

```
                                  ┌───────────────────────────┐
                                  │      Client Browser       │
                                  │  (Next.js 16 + React 19)  │
                                  └─────────────┬─────────────┘
                                                │ HTTPS / REST
                                                ▼
                                  ┌───────────────────────────┐
                                  │   FastAPI Gateway Engine  │
                                  │   (Python 3.12 on Render) │
                                  └──────┬──────────────┬─────┘
                                         │              │
                   ┌─────────────────────┴───┐      ┌───┴─────────────────────┐
                   ▼                         ▼      ▼                         ▼
         ┌───────────────────┐    ┌────────────────────┐    ┌─────────────────┐
         │ 🤖 AI Orchestrator│    │ 🔍 Hybrid Search   │    │ 📄 OCR Pipeline │
         │  • Gemini 1.5     │    │  • Okapi BM25      │    │  • PaddleOCR    │
         │  • Groq Llama 3.3 │    │  • TF-IDF Vector   │    │  • PyMuPDF      │
         │  • Dirichlet Math │    │  • RRF Reranking   │    │  • Layout Tree  │
         └─────────┬─────────┘    └─────────┬──────────┘    └────────┬────────┘
                   │                        │                        │
                   └───────────────────┐    │    ┌───────────────────┘
                                       ▼    ▼    ▼
                                ┌────────────────────────┐
                                │   Supabase PostgreSQL  │
                                │   • Full RLS Security  │
                                │   • Transaction Pooler │
                                │   • Auth & Audit Logs  │
                                └────────────────────────┘
```

---

## 🤖 Dual Keep-Alive Bots Infrastructure

Free-tier cloud deployments (such as Render Web Services and Supabase PostgreSQL) automatically sleep or pause during periods of inactivity. NyayaSarathi implements a **two-tier keep-alive bot architecture** to maintain reliable 24/7 availability:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   🤖 NyayaSarathi Dual Keep-Alive System               │
├───────────────────────────────────┬────────────────────────────────────┤
│ 🌐 Bot 1: Web Service Warm-Up Bot │ 🗄️ Bot 2: Supabase Persistence Bot │
│ Endpoint: GET /ready              │ Endpoint: GET /supa                │
│ Cadence:  Every 10–12 Minutes     │ Cadence:  Every 12–30 Minutes      │
│ Prevents: 15-minute idle spindown │ Prevents: 7-day auto-pause policy  │
│ Mechanism: HTTP readiness ping    │ Mechanism: Write + delete DB pulse │
└───────────────────────────────────┴────────────────────────────────────┘
```

### 1. Bot 1: Web Service Warm-Up Bot (`GET /ready`)
- **Target Route:** `GET /ready`
- **Function:** Queries internal readiness status without running expensive model inferences, keeping the web container warm and eliminating cold starts.

### 2. Bot 2: Supabase Active Persistence Bot (`GET /supa`)
- **Target Route:** `GET /supa` (also supports `HEAD` and `POST`)
- **Function:** Safely inserts and immediately removes a temporary timestamp entry in the database `_supabase_keepalive` table. This registers genuine database write/delete transactions so Supabase's free project inactivity policy (7 days) is never triggered.

### 3. Setting Up the Keep-Alive Monitors
You can hook up any free uptime monitoring tool (e.g., [UptimeRobot](https://uptimerobot.com), [cron-job.org](https://cron-job.org), or a scheduled task):
1. **Monitor 1 (Render Warm-Up):** Set an HTTP `GET` monitor to `<YOUR_BACKEND_URL>/ready` with an interval of **10–12 minutes**.
2. **Monitor 2 (Supabase Keep-Alive):** Set an HTTP `GET` monitor to `<YOUR_BACKEND_URL>/supa` with an interval of **15–30 minutes**.

---

## ✨ Core Capabilities

| Capability | Engine / Technology | Description |
| :--- | :--- | :--- |
| **⚖️ Judgment Success Predictor** | Bayesian Dirichlet + RRF Search | Multi-tier statistical probability engine estimating court outcome probabilities with explicit abstention guardrails. |
| **🏛️ Trial War Room** | Groq LLaMA 3.3 70B | Adversarial bench simulator generating opposing counsel arguments, judge inquiries, and rebuttal strategies. |
| **📄 Legal Document OCR** | PyMuPDF + PaddleOCR | High-precision text and layout extraction from scanned court petitions, affidavits, and orders. |
| **📜 AI Legal Drafting** | Gemini 1.5 Flash + Rule Parser | Jurisdiction-aware automated drafting for Indian High Courts, District Courts, and Tribunals. |
| **🔍 Precedent & Statute Search** | BM25 + Cosine Semantic Search | Dual-tier hybrid retrieval searching relevant precedents across Indian case law repositories. |
| **🛡️ Contract Risk Scanner** | LLM Heuristic Rules Engine | Clause-by-clause contract analysis flagging indemnity traps, termination risks, and jurisdictional ambiguities. |
| **🌐 Multilingual Interface** | i18n Localization Engine | Native user interface and translation support for **English**, **Hindi (हिंदी)**, and **Marathi (मराठी)**. |
| **🔐 Role-Based Access Control** | Supabase Auth + Row-Level Security | Granular RBAC ensuring complete data isolation between `USER`, `ADVOCATE`, and `ADMIN`. |

---

## 🚀 Quickstart & Installation

<details>
<summary><b>💻 1. Backend Setup (FastAPI & Python 3.12)</b></summary>

### Prerequisites
- Python 3.12+
- Supabase Project ([supabase.com](https://supabase.com))

### Steps
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and supply your Supabase and LLM API credentials

# Launch FastAPI development server
uvicorn main:app --reload --port 8000
```
API docs will be available at `http://localhost:8000/docs`.

</details>

<details>
<summary><b>⚡ 2. Frontend Setup (Next.js 16 & React 19)</b></summary>

### Prerequisites
- Node.js 20+
- npm or yarn

### Steps
```bash
# Navigate to frontend directory
cd nyayasarathi-app

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000

# Start local Next.js development server
npm run dev
```
Web application will be live at `http://localhost:3000`.

</details>

<details>
<summary><b>🗄️ 3. Database & Supabase Migrations</b></summary>

All relational tables and security policies are maintained via modular SQL migrations:

```bash
# Run migration script via psycopg2 connection
python backend/scripts/run_migrations.py

# Alternatively, execute the scripts sequentially in Supabase SQL Editor:
# 1. 001_profile_and_history.sql
# 2. 002_role_audit_history.sql
# 3. 003_durable_role_audit_retention.sql
# 4. 004_judge_case_assignments.sql
# 5. 005_remove_judge_role.sql
# 6. 006_chat_tables.sql
# 7. 007_supabase_keepalive.sql
# 8. 008_enable_rls_all_public_tables.sql
```

</details>

---

## 📡 API Endpoint Reference

<details>
<summary><b>🔍 Expand Complete Route Catalog (20+ Endpoints)</b></summary>

### System & Health
| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Lightweight service health ping | Public |
| `GET` | `/ready` | Deep readiness check (Database & dependencies) | Public |
| `GET / HEAD` | `/supa` | Keep-alive transaction pulse for Supabase | Public |

### Authentication & Profiles
| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register new user or advocate account | Public |
| `POST` | `/api/auth/login` | Authenticate and issue signed JWT token | Public |
| `GET` | `/api/auth/google/login` | Initiate Google OAuth 2.0 flow | Public |
| `GET` | `/api/auth/google/callback`| Google OAuth redirect callback handler | Public |
| `GET` | `/api/profile/me` | Fetch active profile and account state | Authenticated |

### Legal Intelligence & AI Workflows
| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/analyze/predict` | Predict case outcome probabilities | Authenticated |
| `POST` | `/api/war-room/simulate` | Run adversarial bench simulator | Authenticated |
| `POST` | `/api/contracts/analyze` | Scan agreement for clause-level risks | Authenticated |
| `POST` | `/api/drafts/generate` | Generate jurisdiction-specific draft | Authenticated |
| `POST` | `/api/ocr/process` | Extract structured text from scanned document | Authenticated |
| `POST` | `/api/search/precedents` | Hybrid search across Indian precedents | Authenticated |
| `POST` | `/api/qa/ask` | Grounded legal RAG question answering | Authenticated |

### Administrative Operations
| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/admin/users` | List platform accounts and current roles | Admin Only |
| `PUT` | `/api/admin/users/{id}/role` | Update user role with mandatory audit logging | Admin Only |
| `GET` | `/api/admin/audit-logs` | Retrieve immutable role change history | Admin Only |

</details>

---

## 🔒 Security & Data Protection

> [!IMPORTANT]
> **Zero Credential Leaks:** NyayaSarathi enforces zero hardcoded secrets. All credentials, API keys, database connection strings, and JWT salts are strictly loaded through environment variables.

- **Row-Level Security (RLS):** Enabled across all 13 PostgreSQL tables in Supabase, preventing unauthorized cross-tenant data access even if an anonymous key is intercepted.
- **Password Hashing:** Passwords are salted and hashed using `bcrypt` (12 rounds).
- **JWT Cryptography:** Authentication tokens use HMAC-SHA256 with strict claims validation (`sub`, `role`, `exp`, `iat`).
- **Audit Logging:** Every administrative elevation or role change is immutably recorded in the `role_audit_history` table.

---

## 🧪 Testing & Verification

NyayaSarathi features a comprehensive automated testing suite covering all backend services, math models, and security boundaries.

```bash
# Run complete test suite (264 tests)
python -m pytest backend/tests -v

# Verify Next.js frontend production build (26 routes)
cd nyayasarathi-app && npm run build
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**NyayaSarathi** — *Democratizing Legal Intelligence Through Explainable AI.*

Made with ❤️ by [Shreedhar Khorate](https://github.com/Shreedhar-Khorate)

</div>

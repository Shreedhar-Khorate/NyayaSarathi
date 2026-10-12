# 🏛️ NyayaSarathi — Demo Login Credentials

This document provides credentials for the **3 primary user roles** configured in the NyayaSarathi platform: **User**, **Judge**, and **Admin**.

These accounts are seeded into the local database (`backend/data/nyayasarathi.db`) and are ready for both **Web UI** and **REST API** authentication.

---

## 📋 Quick Reference Table

| Role | Designation / Persona | Email | Password | Access Scope |
| :--- | :--- | :--- | :--- | :--- |
| **1. User** | Adv. Rohan Verma *(Advocate / Litigant)* | `user@nyayasarathi.in` | `User@12345` | Case outcome prediction, OCR processing, Legal Research RAG |
| **2. Judge** | Hon'ble Justice S. K. Mukherjee *(Bench)* | `judge@nyayasarathi.in` | `Judge@12345` | Precedent scrutiny, judicial holdings, statutory verification |
| **3. Admin** | Judicial System Administrator | `admin@nyayasarathi.in` | `Admin@12345` | System telemetry, dataset ingestion, DB maintenance |

---

## 🔑 Account Details

### 1. User (`USER` / `ADVOCATE`)
- **Full Name**: `Adv. Rohan Verma`
- **Email**: `user@nyayasarathi.in`
- **Password**: `User@12345`
- **Role Code**: `USER`
- **Primary Capabilities**:
  - Submit case briefs to the **General Judgment Success Predictor** (`/predictor`).
  - Upload legal briefs, petitions, and orders to the **Legal Document OCR** engine (`/ocr`).
  - Handoff OCR structured documents directly to the **Legal Research** module.
  - Perform grounded legal Q&A with verified citations (`[S1]`, `[S2]`) in `/legal-research`.

---

### 2. Judge (`JUDGE`)
- **Full Name**: `Hon'ble Justice S. K. Mukherjee`
- **Email**: `judge@nyayasarathi.in`
- **Password**: `Judge@12345`
- **Role Code**: `JUDGE`
- **Primary Capabilities**:
  - Scrutinize empirical judicial precedent similarity and Dirichlet outcome probabilities.
  - Inspect authentic High Court & Supreme Court **CNR (Case Number Record)** citations.
  - Review opposing and supporting factors generated with zero probability mutation.
  - Cross-examine statutory entity extraction across IPC/BNS, CrPC/BNSS, and CPC.

---

### 3. Admin (`ADMIN`)
- **Full Name**: `Judicial System Administrator`
- **Email**: `admin@nyayasarathi.in`
- **Password**: `Admin@12345`
- **Role Code**: `ADMIN`
- **Primary Capabilities**:
  - Monitor database health and indexing across `nyayasarathi.db`.
  - Supervise Hugging Face DuckDB Parquet batch ingestion pipelines.
  - Audit Platt sigmoid calibration curves, Brier scores (`0.0738`), and system logs.
  - Manage application access tokens and authenticated sessions.

---

## 🚀 How to Authenticate

### A. Web Application (Frontend)
1. Start the frontend application:
   ```bash
   cd nyayasarathi-app
   npm run dev
   ```
2. Open your browser and navigate to:
   - **Login Page**: `http://localhost:3000/login`
3. Enter the email and password for any of the 3 accounts above.
4. Upon successful login, you will be automatically redirected to your research workspace (`/predictor`).

---

### B. REST API (Backend)
1. Start the FastAPI backend:
   ```bash
   cd backend
   python main.py
   ```
2. Send an authentication request:
   ```bash
   curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@nyayasarathi.in",
       "password": "User@12345"
     }'
   ```
3. **Example JSON Response**:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer",
     "user": {
       "id": "e43b171f-0e42-45e0-b6f2-7104b2a472c3",
       "email": "user@nyayasarathi.in",
       "full_name": "Adv. Rohan Verma",
       "role": "USER",
       "created_at": "2026-10-12T18:12:48.000000+00:00"
     }
   }
   ```
4. Use the returned `access_token` in the `Authorization` header for protected endpoints:
   ```bash
   curl -X GET "http://localhost:8000/api/auth/me" \
     -H "Authorization: Bearer <your_access_token>"
   ```

---

## 🔄 Re-seeding / Resetting Credentials

If the database is refreshed or you need to restore these default credentials, run the seed script:
```bash
cd backend
python scripts/seed_demo_logins.py
```

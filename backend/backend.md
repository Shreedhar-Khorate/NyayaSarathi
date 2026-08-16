# ⚖️ NyayaSarathi — Backend Documentation

> **NyayaSarathi** is an AI-Powered Judicial Case Intelligence & Decision Support System.
> This document details the backend architecture, every feature it supports, and the API contract for each — covering what is **currently implemented (MVP)** and what is **designed/proposed** per the project's RAG architecture.

*Last updated: August 2026*

---

## 📐 1. Architecture Overview

```
┌───────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                      │
│              nyayasarathi-app/  ·  Port 3000                │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST · HTTP/JSON
                            ▼
┌───────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│                  backend/  ·  Port 8000                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │ Ingestion &  │  │  Hybrid      │  │  Generative RAG /  │ │
│  │ OCR Pipeline │→ │  Retrieval   │→ │  XAI Synthesis     │ │
│  └─────────────┘  └──────────────┘  └────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
        ┌───────────────┬───────────────┬───────────────┐
        │  PostgreSQL   │  Qdrant       │ Elasticsearch │
        │  + Redis      │ (vector idx)  │ (lexical idx) │
        └───────────────┴───────────────┴───────────────┘
```

**Status legend used throughout this doc:**

| Badge | Meaning |
|---|---|
| ✅ **Live** | Implemented and running in `backend/main.py` today |
| 🚧 **In Progress** | Partially scaffolded or actively being built |
| 📋 **Planned** | Designed in the proposal, not yet in code |

---

## ⚙️ 2. Core Framework & Runtime

| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.8+ | Backend language |
| **FastAPI** | >=0.100.0 | Async REST API framework |
| **Uvicorn** | >=0.22.0 | ASGI server (hot-reload in dev) |
| **Pydantic** | >=2.0.0 | Request/response validation & serialization |
| **CORSMiddleware** | — | Allows `localhost:3000` (Next.js) and `localhost:5173` (Vite) origins |

**Run locally:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python main.py              # http://localhost:8000
```

---

## 🧩 3. Feature-by-Feature Breakdown

### 3.1 Judgment Success Predictor ✅ **Live**

The current MVP endpoint. Given a case type and description, returns an estimated success probability, cited precedents, and a plain-language takeaway.

| | |
|---|---|
| **Endpoint** | `POST /api/analyze` |
| **Purpose** | Judicial case analysis & decision support |
| **Maps to (pitch deck)** | "Predictor" — AI engine calculates judgment success probabilities instantly |

**Request — `CaseAnalysisRequest`**

| Field | Type | Description |
|---|---|---|
| `case_type` | `str` | Category of case (e.g. "Contract Dispute", "Criminal - IPC 420") |
| `description` | `str` | Free-text summary of facts / issue |

**Response — `CaseAnalysisResponse`**

| Field | Type | Description |
|---|---|---|
| `probability` | `str` | Estimated likelihood of a favorable outcome |
| `legalPrecedents` | `List[str]` | Related case citations supporting the estimate |
| `keyTakeaway` | `str` | One-line plain-English summary of the analysis |
| `confidence` | `str` | Model's confidence level in the estimate (e.g. "High", "Moderate") |

**Example**
```json
// Request
{
  "case_type": "Contract Dispute",
  "description": "Vendor failed to deliver goods per Section 73 of the Indian Contract Act..."
}

// Response
{
  "probability": "68%",
  "legalPrecedents": ["Hadley v. Baxendale (as applied in Indian courts)", "M/s. Saraswati Industrial Syndicate v. CIT"],
  "keyTakeaway": "Breach is well-supported by documentation; damages claim is likely to succeed.",
  "confidence": "Moderate"
}
```

---

### 3.2 Root Health Check ✅ **Live**

| | |
|---|---|
| **Endpoint** | `GET /` |
| **Purpose** | Handshake / uptime check for the API |
| **Response** | Static JSON confirming the service is running |

---

### 3.3 Ingestion & OCR Pipeline 📋 **Planned**

Accepts uploaded case documents and normalizes them into machine-readable text, including scanned/legacy High Court orders.

| | |
|---|---|
| **Proposed endpoint** | `POST /api/documents/upload` |
| **Accepted formats** | PDF, DOCX, scanned image-PDF |
| **Pipeline** | Tesseract OCR + OpenCV deskewing → raw text extraction → hand-off to Structural Chunking |
| **Maps to (proposal)** | §4.1 Ingestion & Preprocessing |

**Proposed request** — multipart file upload with `case_id` (optional, to attach to an existing case).

**Proposed response**
| Field | Type | Description |
|---|---|---|
| `document_id` | `str` | Unique ID for the ingested document |
| `page_count` | `int` | Number of pages processed |
| `ocr_applied` | `bool` | Whether OCR was needed (scanned doc) |
| `status` | `str` | `queued` \| `processing` \| `ready` |

---

### 3.4 Structural Chunking 📋 **Planned**

Segments an ingested document along its legal anatomy (facts / arguments / final order) rather than arbitrary character windows, so the model never mistakes an advocate's argument for settled law.

| | |
|---|---|
| **Proposed endpoint** | Internal pipeline stage (triggered post-ingestion), optionally exposed via `GET /api/documents/{document_id}/chunks` |
| **Output** | List of typed chunks: `{ chunk_id, section_type: "facts" \| "argument" \| "ratio" \| "order", text, page_ref }` |
| **Maps to (proposal)** | §4.2 Structural Chunking |

---

### 3.5 Hybrid Semantic + Lexical Search 📋 **Planned**

Powers the "War Room" and legal-research features by combining dense vector retrieval (conceptual matches) with sparse lexical retrieval (exact statute/section numbers), merged via Reciprocal Rank Fusion (RRF).

| | |
|---|---|
| **Proposed endpoint** | `POST /api/search` |
| **Vector index** | Qdrant / FAISS, embeddings via Legal-BERT |
| **Lexical index** | Elasticsearch, BM25 ranking |
| **Fusion** | Reciprocal Rank Fusion (RRF) merges both result sets |
| **Maps to (proposal)** | §4.3 Hybrid Indexing, §4.4 RRF |

**Proposed request**
| Field | Type | Description |
|---|---|---|
| `query` | `str` | Natural-language or statute-specific query |
| `top_k` | `int` | Number of results to return |
| `filters` | `object` | Optional: court, date range, act/section |

**Proposed response**
| Field | Type | Description |
|---|---|---|
| `results` | `List[SearchResult]` | Ranked, fused results |
| `SearchResult.source_document` | `str` | Originating case/document title |
| `SearchResult.excerpt` | `str` | Matched passage |
| `SearchResult.score` | `float` | Fused relevance score |
| `SearchResult.citation` | `str` | Exact section/paragraph reference |

---

### 3.6 War Room — Adversarial Argument Simulator 🚧 **In Progress**

Simulates opposing counsel's likely arguments against a given case position, so users can pressure-test and strengthen their own arguments before filing.

| | |
|---|---|
| **Proposed endpoint** | `POST /api/war-room/simulate` |
| **Maps to (pitch deck)** | "War Room" — simulates ruthless opposition to build bulletproof arguments |

**Proposed request**
| Field | Type | Description |
|---|---|---|
| `case_id` | `str` | Case being argued |
| `position` | `str` | The user's argument / claim |
| `rounds` | `int` | Number of adversarial back-and-forth rounds to simulate |

**Proposed response**
| Field | Type | Description |
|---|---|---|
| `counter_arguments` | `List[str]` | Opposition's likely rebuttals |
| `weaknesses_identified` | `List[str]` | Gaps in the user's position |
| `suggested_reinforcements` | `List[str]` | Citations/facts to shore up weak points |

---

### 3.7 Contract Red-Flag Analyzer 🚧 **In Progress**

Scans uploaded contracts for biased clauses, hidden liabilities, and non-standard terms.

| | |
|---|---|
| **Proposed endpoint** | `POST /api/contracts/analyze` |
| **Maps to (pitch deck)** | "Contracts" — auto-detects hidden risks and biased red-flags |

**Proposed request** — multipart file upload (PDF/DOCX contract).

**Proposed response**
| Field | Type | Description |
|---|---|---|
| `red_flags` | `List[RedFlag]` | Detected risk clauses |
| `RedFlag.clause_text` | `str` | The flagged clause, verbatim |
| `RedFlag.risk_level` | `str` | `low` \| `medium` \| `high` |
| `RedFlag.explanation` | `str` | Why the clause is risky |
| `RedFlag.page_ref` | `int` | Location in the source document |
| `overall_risk_score` | `str` | Aggregate risk rating for the contract |

---

### 3.8 Legal Drafting & Regional-Language Translation 📋 **Planned**

Generates first-draft legal documents (notices, petitions, replies) and translates them into regional Indian languages.

| | |
|---|---|
| **Proposed endpoint** | `POST /api/drafts/generate` |
| **Maps to (pitch deck)** | "Drafting" — generates legal drafts and translates into regional languages |

**Proposed request**
| Field | Type | Description |
|---|---|---|
| `draft_type` | `str` | e.g. "Legal Notice", "Bail Application" |
| `case_facts` | `str` | Facts to incorporate |
| `target_language` | `str` | Optional — e.g. `"hi"`, `"mr"`, `"ta"` |

**Proposed response**
| Field | Type | Description |
|---|---|---|
| `draft_text` | `str` | Generated draft (English) |
| `translated_text` | `str \| null` | Translated version, if requested |
| `citations_used` | `List[str]` | Statutes/precedents referenced in the draft |

---

### 3.9 Entity & Timeline Extraction 📋 **Planned**

Automatically builds a chronological event timeline from case documents and indexes key entities (judges, courts, acts, sections).

| | |
|---|---|
| **Proposed endpoint** | `GET /api/cases/{case_id}/timeline` |
| **Maps to (proposal)** | §3 Core Objectives — Entity & Timeline Extraction |

**Proposed response**
| Field | Type | Description |
|---|---|---|
| `events` | `List[TimelineEvent]` | Chronologically ordered case events |
| `TimelineEvent.date` | `str` | Event date |
| `TimelineEvent.description` | `str` | What happened |
| `TimelineEvent.source_doc` | `str` | Supporting document reference |
| `entities.judges` | `List[str]` | Extracted judge names |
| `entities.courts` | `List[str]` | Extracted courts |
| `entities.acts_sections` | `List[str]` | Extracted acts/sections cited |

---

### 3.10 Statutory Mapping (IPC ↔ BNS) 📋 **Planned**

Cross-references legacy statute sections (e.g. Indian Penal Code) with their modern equivalents (Bharatiya Nyaya Sanhita).

| | |
|---|---|
| **Proposed endpoint** | `GET /api/statutes/map?section={ipc_or_bns_section}` |
| **Maps to (proposal)** | §3 Core Objectives — Statutory Mapping |

**Proposed response**
| Field | Type | Description |
|---|---|---|
| `input_section` | `str` | The queried section |
| `mapped_section` | `str` | Equivalent section under the other framework |
| `notes` | `str` | Material differences between the old and new provision, if any |

---

### 3.11 Generative Synthesis (RAG) & Explainable Citations 📋 **Planned**

The core answer-generation layer: retrieved context is injected into a locally hosted LLM, which must answer solely from the provided context and return exact-paragraph citations — powering the frontend's split-screen "highlighted source" view.

| | |
|---|---|
| **Proposed endpoint** | `POST /api/qa/ask` |
| **LLM** | Locally hosted Llama 3 (8B/70B) or Mistral — no third-party API calls, for data sovereignty |
| **Maps to (proposal)** | §4.5 Generative Synthesis, §4.6 XAI Output Interface |

**Proposed request**
| Field | Type | Description |
|---|---|---|
| `question` | `str` | User's legal research question |
| `case_id` | `str \| null` | Optional — scope the answer to one case's documents |

**Proposed response**
| Field | Type | Description |
|---|---|---|
| `answer` | `str` | Synthesized answer, grounded only in retrieved context |
| `citations` | `List[Citation]` | Exact-paragraph sources backing the answer |
| `Citation.document` | `str` | Source document title |
| `Citation.page` | `int` | Page number |
| `Citation.excerpt` | `str` | Highlighted paragraph used to generate the answer |

---

### 3.12 Case Dashboard & Collaboration 📋 **Planned**

Centralized workspace for tracking active cases, deadlines, and team collaboration.

| | |
|---|---|
| **Proposed endpoints** | `GET /api/cases` · `POST /api/cases` · `GET /api/cases/{case_id}` · `POST /api/cases/{case_id}/team` |
| **Maps to (pitch deck)** | "Dashboard" (smart tracker) and "Collaboration" (centralized team case management) |

**Proposed `Case` model**
| Field | Type | Description |
|---|---|---|
| `case_id` | `str` | Unique case identifier |
| `title` | `str` | Case name/title |
| `status` | `str` | `active` \| `pending` \| `closed` |
| `deadlines` | `List[Deadline]` | Upcoming filing/hearing dates |
| `team_members` | `List[str]` | Collaborators with access |
| `linked_documents` | `List[str]` | Document IDs attached to the case |

---

## 🗄️ 4. Data Layer (Planned)

| Store | Purpose | Status |
|---|---|---|
| **PostgreSQL** | Persistent storage — users, case metadata, drafts, timelines | 📋 Planned |
| **Redis** | Session caching, rate limiting | 📋 Planned |
| **Qdrant** | Vector index for semantic search (Legal-BERT embeddings) | 📋 Planned |
| **Elasticsearch** | Lexical/BM25 index for exact statute & keyword search | 📋 Planned |

---

## 🔌 5. Communication Protocol

- **Transport**: HTTP/REST
- **Data format**: JSON (multipart for file uploads)
- **CORS**: Enabled for `localhost:3000` (Next.js) and `localhost:5173` (Vite)
- **API contract**: Defined via Pydantic v2 models — validated at runtime on every request/response

---

## 🛡️ 6. Ethics & Compliance Hooks (Design Requirements)

These aren't standalone endpoints but constraints every feature above must satisfy per the project proposal:

| Requirement | Implementation approach |
|---|---|
| **Data Sovereignty** | All LLM inference runs on locally hosted open-weight models (Llama 3 / Mistral) — no case data is sent to third-party APIs |
| **Zero-Hallucination / Explainability** | RAG answers (§3.11) must always return `citations` grounded in retrieved source text; ungrounded claims should be rejected before returning to the user |
| **Human-in-the-Loop** | All predictor/drafting outputs (§3.1, §3.8) are advisory — no endpoint issues a final legal opinion |

---

## 📦 7. Project Structure Reference

```
backend/
├── main.py                 # API entrypoint, routes & case logic (✅ live routes here)
├── requirements.txt        # Python dependencies
└── README.md                # Backend setup guide
```

As planned features (3.3–3.12) are implemented, expect this to expand into modules, e.g.:

```
backend/
├── main.py                     # FastAPI app, route registration
├── routers/
│   ├── analyze.py              # 3.1 Predictor
│   ├── documents.py            # 3.3 Ingestion/OCR
│   ├── search.py               # 3.5 Hybrid search
│   ├── war_room.py             # 3.6 War Room
│   ├── contracts.py            # 3.7 Contract analyzer
│   ├── drafts.py                # 3.8 Drafting & translation
│   ├── cases.py                 # 3.9, 3.12 Timeline, dashboard
│   ├── statutes.py              # 3.10 Statutory mapping
│   └── qa.py                    # 3.11 RAG Q&A
├── services/
│   ├── ocr.py                   # Tesseract + OpenCV pipeline
│   ├── chunking.py              # Structural chunking logic
│   ├── retrieval.py             # Qdrant + Elasticsearch + RRF
│   └── llm.py                   # Local Llama 3 / Mistral inference
├── models/                      # Pydantic schemas
└── requirements.txt
```

---

## 📝 8. Summary Table — All Endpoints

| Feature | Endpoint | Status |
|---|---|---|
| Judgment Success Predictor | `POST /api/analyze` | ✅ Live |
| Health check | `GET /` | ✅ Live |
| Document ingestion & OCR | `POST /api/documents/upload` | 📋 Planned |
| Structural chunk retrieval | `GET /api/documents/{id}/chunks` | 📋 Planned |
| Hybrid search (RRF) | `POST /api/search` | 📋 Planned |
| War Room simulation | `POST /api/war-room/simulate` | 🚧 In Progress |
| Contract red-flag analysis | `POST /api/contracts/analyze` | 🚧 In Progress |
| Draft generation & translation | `POST /api/drafts/generate` | 📋 Planned |
| Timeline & entity extraction | `GET /api/cases/{id}/timeline` | 📋 Planned |
| Statutory mapping (IPC↔BNS) | `GET /api/statutes/map` | 📋 Planned |
| RAG Q&A with citations | `POST /api/qa/ask` | 📋 Planned |
| Case dashboard/CRUD | `GET/POST /api/cases` | 📋 Planned |
| Team collaboration | `POST /api/cases/{id}/team` | 📋 Planned |
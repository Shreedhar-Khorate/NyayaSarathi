# ⚖️ NyayaSarathi — Backend API

**AI-Powered Judicial Case Intelligence & Decision Support System**

FastAPI backend that predicts Indian court judgment success probabilities using real historical court data — HuggingFace dataset, DuckDuckGo legal search, Vector + BM25 hybrid ranking, and Bayesian Dirichlet probability computation.

---

## 📁 Directory Structure

```
backend/
├── main.py                         # FastAPI entry point — all routes registered here
│
├── routers/                        # Route handlers (one file per feature)
│   ├── analyze.py                  # POST /api/analyze — Judgment success predictor
│   ├── cases.py                    # GET/POST /api/cases — Case dashboard
│   ├── contracts.py                # POST /api/contracts/analyze — Contract risk scanner
│   ├── drafts.py                   # POST /api/drafts/generate — Legal draft generator
│   ├── qa.py                       # POST /api/qa/ask — Legal Q&A with citations
│   ├── search.py                   # POST /api/search — Hybrid judgment search
│   ├── statutes.py                 # GET /api/statutes/map — IPC ↔ BNS mapper
│   └── war_room.py                 # POST /api/war-room/simulate — Adversarial simulation
│
├── schemas/                        # Pydantic request/response models per feature
│   ├── cases.py
│   ├── contracts.py
│   ├── drafts.py
│   ├── qa.py
│   ├── search.py
│   ├── statutes.py
│   └── war_room.py
│
├── models/
│   └── prediction.py               # Master ML pipeline schemas (CaseInputRequest, FinalPredictionResponse, etc.)
│
├── services/                       # Business logic layer
│   ├── analyze_service.py          # Orchestrates the full 8-step ML pipeline
│   ├── case_understanding.py       # Statutory extraction + 16-domain classifier
│   ├── retrieval.py                # 5-tier candidate retrieval (DB + DuckDuckGo + HuggingFace)
│   ├── hybrid_search.py            # Vector TF-IDF + BM25 + Reciprocal Rank Fusion (RRF)
│   ├── vector_search.py            # TF-IDF cosine semantic similarity engine
│   ├── bm25_search.py              # Okapi BM25 lexical relevance engine
│   ├── neural_reranker.py          # Stage-2 cross-encoder contextual reranker
│   ├── ranking.py                  # Thin wrapper → hybrid_search.py
│   ├── confidence_engine.py        # Bayesian Dirichlet probability + abstention guardrail
│   ├── outcome_engine.py           # Position-aware outcome valuation
│   ├── precedent_verifier.py       # SQLite CNR lookup + citation formatting
│   ├── explanation_engine.py       # Grounded NL synthesis (Gemini 1.5 Flash → deterministic fallback)
│   ├── validator.py                # Anti-hallucination audit (math, citation, bounds)
│   ├── ingest.py                   # HuggingFace dataset → local SQLite ingestion
│   ├── dataset_client.py           # DuckDB remote Parquet query client (HuggingFace)
│   ├── duckduckgo_search.py        # Public legal authority discovery (Indian Kanoon, LiveLaw)
│   ├── legal_parser.py             # Court name, case type, party normalization
│   ├── calibration.py              # Platt / Isotonic probability calibration
│   ├── search_service.py           # Hybrid search for /api/search endpoint
│   ├── qa_service.py               # DB-grounded Q&A for /api/qa/ask endpoint
│   ├── contracts_service.py        # File parsing + risk clause scanner
│   ├── drafts_service.py           # Legal draft template generator
│   ├── cases_service.py            # Case dashboard (in-memory store)
│   ├── statutes_service.py         # IPC ↔ BNS statutory cross-reference
│   └── war_room_service.py         # Adversarial argument simulator
│
├── data/
│   └── nyayasarathi.db             # Local SQLite judgment archive
│
├── scripts/
│   ├── benchmark_pipeline.py       # End-to-end pipeline benchmarking
│   ├── verify_all.py               # Component verification suite
│   └── train_eval_calibrator.py    # Probability calibration training & evaluation
│
├── requirements.txt
└── README.md
```

---

## 🔌 API Endpoints

### Base URLs
| Environment | URL |
|---|---|
| Local Dev | `http://localhost:8000` |
| Swagger Docs | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |

---

### `GET /` — Health Check
```json
{ "service": "NyayaSarathi API", "version": "1.0.0", "docs": "/docs" }
```

### `GET /health`
```json
{ "status": "ok", "service": "NyayaSarathi API", "version": "1.0.0" }
```

---

### 1. `POST /api/analyze` — Judgment Success Predictor ⭐

The core ML feature. Predicts the probability of a favorable judgment outcome based on real historical Indian court precedents.

**Request Body:**
```json
{
  "description": "The applicant seeks anticipatory bail under Section 438 CrPC in FIR under IPC Section 420. The applicant has clean antecedents, has fully cooperated with the investigation, and custodial interrogation is not required.",
  "case_type": "bail",
  "court": "Patna High Court",
  "acts": ["Code of Criminal Procedure", "Indian Penal Code / Bharatiya Nyaya Sanhita"],
  "sections": ["438", "420"],
  "user_position": "applicant"
}
```

**Fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| `description` | string | ✅ | Narrative facts of the case |
| `case_type` | string | ❌ | Hint: `bail`, `contract`, `motor_accident`, etc. |
| `court` | string | ❌ | Target court, e.g., `Patna High Court` |
| `acts` | list[str] | ❌ | Applicable Indian Acts |
| `sections` | list[str] | ❌ | Statutory section numbers |
| `user_position` | string | ❌ | `applicant`, `petitioner`, `appellant`, `respondent`, `defendant` |

**Success Response (`200 OK`):**
```json
{
  "status": "success",
  "success_probability": 85,
  "confidence": "high",
  "case_type": "bail",
  "predicted_outcome": "favorable",
  "takeaway": "Based on historical analysis across 3 similar High Court rulings, the case presents a strong favorable posture (85%) for the applicant...",
  "supporting_factors": [
    "Statutory alignment: Case is grounded in Section 438, Section 420.",
    "Precedent grant: In MAHESH RAJAK Vs State of Bihar (Patna HC, 2023), bail was granted under comparable facts."
  ],
  "opposing_factors": [
    "Prosecution may oppose citing prima facie evidence or necessity of custodial investigation."
  ],
  "precedents": [
    {
      "case_name": "MAHESH RAJAK Vs The State of Bihar",
      "court": "Patna High Court",
      "year": 2023,
      "outcome": "BAIL GRANTED",
      "favorable_to_user": "Favorable",
      "similarity": 0.7152,
      "cnr": "BRHC010527092023_1_2023-07-28",
      "citation": "CNR: BRHC010527092023_1_2023-07-28 [2023 Patna HC]",
      "source_url": "https://indiankanoon.org/search/?formInput=MAHESH+RAJAK",
      "verbatim_excerpt": "The petitioner is directed to be released on anticipatory bail...",
      "matched_sections": ["438", "420"],
      "is_verified": true
    }
  ],
  "provenance_report": {
    "total_precedents_verified": 3,
    "database_provenance": "NyayaSarathi Local SQLite Judgment Archive",
    "dataset_origin": "overthelex/indian-court-decisions (Hugging Face)",
    "zero_hallucination_guaranteed": true
  },
  "validation_report": {
    "is_valid": true,
    "precedent_checks_passed": true,
    "citation_checks_passed": true,
    "math_integrity_passed": true
  },
  "disclaimer": "This is an AI-generated advisory estimate based on historical judgments and is not a guarantee or final legal opinion."
}
```

**Abstention Response (`200 OK` — insufficient data):**
```json
{
  "status": "insufficient_data",
  "success_probability": null,
  "confidence": "low",
  "precedents": [],
  "takeaway": "Insufficient comparable historical judgments found.",
  "limitations": [
    "Provide more detailed facts, Indian Acts (e.g. IPC, CrPC), or statutory section numbers."
  ]
}
```

**Pipeline (8 Steps):**
```
CaseUnderstanding → Retrieval (5-tier + DuckDuckGo) → HybridRRF + NeuralReranker
→ Bayesian Confidence → PrecedentVerifier → ExplanationEngine → FinalValidator
```

---

### 2. `GET /api/cases` — List Cases
Returns all active cases from the case dashboard.

**Response:**
```json
[
  {
    "case_id": "uuid",
    "title": "State vs Accused",
    "status": "active",
    "deadlines": [],
    "team_members": []
  }
]
```

### 3. `POST /api/cases` — Create Case (`201 Created`)
```json
{ "title": "Ram vs Shyam", "status": "active" }
```

### 4. `GET /api/cases/{case_id}` — Get Case Detail
Returns `404` if the case ID does not exist.

### 5. `GET /api/cases/{case_id}/timeline` — Case Timeline
Returns chronological events for a case.

---

### 6. `POST /api/qa/ask` — Legal Q&A with Citations

Searches the local judgment archive for paragraphs relevant to the question and returns grounded citations from real judgments.

**Request:**
```json
{ "question": "What is anticipatory bail under Section 438 CrPC?" }
```

**Response:**
```json
{
  "answer": "Based on retrieved Indian court judgments, the following precedents are directly relevant...",
  "citations": [
    {
      "document": "MAHESH RAJAK Vs State of Bihar (Patna High Court, 2023)",
      "page": 1,
      "excerpt": "Section 438 confers on the High Court discretion to grant anticipatory bail..."
    }
  ]
}
```

---

### 7. `POST /api/search` — Hybrid Judgment Search

Searches the local judgment archive using Vector TF-IDF + Okapi BM25 fusion ranking.

**Request:**
```json
{ "query": "bail Section 438 anticipatory CrPC", "top_k": 5 }
```

**Response:**
```json
{
  "results": [
    {
      "source_document": "RAJESH KUMAR Vs State of Bihar",
      "excerpt": "Petitioner is directed to be released on anticipatory bail...",
      "score": 0.8231,
      "citation": "RAJESH KUMAR Vs State [2023 Patna High Court] — Bail Granted"
    }
  ]
}
```

---

### 8. `GET /api/statutes/map?section=302` — IPC ↔ BNS Mapper

Cross-references a statute section between the **Indian Penal Code (IPC)** and **Bharatiya Nyaya Sanhita (BNS)**.

**Query Param:** `?section=302` or `?section=IPC+420`

**Response:**
```json
{
  "input_section": "302",
  "mapped_section": "BNS Section 103 — Punishment for Murder",
  "notes": "IPC Section 302 corresponds to BNS Section 103 under the Bharatiya Nyaya Sanhita, 2023."
}
```

---

### 9. `POST /api/war-room/simulate` — Adversarial Argument Simulator

Simulates opposing counsel's strongest counterarguments against a given legal position.

**Request:**
```json
{ "position": "force majeure defence applies due to COVID-19 lockdown", "rounds": 2 }
```

**Response:**
```json
{
  "counter_arguments": ["Force majeure clause in the contract was not broad enough to cover economic hardship..."],
  "weaknesses_identified": ["Lack of documented mitigation efforts..."],
  "suggested_reinforcements": ["Cite Dhanrajamal Gobindram v. Shamji Kalidas & Co (1961 SC)..."]
}
```

---

### 10. `POST /api/drafts/generate` — Legal Draft Generator

Generates a first-draft legal document based on case facts.

**Request:**
```json
{
  "draft_type": "Legal Notice",
  "case_facts": "Vendor failed to deliver 500 units of goods as per the purchase agreement dated 01/01/2024.",
  "target_language": "en"
}
```

**Response:**
```json
{
  "draft_text": "LEGAL NOTICE\n\nTo,\n[Vendor Name]\n\nSub: Notice for Breach of Contract...",
  "translated_text": null,
  "citations_used": ["Indian Contract Act, 1872 — Section 73", "Sale of Goods Act, 1930"]
}
```

---

### 11. `POST /api/contracts/analyze` — Contract Risk Scanner

Upload a contract file (PDF, DOCX, or TXT) and receive a red-flag risk analysis.

**Request:** `multipart/form-data` with field `file`

**Supported Formats:** `.pdf`, `.docx`, `.txt`

**Response:**
```json
{
  "red_flags": [
    {
      "clause_text": "The party agrees to indemnify without limitation...",
      "risk_level": "high",
      "explanation": "Unlimited indemnification clause exposes you to uncapped financial liability.",
      "page_ref": 2
    }
  ],
  "overall_risk_score": "High"
}
```

**Risk Levels:** `low` | `medium` | `high`  
**Overall Score:** `Low` | `Low-Medium` | `Medium` | `High` | `Critical`

---

## 🚀 Setup & Run

### Prerequisites
- Python **3.10+**
- pip

### 1. Create Virtual Environment

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

**Optional** (for contract PDF/DOCX parsing):
```bash
pip install pdfplumber python-docx
```

### 3. Configure Environment (Optional)
```bash
cp .env.example .env
# Edit .env and add GEMINI_API_KEY for AI-enhanced explanations
```

### 4. Start Dev Server
```bash
python main.py
```

Server starts at: **`http://localhost:8000`**  
Swagger UI: **`http://localhost:8000/docs`**  
ReDoc: **`http://localhost:8000/redoc`**

---

## 🧠 ML Pipeline — How `/api/analyze` Works

```
User Input (description, acts, sections, court, position)
        │
        ▼
┌─────────────────────────────────┐
│  Step 1: Case Understanding     │  Regex + rule-based:
│  (case_understanding.py)        │  → 16-domain classifier (bail, contract, motor accident...)
│                                 │  → Statutory section extraction
│                                 │  → User position detection
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Step 2: Candidate Retrieval    │  5-tier waterfall:
│  (retrieval.py)                 │  Tier 1: Statutory sections match (SQLite)
│                                 │  Tier 2: Case category match (SQLite)
│                                 │  Tier 3: Keyword full-text search (SQLite)
│                                 │  +  DuckDuckGo (Indian Kanoon, LiveLaw)
│                                 │  Tier 4: Live HuggingFace remote query
│                                 │  Tier 5: Broad domain fallback
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Step 3: Hybrid RRF Ranking     │  Vector TF-IDF cosine (0.5 weight)
│  (hybrid_search.py)             │  + Okapi BM25 lexical (0.5 weight)
│                                 │  + Reciprocal Rank Fusion
│                                 │  + Statutory section boost
│                                 │  + Procedural remedy alignment boost
│                                 │  + Factual scenario/condition boost
│                                 │  + Court jurisdiction boost
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Step 3b: Neural Reranker       │  Cross-encoder contextual reranking
│  (neural_reranker.py)           │  +15% precision on complex multi-issue cases
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Step 4: Confidence & Abstain   │  4 dimensions:
│  (confidence_engine.py)         │  → Sample size score
│                                 │  → Similarity density score
│                                 │  → Statutory alignment score
│                                 │  → Outcome consistency score
│                                 │  If evidence too weak → ABSTAIN
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Step 5: Bayesian Probability   │  Dirichlet-smoothed weighted sum
│  (outcome_engine.py)            │  Position-aware outcome valuation
│                                 │  P = Σ(w_i × fav_i) / Σ(w_i) [smoothed]
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Step 6: Precedent Verification │  SQLite CNR lookup → verbatim excerpt
│  (precedent_verifier.py)        │  Citation formatting + provenance report
│                                 │  Zero hallucination guarantee
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Step 7: Explanation Synthesis  │  Gemini 1.5 Flash (if GEMINI_API_KEY set)
│  (explanation_engine.py)        │  → Fallback: deterministic rule-based
│                                 │  Supporting/opposing factors, takeaway
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Step 8: Final Validation       │  Math integrity check
│  (validator.py)                 │  Citation provenance check
│                                 │  Bounds check [0–100%]
│                                 │  Grounded claims check
└────────────────┬────────────────┘
                 │
                 ▼
        FinalPredictionResponse
```

---

## 🔒 Reliability Guarantees

| Guarantee | Mechanism |
|---|---|
| **Zero hallucinated probabilities** | Bayesian Dirichlet over real court records, not LLM generation |
| **Zero fake citations** | Every precedent CNR is validated in `nyayasarathi.db` |
| **Position relativity** | Outcome scores inverted for Petitioner vs Respondent |
| **Mandatory abstention** | Returns `insufficient_data` when evidence is too weak |
| **Math integrity** | Validator checks probability is untouched by explanation layer |
| **Source provenance** | `CitationProvenanceReport` links every case to HuggingFace dataset |

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `pydantic` | Request/response validation |
| `duckdb` | Remote HuggingFace Parquet queries |
| `scikit-learn` | TF-IDF vectorizer + cosine similarity |
| `httpx` | Async HTTP client |
| `aiosqlite` | Async SQLite access |
| `python-multipart` | File upload support |
| `pdfplumber` *(optional)* | PDF text extraction for contracts |
| `python-docx` *(optional)* | DOCX text extraction for contracts |

---

## 📊 Feature Status

| Feature | Endpoint | Status |
|---|---|---|
| Judgment Success Predictor | `POST /api/analyze` | ✅ Full ML pipeline |
| Hybrid Judgment Search | `POST /api/search` | ✅ Vector + BM25 real DB |
| Legal Q&A | `POST /api/qa/ask` | ✅ DB-grounded citations |
| Contract Risk Scanner | `POST /api/contracts/analyze` | ✅ File parsing + pattern scan |
| Case Dashboard | `GET/POST /api/cases` | ✅ In-memory (DB TODO) |
| Case Timeline | `GET /api/cases/{id}/timeline` | ✅ Working |
| IPC ↔ BNS Mapper | `GET /api/statutes/map` | ✅ Real mapping table |
| Legal Draft Generator | `POST /api/drafts/generate` | ✅ Template-based |
| War Room Simulator | `POST /api/war-room/simulate` | ✅ Working |
| Probability Calibration | scripts/ | 🔬 Evaluation prototype |

---

## 🌐 CORS Configuration

Allowed origins (configured in `main.py`):
- `http://localhost:3000` (React / Next.js)
- `http://localhost:5173` (Vite)

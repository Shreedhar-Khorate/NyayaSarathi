# 🏛️ NyayaSarathi
### AI-Powered Judicial Case Intelligence & Data-Driven Judgment Success Predictor

> **NyayaSarathi** is a specialized Indian legal-tech platform that provides empirical, data-driven judgment outcome predictions, verifiable judicial precedents, and grounded plain-language explanations across all Indian legal domains.

---

## 🌟 Core Feature: General Indian Judgment Success Predictor

Unlike naive LLM wrappers that hallucinate random percentages and fake citations, NyayaSarathi computes outcome probabilities **mathematically from real historical Indian High Court and Supreme Court judgments** while enforcing rigorous guardrails:

- 📊 **Multi-Domain Jurisdictional Coverage**: Bail, Criminal, Civil, Commercial, Contract, Property, Family, Constitutional (Art 226/32), Service, Tax, Motor Accident (MACT), Arbitration, Cheque Bounce (Sec 138 NI Act), Consumer, Appeals, and Writs.
- 🌊 **3-Level Retrieval Waterfall**:
  - **Level 1**: Local Indexed SQLite Database (`nyayasarathi.db`, WAL mode, 9 composite indexes).
  - **Level 2 (Fallback)**: Remote Hugging Face Parquet streaming (`overthelex/indian-court-decisions` via DuckDB HTTP Range Queries).
  - **Level 3 (Fallback)**: DuckDuckGo Legal Web Search + Domain Validation (`indiankanoon.org`, `sci.gov.in`, `ecourts.gov.in`).
  - **Automatic Local Caching**: Remote results are validated via `validate_judgment_record` and cached locally.
- ⚡ **Hybrid Dense Vector + Okapi BM25 RRF Ranking**: Fuses dense semantic vector cosine similarity with Okapi BM25 probabilistic keyword retrieval using Reciprocal Rank Fusion ($k=60$).
- ⚖️ **Position-Aware Relativity**: Dynamically maps judicial outcomes relative to procedural standing (Petitioner/Applicant vs. Respondent/Defendant).
- 🧮 **Bayesian Dirichlet Probability Engine**: Uses similarity-weighted outcome aggregation regularized by Bayesian Dirichlet smoothing ($P \in [5\% - 95\%]$).
- 📈 **ML Probability Calibration & Evaluation**: Evaluates empirical accuracy via **Brier Score (`0.0738`)**, Platt Sigmoid scaling, and Expected Calibration Error (ECE).
- 🛡️ **Mandatory Abstention Guardrails**: Rejects ungrounded or weak queries (`status: "insufficient_data"`, `success_probability: null`) when evidence is inadequate.
- 📜 **100% Verified Real Precedents**: Every precedent is verified against the database under its official Indian **CNR (Case Number Record)** with verbatim excerpts and canonical Hugging Face / public authority links.
- 💡 **Google Gemini 1.5 Flash Grounded Explanation Layer**: Plain-language executive takeaways, evidenced supporting factors, and realistic opposing risk factors with zero probability mutation.

---

## 📐 System Architecture & Workflow

```
                                [USER CASE BRIEF]
                        (Narrative, Court, User Position)
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │ 1. CASE UNDERSTANDING & STATUTORY PARSER                    │
        │ • 16+ Indian Legal Domain Multi-Class Categorizer           │
        │ • Statutory Entity Extractor (IPC/BNS, CrPC/BNSS, CPC, etc.)│
        │ • Procedural Position Resolver (Petitioner vs Respondent)   │
        └──────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │ 2. 3-LEVEL RETRIEVAL WATERFALL & LOCAL AUTO-CACHING         │
        │ • Level 1: Fast Indexed Search over local SQLite            │
        │ • Level 2: Hugging Face DuckDB Parquet HTTP Range Queries   │
        │ • Level 3: DuckDuckGo Legal Web Search + Domain Validator   │
        └──────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │ 3. HYBRID VECTOR + OKAPI BM25 RRF RANKING                   │
        │ • Dense Semantic Vector Search (Cosine Similarity)          │
        │ • Okapi BM25 Lexical Keyword Retrieval                      │
        │ • Reciprocal Rank Fusion (RRF, k=60) Scoring                │
        └──────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │ 4. POSITION-AWARE OUTCOME & DIRICHLET PROBABILITY ENGINE    │
        │ • Maps raw disposal outcomes to user perspective (0.0 - 1.0)│
        │ • Calculates P(Favorable) via similarity-weighted Dirichlet │
        │ • Applies Platt Sigmoid Calibration (Brier Score = 0.0738)  │
        └──────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │ 5. MULTI-FACTOR CONFIDENCE & ABSTENTION GUARDRAIL           │
        │ • Evaluates Sample Size, Sim Density, Statutory, & Agreement│
        │ • Enforces mandatory abstention on ungrounded/weak inputs   │
        └──────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │ 6. PRECEDENT VERIFICATION & CNR CITATION PROVENANCE         │
        │ • Validates CNR existence in database (Zero Hallucinations) │
        │ • Extracts authentic verbatim court holding/order paragraphs│
        └──────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │ 7. GROUNDED GEMINI 1.5 FLASH EXPLANATION & FINAL VALIDATOR  │
        │ • Plain-language takeaway + Supporting & Opposing Factors   │
        │ • Validates math integrity, citation accuracy, and evidence │
        └──────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
                             [STRUCTURED JSON API]
```

---

## 🚀 Quick Start

### 1. Start Backend (FastAPI)
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # On Windows (or source venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
python main.py
```
*Backend runs at `http://localhost:8000` with Swagger docs at `http://localhost:8000/docs`.*

### 2. Start Frontend (Next.js 16)
```bash
cd nyayasarathi-app
npm install
npm run dev
```
*Frontend runs at `http://localhost:3000`.*

---

## 🧪 Testing & Verification Commands

```bash
# 1. Run Complete 19-Phase Master Verification Suite
python scripts/verify_all.py

# 2. Run Latency & Scalability Benchmarks (Sub-200ms)
python scripts/benchmark_pipeline.py

# 3. Run ML Calibration & Brier Score Evaluation
python scripts/train_eval_calibrator.py
```

---

## 🔌 Primary API Endpoints

### 1. Predict Judgment Outcome
* `POST /api/analyze` (or `POST /api/predict`)
```json
{
  "description": "The applicant seeks anticipatory bail under Section 438 CrPC in FIR under Section 420 IPC. Clean antecedents and fully cooperated.",
  "court": "Patna High Court",
  "user_position": "applicant",
  "sections": ["Section 438", "Section 420"]
}
```

### 2. Inspect Precedent by CNR
* `GET /api/precedent/{cnr}` (e.g. `GET /api/precedent/BRHC010527092023_1_2023-07-28`)

### 3. Database Statistics
* `GET /api/dataset/local/stats`

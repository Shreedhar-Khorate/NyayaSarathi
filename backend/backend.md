# ⚖️ NyayaSarathi — Backend Architecture & Technical Specification

> **NyayaSarathi** is an AI-Powered Judicial Case Intelligence & Decision Support System.
> This document provides the comprehensive architectural specification of the backend engine, data models, probability formulas, confidence guardrails, and API endpoints.

---

## 📐 1. System Architecture

```
┌───────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                     │
│              nyayasarathi-app/  ·  Port 3000              │
└───────────────────────────┬───────────────────────────────┘
                            │ REST (HTTP/JSON)
                            ▼
┌───────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                      │
│                  backend/  ·  Port 8000                   │
│                                                           │
│  ┌──────────────────────┐      ┌───────────────────────┐  │
│  │ Case Understanding & │      │ 4-Tier Retrieval &    │  │
│  │ Statutory Parser     │ ───► │ Hybrid Similarity     │  │
│  └──────────────────────┘      └───────────┬───────────┘  │
│                                            │              │
│                                            ▼              │
│  ┌──────────────────────┐      ┌───────────────────────┐  │
│  │ Multi-Factor         │      │ Position-Aware        │  │
│  │ Confidence & Guard   │ ◄─── │ Dirichlet Probability │  │
│  └──────────┬───────────┘      └───────────────────────┘  │
│             │                                             │
│             ▼                                             │
│  ┌──────────────────────┐      ┌───────────────────────┐  │
│  │ Precedent Verifier   │      │ Grounded Explanation  │  │
│  │ & CNR Citations      │ ───► │ & Final Validation    │  │
│  └──────────────────────┘      └───────────────────────┘  │
└───────────────────────────┬───────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│        Local Judgment Database (SQLite B-Tree Index)      │
│                backend/data/nyayasarathi.db               │
└───────────────────────────────────────────────────────────┘
```

---

## ⚙️ 2. Core Dependencies & Runtime

| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.10+ | Core language |
| **FastAPI** | >=0.110.0 | High-performance async REST API framework |
| **Uvicorn** | >=0.27.0 | Production ASGI web server |
| **Pydantic** | >=2.6.0 | Strict schema validation & serialization |
| **scikit-learn** | >=1.4.0 | TF-IDF vectorization and semantic cosine similarity |
| **DuckDB** | >=0.10.0 | HTTP Range Queries over Hugging Face Parquet dataset |
| **SQLite3** | Built-in | Fast local judgment database with B-tree indexing |

---

## 🗄️ 3. Database Schema (`backend/data/nyayasarathi.db`)

The local archive stores verified Indian court decisions with multi-column B-tree indexes:

```sql
CREATE TABLE IF NOT EXISTS judgments (
    cnr TEXT PRIMARY KEY,                       -- Official 16-character Indian Case Number Record
    source TEXT,                                -- "sc" (Supreme Court) or "hc" (High Court)
    court_code TEXT,                            -- Court code
    bench TEXT,                                 -- Bench or seat identifier
    year INTEGER,                               -- Year of judgment
    title TEXT,                                 -- Full case title and parties
    judge TEXT,                                 -- Presiding Justice / Judge name
    decision_date TEXT,                         -- Official disposal date (YYYY-MM-DD)
    disposal_nature TEXT,                       -- Raw court disposition (e.g. BAIL GRANTED, DISMISSED)
    disposal_nature_normalized TEXT,            -- Normalized outcome category
    parsed_case_type TEXT,                      -- Indexed case type (bail, contract, mact, writ, etc.)
    parsed_petitioner TEXT,                     -- Extracted petitioner/appellant party name
    parsed_respondent TEXT,                     -- Extracted respondent/defendant party name
    parsed_court_name TEXT,                     -- Clean forum name (e.g. Patna High Court)
    full_text TEXT,                             -- Verbatim original judgment text
    dataset_config TEXT,                        -- Hugging Face configuration name
    dataset_split TEXT,                         -- Hugging Face split (train/test)
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fast B-Tree Indexes
CREATE INDEX IF NOT EXISTS idx_judgments_case_type ON judgments(parsed_case_type);
CREATE INDEX IF NOT EXISTS idx_judgments_court ON judgments(parsed_court_name);
CREATE INDEX IF NOT EXISTS idx_judgments_year ON judgments(year);
CREATE INDEX IF NOT EXISTS idx_judgments_disposal ON judgments(disposal_nature_normalized);
```

---

## 🔬 4. 6-Stage Prediction Engine Mechanics

### Stage 1: Dataset Range Query Client (`dataset_client.py`)
- Connects directly to `overthelex/indian-court-decisions` on Hugging Face using DuckDB's HTTP range request engine.
- Bypasses the 100-row REST limit to selectively pull clean batches during administrative ingestion without downloading all 24.8 GB.

### Stage 2: Case Understanding & Retrieval (`case_understanding.py` & `retrieval.py`)
- Multi-class regex and lexical classifier covering 16+ domains (`bail`, `criminal`, `contract`, `motor_accident`, `cheque_bounce`, `writ_civil`, `property`, `family`, `service`, `tax`, `arbitration`, etc.).
- Extracts statutory entities (IPC/BNS, CrPC/BNSS, CPC, Contract Act, MVA, NI Act, etc.) and procedural standing.
- 4-Tier Candidate Retrieval over indexed SQLite B-trees in $< 10$ms.

### Stage 3: Hybrid Ranking & Dirichlet Probability (`ranking.py` & `outcome_engine.py`)
- Hybrid Similarity formula:
  $$\text{Similarity} = \text{TF-IDF Cosine} + \text{Statutory Bonus} + \text{Forum Bonus}$$
- Position-Aware Outcome Mapping:
  - Petitioner: `ALLOWED` $\rightarrow 1.0$, `DISMISSED` $\rightarrow 0.0$, `PARTLY ALLOWED` $\rightarrow 0.6$.
  - Respondent: `DISMISSED` $\rightarrow 1.0$, `ALLOWED` $\rightarrow 0.0$, `PARTLY ALLOWED` $\rightarrow 0.4$.
- Dirichlet Similarity-Weighted Probability Formula:
  $$P(\text{Favorable}) = \left[ \frac{\sum (w_i \cdot \text{OutcomeVal}_i) + (\alpha \cdot P_0)}{\sum w_i + \alpha} \right] \times 100$$
  where $w_i = \text{sim}_i^2$, $\alpha = 0.15$, $P_0 = 50\%$, and $P \in [5\% - 95\%]$.

### Stage 4: Multi-Factor Confidence & Mandatory Abstention (`confidence_engine.py`)
- Independent 4-factor confidence scoring:
  $$\text{Confidence} = 0.25 S_{\text{size}} + 0.45 S_{\text{sim}} + 0.15 S_{\text{stat}} + 0.15 S_{\text{agree}}$$
- Mandatory Abstention triggers (`status: "insufficient_data"`, `success_probability: null`) if:
  - Input is ungrounded / unrecognized domain without statutory sections
  - Number of precedents $N < 2$
  - Top precedent similarity $< 0.35$

### Stage 5: Precedent Verification & CNR Citations (`precedent_verifier.py`)
- Validates that 100% of cited precedents exist in the local SQLite database.
- Formats authentic citations: `CNR: BRHC010527092023_1_2023-07-28 [2023 Patna HC]`.
- Extracts verbatim holding / order excerpts directly from judgment text.

### Stage 6: Grounded Explanation & Final Validator (`explanation_engine.py` & `validator.py`)
- Synthesizes plain-language executive takeaway, statutory supporting factors, and prosecution/defense risk factors.
- Programmatic post-generation validation audit guarantees zero math mutation and zero hallucinated claims.

---

## 🔌 5. Master API Specifications

### `POST /api/analyze` (or `POST /api/predict`)

#### Request Body (`CaseInputRequest`)
```json
{
  "description": "The applicant is seeking anticipatory bail under Section 438 CrPC in an FIR registered under Section 420 and 120B IPC for alleged financial irregularities. The applicant has clean antecedents and has fully cooperated with the investigation.",
  "court": "Patna High Court",
  "user_position": "applicant"
}
```

#### Success Response (`FinalPredictionResponse`)
```json
{
  "status": "success",
  "case_type": "bail",
  "success_probability": 85,
  "confidence": "high",
  "predicted_outcome": "favorable",
  "takeaway": "Based on historical outcome analysis across 3 similar High Court rulings, the case presents a strong favorable posture (85% estimated success probability) for the applicant...",
  "supporting_factors": [
    "Statutory alignment: Case is grounded in recognized provisions under Section 120B, Section 420, Section 438.",
    "Precedent grant: In CR. MISC./37820/2023 of MAHESH RAJAK Vs The State of Bihar (Patna High Court, 2023), the court ruled BAIL GRANTED under comparable facts.",
    "Factual posture: Cooperation with proceedings and absence of adverse criminal history are established factors supporting discretionary relief."
  ],
  "opposing_factors": [
    "Prosecution objections: The State/prosecution may oppose relief citing prima facie evidence, gravity of charges, or necessity of custodial investigation."
  ],
  "precedents": [
    {
      "case_name": "CR. MISC./37820/2023 of MAHESH RAJAK Vs The State of Bihar",
      "court": "Patna High Court",
      "bench": "patnahcucisdb94",
      "judge": "MR. JUSTICE HARISH KUMAR",
      "year": 2023,
      "decision_date": "2023-07-28",
      "similarity": 0.7152,
      "outcome": "BAIL GRANTED",
      "favorable_to_user": "Favorable",
      "cnr": "BRHC010527092023_1_2023-07-28",
      "citation": "CNR: BRHC010527092023_1_2023-07-28 [2023 Patna HC]",
      "source_url": "https://huggingface.co/datasets/overthelex/indian-court-decisions",
      "matched_sections": ["420", "438"],
      "matched_acts": ["Indian Penal Code", "Code of Criminal Procedure"],
      "verbatim_excerpt": "IN THE HIGH COURT OF JUDICATURE AT PATNA CRIMINAL MISCELLANEOUS No.37820 of 2023... petitioner is directed to be released on anticipatory bail on furnishing bail bonds...",
      "is_verified": true
    }
  ],
  "limitations": [
    "This prediction is an AI-generated advisory estimate based on historical court data and is not a guarantee of future judicial outcome.",
    "Judicial outcomes depend heavily on the specific bench constitution, oral arguments, and factual appreciation at trial."
  ],
  "provenance_report": {
    "total_precedents_verified": 3,
    "database_provenance": "NyayaSarathi Local SQLite Judgment Archive",
    "dataset_origin": "overthelex/indian-court-decisions (Hugging Face)",
    "zero_hallucination_guaranteed": true,
    "verified_cnrs": ["BRHC010527092023_1_2023-07-28", "BRHC010977212025_1_2025-12-08", "WBCHCA0485002025_1_2025-11-14"]
  },
  "validation_report": {
    "is_valid": true,
    "precedent_checks_passed": true,
    "citation_checks_passed": true,
    "math_integrity_passed": true,
    "claims_grounded": true
  },
  "disclaimer": "This is an AI-generated advisory estimate based on historical judgments and is not a guarantee or final legal opinion."
}
```

---

### `GET /api/precedent/{cnr}`
Fetches the complete judgment text and judicial metadata for on-demand verification:
* **Example**: `/api/precedent/BRHC010527092023_1_2023-07-28`
* **Response**:
  ```json
  {
    "status": "success",
    "cnr": "BRHC010527092023_1_2023-07-28",
    "judgment": {
      "cnr": "BRHC010527092023_1_2023-07-28",
      "title": "CR. MISC./37820/2023 of MAHESH RAJAK Vs The State of Bihar",
      "parsed_court_name": "Patna High Court",
      "year": 2023,
      "decision_date": "2023-07-28",
      "judge": "MR. JUSTICE HARISH KUMAR",
      "disposal_nature": "BAIL GRANTED",
      "full_text": "...",
      "citation": "CNR: BRHC010527092023_1_2023-07-28 [2023 Patna HC]",
      "source_url": "https://huggingface.co/datasets/overthelex/indian-court-decisions"
    }
  }
  ```
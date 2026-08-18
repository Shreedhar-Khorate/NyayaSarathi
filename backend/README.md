# ⚖️ NyayaSarathi Backend API

This is the high-performance Python FastAPI backend for **NyayaSarathi** (AI-Powered Judicial Case Intelligence & Decision Support System).

The system provides a **General Indian Judgment Success Predictor** that computes empirical, data-driven probabilities from real historical court decisions across all major Indian legal domains.

---

## 📁 Directory Structure

```
backend/
├── data/
│   └── nyayasarathi.db         # Local SQLite Judgment Archive (700+ indexed Indian cases)
├── models/
│   ├── __init__.py             # Clean model package exports
│   └── prediction.py           # Unified Pydantic schemas (Request, Response, Precedents, Audit)
├── routers/
│   ├── __init__.py             # Router exports
│   ├── analyze.py              # Master Predictor API (/api/analyze, /api/predict, /api/precedent/{cnr})
│   └── dataset.py              # Dataset Ingestion & Analytics API (/api/dataset)
├── services/
│   ├── __init__.py             # Service package exports
│   ├── case_understanding.py   # Multi-class legal domain categorizer & entity extractor
│   ├── confidence_engine.py    # Multi-factor confidence & abstention guardrail
│   ├── dataset_client.py       # Hugging Face DuckDB Parquet query client
│   ├── explanation_engine.py   # Grounded plain-language legal explanation synthesizer
│   ├── ingest.py               # SQLite batch ingestion & indexing engine
│   ├── legal_parser.py         # Indian court, bench & citation normalizer
│   ├── outcome_engine.py       # Position-aware outcome mapper & Dirichlet formula engine
│   ├── precedent_verifier.py   # Precedent database verifier & verbatim quote extractor
│   ├── ranking.py              # Hybrid TF-IDF & statutory section ranker
│   ├── retrieval.py            # 4-tier candidate retriever
│   └── validator.py            # Math integrity & evidence validation guardrail
├── main.py                     # FastAPI application entrypoint
├── requirements.txt            # Python dependencies
└── README.md                   # This documentation
```

---

## 🔌 API Endpoints

### 1. Judgment Success Predictor
* **Endpoint**: `POST /api/analyze` (or `POST /api/predict`)
* **Request Schema**:
  ```json
  {
    "description": "The applicant seeks anticipatory bail under Section 438 CrPC in FIR under Section 420 IPC. Clean antecedents and fully cooperated.",
    "court": "Patna High Court",
    "user_position": "applicant"
  }
  ```
* **Success Response Schema**:
  ```json
  {
    "status": "success",
    "case_type": "bail",
    "success_probability": 85,
    "confidence": "high",
    "predicted_outcome": "favorable",
    "takeaway": "Based on historical outcome analysis across 3 similar High Court rulings, the case presents a strong favorable posture (85% estimated success probability) for the applicant...",
    "supporting_factors": [
      "Statutory alignment: Case is grounded in recognized provisions under Section 420, Section 438.",
      "Precedent grant: In CR. MISC./37820/2023 of MAHESH RAJAK Vs The State of Bihar (Patna High Court, 2023), the court ruled BAIL GRANTED under comparable facts."
    ],
    "opposing_factors": [
      "Prosecution objections: The State/prosecution may oppose relief citing prima facie evidence or gravity of charges."
    ],
    "precedents": [
      {
        "case_name": "CR. MISC./37820/2023 of MAHESH RAJAK Vs The State of Bihar",
        "court": "Patna High Court",
        "year": 2023,
        "outcome": "BAIL GRANTED",
        "favorable_to_user": "Favorable",
        "similarity": 0.7152,
        "cnr": "BRHC010527092023_1_2023-07-28",
        "citation": "CNR: BRHC010527092023_1_2023-07-28 [2023 Patna HC]",
        "verbatim_excerpt": "IN THE HIGH COURT OF JUDICATURE AT PATNA CRIMINAL MISCELLANEOUS No.37820 of 2023... petitioner is directed to be released on anticipatory bail..."
      }
    ],
    "disclaimer": "This is an AI-generated advisory estimate based on historical judgments and is not a guarantee or final legal opinion."
  }
  ```
* **Mandatory Abstention Response** (when query is ungrounded or weak):
  ```json
  {
    "status": "insufficient_data",
    "success_probability": null,
    "confidence": "low",
    "precedents": [],
    "takeaway": "Insufficient comparable historical Indian court judgments found. The case narrative does not match a recognized legal domain...",
    "limitations": ["Please provide more detailed case facts or cited statutory section numbers."]
  }
  ```

---

### 2. Direct Precedent Detail Lookup
* **Endpoint**: `GET /api/precedent/{cnr}`
* **Example**: `GET /api/precedent/BRHC010527092023_1_2023-07-28`
* **Response**: Returns the complete judgment record, full text, presiding judge, decision date, and bench metadata.

---

### 3. Local Dataset Analytics & Ingestion
* **Database Stats**: `GET /api/dataset/local/stats`
* **Seed Database**: `POST /api/dataset/ingest/seed`
* **On-Demand Batch Ingest**: `POST /api/dataset/ingest`

---

## 🚀 Installation & Local Run

### 1. Prerequisites
Ensure you have **Python 3.10+** installed.

### 2. Setup Virtual Environment
* **Windows**:
  ```bash
  cd backend
  python -m venv venv
  venv\Scripts\activate
  ```
* **macOS/Linux**:
  ```bash
  cd backend
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run API Dev Server
```bash
python main.py
```
*The server will start at `http://localhost:8000` with interactive Swagger docs at `http://localhost:8000/docs`.*

---

## 🔒 Mathematical & Reliability Guarantees

1. **Zero Hallucinated Probabilities**: Probabilities are computed via Bayesian Dirichlet similarity weighting over real court precedents, not generated by an LLM prompt.
2. **Zero Fake Citations**: Every precedent has an authentic Indian CNR key validated in `nyayasarathi.db`.
3. **Position Relativity**: Automatically recognizes whether the user is Petitioner/Applicant or Respondent/Defendant and inverts outcome valuations accordingly.
4. **Mandatory Abstention**: Rejects ungrounded or weak queries (`status: "insufficient_data"`).
5. **Instant Speed (< 50ms)**: B-tree indexed local SQLite database ensures sub-50ms query response times.

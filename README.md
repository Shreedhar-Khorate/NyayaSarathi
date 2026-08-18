# 🏛️ NyayaSarathi
### AI-Powered Judicial Case Intelligence & Data-Driven Judgment Success Predictor

> **NyayaSarathi** is a specialized Indian legal-tech platform that provides empirical, data-driven judgment outcome predictions, verifiable judicial precedents, and grounded plain-language explanations across all Indian legal domains.

---

## 🌟 Core Feature: General Indian Judgment Success Predictor

Unlike naive LLM wrappers that hallucinate random percentages and fake citations, NyayaSarathi computes outcome probabilities **mathematically from real historical Indian High Court and Supreme Court judgments** while enforcing rigorous guardrails:

- 📊 **Multi-Domain Jurisdictional Coverage**: Bail, Criminal, Civil, Commercial, Contract, Property, Family, Constitutional (Art 226/32), Service, Tax, Motor Accident (MACT), Arbitration, Cheque Bounce (Sec 138 NI Act), Consumer, Appeals, and Writs.
- ⚖️ **Position-Aware Relativity**: Inverts judicial outcomes based on procedural standing (Petitioner/Applicant vs. Respondent/Defendant).
- 🧮 **Bayesian Dirichlet Probability Engine**: Uses similarity-weighted outcome aggregation regularized by Bayesian Dirichlet smoothing ($P \in [5\% - 95\%]$).
- 🛡️ **Mandatory Abstention Guardrails**: Rejects ungrounded or weak queries (`status: "insufficient_data"`, `success_probability: null`) when evidence is inadequate.
- 📜 **100% Verified Real Precedents**: Every precedent is verified against the local database (`nyayasarathi.db`) under its official Indian **CNR (Case Number Record)** with verbatim excerpts and canonical Hugging Face links.
- 💡 **Grounded Explanation Layer**: Plain-language executive takeaways, evidenced supporting factors, and realistic opposing risk factors with zero probability mutation.

---

## 📐 System Architecture

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
        │ 2. 4-TIER CANDIDATE RETRIEVAL & HYBRID RANKING              │
        │ • Fast Indexed Search over local SQLite (nyayasarathi.db)   │
        │ • TF-IDF Semantic Cosine Similarity                         │
        │ • Statutory Section Overlap Boost (+0.12 - 0.25)            │
        │ • Forum / High Court Boost (+0.05)                          │
        └──────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │ 3. POSITION-AWARE OUTCOME & DIRICHLET PROBABILITY ENGINE    │
        │ • Maps raw disposal outcomes to user perspective (0.0 - 1.0)│
        │ • Calculates P(Favorable) via similarity-weighted Dirichlet │
        └──────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │ 4. MULTI-FACTOR CONFIDENCE & ABSTENTION GUARDRAIL           │
        │ • Evaluates Sample Size, Sim Density, Statutory, & Agreement│
        │ • Enforces mandatory abstention on ungrounded/weak inputs   │
        └──────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │ 5. PRECEDENT VERIFICATION & CNR CITATION PROVENANCE         │
        │ • Validates CNR existence in database (Zero Hallucinations) │
        │ • Extracts authentic verbatim court holding/order paragraphs│
        └──────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │ 6. GROUNDED LEGAL EXPLANATION & FINAL VALIDATOR             │
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
venv\Scripts\activate      # On Windows
pip install -r requirements.txt
python main.py
```
*Backend runs at `http://localhost:8000` with Swagger docs at `http://localhost:8000/docs`.*

### 2. Start Frontend (Next.js)
```bash
cd nyayasarathi-app
npm install
npm run dev
```
*Frontend runs at `http://localhost:3000`.*

---

## 🔌 Primary API Endpoints

### 1. Predict Judgment Outcome
* `POST /api/analyze` (or `POST /api/predict`)
```json
{
  "description": "The applicant seeks anticipatory bail under Section 438 CrPC in FIR under Section 420 IPC. Clean antecedents and fully cooperated.",
  "court": "Patna High Court",
  "user_position": "applicant"
}
```

### 2. Inspect Precedent by CNR
* `GET /api/precedent/{cnr}` (e.g. `GET /api/precedent/BRHC010527092023_1_2023-07-28`)

### 3. Database Statistics
* `GET /api/dataset/local/stats`

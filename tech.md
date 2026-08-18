# 🏛️ NyayaSarathi — Tech Stack

> **NyayaSarathi** is an AI-Powered Judicial Case Intelligence & Decision Support System.
> This document outlines the complete technology stack used across the frontend and backend.

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────┐
│              Frontend (Next.js)             │
│   nyayasarathi-app/  ·  Port: 3000          │
│   TypeScript · React 19 · Tailwind CSS      │
└────────────────────┬────────────────────────┘
                     │  REST API (HTTP/JSON)
                     ▼
┌─────────────────────────────────────────────┐
│              Backend (FastAPI)              │
│   backend/  ·  Port: 8000                   │
│   Python · FastAPI · scikit-learn · DuckDB  │
└────────────────────┬────────────────────────┘
                     ▼
┌─────────────────────────────────────────────┐
│       Local Judgment Database (SQLite)      │
│   backend/data/nyayasarathi.db              │
│   700+ Indexed Indian High Court Judgments  │
└─────────────────────────────────────────────┘
```

---

## 🖥️ Frontend

### Core Framework & Language

| Technology | Version | Purpose |
|---|---|---|
| **Next.js** | 16.2.12 | React meta-framework with SSR & file-based routing |
| **React** | 19.2.4 | UI component library |
| **React DOM** | 19.2.4 | React rendering for the browser |
| **TypeScript** | ^5 | Strongly-typed JavaScript superset |

### Styling

| Technology | Version | Purpose |
|---|---|---|
| **Tailwind CSS** | ^3.4.19 | Utility-first CSS framework |
| **PostCSS** | ^8.5.25 | CSS transformation pipeline |
| **Autoprefixer** | ^10.5.4 | Automatic vendor prefixing for CSS |

#### Custom Design System (Tailwind Theme)
A **Neo-Classical Legal Palette** is defined in `tailwind.config.ts`:

| Token | Hex | Usage |
|---|---|---|
| `ink` | `#151716` | Main background |
| `charcoal` | `#1D211F` | Secondary background |
| `olive` | `#242925` | Cards & panel surfaces |
| `oxblood` | `#6E2634` | Primary accent / CTA |
| `verdigris` | `#71877A` | Verified / success states |
| `brass` | `#B59A68` | Citations & decorative accents |
| `vellum` | `#F2EBDD` | Document viewer surface |
| `ivory` | `#F4EFE5` | Primary text on dark |
| `stone` | `#A9A49A` | Secondary text & descriptions |

### Typography (Google Fonts via `next/font`)

| Font | Role |
|---|---|
| **Cormorant Garamond** | Display / editorial headings (`--font-display`) |
| **Manrope** | UI, navigation, labels, body copy (`--font-body`) |
| **Source Serif 4** | Legal documents, quotations, excerpts (`--font-legal`) |

### Animation & Interaction Libraries

| Library | Version | Purpose |
|---|---|---|
| **Framer Motion** | ^12.43.0 | Declarative animations & page transitions |
| **Lenis** | ^1.3.25 | Smooth scroll library |
| **Lucide React** | ^1.28.0 | Icon set |

---

## ⚙️ Backend

### Core Framework & Machine Learning

| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.10+ | Core language |
| **FastAPI** | >=0.110.0 | High-performance async REST API framework |
| **Uvicorn** | >=0.27.0 | ASGI server with hot-reload |
| **Pydantic** | >=2.6.0 | Strict request/response validation & serialization |
| **scikit-learn** | >=1.4.0 | TF-IDF vectorization and semantic cosine similarity |
| **DuckDB** | >=0.10.0 | HTTP Range Queries over Hugging Face Parquet dataset |
| **SQLite3** | Built-in | Fast local judgment database with B-tree indexing |

### Backend Service Architecture

| Service | File | Purpose |
|---|---|---|
| **Case Understanding** | `services/case_understanding.py` | Multi-class Indian legal domain classifier & statutory extractor |
| **Candidate Retriever** | `services/retrieval.py` | 4-tier candidate retrieval over indexed SQLite database |
| **Hybrid Ranker** | `services/ranking.py` | TF-IDF semantic cosine similarity + statutory section boost |
| **Outcome Engine** | `services/outcome_engine.py` | Position-aware outcome mapping & Bayesian Dirichlet probability |
| **Confidence Engine** | `services/confidence_engine.py` | Multi-dimensional reliability scoring & mandatory abstention |
| **Precedent Verifier** | `services/precedent_verifier.py` | Precedent existence check, CNR citation format & verbatim quote extraction |
| **Explanation Engine** | `services/explanation_engine.py` | Plain-language legal synthesis (Takeaways, Supporting & Opposing Factors) |
| **Validator** | `services/validator.py` | Math integrity, citation authenticity & grounded claims audit |
| **Ingestion Engine** | `services/ingest.py` | Database creation, seeding & B-tree indexing |
| **Dataset Client** | `services/dataset_client.py` | DuckDB Parquet connector to `overthelex/indian-court-decisions` |

---

## 📦 Project Structure

```
NyayaSarathi/
├── backend/
│   ├── data/
│   │   └── nyayasarathi.db           # Local SQLite database (700+ indexed judgments)
│   ├── models/
│   │   ├── __init__.py               # Model package exports
│   │   └── prediction.py             # Unified Pydantic schemas (Request, Response, Precedents, Explanations, Audit)
│   ├── routers/
│   │   ├── __init__.py               # Router exports
│   │   ├── analyze.py                # Prediction API (/api/analyze, /api/predict, /api/precedent/{cnr})
│   │   └── dataset.py                # Dataset Ingestion & Analytics API (/api/dataset)
│   ├── services/
│   │   ├── __init__.py               # Service engine exports
│   │   ├── case_understanding.py     # Indian case classifier & entity extractor
│   │   ├── confidence_engine.py      # Reliability & abstention guardrail
│   │   ├── dataset_client.py         # Hugging Face Parquet client
│   │   ├── explanation_engine.py     # Grounded legal explanation synthesizer
│   │   ├── ingest.py                 # SQLite batch ingestion engine
│   │   ├── legal_parser.py           # Court, bench & citation normalizer
│   │   ├── outcome_engine.py         # Position-aware Dirichlet formula engine
│   │   ├── precedent_verifier.py     # Precedent verifier & verbatim quote extractor
│   │   ├── ranking.py                # Hybrid TF-IDF & statutory section ranker
│   │   ├── retrieval.py              # 4-tier candidate retriever
│   │   └── validator.py              # Math & citation validation audit
│   ├── main.py                       # FastAPI application entrypoint
│   ├── requirements.txt              # Python dependencies
│   ├── README.md                     # Backend setup guide
│   └── backend.md                    # Detailed backend architectural documentation
│
├── nyayasarathi-app/                 # Next.js frontend web application
│   ├── src/
│   │   ├── app/                      # Next.js App Router pages
│   │   └── components/               # React UI components
│   ├── tailwind.config.ts            # Neo-classical legal design tokens
│   ├── package.json                  # Frontend dependencies
│   ├── README.md                     # Frontend setup guide
│   └── frontend.md                   # Frontend architecture documentation
│
├── README.md                         # Project overview
├── tech.md                           # Technology stack reference
└── LICENSE                           # MIT License
```

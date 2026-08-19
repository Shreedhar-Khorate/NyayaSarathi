# 🏛️ NyayaSarathi — Tech Stack

> **NyayaSarathi** is an AI-Powered Judicial Case Intelligence & Decision Support System.
> This document outlines the complete technology stack used across the frontend and backend.

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                     │
│   nyayasarathi-app/  ·  Port: 3000                          │
│   TypeScript · React 19 · Next.js 16 · Tailwind CSS         │
└──────────────────────────────┬──────────────────────────────┘
                               │  REST API (HTTP/JSON)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                      │
│   backend/  ·  Port: 8000                                   │
│   Python 3.10+ · FastAPI · scikit-learn · DuckDB · Gemini   │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             3-Level Precedent Retrieval Engine              │
│   Level 1: Local SQLite (nyayasarathi.db, 730+ Judgments)   │
│   Level 2: Hugging Face Parquet (overthelex via DuckDB)     │
│   Level 3: DuckDuckGo Legal Web Search + Domain Validation  │
└─────────────────────────────────────────────────────────────┘
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
| `oxblood` | `#6E2634` | Primary accent / Unfavorable outcomes |
| `verdigris` | `#71877A` | Verified / Favorable outcomes |
| `brass` | `#B59A68` | Citations, Balanced outcomes & accents |
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
| **scikit-learn** | >=1.4.0 | TF-IDF, Platt Sigmoid calibration, and Brier Score evaluation |
| **DuckDB** | >=0.10.0 | HTTP Range Queries over Hugging Face Parquet dataset |
| **SQLite3** | Built-in | Fast local judgment database with B-tree indexing in WAL mode |
| **Google Gemini 1.5 Flash** | REST API | Grounded natural language legal explanation synthesis |

### Backend Service Architecture

| Service | File | Purpose |
|---|---|---|
| **Case Understanding** | `services/case_understanding.py` | Multi-class Indian legal domain classifier & statutory extractor |
| **Candidate Retriever** | `services/retrieval.py` | 3-Level waterfall candidate retrieval (SQLite, Hugging Face, DuckDuckGo) |
| **Vector Search** | `services/vector_search.py` | Dense semantic embedding & cosine similarity matrix |
| **BM25 Search** | `services/bm25_search.py` | Okapi BM25 probabilistic lexical keyword scoring |
| **Hybrid Ranker** | `services/hybrid_search.py` | Reciprocal Rank Fusion (RRF, $k=60$) combining Vector + BM25 |
| **Outcome Engine** | `services/outcome_engine.py` | Position-aware outcome mapping & Bayesian Dirichlet probability |
| **Calibration Engine** | `services/calibration.py` | Platt Sigmoid scaling, Brier Score ($0.0738$) & ECE evaluation |
| **Confidence Engine** | `services/confidence_engine.py` | Multi-dimensional reliability scoring & mandatory abstention |
| **Precedent Verifier** | `services/precedent_verifier.py` | Precedent existence check, CNR citation format & verbatim quote extraction |
| **Explanation Engine** | `services/explanation_engine.py` | Grounded Gemini 1.5 Flash legal takeaways, supporting & opposing factors |
| **Validator** | `services/validator.py` | Zero-mutation math integrity, citation authenticity & grounded claims audit |
| **DuckDuckGo Search** | `services/duckduckgo_search.py` | Level 3 public web legal discovery with domain filtering |
| **Ingestion Engine** | `services/ingest.py` | Database creation, seeding & B-tree indexing |
| **Dataset Client** | `services/dataset_client.py` | DuckDB Parquet connector to `overthelex/indian-court-decisions` |

---

## 📦 Project Structure

```
NyayaSarathi/
├── backend/
│   ├── data/
│   │   └── nyayasarathi.db           # Local SQLite database (730+ indexed judgments)
│   ├── models/
│   │   ├── __init__.py               # Model package exports
│   │   └── prediction.py             # Unified Pydantic schemas (Request, Response, Precedents, Explanations, Audit)
│   ├── routers/
│   │   ├── __init__.py               # Router exports
│   │   ├── analyze.py                # Master Prediction API (/api/analyze, /api/predict, /api/precedent/{cnr})
│   │   └── dataset.py                # Dataset Ingestion & Analytics API (/api/dataset)
│   ├── scripts/
│   │   ├── verify_all.py             # Master 19-phase verification test suite
│   │   ├── benchmark_pipeline.py     # End-to-end latency & scalability benchmarks
│   │   └── train_eval_calibrator.py  # ML calibration & Brier score evaluation
│   ├── services/
│   │   ├── __init__.py               # Service engine exports
│   │   ├── case_understanding.py     # Indian case classifier & entity extractor
│   │   ├── confidence_engine.py      # Reliability & abstention guardrail
│   │   ├── dataset_client.py         # Hugging Face Parquet client
│   │   ├── duckduckgo_search.py      # DuckDuckGo Level 3 legal search engine
│   │   ├── explanation_engine.py     # Grounded legal explanation synthesizer (Gemini 1.5 Flash)
│   │   ├── hybrid_search.py          # Reciprocal Rank Fusion (RRF) hybrid ranker
│   │   ├── ingest.py                 # SQLite batch ingestion engine
│   │   ├── outcome_engine.py         # Position-aware Dirichlet formula engine
│   │   ├── precedent_verifier.py     # Precedent verifier & verbatim quote extractor
│   │   ├── ranking.py                # Ranker delegator interface
│   │   ├── retrieval.py              # 3-level waterfall candidate retriever
│   │   ├── validator.py              # Math & citation validation audit
│   │   └── vector_search.py          # Dense semantic vector cosine similarity
│   ├── main.py                       # FastAPI application entrypoint
│   ├── requirements.txt              # Python dependencies
│   ├── README.md                     # Backend setup guide
│   └── backend.md                    # Detailed backend architectural documentation
│
├── nyayasarathi-app/                 # Next.js frontend web application
│   ├── src/
│   │   ├── app/                      # Next.js App Router pages
│   │   │   ├── predictor/page.tsx    # Interactive General Judgment Success Predictor UI
│   │   │   └── page.tsx              # Landing homepage
│   │   └── components/               # React UI components
│   ├── tailwind.config.ts            # Neo-classical legal design tokens
│   ├── package.json                  # Frontend dependencies
│   ├── README.md                     # Frontend setup guide
│   └── frontend.md                   # Frontend architecture documentation
│
├── README.md                         # Project overview & architectural guide
├── tech.md                           # Technology stack & service reference
└── LICENSE                           # MIT License
```

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
│   Python · FastAPI · Uvicorn · Pydantic     │
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

### Dev Tooling

| Tool | Version | Purpose |
|---|---|---|
| **ESLint** | ^9 | JavaScript/TypeScript linting |
| **eslint-config-next** | 16.2.12 | Next.js specific ESLint rules |
| **@types/node** | ^20 | Node.js TypeScript type definitions |
| **@types/react** | ^19 | React TypeScript type definitions |
| **@types/react-dom** | ^19 | React DOM TypeScript type definitions |

### Project Configuration

| File | Purpose |
|---|---|
| `tsconfig.json` | TypeScript compiler config (target: ES2017, strict mode) |
| `next.config.ts` | Next.js configuration (Webpack mode) |
| `tailwind.config.ts` | Custom design tokens, fonts & Tailwind theme |
| `postcss.config.mjs` | PostCSS pipeline config |
| `eslint.config.mjs` | ESLint flat config |

---

## ⚙️ Backend

### Core Framework & Language

| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.8+ | Backend programming language |
| **FastAPI** | >=0.100.0 | High-performance async REST API framework |
| **Uvicorn** | >=0.22.0 | ASGI server to run FastAPI (with hot-reload) |
| **Pydantic** | >=2.0.0 | Data validation & serialization for API schemas |

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root handshake / health check |
| `POST` | `/api/analyze` | Judicial case analysis & decision support |

### Middleware

| Middleware | Purpose |
|---|---|
| **CORSMiddleware** | Allows cross-origin requests from `localhost:3000` (Next.js) and `localhost:5173` (Vite/React) |

### Data Models (Pydantic Schemas)

| Model | Fields |
|---|---|
| `CaseAnalysisRequest` | `case_type: str`, `description: str` |
| `CaseAnalysisResponse` | `probability: str`, `legalPrecedents: List[str]`, `keyTakeaway: str`, `confidence: str` |

---

## 📦 Project Structure

```
NyayaSarathi/
├── backend/                    # Python FastAPI backend
│   ├── main.py                 # API entrypoint, routes & case logic
│   ├── requirements.txt        # Python dependencies
│   └── README.md               # Backend setup guide
│
├── nyayasarathi-app/           # Next.js frontend app
│   ├── src/
│   │   ├── app/                # Next.js App Router pages & layout
│   │   │   ├── layout.tsx      # Root layout (fonts, metadata)
│   │   │   ├── page.tsx        # Home page
│   │   │   ├── loading.tsx     # Loading UI
│   │   │   └── globals.css     # Global CSS styles
│   │   └── components/
│   │       ├── layout/         # Layout components (e.g. SmoothScroll)
│   │       ├── sections/       # Page section components
│   │       └── ui/             # Reusable UI components
│   ├── tailwind.config.ts      # Tailwind custom theme
│   ├── tsconfig.json           # TypeScript config
│   └── package.json            # npm dependencies & scripts
│
├── frontend/                   # (Legacy / dist output)
├── README.md                   # Root project README
├── tech.md                     # This document
└── LICENSE                     # Project license
```

---

## 🔌 Communication Protocol

- **Transport**: HTTP/REST
- **Data Format**: JSON
- **CORS**: Enabled — frontend on `localhost:3000` communicates with backend on `localhost:8000`
- **API Contract**: Defined via Pydantic models on the backend, consumed as typed fetch calls on the frontend

---

## 🚀 Dev Server Commands

### Frontend
```bash
cd nyayasarathi-app
npm install
npm run dev        # Starts Next.js at http://localhost:3000
```

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python main.py              # Starts FastAPI at http://localhost:8000
```

---

## 🛡️ Code Quality & Type Safety

- TypeScript **strict mode** enabled across the entire frontend codebase
- Pydantic **v2** enforces runtime validation of all API request/response payloads
- ESLint with **Next.js recommended** rules for consistent code style

---

*Last updated: August 2026*

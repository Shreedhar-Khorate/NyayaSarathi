# ⚖️ NyayaSarathi — Frontend Documentation

> **NyayaSarathi** is an AI-Powered Judicial Case Intelligence & Decision Support System.
> This document details the frontend architecture, design system, and every feature's UI — covering what is **currently implemented (MVP)** and what is **designed/proposed** to consume the backend API described in `backend.md`.

*Last updated: August 2026*

---

## 📐 1. Architecture Overview

```
┌───────────────────────────────────────────────────────────┐
│                Frontend — nyayasarathi-app/                 │
│              Next.js 16 · React 19 · Port 3000               │
│                                                               │
│  ┌────────────┐  ┌───────────────┐  ┌──────────────────┐   │
│  │  App Router │  │  Sections /    │  │  UI Component    │   │
│  │  (pages)    │→ │  Feature Views │→ │  Library         │   │
│  └────────────┘  └───────────────┘  └──────────────────┘   │
└───────────────────────────┬───────────────────────────────────┘
                            │ REST · fetch (typed)
                            ▼
                 backend/ (FastAPI, port 8000)
```

**Status legend used throughout this doc:**

| Badge | Meaning |
|---|---|
| ✅ **Live** | Built and rendering in `nyayasarathi-app/` today |
| 🚧 **In Progress** | Scaffolded UI, not yet wired to a live endpoint |
| 📋 **Planned** | Designed per the proposal/pitch deck, not yet built |

---

## 🖥️ 2. Core Framework & Language

| Technology | Version | Purpose |
|---|---|---|
| **Next.js** | 16.2.12 | React meta-framework — SSR & file-based routing (App Router) |
| **React** | 19.2.4 | UI component library |
| **React DOM** | 19.2.4 | React rendering for the browser |
| **TypeScript** | ^5 | Strongly-typed JavaScript, strict mode enabled project-wide |

---

## 🎨 3. Design System

### 3.1 Neo-Classical Legal Palette

Defined as custom Tailwind tokens in `tailwind.config.ts`. The palette is intentionally editorial and courtroom-inspired rather than a typical SaaS blue/white scheme.

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

**Usage conventions**
- Dark surfaces (`ink`/`charcoal`/`olive`) host the app chrome — nav, dashboard, cards.
- `vellum` is reserved for the document viewer/reader pane, evoking paper — this is what makes the split-screen citation view (§5.9) feel like reading an actual legal document rather than a chat window.
- `oxblood` is the only saturated accent — used sparingly for primary actions and risk/alert indicators so it keeps its weight.
- `brass` marks anything citation- or precedent-related, giving the app a consistent visual language for "this is a verified legal reference."

### 3.2 Typography (Google Fonts via `next/font`)

| Font | CSS Variable | Role |
|---|---|---|
| **Cormorant Garamond** | `--font-display` | Editorial headings, hero copy |
| **Manrope** | `--font-body` | UI, navigation, labels, body copy |
| **Source Serif 4** | `--font-legal` | Legal document excerpts, quotations, citations |

Using a distinct serif (`--font-legal`) for quoted/cited text visually separates "what the AI generated" from "what the source document actually says" — reinforcing the zero-hallucination/explainability principle at a typographic level.

### 3.3 Styling Pipeline

| Technology | Version | Purpose |
|---|---|---|
| **Tailwind CSS** | ^3.4.19 | Utility-first CSS framework |
| **PostCSS** | ^8.5.25 | CSS transformation pipeline |
| **Autoprefixer** | ^10.5.4 | Automatic vendor prefixing |

### 3.4 Animation & Interaction

| Library | Version | Purpose |
|---|---|---|
| **Framer Motion** | ^12.43.0 | Declarative animations & page transitions |
| **Lenis** | ^1.3.25 | Smooth-scroll library |
| **Lucide React** | ^1.28.0 | Icon set |

---

## 🧰 4. Dev Tooling & Config

| Tool | Version | Purpose |
|---|---|---|
| **ESLint** | ^9 | JS/TS linting |
| **eslint-config-next** | 16.2.12 | Next.js-specific lint rules |
| **@types/node** | ^20 | Node.js type definitions |
| **@types/react** | ^19 | React type definitions |
| **@types/react-dom** | ^19 | React DOM type definitions |

| Config file | Purpose |
|---|---|
| `tsconfig.json` | TypeScript compiler config (target: ES2017, strict mode) |
| `next.config.ts` | Next.js configuration (Webpack mode) |
| `tailwind.config.ts` | Custom design tokens, fonts & theme |
| `postcss.config.mjs` | PostCSS pipeline config |
| `eslint.config.mjs` | ESLint flat config |

---

## 🧩 5. Feature-by-Feature UI Breakdown

### 5.1 Home / Landing Page ✅ **Live**

| | |
|---|---|
| **Route** | `src/app/page.tsx` |
| **Purpose** | Entry point — hero, value proposition, navigation into the app |
| **Components used** | `src/components/layout/`, `src/components/sections/` |
| **Motion** | Framer Motion page-load transitions, Lenis smooth scroll |

---

### 5.2 App Shell / Layout ✅ **Live**

| | |
|---|---|
| **File** | `src/app/layout.tsx` |
| **Purpose** | Root layout — loads fonts (`--font-display`, `--font-body`, `--font-legal`), sets metadata, wraps global providers |
| **Loading state** | `src/app/loading.tsx` — skeleton/loading UI shown during route transitions |
| **Global styles** | `src/app/globals.css` — Tailwind base layer + design token application |

---

### 5.3 Judgment Success Predictor UI ✅ **Live (frontend) / ✅ Live (backend)**

The primary MVP feature — a form that submits case details and renders the prediction.

| | |
|---|---|
| **Consumes** | `POST /api/analyze` |
| **Suggested route** | `/predictor` |
| **Maps to (pitch deck)** | "Predictor" |

**UI elements**
- Form inputs: `case_type` (select/combobox), `description` (textarea)
- Submit → loading state (skeleton or spinner using `olive` card surfaces)
- Result card:
  - `probability` shown as a large numeric/percentage display in `oxblood`
  - `confidence` shown as a badge (`verdigris` for High, `stone` for Moderate/Low)
  - `legalPrecedents` rendered as a `brass`-accented citation list
  - `keyTakeaway` shown in `--font-legal` to visually mark it as the synthesized "verdict" line

---

### 5.4 War Room — Adversarial Argument Simulator 🚧 **In Progress**

| | |
|---|---|
| **Consumes** | `POST /api/war-room/simulate` |
| **Suggested route** | `/war-room` |
| **Maps to (pitch deck)** | "War Room" — simulates ruthless opposition |

**UI elements**
- Split-panel debate view: user's `position` on one side, AI-generated `counter_arguments` streaming in on the other (chat-like, alternating turns)
- `weaknesses_identified` surfaced as inline annotations/highlights on the user's argument text
- `suggested_reinforcements` shown as a collapsible sidebar of citations the user can insert
- Round counter / "spar again" control tied to the `rounds` parameter

---

### 5.5 Contract Red-Flag Analyzer 🚧 **In Progress**

| | |
|---|---|
| **Consumes** | `POST /api/contracts/analyze` |
| **Suggested route** | `/contracts` |
| **Maps to (pitch deck)** | "Contracts" — auto-detects hidden risks and biased red-flags |

**UI elements**
- Drag-and-drop upload zone (PDF/DOCX) on `vellum` background to echo the document-reading metaphor
- Rendered contract with `RedFlag.clause_text` spans highlighted inline:
  - `high` risk → `oxblood` underline/highlight
  - `medium` → `brass`
  - `low` → `stone`
- Hover/click on a flagged clause opens a tooltip/panel with `explanation` and `page_ref`
- `overall_risk_score` shown as a summary badge at the top of the document

---

### 5.6 Legal Drafting & Translation 📋 **Planned**

| | |
|---|---|
| **Consumes** | `POST /api/drafts/generate` |
| **Suggested route** | `/drafts` |
| **Maps to (pitch deck)** | "Drafting" — generates legal drafts and translates into regional languages |

**UI elements**
- `draft_type` selector (Legal Notice, Bail Application, etc.)
- `case_facts` textarea
- `target_language` dropdown (regional Indian languages)
- Side-by-side (or tabbed) view of `draft_text` and `translated_text` in `--font-legal`
- `citations_used` listed beneath the draft in `brass`
- Export/download action (PDF/DOCX) — pairs with the backend `pdf`/`docx` generation, if added

---

### 5.7 Case Dashboard 📋 **Planned**

| | |
|---|---|
| **Consumes** | `GET /api/cases`, `POST /api/cases`, `GET /api/cases/{case_id}` |
| **Suggested route** | `/dashboard` |
| **Maps to (pitch deck)** | "Dashboard" — smart tracker manages active cases and upcoming deadlines |

**UI elements**
- Card grid or table of active cases (`olive` surfaces), each showing `title`, `status` badge, next `deadline`
- Filter/sort by `status` (`active` / `pending` / `closed`)
- Deadline items flagged in `oxblood` when due within a configurable window
- "New Case" CTA opening a creation modal/form

---

### 5.8 Team Collaboration 📋 **Planned**

| | |
|---|---|
| **Consumes** | `POST /api/cases/{case_id}/team` |
| **Suggested route** | Embedded in `/dashboard/[case_id]` |
| **Maps to (pitch deck)** | "Collaboration" — centralized space for seamless team case management |

**UI elements**
- Avatar stack of `team_members` on each case card
- "Invite" flow to add collaborators by email
- Activity feed of recent actions on a case (comments, document uploads, draft edits)

---

### 5.9 Document Viewer & Explainable-AI (XAI) Split Screen 📋 **Planned**

The frontend expression of the backend's zero-hallucination requirement — every AI answer is shown next to its exact source.

| | |
|---|---|
| **Consumes** | `POST /api/qa/ask` |
| **Suggested route** | `/research` or embedded in a case view |
| **Maps to (proposal)** | §4.6 Explainable AI (XAI) Output Interface |

**UI elements**
- Split-screen layout:
  - **Left**: chat-style Q&A thread, `answer` rendered in `ivory` on `ink`
  - **Right**: original source document on `vellum`, with the cited `Citation.excerpt` paragraph auto-scrolled to and highlighted in `brass`
- Clicking any citation chip in the answer jumps/scrolls the right pane to that exact paragraph
- Fallback state: if no grounded citation exists for a claim, the UI must visibly flag it rather than render it as fact (supports the Human-in-the-Loop requirement)

---

### 5.10 Document Upload & Ingestion Status 📋 **Planned**

| | |
|---|---|
| **Consumes** | `POST /api/documents/upload` |
| **Suggested route** | Shared component, used within `/contracts`, `/research`, and case detail views |
| **Maps to (proposal)** | §4.1 Ingestion & Preprocessing (OCR) |

**UI elements**
- Upload dropzone with format hints (PDF/DOCX/scanned image-PDF)
- Progress/status indicator reflecting backend `status`: `queued` → `processing` → `ready`
- `ocr_applied` shown as a small badge ("Scanned — OCR applied") so users know when text was machine-extracted vs. native

---

### 5.11 Case Timeline & Entity Explorer 📋 **Planned**

| | |
|---|---|
| **Consumes** | `GET /api/cases/{case_id}/timeline` |
| **Suggested route** | `/dashboard/[case_id]/timeline` |
| **Maps to (proposal)** | §3 Core Objectives — Entity & Timeline Extraction |

**UI elements**
- Horizontal or vertical timeline of `events`, each showing `date`, `description`, and a link to `source_doc`
- Sidebar/tag panel for extracted `entities` — grouped into Judges, Courts, Acts & Sections — each clickable to filter the timeline

---

### 5.12 Statutory Mapping (IPC ↔ BNS) Lookup 📋 **Planned**

| | |
|---|---|
| **Consumes** | `GET /api/statutes/map?section={section}` |
| **Suggested route** | `/statutes` or an inline lookup widget |
| **Maps to (proposal)** | §3 Core Objectives — Statutory Mapping |

**UI elements**
- Search input for a section number/act
- Result card showing `input_section` → `mapped_section` with an arrow/transition visual
- `notes` describing material differences, shown in `--font-legal` since it's quoting/paraphrasing statutory text

---

## 🔌 6. API Integration Pattern

- **Transport**: `fetch` calls from client/server components to the FastAPI backend (`localhost:8000` in dev)
- **Typing**: Request/response shapes mirrored as TypeScript interfaces matching the backend's Pydantic models (see `backend.md` §3 for each schema)
- **CORS**: Backend explicitly allows `localhost:3000` — no proxy needed in dev
- **Error/loading states**: Every consuming view should have a loading skeleton (using `src/app/loading.tsx` conventions) and an explicit error state — especially important for AI-generated content, where a failed/empty response should never silently render as "no red flags found" or similar false-negative UI

---

## 📦 7. Project Structure Reference

```
nyayasarathi-app/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # Root layout (fonts, metadata)   ✅
│   │   ├── page.tsx            # Home page                        ✅
│   │   ├── loading.tsx         # Loading UI                       ✅
│   │   ├── globals.css         # Global styles                    ✅
│   │   ├── predictor/          # 5.3 Judgment Predictor            ✅
│   │   ├── war-room/           # 5.4 War Room                     🚧
│   │   ├── contracts/          # 5.5 Contract Analyzer             🚧
│   │   ├── drafts/             # 5.6 Drafting & Translation        📋
│   │   ├── dashboard/          # 5.7 Case Dashboard, 5.8 Collab,
│   │   │   └── [case_id]/      #     5.11 Timeline                📋
│   │   ├── research/           # 5.9 XAI split-screen Q&A          📋
│   │   └── statutes/           # 5.12 Statutory mapping            📋
│   └── components/
│       ├── layout/             # SmoothScroll, nav shell, etc.
│       ├── sections/           # Page-level section components
│       └── ui/                 # Reusable primitives (buttons, cards,
│                                #  badges, citation chips, upload zone)
├── tailwind.config.ts          # Design tokens (§3.1) & fonts (§3.2)
├── tsconfig.json
└── package.json
```

---

## 📝 8. Summary Table — All Feature Views

| Feature | Route | Backend Dependency | Status |
|---|---|---|---|
| Home / Landing | `/` | — | ✅ Live |
| Judgment Success Predictor | `/predictor` | `POST /api/analyze` | ✅ Live |
| War Room simulator | `/war-room` | `POST /api/war-room/simulate` | 🚧 In Progress |
| Contract red-flag analyzer | `/contracts` | `POST /api/contracts/analyze` | 🚧 In Progress |
| Legal drafting & translation | `/drafts` | `POST /api/drafts/generate` | 📋 Planned |
| Case dashboard | `/dashboard` | `GET/POST /api/cases` | 📋 Planned |
| Team collaboration | `/dashboard/[case_id]` | `POST /api/cases/{id}/team` | 📋 Planned |
| XAI research / Q&A split screen | `/research` | `POST /api/qa/ask` | 📋 Planned |
| Document upload & ingestion status | shared component | `POST /api/documents/upload` | 📋 Planned |
| Case timeline & entity explorer | `/dashboard/[case_id]/timeline` | `GET /api/cases/{id}/timeline` | 📋 Planned |
| Statutory mapping lookup | `/statutes` | `GET /api/statutes/map` | 📋 Planned |
⚖️ NyayaSarathi
AI-Powered Legal Research, Document Intelligence & Drafting Platform
NyayaSarathi is an AI-powered legal technology platform designed to simplify legal research, document analysis, and legal drafting. It combines Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), Optical Character Recognition (OCR), and role-based access control to help users interact with legal documents and access legal information more efficiently.

The platform provides dedicated workflows for users and advocates, along with administrative controls for managing platform access.

✨ Key Features
🤖 AI-Powered Legal Assistant
Conversational AI for legal questions and explanations.

Context-aware responses using relevant legal information.

Follow-up questions and multi-turn conversations.

AI-powered assistance for understanding complex legal language.

📚 Legal Research & RAG
Retrieval-Augmented Generation for context-aware legal responses.

Document ingestion and text extraction.

Document chunking and embedding generation.

Semantic retrieval of relevant information.

Context-based answer generation using retrieved passages.

📄 Legal Document OCR
Upload supported legal documents for text extraction.

Process digital PDFs and scanned documents.

Extract printed text from scanned documents using OCR.

Preprocess scanned pages to improve extraction quality.

Reconstruct document reading order and organize extracted text for downstream processing.

Pass extracted legal text to the legal research and AI workflows.

OCR accuracy depends on document quality, language, layout, and the configured OCR engine.

✍️ AI Legal Drafting
Generate legal drafts from user-provided instructions.

Assist with structuring legal documents.

Refine and rewrite draft content.

Generate context-aware content using supplied facts and relevant legal information.

AI-generated legal content must be reviewed by a qualified legal professional before use.

🔐 Authentication & Role-Based Access Control
The platform supports role-based access for:

USER — access to available user-facing legal AI features.

ADVOCATE — access to advocate-oriented legal workflows.

ADMIN — administrative access and authorized platform management.

Public registrations must not be allowed to assign privileged roles through user-controlled request data. Administrative privileges should be granted only through authorized procedures.

🌐 Multilingual Interface
The frontend includes localization support for:

English (en)

Hindi (hi)

Marathi (mr)

📊 Administrative Management
Administrative access management.

Controlled role assignment.

Protected administrative operations.

Audit-oriented tracking for sensitive role changes, where configured.

🏗️ System Architecture
NyayaSarathi follows a frontend-backend architecture in which the Next.js application communicates with a FastAPI backend. Supabase PostgreSQL provides persistent relational storage.

                   ┌──────────────────────┐
                   │       User           │
                   └──────────┬───────────┘
                              │
                   ┌──────────▼───────────┐
                   │  Next.js Frontend    │
                   │  Vercel Deployment   │
                   └──────────┬───────────┘
                              │ HTTPS / API
                   ┌──────────▼───────────┐
                   │   FastAPI Backend    │
                   │   Render Deployment  │
                   └──────────┬───────────┘
                              │
              ┌───────────────┼────────────────┐
              │               │                │
     ┌────────▼────────┐ ┌────▼─────────┐ ┌────▼────────────┐
     │ Authentication  │ │ Legal AI /   │ │ OCR & Document  │
     │ & Authorization │ │ RAG / Drafts  │ │ Processing      │
     └────────┬────────┘ └────┬─────────┘ └─────────────────┘
              │               │
              └───────┬───────┘
                      │
             ┌────────▼─────────┐
             │ Supabase         │
             │ PostgreSQL       │
             │ Persistent Data  │
             └──────────────────┘
This diagram represents the logical architecture; exact model providers, storage integrations, and service boundaries depend on the implementation.

🛠️ Technology Stack
Component	Technologies
Frontend	Next.js, React, TypeScript
Backend	Python, FastAPI
Database	Supabase PostgreSQL
Authentication	Google OAuth and application JWT authentication
AI	LLM APIs and model integrations
Retrieval	RAG, embeddings, document chunking
OCR	Tesseract and configured OCR/document-processing components
Document Processing	PDF and extracted-text processing
Deployment	Vercel, Render, Supabase
Version Control	Git, GitHub
The exact models, libraries, and integrations may vary by feature and configuration.

📁 Project Structure
The following is a conceptual overview. Refer to the actual repository for the authoritative directory structure.

NyayaSarathi/
├── backend/
│   ├── main.py
│   ├── routers/
│   ├── services/
│   ├── models/
│   ├── schemas/
│   ├── scripts/
│   ├── migrations/
│   └── requirements.txt
│
├── nyayasarathi-app/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   ├── public/
│   └── package.json
│
├── logs.md
├── README.md
└── .gitignore
Directory and filename details should be adjusted to match the current repository.

⚙️ Getting Started
Prerequisites
Install or configure the following:

Python and pip

Node.js and npm

Git

A Supabase project

Required AI provider API keys

Google OAuth credentials, if using Google sign-in

1. Clone the Repository
git clone https://github.com/Shreedhar-Khorate/NyayaSarathi.git
cd NyayaSarathi
2. Configure the Backend
cd backend

python -m venv .venv
Activate the virtual environment.

Windows:

.venv\Scripts\Activate.ps1
macOS / Linux:

source .venv/bin/activate
Install the backend dependencies:

pip install -r requirements.txt
Create the backend environment file using the variable names expected by the current source code.

Typical configuration values may include:

SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
JWT_SECRET_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
LLM_API_KEY=
FRONTEND_URL=
These names are illustrative, not a verified list of the project's actual environment variables. Check the configuration modules before using them. Never commit real credentials or secret keys.

Start the backend using the actual FastAPI application import path. For example, if the application object is app in main.py:

uvicorn main:app --reload
If main.py is inside a Python package or the application object has a different name, adjust the command accordingly.

3. Configure the Frontend
Open a separate terminal:

cd nyayasarathi-app
npm install
Create the frontend environment file and configure the backend API URL using the variable name expected by the application.

For example:

NEXT_PUBLIC_API_URL=http://localhost:8000
Use this name only if it matches the frontend's configuration. Next.js exposes variables prefixed with NEXT_PUBLIC_ to browser code, so never put private keys in such variables.

Start the development server:

npm run dev
Open the local URL shown in the terminal, typically:

http://localhost:3000

4. Configure Supabase
Create or select a Supabase project.

Configure the PostgreSQL schema and required migrations.

Configure database connectivity and authentication-related environment variables.

Configure Google OAuth redirect URLs if Google sign-in is enabled.

Verify the required tables, indexes, permissions, and row-level security policies.

Confirm that the application can read and write the required records.

Do not expose privileged Supabase keys in the frontend. Apply least-privilege access controls and keep sensitive operations in the trusted backend.

🔄 Core Workflows
AI Chat and Legal Research
User Question
     ↓
FastAPI Endpoint
     ↓
Context Retrieval (if applicable)
     ↓
LLM Request
     ↓
Generated Response
     ↓
Frontend Display
Document OCR and Processing
Document Upload
     ↓
File Validation
     ↓
Digital Text Extraction or OCR
     ↓
Reading-Order Reconstruction
     ↓
Structured Legal Text
     ↓
Chunking and Metadata Extraction
     ↓
Embedding / Retrieval Workflows
Legal Drafting
User Instructions
     ↓
Input Validation
     ↓
Relevant Context Retrieval (if configured)
     ↓
LLM Draft Generation
     ↓
Draft Display and User Review
🚀 Deployment
NyayaSarathi can be deployed using the following services.

Frontend — Vercel
Import the GitHub repository into Vercel.

Configure the frontend root directory as nyayasarathi-app if that matches the repository structure.

Configure the required frontend environment variables.

Deploy the application.

Add the production frontend URL to the backend's allowed CORS origins and OAuth configuration where required.

Backend — Render
Create a Web Service connected to the GitHub repository.

Configure the backend root directory and Python environment.

Set the build command to install the project's dependencies.

Configure the appropriate Uvicorn start command.

Add the required secrets and environment variables.

Configure CORS, frontend URLs, and health checks.

Deploy and verify the API endpoints.

Database — Supabase
Keep Supabase PostgreSQL as the persistent database. Configure the production database URL and credentials securely, and apply the required schema migrations.

Before production deployment, verify that all required database tables and extensions exist and that the application uses the intended persistent storage.

🆓 Free-Tier Deployment Considerations
The free tiers of Vercel, Render, and Supabase can be useful for development, testing, and small demonstrations. They do not guarantee uninterrupted production availability.

Render
Free web services can spin down after inactivity.

The first request after a spin-down may take longer while the service starts.

CPU and memory constraints can affect OCR, large documents, and concurrent AI requests.

Temporary local files should not be treated as persistent storage.

Supabase
Free projects can be paused under the platform's inactivity policy.

Database health checks are useful for monitoring connectivity but do not guarantee that an inactive project will never be paused.

Monitor project status, resource usage, and dashboard notifications.

Maintain backups of important data.

Vercel
The Hobby plan has usage limits.

Monitor build, deployment, and request usage.

Recommendation: Use the free tiers for a prototype, optimize resource-intensive operations, and upgrade services if the application requires dependable availability or sustained usage.

🔒 Security Considerations
Keep all secrets in environment variables.

Never commit .env files, API keys, passwords, or private credentials.

Validate uploaded files, file types, sizes, and page counts.

Enforce authentication and authorization on protected backend routes.

Do not trust frontend role values or user-supplied authorization fields.

Restrict administrative operations to authorized accounts.

Use secure password hashing and validated JWT handling.

Apply appropriate database permissions and row-level security.

Configure CORS with explicit trusted origins.

Avoid logging sensitive legal documents, access tokens, or personal information unnecessarily.

Review AI-generated legal content before relying on it.

🧪 Testing and Quality Assurance
Before a release, verify:

Authentication and session handling.

Role-based authorization.

AI chat and legal drafting workflows.

Legal research and retrieval quality.

OCR extraction for representative digital and scanned documents.

Database persistence and access controls.

API validation and error handling.

Frontend production build and TypeScript checks.

Environment variable configuration and production CORS.

Deployment health checks and resource usage.

Run the tests and commands configured in the current repository rather than assuming that a particular test command or test suite exists.

⚠️ Legal Disclaimer
NyayaSarathi is intended to assist with legal information, research, document processing, and drafting. It does not replace qualified legal advice, professional judgment, or verification of applicable laws and precedents.

AI-generated content may contain errors, omissions, outdated information, or unsupported statements. Verify legal citations and factual claims against authoritative sources before relying on them or submitting documents to a court or other authority.

🗺️ Future Improvements
Potential areas for continued development include:

Improved legal document classification and metadata extraction.

More reliable structural legal chunking.

Better retrieval relevance and source attribution.

Token usage and context-window monitoring.

Background processing for large documents.

Stronger observability, error tracking, and performance monitoring.

Automated tests for authorization and document-processing pipelines.

More robust backups and production deployment practices.

These are potential improvements and should not be interpreted as features that are all currently implemented.

👨‍💻 Development
Contributions and improvements should follow the existing repository architecture, coding conventions, security requirements, and test procedures.

Before submitting changes:

Create a separate feature branch.

Keep secrets and local database artifacts out of version control.

Run relevant tests and static checks.

Review database migrations and authorization changes carefully.

Document new environment variables and setup requirements.

Submit changes for review before merging into the main branch.

📄 License
Add the project's chosen open-source license here if one has been selected. Until a license is added, do not assume that the repository is licensed for unrestricted reuse.

NyayaSarathi — Making legal information more accessible through AI.

"""
NyayaSarathi Backend — Main Entry Point
AI-Powered Judicial Case Intelligence & Decision Support API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request

from routers import analyze, cases, contracts, drafts, qa, search, statutes, war_room

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="NyayaSarathi API",
    description="AI-Powered Judicial Case Intelligence & Decision Support API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception Handlers ────────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "path": str(request.url)},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": exc.errors()},
    )

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(analyze.router,   prefix="/api/analyze",    tags=["Judgment Predictor"])
app.include_router(cases.router,     prefix="/api/cases",      tags=["Cases"])
app.include_router(contracts.router, prefix="/api/contracts",  tags=["Contracts"])
app.include_router(drafts.router,    prefix="/api/drafts",     tags=["Drafting"])
app.include_router(qa.router,        prefix="/api/qa",         tags=["RAG Q&A"])
app.include_router(search.router,    prefix="/api/search",     tags=["Hybrid Search"])
app.include_router(statutes.router,  prefix="/api/statutes",   tags=["Statutory Mapping"])
app.include_router(war_room.router,  prefix="/api/war-room",   tags=["War Room"])

# ── Root & Health ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "service": "NyayaSarathi API",
        "version": "1.0.0",
        "docs": "/docs",
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "NyayaSarathi API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

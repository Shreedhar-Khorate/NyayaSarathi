"""
NyayaSarathi Backend — Main Entry Point
AI-Powered Judicial Case Intelligence & Decision Support API
"""

# ── Logging must be configured FIRST ─────────────────────────────────────────
from logger import setup_logging, get_logger
setup_logging()

from dotenv import load_dotenv
load_dotenv()

import time
import uuid
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from routers import analyze, auth, cases, contracts, drafts, qa, search, statutes, translate, war_room
from services.user_repository import init_user_table

log = get_logger("nyayasarathi")

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
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response Logging Middleware ─────────────────────────────────────
# ANSI helpers (reuse from logger module constants)
_R = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GRAY = "\033[90m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_BLUE = "\033[94m"
_CYAN = "\033[96m"
_MAGENTA = "\033[95m"
_WHITE = "\033[97m"


def _method_color(method: str) -> str:
    return {
        "GET":     f"{_BOLD}{_GREEN}",
        "POST":    f"{_BOLD}{_CYAN}",
        "PUT":     f"{_BOLD}{_YELLOW}",
        "PATCH":   f"{_BOLD}{_YELLOW}",
        "DELETE":  f"{_BOLD}{_RED}",
        "OPTIONS": f"{_DIM}{_GRAY}",
    }.get(method, _WHITE)


def _status_color(status: int) -> str:
    if status < 300:
        return f"{_BOLD}{_GREEN}"
    if status < 400:
        return f"{_BOLD}{_YELLOW}"
    if status < 500:
        return f"{_BOLD}{_YELLOW}"
    return f"{_BOLD}{_RED}"


def _duration_color(ms: float) -> str:
    if ms < 200:
        return _GREEN
    if ms < 1000:
        return _YELLOW
    return _RED


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Skip CORS preflight spam
    if request.method == "OPTIONS":
        return await call_next(request)

    # Assign a short request ID
    req_id = uuid.uuid4().hex[:8].upper()
    start = time.perf_counter()

    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path
    query = f"?{request.url.query}" if request.url.query else ""

    method_col = _method_color(method)

    try:
        log.info(
            f"{_GRAY}[{req_id}]{_R} {method_col}{method}{_R} "
            f"{_WHITE}{path}{query}{_R}  "
            f"{_GRAY}← {client_ip}{_R}",
            extra={"component": "REQUEST"},
        )
    except Exception:
        pass

    # Process request
    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        try:
            log.error(
                f"{_GRAY}[{req_id}]{_R} {method_col}{method}{_R} "
                f"{_WHITE}{path}{_R}  "
                f"{_BOLD}{_RED}500 INTERNAL ERROR{_R}  "
                f"{_RED}{elapsed_ms:.0f}ms{_R}  "
                f"{_GRAY}{exc}{_R}",
                extra={"component": "RESPONSE"},
            )
        except Exception:
            pass
        raise

    elapsed_ms = (time.perf_counter() - start) * 1000
    status = response.status_code
    status_col = _status_color(status)
    dur_col = _duration_color(elapsed_ms)

    try:
        log.info(
            f"{_GRAY}[{req_id}]{_R} {method_col}{method}{_R} "
            f"{_WHITE}{path}{query}{_R}  "
            f"{status_col}{status}{_R}  "
            f"{dur_col}{elapsed_ms:.0f}ms{_R}",
            extra={"component": "RESPONSE"},
        )
    except Exception:
        pass

    return response


# ── Exception Handlers ────────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    log.warning(
        f"{request.method} {request.url.path}  "
        f"\033[93m{exc.status_code}\033[0m  {exc.detail}",
        extra={"component": "ERROR"},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "path": str(request.url)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    log.warning(
        f"{request.method} {request.url.path}  422 Validation error",
        extra={"component": "ERROR"},
    )
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": exc.errors()},
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/api/auth",       tags=["Authentication"])
app.include_router(analyze.router,   prefix="/api/analyze",    tags=["Judgment Predictor"])
app.include_router(cases.router,     prefix="/api/cases",      tags=["Cases"])
app.include_router(contracts.router, prefix="/api/contracts",  tags=["Contracts"])
app.include_router(drafts.router,    prefix="/api/drafts",     tags=["Drafting"])
app.include_router(qa.router,        prefix="/api/qa",         tags=["RAG Q&A"])
app.include_router(search.router,    prefix="/api/search",     tags=["Hybrid Search"])
app.include_router(statutes.router,  prefix="/api/statutes",   tags=["Statutory Mapping"])
app.include_router(translate.router, prefix="/api/translate",  tags=["Translation"])
app.include_router(war_room.router,  prefix="/api/war-room",   tags=["War Room"])


# ── Root & Health ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"service": "NyayaSarathi API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "NyayaSarathi API", "version": "1.0.0"}


# ── Startup / Shutdown Events ─────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    # Initialize user database table
    try:
        init_user_table()
    except Exception as e:
        log.error(f"Failed to initialize user database table: {e}", extra={"component": "STARTUP"})

    log.info(
        f"\033[1m\033[92m⚖  NyayaSarathi API\033[0m  "
        f"\033[90mv1.0.0 · http://0.0.0.0:8000 · docs → /docs\033[0m",
        extra={"component": "STARTUP"},
    )
    log.info(
        "Routes: /api/auth  /api/analyze  /api/cases  /api/contracts  /api/drafts  "
        "/api/qa  /api/search  /api/statutes  /api/war-room",
        extra={"component": "STARTUP"},
    )


@app.on_event("shutdown")
async def on_shutdown():
    log.info("NyayaSarathi API shutting down.", extra={"component": "STARTUP"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

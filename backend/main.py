"""
NyayaSarathi Backend — Main Entry Point
AI-Powered Judicial Case Intelligence & Decision Support API
"""

# ── Load environment before configuring logging ──────────────────────────────
from dotenv import load_dotenv
load_dotenv()

import os
import re
import json
import time
import uuid
import logging
from datetime import datetime, timezone

from logger import (
    setup_logging, get_logger,
    RESET as _R, BOLD as _BOLD, DIM as _DIM,
    GREEN as _GREEN, YELLOW as _YELLOW, RED as _RED,
    BLUE as _BLUE, CYAN as _CYAN, MAGENTA as _MAGENTA,
    WHITE as _WHITE, GRAY as _GRAY
)
setup_logging()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.encoders import jsonable_encoder

from routers import admin, analyze, auth, cases, contracts, drafts, advocate, news, ocr, qa, search, statutes, translate, war_room
from routers import google_oauth, profile, chat
from services.user_repository import init_user_table
from services.document_processor import init_document_tables
from services.ingest import init_database
from services.war_room_repository import init_war_room_tables
from services.chat_repository import init_chat_tables

log = get_logger("nyayasarathi")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="NyayaSarathi API",
    description="AI-Powered Judicial Case Intelligence & Decision Support API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
def _get_cors_origins():
    cors_env = os.getenv("CORS_ORIGINS", "").strip()
    origins = [
        "https://nyayasarathi.vercel.app",
    ]
    if cors_env:
        try:
            parsed = json.loads(cors_env)
            if isinstance(parsed, list):
                origins.extend([o.strip() for o in parsed if o and isinstance(o, str)])
        except Exception:
            origins.extend([o.strip() for o in cors_env.split(",") if o.strip()])

    frontend_url = os.getenv("FRONTEND_BASE_URL", "").strip()
    if frontend_url and frontend_url not in origins:
        origins.append(frontend_url)

    is_prod = os.getenv("ENVIRONMENT", "").strip().lower() == "production"
    if not is_prod:
        # Default local development origins
        dev_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
        for do in dev_origins:
            if do not in origins:
                origins.append(do)
    return list(dict.fromkeys([o.rstrip("/") for o in origins if o]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_origin_regex=r"^https://nyayasarathi.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response Logging Middleware ─────────────────────────────────────
LOG_HEALTH_CHECKS = os.getenv("LOG_HEALTH_CHECKS", "").strip().lower() in ("1", "true", "yes")
HEALTH_PROBE_PATHS = {"/health", "/ready", "/favicon.ico"}

_SENSITIVE_PARAM_RE = re.compile(
    r"((?:token|password|secret|key|access_token|authorization)=)([^&]+)",
    re.IGNORECASE,
)

def _sanitize_query(query: str) -> str:
    """Mask sensitive query parameter values in logs."""
    if not query:
        return ""
    return _SENSITIVE_PARAM_RE.sub(r"\1[REDACTED]", query)


def _method_color(method: str) -> str:
    return {
        "GET":     f"{_BOLD}{_GREEN}",
        "POST":    f"{_BOLD}{_CYAN}",
        "PUT":     f"{_BOLD}{_YELLOW}",
        "PATCH":   f"{_BOLD}{_YELLOW}",
        "DELETE":  f"{_BOLD}{_RED}",
        "OPTIONS": f"{_DIM}{_GRAY}",
        "HEAD":    f"{_DIM}{_GRAY}",
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

    path = request.url.path
    method = request.method
    is_health_probe = (path in HEALTH_PROBE_PATHS) or (path == "/" and method in ("GET", "HEAD"))
    should_suppress_log = is_health_probe and not LOG_HEALTH_CHECKS

    req_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:8].upper()
    start = time.perf_counter()

    client_ip = request.client.host if request.client else "unknown"
    raw_query = f"?{request.url.query}" if request.url.query else ""
    query = _sanitize_query(raw_query)

    method_col = _method_color(method)

    if not should_suppress_log:
        try:
            log.info(
                f"{_GRAY}[{req_id}]{_R} {method_col}{method}{_R} "
                f"{_WHITE}{path}{query}{_R}  "
                f"{_GRAY}<- {client_ip}{_R}",
                extra={"component": "REQUEST"},
            )
        except Exception:
            pass
    elif log.isEnabledFor(logging.DEBUG):
        log.debug(
            f"[{req_id}] {method} {path} <- {client_ip}",
            extra={"component": "HEALTH"},
        )

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
                extra={"component": "ERROR"},
                exc_info=True,
            )
        except Exception:
            pass
        raise

    elapsed_ms = (time.perf_counter() - start) * 1000
    status = response.status_code

    # Always inject X-Request-ID into response headers for traceability
    response.headers["X-Request-ID"] = req_id

    # Suppress successful health check probe responses to keep logs clean on Render
    if should_suppress_log and status < 400:
        return response

    status_col = _status_color(status)
    dur_col = _duration_color(elapsed_ms)

    level = logging.INFO
    if status >= 500:
        level = logging.ERROR
    elif status >= 400:
        level = logging.WARNING

    try:
        log.log(
            level,
            f"{_GRAY}[{req_id}]{_R} {method_col}{method}{_R} "
            f"{_WHITE}{path}{query}{_R}  "
            f"{status_col}{status}{_R}  "
            f"{dur_col}{elapsed_ms:.0f}ms{_R}",
            extra={"component": "RESPONSE" if status < 400 else "ERROR"},
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
        content={"error": "Validation error", "details": jsonable_encoder(exc.errors())},
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,         prefix="/api/auth",            tags=["Authentication"])
app.include_router(google_oauth.router, prefix="/api/auth/google",     tags=["Google OAuth"])
app.include_router(profile.router,      prefix="/api/profile",         tags=["Member Profile"])
app.include_router(profile.router,      prefix="/api",                 tags=["User History"], include_in_schema=False)
app.include_router(analyze.router,   prefix="/api/analyze",    tags=["Judgment Predictor"])
app.include_router(cases.router,     prefix="/api/cases",      tags=["Cases"])
app.include_router(contracts.router, prefix="/api/contracts",  tags=["Contracts"])
app.include_router(drafts.router,    prefix="/api/drafts",     tags=["Drafting"])
app.include_router(qa.router,        prefix="/api/qa",         tags=["RAG Q&A"])
app.include_router(search.router,    prefix="/api/search",     tags=["Hybrid Search"])
app.include_router(statutes.router,  prefix="/api/statutes",   tags=["Statutory Mapping"])
app.include_router(translate.router, prefix="/api/translate",  tags=["Translation"])
app.include_router(ocr.router,         prefix="/api/ocr",        tags=["Legal Document OCR"])
app.include_router(ocr.router,         prefix="/api/legal-documents", tags=["Legal Document OCR"], include_in_schema=False)
app.include_router(ocr.router,         prefix="/api/v1/documents", tags=["Legacy OCR"], include_in_schema=False)
app.include_router(war_room.router,    prefix="/api/war-room",   tags=["Legal War Room"])
app.include_router(admin.router,         prefix="/api/admin",           tags=["Admin Dashboard"])
app.include_router(advocate.router,      prefix="/api/advocate",        tags=["Advocate Portal"])
app.include_router(news.router,          prefix="/api/news",            tags=["Legal News"])
app.include_router(chat.router,          prefix="/api/chat",            tags=["Chat"])

@app.get("/robots.txt", response_class=PlainTextResponse, include_in_schema=False)
def robots_txt():
    """Polite crawler directives for web crawlers scanning Render host."""
    return "User-agent: *\nDisallow: /api/\n"


# ── REST endpoints ────────────────────────────────────────────────────────────

@app.get("/")
@app.get("/health")
@app.head("/")
@app.head("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/ready", tags=["Health"])
def readiness_check():
    """
    Readiness probe: verifies application dependencies (authoritative PostgreSQL).
    Returns 200 if ready to serve traffic, 503 if primary database connection fails in production.
    """
    is_prod = os.getenv("ENVIRONMENT", "").strip().lower() == "production"
    from services.user_repository import is_postgres_authoritative, pg_connection_scope

    try:
        authoritative = is_postgres_authoritative()
    except Exception as e:
        if is_prod:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "database": "configuration_error", "detail": str(e)},
            )
        authoritative = False

    db_status = "connected"
    if authoritative:
        try:
            with pg_connection_scope() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    cur.fetchone()
        except Exception:
            db_status = "unavailable"
            if is_prod:
                return JSONResponse(
                    status_code=503,
                    content={"status": "unhealthy", "database": "unavailable", "detail": "PostgreSQL connection failed"},
                )
    else:
        db_status = "sqlite_fallback"
        if is_prod:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "database": "sqlite_unauthorized", "detail": "Production requires PostgreSQL"},
            )

    return {
        "status": "ready",
        "service": "NyayaSarathi API",
        "database": db_status,
        "authoritative_postgres": authoritative,
    }


@app.get("/supa", tags=["Health"])
@app.head("/supa", tags=["Health"])
@app.post("/supa", tags=["Health"])
def supabase_keepalive():
    """
    Supabase Keep-Alive Route:
    Inserts a dummy record into `_supabase_keepalive` and immediately deletes it
    to register genuine write activity and prevent Supabase free-tier auto-pausing.
    """
    is_prod = os.getenv("ENVIRONMENT", "").strip().lower() == "production"
    from services.user_repository import (
        is_postgres_authoritative,
        pg_connection_scope,
        get_db_connection,
    )

    try:
        authoritative = is_postgres_authoritative()
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "configuration_error", "detail": str(e)},
        )

    ping_id = uuid.uuid4().hex
    pinged_at = datetime.now(timezone.utc).isoformat()

    if authoritative:
        try:
            with pg_connection_scope() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS public._supabase_keepalive (
                            id TEXT PRIMARY KEY,
                            pinged_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
                        );
                        ALTER TABLE public._supabase_keepalive ENABLE ROW LEVEL SECURITY;
                        """
                    )
                    cur.execute(
                        "INSERT INTO public._supabase_keepalive (id, pinged_at) VALUES (%s, %s);",
                        (ping_id, pinged_at),
                    )
                    conn.commit()
                    cur.execute(
                        "DELETE FROM public._supabase_keepalive WHERE id = %s;",
                        (ping_id,),
                    )
                    conn.commit()
            log.info(f"Supabase keep-alive write+delete verified (ping_id={ping_id}).", extra={"component": "DB"})
            return {
                "status": "ok",
                "database": "supabase_postgres",
                "operation": "insert_and_delete",
                "table": "_supabase_keepalive",
                "ping_id": ping_id,
                "pinged_at": pinged_at,
            }
        except Exception as e:
            log.error(f"Supabase keep-alive failed: {e}", extra={"component": "DB"})
            return JSONResponse(
                status_code=503,
                content={"status": "error", "database": "supabase_postgres", "detail": "Keep-alive write failed."},
            )

    if is_prod:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "sqlite_unauthorized", "detail": "Production requires PostgreSQL"},
        )

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS _supabase_keepalive (
                id TEXT PRIMARY KEY,
                pinged_at TEXT NOT NULL
            );
            """
        )
        cur.execute(
            "INSERT INTO _supabase_keepalive (id, pinged_at) VALUES (?, ?);",
            (ping_id, pinged_at),
        )
        conn.commit()
        cur.execute("DELETE FROM _supabase_keepalive WHERE id = ?;", (ping_id,))
        conn.commit()
        log.info(f"Local keep-alive write+delete verified (ping_id={ping_id}).", extra={"component": "DB"})
        return {
            "status": "ok",
            "database": "sqlite_fallback",
            "operation": "insert_and_delete",
            "table": "_supabase_keepalive",
            "ping_id": ping_id,
            "pinged_at": pinged_at,
        }
    except Exception as e:
        log.error(f"Local keep-alive failed: {e}", extra={"component": "DB"})
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "sqlite_fallback", "detail": str(e)},
        )
    finally:
        conn.close()


# ── Startup / Shutdown Events ─────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    # Initialize all database tables safely
    try:
        init_user_table()
    except Exception as e:
        log.error(f"Failed to initialize user database table: {e}", extra={"component": "STARTUP"})

    try:
        init_document_tables()
    except Exception as e:
        log.error(f"Failed to initialize document database tables: {e}", extra={"component": "STARTUP"})

    try:
        init_database()
    except Exception as e:
        log.error(f"Failed to initialize judgment database schema: {e}", extra={"component": "STARTUP"})

    try:
        init_war_room_tables()
    except Exception as e:
        log.error(f"Failed to initialize war room database tables: {e}", extra={"component": "STARTUP"})

    try:
        init_chat_tables()
    except Exception as e:
        log.error(f"Failed to initialize chat database tables: {e}", extra={"component": "STARTUP"})

    # Startup Diagnostics Summary
    port = int(os.environ.get("PORT", 8000))
    is_prod = os.getenv("ENVIRONMENT", "").strip().lower() == "production"
    from services.user_repository import is_postgres_authoritative

    try:
        authoritative = is_postgres_authoritative()
        db_mode = f"Authoritative PostgreSQL Pooler {_GREEN}[CONNECTED]{_R}" if authoritative else f"SQLite Fallback {_YELLOW}[DEV_MODE]{_R}"
    except Exception as e:
        db_mode = f"{_RED}[ERROR: {e}]{_R}"

    sb_url = os.getenv("SUPABASE_URL", "")
    storage_mode = f"Supabase Storage (chat-attachments, document-uploads) {_GREEN}[CONFIGURED]{_R}" if sb_url else f"{_YELLOW}[LOCAL_ONLY]{_R}"
    
    gemini_ready = bool(os.getenv("GEMINI_API_KEY") or os.getenv("PREDICTOR_GEMINI_API_KEY"))
    groq_ready = bool(os.getenv("GROQ_API_KEY") or os.getenv("WAR_ROOM_GROQ_API_KEY"))
    ai_status = f"Gemini: {'OK' if gemini_ready else 'MISSING'} | Groq: {'OK' if groq_ready else 'MISSING'}"
    
    health_mode = "Active (Silenced on 200 OK — set LOG_HEALTH_CHECKS=true to show all)" if not LOG_HEALTH_CHECKS else "Active (Verbose Logging)"

    log.info(
        f"{_BOLD}{_GREEN}========================================================================{_R}",
        extra={"component": "STARTUP"},
    )
    log.info(
        f"{_BOLD}{_GREEN} NyayaSarathi API v2.0.0 — Production Diagnostics{_R}",
        extra={"component": "STARTUP"},
    )
    log.info(
        f"{_BOLD}{_GREEN}========================================================================{_R}",
        extra={"component": "STARTUP"},
    )
    log.info(f"  Environment   : {'PRODUCTION (Render)' if is_prod else 'DEVELOPMENT (Local)'}", extra={"component": "STARTUP"})
    log.info(f"  Database      : {db_mode}", extra={"component": "STARTUP"})
    log.info(f"  File Storage  : {storage_mode}", extra={"component": "STARTUP"})
    log.info(f"  AI Engines    : {ai_status}", extra={"component": "STARTUP"})
    log.info(f"  Health Probes : {health_mode}", extra={"component": "STARTUP"})
    log.info(f"  CORS Allowed  : {len(_get_cors_origins())} origin(s) configured", extra={"component": "STARTUP"})
    log.info(f"  Service Port  : {port} · Swagger UI: http://0.0.0.0:{port}/docs", extra={"component": "STARTUP"})
    log.info(
        f"{_BOLD}{_GREEN}========================================================================{_R}",
        extra={"component": "STARTUP"},
    )


@app.on_event("shutdown")
async def on_shutdown():
    log.info("NyayaSarathi API shutting down.", extra={"component": "STARTUP"})


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)



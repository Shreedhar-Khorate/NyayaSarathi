from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.exceptions import http_exception_handler, validation_exception_handler
from app.api.v1.router import router as v1_router

# ── App factory ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-Powered Judicial Case Intelligence & Decision Support API. "
        "Full Swagger docs available below."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────────────────
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(v1_router, prefix="/api/v1")

# ── Legacy redirect: old /api/analyze → new /api/v1/analyze ─────────────────
@app.post("/api/analyze", include_in_schema=False)
async def legacy_analyze_redirect():
    return RedirectResponse(url="/api/v1/analyze", status_code=308)

# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

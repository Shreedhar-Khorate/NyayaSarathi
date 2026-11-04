"""
NyayaSarathi — Industry-Standard Cloud & Production Logging System
Optimized for Render, Docker, and Multi-Cloud environments.

Features:
- Colored human-friendly console output with precise microsecond timing and component badges.
- Automatic component deduction from module/logger hierarchy.
- Production JSON logging mode (LOG_FORMAT=json) for APM/Datadog/CloudWatch.
- Automatic de-noising of high-frequency health probes and Uvicorn access lines.
- Safe Unicode & ANSI handling across Windows, Linux, and Cloud container environments.
"""

import io
import json
import logging
import os
import re
import sys
from datetime import datetime
from typing import Optional

# ── ANSI Color Codes ──────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"

# Foreground colors
WHITE   = "\033[97m"
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
GRAY    = "\033[90m"

# Background colors
BG_RED    = "\033[41m"
BG_GREEN  = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE   = "\033[44m"
BG_CYAN   = "\033[46m"
BG_GRAY   = "\033[100m"

# Determine whether color is enabled
def _colors_enabled() -> bool:
    if os.getenv("NO_COLOR", "").strip() or os.getenv("LOG_COLORS", "").lower() in ("false", "0", "no"):
        return False
    # Render, Github Actions, and modern CI/CD consoles support colors
    if os.getenv("RENDER") or os.getenv("CI") or os.getenv("TERM"):
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


USE_COLORS = _colors_enabled()

# ── Level → Color + Badge mapping ────────────────────────────────────────────
LEVEL_STYLES = {
    "DEBUG":    (GRAY,   f"{DIM}DEBUG {RESET}" if USE_COLORS else "DEBUG"),
    "INFO":     (WHITE,  f"{BOLD}{CYAN}INFO  {RESET}" if USE_COLORS else "INFO "),
    "WARNING":  (YELLOW, f"{BOLD}{YELLOW}WARN  {RESET}" if USE_COLORS else "WARN "),
    "ERROR":    (RED,    f"{BOLD}{RED}ERROR {RESET}" if USE_COLORS else "ERROR"),
    "CRITICAL": (RED,    f"{BOLD}{BG_RED}{WHITE}CRIT  {RESET}" if USE_COLORS else "CRIT "),
}

# ── Component → Color mapping ─────────────────────────────────────────────────
COMPONENT_COLORS = {
    "REQUEST":   f"{BOLD}{BLUE}",
    "RESPONSE":  f"{BOLD}{GREEN}",
    "STARTUP":   f"{BOLD}{GREEN}",
    "SHUTDOWN":  f"{BOLD}{YELLOW}",
    "DB":        f"{BOLD}{CYAN}",
    "STORAGE":   f"{BOLD}{CYAN}",
    "AUTH":      f"{BOLD}{YELLOW}",
    "OAUTH":     f"{BOLD}{YELLOW}",
    "CHAT":      f"{BOLD}{MAGENTA}",
    "CHAT_DB":   f"{BOLD}{MAGENTA}",
    "OCR":       f"{BOLD}{CYAN}",
    "WAR_ROOM":  f"{BOLD}{YELLOW}",
    "CONTRACT":  f"{BOLD}{BLUE}",
    "DRAFT":     f"{BOLD}{MAGENTA}",
    "LEGAL":     f"{BOLD}{BLUE}",
    "USER":      f"{BOLD}{CYAN}",
    "USER_DB":   f"{BOLD}{CYAN}",
    "ADVOCATE":  f"{BOLD}{YELLOW}",
    "ADMIN":     f"{BOLD}{RED}",
    "NEWS":      f"{BOLD}{GREEN}",
    "HEALTH":    f"{DIM}{GRAY}",
    "PIPELINE":  f"{BOLD}{MAGENTA}",
    "ERROR":     f"{BOLD}{RED}",
    "UVICORN":   f"{DIM}{GRAY}",
    "APP":       f"{BOLD}{WHITE}",
}

# Component auto-deduction pattern
def infer_component(name: str) -> str:
    """Infer a concise, readable component tag from a logger's hierarchical name."""
    if not name:
        return "APP"
    low = name.lower()
    if "oauth" in low:
        return "OAUTH"
    if "auth" in low:
        return "AUTH"
    if "chat_repo" in low:
        return "CHAT_DB"
    if "chat" in low:
        return "CHAT"
    if "ocr" in low or "document_processor" in low:
        return "OCR"
    if "war_room" in low:
        return "WAR_ROOM"
    if "contract" in low:
        return "CONTRACT"
    if "draft" in low:
        return "DRAFT"
    if "user_repo" in low or "user_repository" in low:
        return "USER_DB"
    if "user" in low or "profile" in low:
        return "USER"
    if "advocate" in low:
        return "ADVOCATE"
    if "admin" in low:
        return "ADMIN"
    if "statute" in low or "search" in low or "qa" in low or "rag" in low or "precedent" in low:
        return "LEGAL"
    if "news" in low:
        return "NEWS"
    if "supabase" in low or "storage" in low:
        return "STORAGE"
    if "database" in low or "postgres" in low or "sqlite" in low or "db" in low:
        return "DB"
    if "uvicorn" in low:
        return "UVICORN"
    # Fallback to sanitized tail of logger name
    parts = name.split(".")
    clean_tail = parts[-1].replace("_router", "").replace("_service", "").replace("_repo", "").upper()
    return clean_tail[:9] or "APP"


class NyayaFormatter(logging.Formatter):
    """
    Structured, high-contrast log formatter.

    Format:
        HH:MM:SS.mmm  INFO   | COMPONENT  | message
    """

    def format(self, record: logging.LogRecord) -> str:
        now = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.") + \
              f"{int(record.created * 1000) % 1000:03d}"

        level_name = record.levelname
        _, level_badge = LEVEL_STYLES.get(level_name, (WHITE, f"{level_name:<5}"))

        # Extract or infer component tag
        component = getattr(record, "component", None)
        if not component:
            component = infer_component(record.name)

        if USE_COLORS:
            comp_color = COMPONENT_COLORS.get(component, WHITE)
            comp_str = f"{comp_color}{component:<10}{RESET}"
            sep = f"{GRAY}|{RESET}"
            ts_str = f"{GRAY}{now}{RESET}"
        else:
            comp_str = f"{component:<10}"
            sep = "|"
            ts_str = now

        msg = record.getMessage()

        # Sanitize for consoles that do not support unicode
        encoding = getattr(sys.stdout, "encoding", "utf-8") or "utf-8"
        try:
            msg.encode(encoding)
        except (UnicodeEncodeError, LookupError):
            msg = msg.encode("ascii", errors="replace").decode("ascii")

        formatted = f"  {ts_str}  {level_badge} {sep} {comp_str} {sep} {msg}"

        # Append traceback if present
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            formatted += f"\n{record.exc_text}"

        return formatted


class NyayaJsonFormatter(logging.Formatter):
    """Production JSON log formatter for cloud logging collectors (Datadog, AWS, GCP)."""

    def format(self, record: logging.LogRecord) -> str:
        component = getattr(record, "component", None) or infer_component(record.name)
        payload = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "component": component,
            "logger": record.name,
            "message": record.getMessage(),
        }
        req_id = getattr(record, "req_id", None)
        if req_id:
            payload["req_id"] = req_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


class UvicornFilter(logging.Filter):
    """
    Suppresses noisy uvicorn raw HTTP access lines.
    Replaced by our unified FastAPI middleware which tracks request IDs, duration, and IP.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        # Keep startup/shutdown messages, suppress raw HTTP access lines
        if " - \"" in msg:   # e.g. '127.0.0.1 - "GET / HTTP/1.1" 200'
            return False
        return True


def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure the root logger and uvicorn loggers.
    Respects LOG_LEVEL, LOG_FORMAT, and NO_COLOR environment variables.
    """
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    log_level_str = (level or os.getenv("LOG_LEVEL", "INFO")).strip().upper()
    resolved_level = getattr(logging, log_level_str, logging.INFO)

    log_format = os.getenv("LOG_FORMAT", "console").strip().lower()
    if log_format == "json":
        formatter = NyayaJsonFormatter()
    else:
        formatter = NyayaFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Root application logger
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    
    # Enforce root logger level and prevent external libraries (such as paddle) from downgrading it
    root.setLevel(resolved_level)
    _native_set_level = root.setLevel
    def _protected_set_level(new_level):
        try:
            numeric_level = logging._checkLevel(new_level) if isinstance(new_level, (str, int)) else resolved_level
        except Exception:
            numeric_level = resolved_level
        # Prevent third-party packages from silently bumping log level above our configured level
        if numeric_level > resolved_level and numeric_level in (logging.WARNING, logging.ERROR):
            return
        _native_set_level(new_level)
    root.setLevel = _protected_set_level

    # Uvicorn loggers
    for name in ("uvicorn", "uvicorn.error", "uvicorn.asgi"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.addHandler(handler)
        lg.setLevel(resolved_level)
        lg.propagate = False

    # Uvicorn access logger — filtered to eliminate duplicate access lines
    access_log = logging.getLogger("uvicorn.access")
    access_log.addFilter(UvicornFilter())
    access_log.handlers.clear()
    access_log.addHandler(handler)
    access_log.propagate = False

    # Silence noisy low-level HTTP and driver logs
    for noisy in ("httpx", "httpcore", "duckdb", "watchfiles", "passlib", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named child logger inheriting NyayaFormatter from root."""
    lg = logging.getLogger(name)
    log_level_str = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    resolved_level = getattr(logging, log_level_str, logging.INFO)
    lg.setLevel(resolved_level)
    return lg

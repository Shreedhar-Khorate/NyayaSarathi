"""
NyayaSarathi — Structured Logging Configuration
Industry-standard colored terminal logs with request timing and pipeline tracing.
"""

import io
import logging
import sys
from datetime import datetime

# ── ANSI Color Codes ──────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"

# Foreground colors
WHITE  = "\033[97m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"
MAGENTA= "\033[95m"
GRAY   = "\033[90m"

# Background colors (for badges)
BG_GREEN  = "\033[42m"
BG_RED    = "\033[41m"
BG_YELLOW = "\033[43m"
BG_BLUE   = "\033[44m"
BG_CYAN   = "\033[46m"
BG_GRAY   = "\033[100m"


# ── Level → Color + Badge mapping ────────────────────────────────────────────
LEVEL_STYLES = {
    "DEBUG":    (GRAY,    f"{DIM}DEBUG {RESET}"),
    "INFO":     (WHITE,   f"{BOLD}{CYAN}INFO  {RESET}"),
    "WARNING":  (YELLOW,  f"{BOLD}{YELLOW}WARN  {RESET}"),
    "ERROR":    (RED,     f"{BOLD}{RED}ERROR {RESET}"),
    "CRITICAL": (RED,     f"{BOLD}{BG_RED}{WHITE}CRIT  {RESET}"),
}

# ── Component → Color mapping ─────────────────────────────────────────────────
COMPONENT_COLORS = {
    "REQUEST":   f"{BOLD}{BLUE}",
    "RESPONSE":  f"{BOLD}{GREEN}",
    "PIPELINE":  f"{BOLD}{MAGENTA}",
    "DB":        f"{BOLD}{CYAN}",
    "ERROR":     f"{BOLD}{RED}",
    "STARTUP":   f"{BOLD}{GREEN}",
    "UVICORN":   f"{DIM}{GRAY}",
}


class NyayaFormatter(logging.Formatter):
    """
    Colored, structured log formatter.

    Format:
        HH:MM:SS.mmm  INFO   │ COMPONENT  │ message
    """

    def format(self, record: logging.LogRecord) -> str:
        now = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.") + \
              f"{int(record.created * 1000) % 1000:03d}"

        level_name = record.levelname
        _, level_badge = LEVEL_STYLES.get(level_name, (WHITE, level_name))

        # Extract optional component tag injected via `extra={"component": "..."}`
        component = getattr(record, "component", "APP")
        comp_color = COMPONENT_COLORS.get(component, WHITE)
        comp_str = f"{comp_color}{component:<9}{RESET}"

        # Message
        msg = record.getMessage()

        # Separator
        sep = f"{GRAY}|{RESET}"

        return (
            f"  {GRAY}{now}{RESET}  {level_badge} {sep} {comp_str} {sep} {msg}"
        )


class UvicornFilter(logging.Filter):
    """Suppresses noisy uvicorn access log lines (replaced by middleware)."""
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        # Keep startup/shutdown messages, suppress raw HTTP access lines
        if " - \"" in msg:   # e.g. '127.0.0.1 - "GET / HTTP/1.1" 200'
            return False
        return True


def setup_logging() -> None:
    """
    Configure the root logger and uvicorn loggers with the NyayaFormatter.
    Call this once at application startup in main.py.
    """
    # Force UTF-8 on Windows to support colored output correctly
    stdout_utf8 = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    handler = logging.StreamHandler(stdout_utf8)
    handler.setFormatter(NyayaFormatter())

    # Root application logger
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)

    # Uvicorn loggers — re-format them too
    for name in ("uvicorn", "uvicorn.error", "uvicorn.asgi"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.addHandler(handler)
        lg.propagate = False

    # Uvicorn access log — suppress raw access lines (our middleware replaces them)
    access_log = logging.getLogger("uvicorn.access")
    access_log.addFilter(UvicornFilter())
    access_log.handlers.clear()
    access_log.addHandler(handler)
    access_log.propagate = False

    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "duckdb", "watchfiles"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


# ── Convenience logger factory ────────────────────────────────────────────────
def get_logger(name: str) -> logging.Logger:
    """Return a named child logger inheriting NyayaFormatter from root."""
    return logging.getLogger(name)

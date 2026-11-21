"""
NyayaSarathi — Automated Keep-Alive & Infrastructure Warm-Up Bot.

Runs two coordinated keep-alive workers:
  1. Render Warm-Up Bot: Pings /ready every 10 minutes to prevent the 15-minute idle spin-down.
  2. Supabase Persistence Bot: Pings /supa every 30 minutes to execute a safe keep-alive
     write/delete transaction and prevent Supabase 7-day project auto-pausing.

Usage:
  # Run continuous background daemon:
  python backend/scripts/keepalive_bot.py

  # Run a single pre-flight health & keepalive check (for cron):
  python backend/scripts/keepalive_bot.py --once

  # Custom endpoints and intervals:
  python backend/scripts/keepalive_bot.py --base-url https://nyayasarathi.onrender.com --render-interval 600 --supa-interval 1800
"""

import argparse
import datetime
import os
import sys
import time
import urllib.request
import urllib.error
import json

# ANSI Colors
RESET   = "\033[0m"
BOLD    = "\033[1m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
CYAN    = "\033[96m"
GRAY    = "\033[90m"


def timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ping_endpoint(url: str, timeout: int = 45) -> dict:
    """Send an HTTP GET request to an endpoint and return timing and response data."""
    start = time.perf_counter()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "NyayaSarathi-KeepAliveBot/2.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = (time.perf_counter() - start) * 1000
            body = resp.read().decode("utf-8", errors="ignore")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body[:120]
            return {
                "success": True,
                "status_code": resp.status,
                "elapsed_ms": round(elapsed_ms, 1),
                "data": parsed,
                "error": None,
            }
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "success": False,
            "status_code": e.code,
            "elapsed_ms": round(elapsed_ms, 1),
            "data": None,
            "error": f"HTTP {e.code}: {e.reason}",
        }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "success": False,
            "status_code": 0,
            "elapsed_ms": round(elapsed_ms, 1),
            "data": None,
            "error": str(e),
        }


def run_render_bot(base_url: str):
    """Bot 1: Render container warm-up check."""
    url = f"{base_url.rstrip('/')}/ready"
    res = ping_endpoint(url)
    ts = timestamp()
    if res["success"]:
        print(f"[{ts}] {CYAN}[BOT 1: RENDER]{RESET} {GREEN}WARM{RESET} (HTTP {res['status_code']} in {res['elapsed_ms']}ms) -> {url}")
    else:
        print(f"[{ts}] {CYAN}[BOT 1: RENDER]{RESET} {RED}FAIL{RESET} ({res['error']} in {res['elapsed_ms']}ms) -> {url}")
    return res


def run_supabase_bot(base_url: str):
    """Bot 2: Supabase active transaction keepalive check."""
    url = f"{base_url.rstrip('/')}/supa"
    res = ping_endpoint(url)
    ts = timestamp()
    if res["success"]:
        msg = ""
        if isinstance(res["data"], dict) and "action" in res["data"]:
            msg = f" [Action: {res['data'].get('action')}]"
        print(f"[{ts}] {YELLOW}[BOT 2: SUPABASE]{RESET} {GREEN}ACTIVE{RESET} (HTTP {res['status_code']} in {res['elapsed_ms']}ms){msg} -> {url}")
    else:
        print(f"[{ts}] {YELLOW}[BOT 2: SUPABASE]{RESET} {RED}FAIL{RESET} ({res['error']} in {res['elapsed_ms']}ms) -> {url}")
    return res


def main():
    parser = argparse.ArgumentParser(description="NyayaSarathi Dual Keep-Alive Bot")
    parser.add_argument("--base-url", default=os.getenv("BACKEND_URL", "https://nyayasarathi.onrender.com"),
                        help="Backend API base URL (default: https://nyayasarathi.onrender.com)")
    parser.add_argument("--render-interval", type=int, default=int(os.getenv("RENDER_PING_INTERVAL", "600")),
                        help="Render warm-up interval in seconds (default: 600 / 10m)")
    parser.add_argument("--supa-interval", type=int, default=int(os.getenv("SUPA_PING_INTERVAL", "1800")),
                        help="Supabase keep-alive interval in seconds (default: 1800 / 30m)")
    parser.add_argument("--once", action="store_true",
                        help="Run both checks once and exit (exit code 0 if both pass, 1 if any fail)")
    args = parser.parse_args()

    print(f"\n{BOLD}{CYAN}================================================================{RESET}")
    print(f"{BOLD}{CYAN} 🤖 NyayaSarathi Dual Keep-Alive & Infrastructure Warm-Up Bot {RESET}")
    print(f"{BOLD}{CYAN}================================================================{RESET}")
    print(f" Target Host:       {args.base_url}")
    print(f" Bot 1 (Render):    Every {args.render_interval}s ({args.render_interval//60} min) -> /ready")
    print(f" Bot 2 (Supabase):  Every {args.supa_interval}s ({args.supa_interval//60} min) -> /supa\n")

    if args.once:
        r1 = run_render_bot(args.base_url)
        r2 = run_supabase_bot(args.base_url)
        if r1["success"] and r2["success"]:
            print(f"\n{GREEN}{BOLD}✓ Both infrastructure bots completed successfully.{RESET}\n")
            sys.exit(0)
        else:
            print(f"\n{RED}{BOLD}✗ One or more keep-alive checks failed.{RESET}\n")
            sys.exit(1)

    # Continuous daemon loop
    last_render = 0.0
    last_supa = 0.0
    try:
        while True:
            now = time.time()
            if now - last_render >= args.render_interval:
                run_render_bot(args.base_url)
                last_render = now
            if now - last_supa >= args.supa_interval:
                run_supabase_bot(args.base_url)
                last_supa = now
            time.sleep(5)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Keep-Alive Bot stopped gracefully.{RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()

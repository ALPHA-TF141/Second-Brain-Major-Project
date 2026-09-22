#!/usr/bin/env python3
"""
Jarvis OS - Backend API Sweep
=============================
Logs into a RUNNING backend and calls every GET route it can reach, reporting any
5xx (runtime crash) as a failure. This catches real backend exceptions that the
browser smoke test cannot see.

Usage:
    # backend must be running on 127.0.0.1:8000
    python scripts/api_sweep.py
    python scripts/api_sweep.py --base http://127.0.0.1:8000 --user Immanuel --password secondbrain
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

SHOW_SOFT = "--all" in sys.argv
GREEN, RED, YELLOW, DIM, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[2m", "\033[0m"

# Path parameters that need sample values to build a request
SAMPLES = {
    "node_id": "1", "memory_id": "1", "session_id": "1", "screenshot_id": "1",
    "cluster_id": "1", "topic": "ai", "query": "ai", "id": "1", "project_id": "1",
    "key": "theme", "task_id": "1", "reminder_id": "1", "automation_id": "1",
    "card_id": "1", "audio_id": "1", "conversation_id": "1", "screenshot": "1",
}


def build_urls(base: str, token: str) -> list[tuple[str, str]]:
    """(method, url) pairs discovered from the live OpenAPI schema."""
    spec = json.loads(http("GET", f"{base}/openapi.json")[1])
    out: list[tuple[str, str]] = []
    for path, ops in spec.get("paths", {}).items():
        if "{" in path:
            resolved = path
            for name in [p.strip("{}") for p in path.split("{")[1:]]:
                resolved = resolved.replace("{" + name + "}", SAMPLES.get(name, "1"))
            path = resolved
        for method in ops:
            if method.upper() == "GET":
                sep = "&" if "?" in path else "?"
                out.append((method.upper(), f"{base}{path}{sep}token={token}"))
    return out


def http(method: str, url: str, body: dict | None = None, token: str | None = None, timeout: float = 25):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, res.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except Exception as exc:  # connection refused, timeout, ...
        return 0, str(exc)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--user", default="Immanuel")
    ap.add_argument("--password", default="secondbrain")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    print()
    print("=" * 74)
    print("  JARVIS OS - BACKEND API SWEEP")
    print("=" * 74)

    status, raw = http("GET", f"{base}/api/health")
    if status != 200:
        print(f"{RED}  backend not reachable at {base} (status {status}){RESET}")
        print(f"  {DIM}{raw[:200]}{RESET}\n")
        return 1
    print(f"{GREEN}[ OK ]{RESET} backend healthy: {raw.strip()[:120]}")

    status, raw = http("POST", f"{base}/api/auth/login", {"username": args.user, "password": args.password})
    token = ""
    if status == 200:
        try:
            token = json.loads(raw).get("access_token", "")
        except Exception:
            token = ""
    if not token:
        print(f"{YELLOW}[WARN]{RESET} login failed (status {status}) - sweeping unauthenticated")
    else:
        print(f"{GREEN}[ OK ]{RESET} authenticated as '{args.user}'")

    urls = build_urls(base, token)
    failures: list[tuple[str, int, str]] = []
    soft: list[tuple[str, int]] = []
    ok = 0
    for method, url in urls:
        st, body = http(method, url, token=token)
        shown = url.replace(f"token={token}", "token=***") if token else url
        if st >= 500:
            failures.append((shown, st, body.strip()[:220]))
        elif st == 0:
            failures.append((shown, st, body.strip()[:220]))
        elif st in (401, 403, 404, 405, 422):
            soft.append((shown, st))
        else:
            ok += 1

    print(f"{'-' * 74}")
    print(f"  {len(urls)} GET endpoints probed:  {GREEN}{ok} ok{RESET}   "
          f"{YELLOW}{len(soft)} expected-4xx{RESET}   {RED}{len(failures)} failing{RESET}")
    for shown, st, body in failures:
        print(f"  {RED}FAIL {st}{RESET} {shown}")
        print(f"        {DIM}{body}{RESET}")
    if soft:
        by_code: dict[int, int] = {}
        for _shown, st in soft:
            by_code[st] = by_code.get(st, 0) + 1
        print(f"  {DIM}non-2xx breakdown: " + ", ".join(f"{k}x{v}" for k, v in sorted(by_code.items())) + RESET)
        if SHOW_SOFT:
            for shown, st in soft:
                print(f"  {DIM} {st}  {shown}{RESET}")
    print("=" * 74)
    if failures:
        print(f"{RED}  {len(failures)} ENDPOINT(S) CRASHING{RESET}\n")
        return 1
    print(f"{GREEN}  0 BACKEND CRASHES - every GET endpoint responded{RESET}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

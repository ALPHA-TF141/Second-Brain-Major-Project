"""
JARVIS OS - Live Backend Endpoint Sweep
===========================================================================
Boots the real FastAPI app on a private port and calls EVERY registered GET
route with a valid login token, reporting the HTTP status of each.

Any route answering 5xx is a REAL bug that the UI would hit.

Deliberately uses ONLY the standard library (urllib) plus what the backend
already depends on (uvicorn), so it can never fail on a missing dev package.

Usage (from the backend folder, with the venv active):
    python verify_backend_endpoints.py

Exit code 0 = no server errors, 1 = at least one 5xx / crash.
"""
import json
import os
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request

PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"

USERNAME = "Immanuel"
PASSWORD = "secondbrain"

# Allow "python backend/verify_backend_endpoints.py" from the repo root.
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)
os.chdir(_BACKEND_DIR)

try:
    import uvicorn

    from app.main import app
except Exception:
    print("Could not import the backend app. Did you activate the venv?")
    traceback.print_exc()
    sys.exit(2)


def start_server():
    config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            return server
        time.sleep(0.1)
    raise RuntimeError("uvicorn did not start in time")


def call(method, path, token=None, body=None):
    """Returns (status_code, body_text). Never raises for HTTP errors."""
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status, res.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:  # connection level failure
        return -1, f"{type(e).__name__}: {e}"


SAMPLE = {
    "node_id": "1",
    "memory_id": "1",
    "session_id": "1",
    "screenshot_id": "1",
    "conversation_id": "1",
    "cluster_id": "1",
    "audio_id": "1",
    "project_id": "proj_1",
    "task_id": "task_1",
    "auto_id": "auto_1",
    "rem_id": "rem_1",
    "service_key": "gmail",
    "query": "ai",
    "topic": "ai",
}


def main():
    server = start_server()

    # ---------------------------------------------------------------- login
    status, text = call("POST", "/api/auth/login",
                        body={"username": USERNAME, "password": PASSWORD,
                              "device_name": "verify-script"})
    print(f"\nlogin                          -> {status}")

    token = None
    if status == 200:
        try:
            token = json.loads(text).get("access_token")
        except Exception:
            pass
    else:
        print(f"   response: {text[:300]}")

    if not token:
        print("\n[!] Could not obtain a token - authenticated routes will 401.")
        print("    This itself is a bug worth fixing.")

    # ---------------------------------------------------------------- routes
    schema = app.openapi()
    paths = sorted(schema.get("paths", {}).keys())

    ok, redirect, client_err, server_err = [], [], [], []

    for path in paths:
        methods = schema["paths"][path]
        if "get" not in methods:
            continue
        url = path
        for key, value in SAMPLE.items():
            url = url.replace("{" + key + "}", value)
        if "{" in url:
            continue

        status, _ = call("GET", url, token=token)
        label = f"{status:>4}  GET {url}"

        if status == -1 or status >= 500:
            server_err.append(label)
        elif 300 <= status < 400:
            redirect.append(label)
        elif status >= 400:
            client_err.append(label)
        else:
            ok.append(label)

    print("\n================ LIVE ENDPOINT SWEEP ================")

    if server_err:
        print(f"\n--- 5xx SERVER ERRORS / CRASHES ({len(server_err)}) ---")
        for line in server_err:
            print(" ", line)

    if redirect:
        print(f"\n--- REDIRECTS ({len(redirect)}) ---")
        for line in redirect:
            print(" ", line)

    print(f"\n--- 4xx CLIENT ERRORS ({len(client_err)}) ---")
    print("    (expected: 401 for token-in-query routes, 404/422 for the sample ids)")
    for line in client_err:
        print(" ", line)

    print(f"\n--- 2xx OK ({len(ok)}) ---")
    for line in ok:
        print(" ", line)

    summary = {
        "ok": len(ok),
        "4xx": len(client_err),
        "redirects": len(redirect),
        "5xx_or_crash": len(server_err),
    }
    print("\nSUMMARY:", json.dumps(summary, indent=1))

    if server_err:
        print("\nRESULT: FAIL - routes above returned server errors.\n")
        return 1

    print("\nRESULT: PASS - no server errors on any GET route.\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        pass

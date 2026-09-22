"""
JARVIS OS - Live Backend Endpoint Sweep
===========================================================================
Boots the real FastAPI app on a private port, logs in, and calls EVERY
registered GET route - reporting the HTTP status AND the elapsed time of each.

Why the timing matters:
    Some endpoints are legitimately slow the FIRST time they are called
    (the semantic engine loads a sentence-transformers model, the briefing
    endpoint calls the local LLM). A slow-but-successful request is not a
    crash, and a timeout is not a 5xx - the two must be reported separately so
    a real server error never hides behind "it's just slow".

Deliberately uses ONLY the standard library (urllib) plus what the backend
already depends on (uvicorn), so it can never fail on a missing dev package.

Usage (from the repo root or the backend folder, venv active):
    python backend/verify_backend_endpoints.py

Exit code 0 = no server errors, 1 = at least one 5xx / unresponsive route.
"""
import json
import os
import sys
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request

PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"

USERNAME = "Immanuel"
PASSWORD = "secondbrain"

# Generous: a cold embedding-model load can take a while on first ever call.
REQUEST_TIMEOUT = 180
# Anything slower than this is reported as slow even when it succeeds.
SLOW_THRESHOLD = 5.0

# First call is expected to be slow (model / LLM warm-up). Hitting these once
# before the timed sweep keeps the sweep measuring steady-state behaviour.
WARMUP_PATHS = [
    "/api/semantic/status",
    "/api/semantic/related/1",
    "/api/graph/briefing/today",
]

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
    config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(150):
        if server.started:
            return server
        time.sleep(0.1)
    raise RuntimeError("uvicorn did not start in time")


def call(method, path, token=None, body=None, timeout=REQUEST_TIMEOUT):
    """Returns (status_code, body_text, elapsed_seconds). Never raises for HTTP errors."""
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, res.read().decode("utf-8", "replace"), time.time() - started
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), time.time() - started
    except Exception as e:  # connection / timeout level failure
        return -1, f"{type(e).__name__}: {e}", time.time() - started


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
    "account_id": "gacct_probe",   # google routes: unknown id -> clean 502/400
}


def main(server):
    # ---------------------------------------------------------------- login
    status, text, _ = call("POST", "/api/auth/login",
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
        print("    That is itself a bug worth fixing.")

    # ------------------------------------------------------------ warm-up
    print("\n--- warm-up (first calls can be slow: model + LLM load) ---")
    for path in WARMUP_PATHS:
        code, _, elapsed = call("GET", path, token=token)
        print(f"  {code:>4}  {elapsed:6.1f}s  {path}")

    # ---------------------------------------------------------------- routes
    schema = app.openapi()
    paths = sorted(schema.get("paths", {}).keys())

    ok, slow, redirect, client_err, timeouts, server_err = [], [], [], [], [], []

    for path in paths:
        methods = schema["paths"][path]
        if "get" not in methods:
            continue
        url = path
        for key, value in SAMPLE.items():
            url = url.replace("{" + key + "}", value)
        if "{" in url:
            continue

        # Fill in REQUIRED QUERY parameters too. Without this, routes like
        # /api/google/gmail/messages?account_id=... just answer 422 for a
        # missing parameter and the endpoint is never actually exercised.
        required_query = [
            q["name"]
            for q in methods["get"].get("parameters", [])
            if q.get("in") == "query" and q.get("required")
        ]
        if required_query:
            parts = []
            for name in required_query:
                value = str(SAMPLE.get(name, "1"))
                parts.append(f"{name}={urllib.parse.quote(value)}")
            url = f"{url}?{'&'.join(parts)}"

        code, body, elapsed = call("GET", url, token=token)
        label = f"{code:>4}  {elapsed:6.1f}s  GET {url}"

        if code == -1:
            if "timeout" in body.lower() or "timed out" in body.lower():
                timeouts.append(f"{label}   <- {body}")
            else:
                timeouts.append(f"{label}   <- {body}")
        elif code >= 500:
            server_err.append(f"{label}   <- {body[:160]}")
        elif 300 <= code < 400:
            redirect.append(label)
        elif code >= 400:
            client_err.append(label)
        else:
            ok.append(label)
            if elapsed >= SLOW_THRESHOLD:
                slow.append(label)

    print("\n================ LIVE ENDPOINT SWEEP ================")

    if server_err:
        print(f"\n--- 5xx SERVER / GATEWAY ERRORS ({len(server_err)}) ---")
        print("    500 = our bug. 502 = an upstream service (Google/IMAP) failed.")
        print("    A missing account id should be 404, never 502.")
        for line in server_err:
            print(" ", line)

    if timeouts:
        print(f"\n--- NO RESPONSE / TIMEOUT ({len(timeouts)}) ---")
        print("    (not an HTTP error - the route never answered in time)")
        for line in timeouts:
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

    if slow:
        print(f"\n--- SLOW BUT SUCCESSFUL ({len(slow)}) >= {SLOW_THRESHOLD:.0f}s ---")
        for line in slow:
            print(" ", line)

    summary = {
        "ok": len(ok),
        "slow": len(slow),
        "4xx": len(client_err),
        "redirects": len(redirect),
        "timeout_or_no_response": len(timeouts),
        "5xx_or_crash": len(server_err),
    }
    print("\nSUMMARY:", json.dumps(summary, indent=1))

    if server_err or timeouts:
        print("\nRESULT: FAIL - see the sections above.\n")
        return 1

    print("\nRESULT: PASS - no server errors on any GET route.\n")
    return 0


def shutdown(server) -> None:
    """
    Stop what startup started, WHILE the interpreter is still healthy.

    Why this is not optional: this script runs uvicorn in a daemon thread inside
    its own process. The app's startup handler then opens a microphone stream
    (wake word -> sounddevice/PortAudio + onnxruntime) and, when
    sentence-transformers is installed, loads ~90MB of torch weights in a
    background thread. Simply returning from main() hands all of that to
    interpreter finalization, which unloads native libraries out from under
    threads still parked inside them. On Windows that ends the process with an
    access violation - AFTER the verdict has been printed.

    The symptom is thoroughly confusing, and was reported from the project
    laptop: "RESULT: PASS - no server errors on any GET route." on screen,
    followed by PowerShell reporting a non-zero exit code, so the verification
    chain stopped with "CHECK FAILED - scroll up for the [FAIL] lines" and no
    [FAIL] line anywhere to scroll up to.

    So: close the microphone first, give the ASGI app its shutdown, and only
    then let the caller exit. Nothing here may change the verdict - a failure to
    stop cleanly is reported, not turned into a test failure.
    """
    # 1. the microphone + the wake-word model session
    try:
        from app.services.wake_service import stop_wake_word

        stop_wake_word()
        print("  (wake-word listener stopped; microphone released)")
    except Exception as exc:
        print(f"  (wake word was not running: {type(exc).__name__})")

    # 2. uvicorn: stop serving and run the app's shutdown path
    try:
        server.should_exit = True
        for _ in range(50):                 # up to ~5s, then exit anyway
            if not server.started:
                break
            time.sleep(0.1)
    except Exception as exc:
        print(f"  (uvicorn shutdown: {type(exc).__name__}: {exc})")


if __name__ == "__main__":
    server = start_server()
    # Defaults to FAIL: if the sweep itself raises, the exit code must not claim
    # an all-clear just because main() never returned a verdict.
    code = 1
    try:
        code = main(server)
    except Exception:
        traceback.print_exc()
        print("\nRESULT: FAIL - the sweep itself crashed before it could judge "
              "the routes.\n")
    finally:
        print("--- shutting down the probe server ---")
        shutdown(server)
        sys.stdout.flush()
        sys.stderr.flush()
        # os._exit, deliberately: it skips interpreter finalization, which is
        # where the crash described in shutdown() lives. Output is already
        # flushed, and the verdict above is the authority on pass/fail, so
        # nothing is lost by not running atexit handlers or joining the threads
        # the app left behind.
        os._exit(code)

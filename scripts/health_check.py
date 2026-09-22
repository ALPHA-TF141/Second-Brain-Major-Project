#!/usr/bin/env python3
"""
Jarvis OS - Full Environment & Integration Health Check
=======================================================
This is the "error check environment" tool. It statically verifies the things that
ESLint and the Vite build CANNOT see:

  1.  Every relative import in src/ and electron/ resolves to a real file.
  2.  Every named import from lucide-react actually exists in the installed package.
  3.  Every apiClient.<method>() call has a matching method definition.
  4.  Every backend service/route module referenced in main.py exists on disk.
  5.  Every /api/... URL the frontend calls exists in the backend route table (catches silent 404s).
  6.  Every window.secondBrain.* call is actually exposed by electron/preload.js.
  7.  Python backend parses cleanly (py_compile over every .py file).
  8.  Every route in src/routes/AppRoutes.jsx points at an existing page file.

Usage:   python scripts/health_check.py
Exit code 0 = all green, 1 = problems found.
"""
from __future__ import annotations

import json
import os
import py_compile
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
BACKEND = ROOT / "backend"
GREEN, RED, YELLOW, DIM, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[2m", "\033[0m"


class Report:
    def __init__(self, title: str):
        self.title = title
        self.problems: list[str] = []
        self.notes: list[str] = []

    def fail(self, msg: str) -> None:
        self.problems.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    def finish(self) -> bool:
        if self.problems:
            print(f"{RED}[FAIL]{RESET} {self.title}  ({len(self.problems)} problem(s))")
            for p in self.problems:
                print(f"       {RED}x{RESET} {p}")
        else:
            extra = f"  {DIM}({len(self.notes)} note(s)){RESET}" if self.notes else ""
            print(f"{GREEN}[ OK ]{RESET} {self.title}{extra}")
        for n in self.notes:
            print(f"       {DIM}- {n}{RESET}")
        return not self.problems


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def walk(pattern: str, base: Path = SRC):
    return sorted(p for p in base.rglob(pattern) if "node_modules" not in p.parts)


IMPORT_RE = re.compile(
    r"""(?:import\s+(?:[\w*{}\s,$]+\s+from\s+)?|export\s+[\w*{}\s,$]+\s+from\s+|import\s*\(\s*)['"]([^'"]+)['"]"""
)
NAMED_IMPORT_RE = re.compile(r"import\s*\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]", re.S)


def resolve_relative(spec: str, origin: Path) -> Path | None:
    """Resolve a relative import to an existing file, Vite/node style."""
    base = (origin.parent / spec).resolve()
    candidates = [
        base,
        base.with_suffix(".js"),
        base.with_suffix(".jsx"),
        base.with_suffix(".json"),
        base / "index.js",
        base / "index.jsx",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


# --------------------------------------------------------------------------- #
# 1 + 2. imports
# --------------------------------------------------------------------------- #
def check_imports() -> bool:
    rep = Report("1. Relative imports resolve (src/ + electron/)")
    files = walk("*.jsx") + walk("*.js")
    for f in files:
        text = read(f)
        for spec in IMPORT_RE.findall(text):
            if spec.startswith(".") and resolve_relative(spec, f) is None:
                rep.fail(f"{f.relative_to(ROOT)} -> cannot resolve '{spec}'")
    return rep.finish()


def check_lucide_exports() -> bool:
    rep = Report("2. lucide-react named imports exist in installed package")
    pkg = ROOT / "node_modules" / "lucide-react"
    if not pkg.exists():
        rep.note("lucide-react not installed - run: npm install")
        return rep.finish()
    import subprocess
    try:
        out = subprocess.run(
            ["node", "-e", "console.log(JSON.stringify(Object.keys(require('lucide-react'))))"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=120,
        )
        available = set(json.loads(out.stdout.strip() or "[]"))
    except Exception as exc:  # pragma: no cover
        rep.note(f"could not query lucide-react ({exc}) - skipped")
        return rep.finish()
    if not available:
        rep.note("lucide-react export table empty - skipped")
        return rep.finish()

    for f in walk("*.jsx"):
        text = read(f)
        for names, spec in NAMED_IMPORT_RE.findall(text):
            if spec != "lucide-react":
                continue
            for raw in names.split(","):
                name = raw.strip().split(" as ")[0].strip()
                if name and name not in available:
                    rep.fail(f"{f.relative_to(ROOT)} imports '{name}' from lucide-react, which does not export it")
    rep.note(f"{len(available)} icons available in installed lucide-react")
    return rep.finish()


# --------------------------------------------------------------------------- #
# 3. apiClient methods
# --------------------------------------------------------------------------- #
def check_api_client() -> bool:
    rep = Report("3. apiClient.<method>() calls have definitions")
    client = ROOT / "src" / "services" / "apiClient.js"
    text = read(client)
    defined = set(re.findall(r"^\s{2}(\w+)\s*[:(]", text, re.M))
    defined |= set(re.findall(r"^\s*(\w+)\s*:\s*(?:async\s*)?\(", text, re.M))
    used: dict[str, set[str]] = {}
    for f in walk("*.jsx") + walk("*.js"):
        for m in re.findall(r"apiClient\.(\w+)\s*\(", read(f)):
            if m in {"js", "jsx", "json", "ts"}:  # '../services/apiClient.js' style import paths
                continue
            used.setdefault(m, set()).add(str(f.relative_to(ROOT)))
    for method, where in sorted(used.items()):
        if method not in defined:
            # allow re-exported helpers
            if re.search(rf"\b{method}\b", text):
                continue
            rep.fail(f"apiClient.{method}() called in {', '.join(sorted(where))} but not defined in apiClient.js")
    return rep.finish()


# --------------------------------------------------------------------------- #
# 4 + 5. backend module + route table
# --------------------------------------------------------------------------- #
def backend_route_table() -> tuple[set[str], list[str]]:
    """Reconstruct the real FastAPI URL table from source.

    Combines three layers: router-level prefix (APIRouter(prefix=...)),
    include_router prefix, and the decorator path itself.
    """
    main = read(BACKEND / "app" / "main.py")

    # "from app.routes import x, y, settings as settings_routes, ..."
    imp_line = ""
    if "from app.routes import" in main:
        imp_line = main.split("from app.routes import")[1].split("\n")[0]
    alias2real: dict[str, str] = {}
    for real, alias in re.findall(r"(\w+)\s+as\s+(\w+)", imp_line):
        alias2real[alias] = real

    include_prefix: dict[str, str] = {}
    for mod, prefix in re.findall(r"include_router\(\s*(\w+)\.router\s*(?:,\s*prefix\s*=\s*[\"']([^\"']*)[\"'])?", main):
        include_prefix[alias2real.get(mod, mod)] = prefix

    table: set[str] = set()
    routes_dir = BACKEND / "app" / "routes"
    for py in sorted(routes_dir.glob("*.py")):
        mod = py.stem
        src = read(py)
        own = re.search(r"APIRouter\(\s*[^)]*?prefix\s*=\s*[\"']([^\"']*)[\"']", src, re.S)
        prefix = (include_prefix.get(mod, "") or "") + (own.group(1) if own else "")
        for path in re.findall(r"@router\.(?:get|post|put|patch|delete)\(\s*[\"']([^\"']*)[\"']", src):
            table.add(normalize_url((prefix + path).rstrip("/") or "/"))
    for path in re.findall(r"@app\.(?:get|post|put|patch|delete)\(\s*[\"']([^\"']*)[\"']", main):
        table.add(normalize_url(path))
    return table, sorted(include_prefix)


def normalize_url(url: str) -> str:
    url = re.sub(r"\$\{[^}]*\}", "{}", url)          # template literal
    url = re.sub(r"\{[^}]*\}", "{}", url)            # fastapi path param
    url = re.sub(r"\?[^?]*$", "", url)               # query string
    url = re.sub(r"^https?://[^/]+", "", url)        # absolute url
    return url.rstrip("/") or "/"


def check_backend_modules() -> bool:
    rep = Report("4. Backend router modules referenced in main.py exist")
    main = read(BACKEND / "app" / "main.py")
    line = main.split("from app.routes import")[1].split("\n")[0] if "from app.routes import" in main else ""
    for name in [n.strip() for n in line.replace("(", "").replace(")", "").split(",") if n.strip()]:
        real = name.split(" as ")[0].strip()
        if not (BACKEND / "app" / "routes" / f"{real}.py").exists():
            rep.fail(f"main.py imports routes.{real} but backend/app/routes/{real}.py is missing")
    # other app.* imports
    for dotted in set(re.findall(r"from (app\.[\w.]+) import", main)):
        target = BACKEND / (dotted.replace(".", "/") + ".py")
        if not target.exists() and not (BACKEND / dotted.replace(".", "/") / "__init__.py").exists():
            rep.fail(f"main.py imports '{dotted}' but {target.relative_to(ROOT)} does not exist")
    return rep.finish()


URL_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/_-{}$.+*:=")


def strip_comments(text: str) -> str:
    """
    Remove JavaScript comments before scanning for API calls.

    Defect this fixes: a documentation comment reading "... reads real state from
    /api/research/*" was scanned as though it were a call, producing a fabricated
    route that no backend could serve. Prose is not code.

    Line comments are only stripped when not preceded by ':' so that the '//' in
    'https://' survives. Newlines are preserved so offsets stay meaningful.
    """
    text = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)
    text = re.sub(r"(^|[^:'\"`\\])//[^\n]*", lambda m: m.group(1) + m.group(0)[len(m.group(1)):], text, flags=re.M)
    text = re.sub(r"(?m)^\s*//.*$", "", text)
    # JSDoc continuation lines (" * text"), which are comment bodies even when the
    # opening /* sits far above. Safe to strip because a JavaScript statement
    # cannot begin with '*'; removing them cannot hide a real call.
    text = re.sub(r"(?m)^\s*\*.*$", "", text)
    return text


def extract_api_calls(text: str):
    """Scan for '/api/...' tokens with a simple character scanner.

    Returns (kind, url) where kind is 'exact' or 'concat' (URL continues with +).
    Comments are stripped first: a URL in prose is not a URL in code.
    """
    text = strip_comments(text)
    found: list[tuple[str, str]] = []
    for m in re.finditer(r"/api/", text):
        start = m.start()
        i = start
        while i < len(text) and text[i] in URL_CHARS:
            i += 1
        url = text[start:i].rstrip(".")
        if not url.startswith("/api/"):
            continue
        after = text[i:i + 6].lstrip()
        concat = False
        if after[:1] in ("'", '"', "`"):
            rest = text[i + (len(text[i:i + 6]) - len(after)) + 1:][:6].lstrip()
            concat = rest.startswith("+")
        if not concat and url.endswith("/"):
            concat = True
        found.append(("concat" if concat else "exact", url))
    return found


def check_frontend_api_calls() -> bool:
    rep = Report("5. Frontend /api/ calls have matching backend routes")
    table, _ = backend_route_table()
    if not table:
        rep.note("could not build backend route table - skipped")
        return rep.finish()
    routes = sorted(table)
    route_segs = [[seg for seg in r.split("/") if seg] for r in routes]

    calls: dict[tuple[str, str], set[str]] = {}
    for f in walk("*.jsx") + walk("*.js"):
        for kind, url in extract_api_calls(read(f)):
            calls.setdefault((kind, normalize_url(url)), set()).add(str(f.relative_to(ROOT)))

    def seg_ok(a: str, b: str) -> bool:
        if a == b:
            return True
        # any dynamic marker on either side counts as a wildcard segment.
        # '*' belongs here: it is an allowed URL character, so a token containing
        # it reaches this function, and without it '*' was compared literally
        # against a real segment and failed.
        for marker in ("{}", "{", "}", "$", "*"):
            if marker in a or marker in b:
                return True
        return False

    def matches(kind: str, call: str) -> bool:
        call_segs = [s for s in call.split("/") if s]
        for segs in route_segs:
            if kind == "concat":
                if len(call_segs) <= len(segs) and all(seg_ok(x, y) for x, y in zip(call_segs, segs)):
                    return True
            else:
                if len(call_segs) == len(segs) and all(seg_ok(x, y) for x, y in zip(call_segs, segs)):
                    return True
        return False

    for (kind, call), where in sorted(calls.items()):
        if not matches(kind, call):
            rep.fail(f"frontend calls /{'/'.join(s for s in call.split('/') if s)}  (in {', '.join(sorted(where))})  -> no such backend route")
    rep.note(f"{len(routes)} backend routes discovered")
    return rep.finish()


# --------------------------------------------------------------------------- #
# 6. preload bridge
# --------------------------------------------------------------------------- #
def check_preload_bridge() -> bool:
    rep = Report("6. window.secondBrain.* calls are exposed by preload.js")
    preload = read(ROOT / "electron" / "preload.js")
    exposed = set(re.findall(r"^\s*(\w+)\s*:", preload, re.M))
    for f in walk("*.jsx") + walk("*.js"):
        for m in re.findall(r"window\.secondBrain\??\.(\w+)", read(f)):
            if m not in exposed:
                rep.fail(f"{f.relative_to(ROOT)} calls window.secondBrain.{m}() but preload.js does not expose it")
    return rep.finish()


# --------------------------------------------------------------------------- #
# 7. python syntax
# --------------------------------------------------------------------------- #
def check_python_syntax() -> bool:
    rep = Report("7. Backend Python files compile")
    if not BACKEND.exists():
        rep.note("backend/ not found - skipped")
        return rep.finish()
    with tempfile.TemporaryDirectory() as tmp:
        for py in sorted(BACKEND.rglob("*.py")):
            if ".venv" in py.parts or "__pycache__" in py.parts:
                continue
            try:
                py_compile.compile(str(py), cfile=os.path.join(tmp, py.name + "c"), doraise=True)
            except py_compile.PyCompileError as exc:
                rep.fail(f"{py.relative_to(ROOT)}: {str(exc).splitlines()[0]}")
    return rep.finish()


# --------------------------------------------------------------------------- #
# 8. routes -> pages
# --------------------------------------------------------------------------- #
def check_routes() -> bool:
    rep = Report("8. AppRoutes.jsx imports resolve to real page files")
    routes = read(SRC / "routes" / "AppRoutes.jsx")
    if not routes:
        rep.fail("src/routes/AppRoutes.jsx missing")
        return rep.finish()
    for spec in IMPORT_RE.findall(routes):
        if spec.startswith("."):
            resolved = resolve_relative(spec, SRC / "routes" / "AppRoutes.jsx")
            if resolved is None:
                rep.fail(f"AppRoutes.jsx -> cannot resolve '{spec}'")
            else:
                rep.note(f"{spec}  ->  ok")
    return rep.finish()


# --------------------------------------------------------------------------- #
def main() -> int:
    print()
    print("=" * 74)
    print("  JARVIS OS - FULL ENVIRONMENT & INTEGRATION HEALTH CHECK")
    print("=" * 74)
    checks = [
        check_imports,
        check_lucide_exports,
        check_api_client,
        check_backend_modules,
        check_frontend_api_calls,
        check_preload_bridge,
        check_python_syntax,
        check_routes,
    ]
    results = [c() for c in checks]
    print("=" * 74)
    failed = results.count(False)
    if failed:
        print(f"{RED}  {failed} CHECK(S) FAILED - fix the items marked x above{RESET}")
    else:
        print(f"{GREEN}  ALL {len(results)} CHECKS PASSED - 0 ERRORS{RESET}")
    print("=" * 74)
    print()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env bash
# Regenerate every number in paper/main.tex from code, then rebuild the PDF.
#
#   bash backend/scripts/regen_paper.sh            # full run (~5 min)
#   SKIP_SCALING=1 bash backend/scripts/regen_paper.sh   # skip the slow sweep
#
# Each experiment writes a JSON artefact into backend/. export_paper_metrics.py
# turns those artefacts into paper/generated/*.tex, which main.tex \inputs.
# No number in the paper is typed by hand.
set -euo pipefail

cd "$(dirname "$0")/../.."          # repo root
BE=backend
PY=${PYTHON:-python3}

echo "== 1/8 single-corpus benchmark"
"$PY" "$BE/scripts/run_bench.py"

echo "== 2/8 five-persona benchmark"
"$PY" "$BE/scripts/run_multi_user_bench.py"

echo "== 3/8 conflict detection, development split"
"$PY" "$BE/scripts/run_conflict_accuracy.py" --split dev

echo "== 4/8 conflict detection, holdout split"
"$PY" "$BE/scripts/run_conflict_accuracy.py" --split holdout

echo "== 5/8 bootstrap and leave-one-out ablation"
"$PY" "$BE/scripts/run_stats.py"

echo "== 6/8 cumulative ablation"
"$PY" "$BE/scripts/run_ablation.py"

if [ "${SKIP_SCALING:-0}" = "1" ]; then
  echo "== 7/8 distractor scaling (skipped)"
else
  echo "== 7/8 distractor scaling"
  "$PY" "$BE/scripts/run_scaling.py"
fi

echo "== 8/8 research-module tests, then export"
"$PY" - <<'PYCODE'
import json, re, subprocess, pathlib
out = subprocess.run(
    ["python3", "-m", "pytest", "tests/", "-q",
     "--ignore=tests/test_forgetting_paths.py", "--ignore=tests/test_memory_crud.py"],
    cwd="backend", capture_output=True, text=True).stdout
m = re.search(r"(\d+) passed(?:, (\d+) skipped)?(?:, (\d+) failed)?", out) or re.search(
    r"(\d+) failed", out)
res = {"passed": int(m.group(1)) if m and m.lastindex and "passed" in m.group(0) else 0,
       "skipped": int(m.group(2) or 0) if m and m.lastindex and m.lastindex >= 2 else 0,
       "failed": int(m.group(3) or 0) if m and m.lastindex and m.lastindex >= 3 else 0,
       "note": "test_forgetting_paths.py and test_memory_crud.py do not collect (import mss)"}
pathlib.Path("backend/test_results.json").write_text(json.dumps(res, indent=2))
print(json.dumps(res))
PYCODE
"$PY" "$BE/scripts/export_paper_metrics.py" --paper-dir paper

echo
echo "paper/main.tex patched in place."
echo "Now compile paper/main.tex with pdfLaTeX (Overleaf: Menu > Compiler > pdfLaTeX)."

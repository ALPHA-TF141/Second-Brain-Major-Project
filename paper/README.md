# Paper build

`main.tex` is the whole manuscript: one self-contained file, no `\input`, so it
compiles in Overleaf as-is. It is also the file the code writes to.

Every measurement in it is generated from the JSON artefacts in `backend/` by
`backend/scripts/export_paper_metrics.py`, which patches `main.tex` in place:

| Region of `main.tex` | Rewritten from |
| --- | --- |
| `% ==== BEGIN GENERATED METRICS ====` … `% ==== END GENERATED METRICS ====` | all artefacts → one `\newcommand` per value |
| `% ==== BEGIN TABLE tab:core ==== ` … `% ==== END TABLE tab:core ====` | `benchmark_results.json` (Table II) |
| `% ==== BEGIN TABLE tab:category ====` … | `benchmark_results.json` (Table III) |
| `% ==== BEGIN TABLE tab:multi ====` … | `benchmark_multi_user_results.json` (Table IV) |
| `% ==== BEGIN TABLE tab:bootstrap ====` … | `stats_results.json` (Table V) |
| `% ==== BEGIN TABLE tab:scaling ====` … | `scaling_results.json` (Table VI) |
| `% ==== BEGIN TABLE tab:cumulative ====` … | `ablation_results.json` (Table VII) |
| `% ==== BEGIN TABLE tab:loo ====` … | `stats_results.json` (Table VIII) |

Table cells are written as literal digits. Running text quotes the same values
through the macros in the top block (`\CoreAdaptiveMrr`, `\NliHoldFone`, …), so
a value is defined once and cannot drift from the table.

## Regenerate everything

```bash
bash backend/scripts/regen_paper.sh                  # ~5 minutes
SKIP_SCALING=1 bash backend/scripts/regen_paper.sh   # skip the slow sweep
```

That runs the six experiments, records the test tally, and patches `main.tex`
in place. Then compile with **pdfLaTeX** (Overleaf: *Menu → Compiler →
pdfLaTeX*); XeLaTeX also works if Times New Roman or the four `times*.ttf`
files are present.

## Rules for editing

- Prose, figures, bibliography, captions outside the markers: edit `main.tex`
  freely, the generator never touches them.
- Never edit inside a marker pair by hand — the next run replaces it.
- Add a new table by adding a marker pair and one entry to `TABLES` in
  `backend/scripts/export_paper_metrics.py`.

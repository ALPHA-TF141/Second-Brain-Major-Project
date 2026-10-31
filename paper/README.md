# Paper build

`main.tex` is the manuscript. Every number it reports — table cells, confidence
intervals, NLI counts, latency, test counts — is generated from the JSON
artefacts in `backend/` by `backend/scripts/export_paper_metrics.py`. Nothing is
typed by hand, so a code change cannot silently disagree with the paper.

## Regenerate everything

```bash
bash backend/scripts/regen_paper.sh          # ~5 minutes
SKIP_SCALING=1 bash backend/scripts/regen_paper.sh   # skip the slow sweep
```

That runs the six experiments, records the test tally, and rewrites
`paper/generated/`:

| Generated file | Produced from | Used for |
| --- | --- | --- |
| `metrics.tex` | all artefacts | every inline number in the running text |
| `nli_numbers.tex` | `conflict_accuracy{,_holdout}.json` | conflict-detection paragraph |
| `tab_core.tex` | `benchmark_results.json` | Table II |
| `tab_category.tex` | `benchmark_results.json` | Table III |
| `tab_personas.tex` | `benchmark_multi_user_results.json` | Table IV |
| `tab_bootstrap.tex` | `stats_results.json` | Table V |
| `tab_scaling.tex` | `scaling_results.json` | Table VI |
| `tab_cumulative.tex` | `ablation_results.json` | Table VII |
| `tab_loo.tex` | `stats_results.json` | Table VIII |

## Compile

Compile `main.tex` with **pdfLaTeX** (Overleaf: *Menu → Compiler → pdfLaTeX*).
XeLaTeX also works if Times New Roman or the four `times*.ttf` files are present.

Each generated file is a complete `table` float, not a row body: `\input`
inside a `tabular` ends the alignment context and the next `\bottomrule`
fails with "Misplaced \noalign".

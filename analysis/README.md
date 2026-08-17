# Analysis workflow

Keep notebooks and scripts that produce research results in this directory.
Reusable or testable logic belongs in `template_python/`; analysis files
should orchestrate that logic and make the provenance of outputs clear.

Suggested naming follows execution order:

```text
analysis/
├── 01_prepare_data.py
├── 02_fit_model.py
└── 03_make_figures.py
```

For the real project, replace this section with the exact commands needed to
regenerate every table, figure, and reported result. Each analysis should:

- declare its inputs and outputs;
- avoid modifying files under `data/raw/`;
- use deterministic seeds where randomness is involved;
- write generated artefacts to a documented output directory; and
- run from the repository root in a freshly created environment.

Prefer scripts for the final reproducible pipeline. Notebooks are useful for
exploration, but clear their incidental output and document their execution
order before publication.

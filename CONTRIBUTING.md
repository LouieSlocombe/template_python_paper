# Contributing

Thank you for improving the project. Keep changes focused, tested, typed, and
documented so another researcher can reproduce the result from a clean clone.

## Set up a development environment

With `uv`:

```bash
uv sync --group analysis
uv run prek install
```

With standard Python tooling (`pip` 25.1 or newer):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --editable . --group dev --group analysis
prek install
```

The hooks run Ruff, strip notebook outputs, block large files and private
keys, keep `uv.lock` in sync with `pyproject.toml`, and audit the CI workflow.
`pre-commit` reads the same `.pre-commit-config.yaml` if you prefer it.

## Make a change

1. Add or update a test that describes the intended behaviour.
2. Put reusable logic under `src/template_python/`, not in a notebook.
3. Change dependencies with `uv add` or `uv remove` (or edit `pyproject.toml`
   and run `uv lock`), and commit the updated `uv.lock`.
4. Update user-facing documentation and provenance notes where relevant.
5. Run the full local check suite:

   ```bash
   uv run prek run --all-files
   uv run mypy
   uv run pytest --cov
   uv build
   ```

Do not commit generated distributions, local environments, credentials, large
datasets, or sensitive material. If a change affects reported results, describe
which analyses and outputs must be regenerated.

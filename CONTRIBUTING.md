# Contributing

Thank you for improving the project. Keep changes focused, tested, typed, and
documented so another researcher can reproduce the result from a clean clone.

## Set up a development environment

With `uv`:

```bash
uv sync --group analysis
uv run pre-commit install
```

With standard Python tooling:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --editable .
python -m pip install --group dev --group analysis
pre-commit install
```

## Make a change

1. Add or update a test that describes the intended behaviour.
2. Put reusable logic under `template_python/`, not in a notebook.
3. Update user-facing documentation and provenance notes where relevant.
4. Run the full local check suite:

   ```bash
   ruff check .
   ruff format --check .
   mypy template_python tests
   python -m pytest --cov
   python -m build
   python -m twine check --strict dist/*
   ```

Do not commit generated distributions, local environments, credentials, large
datasets, or sensitive material. If a change affects reported results, describe
which analyses and outputs must be regenerated.

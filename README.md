# Modern Python research template

[![CI](https://github.com/LouieSlocombe/template_python_paper/actions/workflows/ci.yml/badge.svg)](https://github.com/LouieSlocombe/template_python_paper/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-2ea44f.svg)](LICENSE)

An opinionated starting point for reproducible research, data analysis, and the
Python code that supports a paper. It keeps package code, analyses, research
data, test fixtures, and build tooling clearly separated while providing a
useful quality baseline out of the box.

> [!IMPORTANT]
> This repository is a template. Complete the [customisation checklist](#customise-the-template)
> before starting a real project.

## What is included

- packaging configured entirely in `pyproject.toml`, built with the fast
  [`uv_build`](https://docs.astral.sh/uv/concepts/build-backend/) backend;
- a `src/` layout, so tests always run against the installed package rather
  than whatever happens to be on the working directory's import path;
- a committed, cross-platform `uv.lock` that pins the exact environment behind
  every result;
- separate core, analysis, and development dependency groups;
- formatting and an extensive lint rule set with Ruff, strict type checking with
  mypy, and pytest with branch-coverage checks;
- Git hooks (run with [`prek`](https://prek.j178.dev/) or `pre-commit`) that
  strip notebook outputs, block large files and private keys, keep the lockfile
  in sync, and audit the CI workflow for security problems;
- continuous integration on Python 3.12–3.14 across Linux, macOS, and Windows,
  plus an early-warning job for the next Python release;
- hardened GitHub Actions (SHA-pinned, least-privilege tokens) and grouped
  weekly Dependabot updates with a cooldown period;
- guidance for reproducible analyses and responsible data handling;
- citation metadata that GitHub and research archives can discover;
- both `uv` and standard `venv`/`pip` setup paths, plus an optional Conda
  environment.

## Quick start

### With `uv` (recommended)

[`uv`](https://docs.astral.sh/uv/) installs the right Python version, creates
the environment, and installs the project and development tools exactly as
recorded in `uv.lock`.

```bash
uv sync --group analysis
uv run pytest --cov
uv run template-python --name Researcher --points 5
```

After changing dependencies in `pyproject.toml`, run `uv lock` (or use
`uv add` and `uv remove`, which do it for you) and commit the updated
`uv.lock`. This gives collaborators and CI the exact same resolution.

### With `venv` and `pip`

`pip` 25.1 or newer is required for the standard development dependency group.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --editable . --group dev --group analysis
python -m pytest --cov
```

This path resolves the newest versions allowed by `pyproject.toml` rather than
the exact versions in `uv.lock`.

On Windows PowerShell, activate the environment with
`.venv\Scripts\Activate.ps1`. Conda users can follow the
[environment guide](build_tools/README.md).

## Use the example package

The included API is intentionally small, so it is easy to replace without
first untangling a demo application.

```python
from template_python import greeting, line

print(greeting("Ada"))
values = line(5)
print(values)
```

```text
Hello, Ada!
[0.   0.25 0.5  0.75 1.  ]
```

The same example is exposed as a command:

```bash
template-python --name Ada --points 5
# or: python -m template_python --name Ada --points 5
```

## Project layout

```text
.
├── .github/workflows/ci.yml   # automated quality, test, and package checks
├── .pre-commit-config.yaml    # Git hooks for prek or pre-commit
├── analysis/                  # notebooks and reproducible analysis scripts
├── build_tools/               # alternative environment definitions
├── data/                      # research data and provenance notes
├── reference/                 # condensed reference papers for context
├── src/template_python/       # installable, typed Python package
├── tests/                     # unit tests and small committed fixtures
├── CITATION.cff               # machine-readable citation metadata
├── CONTRIBUTING.md            # local development workflow
├── pyproject.toml             # metadata, dependencies, and tool configuration
└── uv.lock                    # exact, cross-platform dependency resolution
```

## Development workflow

Run the same checks locally that CI runs:

```bash
uv run prek run --all-files
uv run mypy
uv run pytest --cov
uv build
```

The first command runs every Git hook, including Ruff's linter and formatter,
and applies safe fixes automatically. Install the hooks once with
`uv run prek install` so they run on every commit. `pre-commit` reads the same
configuration if you prefer it. See [CONTRIBUTING.md](CONTRIBUTING.md) for the
full workflow.

## Reproducible research conventions

- Keep reusable logic in `src/template_python/`; analyses should call that
  logic rather than duplicate it in notebooks.
- Number scripts or notebooks in execution order and document the command that
  regenerates every table and figure in `analysis/README.md`.
- Treat raw data as immutable. Record its source, retrieval date, licence, and
  checksum in `data/README.md`.
- Keep only small, non-sensitive fixtures under `tests/data/`.
- Fix random seeds where randomness is intentional. Commit `uv.lock` and tag
  the commit that produced published outputs, so the exact package and
  interpreter versions can be recovered.
- Do not commit credentials, confidential data, virtual environments, or
  generated build artefacts.

## Customise the template

1. Rename the distribution (`template-python`) and import package
   (`src/template_python`) throughout the repository, then run `uv lock`.
2. Replace the description, author, URLs, and classifiers in `pyproject.toml`
   and the metadata in `CITATION.cff`.
3. Replace the example API, CLI, and tests with the project's first real unit
   of behaviour.
4. Review the Python support range and the core, analysis, and development
   dependency groups.
5. Document the real data provenance and analysis execution order.
6. Update this README and remove this checklist.

## Licence

This template is available under the [MIT Licence](LICENSE). Replace it if the
new project's licensing requirements differ.

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

- modern packaging configured entirely in `pyproject.toml`;
- a straightforward `template_python/` package layout;
- separate core, analysis, and development dependencies;
- formatting and linting with Ruff, strict type checking with mypy, and pytest
  coverage checks;
- a Python 3.12–3.14 continuous-integration matrix;
- guidance for reproducible analyses and responsible data handling;
- citation metadata that GitHub and research archives can discover;
- both `uv` and standard `venv`/`pip` setup paths, plus an optional Conda
  environment.

## Quick start

### With `uv` (recommended)

[`uv`](https://docs.astral.sh/uv/) creates the environment, installs the
project and development tools, and maintains a cross-platform lockfile.

```bash
uv sync --group analysis
uv run python -m pytest --cov
uv run template-python --name Researcher --points 5
```

Commit the generated `uv.lock` once the real project's dependencies have been
chosen. This gives collaborators and CI an exact dependency resolution.

### With `venv` and `pip`

`pip` 25.1 or newer is required for the standard development dependency group.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --editable .
python -m pip install --group dev --group analysis
python -m pytest --cov
```

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
├── analysis/                  # notebooks and reproducible analysis scripts
├── build_tools/               # alternative environment definitions
├── data/                      # research data and provenance notes
├── template_python/           # installable, typed Python package
├── tests/                     # unit tests and small committed fixtures
├── CITATION.cff               # machine-readable citation metadata
├── CONTRIBUTING.md            # local development workflow
└── pyproject.toml             # metadata, dependencies, and tool configuration
```

## Development workflow

Run the same checks locally that CI runs:

```bash
ruff check .
ruff format --check .
mypy template_python tests
python -m pytest --cov
python -m build
python -m twine check dist/*
```

To apply safe formatting and lint fixes:

```bash
ruff check --fix .
ruff format .
```

Install the optional Git hooks with `pre-commit install`. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## Reproducible research conventions

- Keep reusable logic in `template_python/`; analyses should call that
  logic rather than duplicate it in notebooks.
- Number scripts or notebooks in execution order and document the command that
  regenerates every table and figure in `analysis/README.md`.
- Treat raw data as immutable. Record its source, retrieval date, licence, and
  checksum in `data/README.md`.
- Keep only small, non-sensitive fixtures under `tests/data/`.
- Fix random seeds where randomness is intentional, and record package and
  interpreter versions alongside published outputs.
- Do not commit credentials, confidential data, virtual environments, or
  generated build artefacts.

## Customise the template

1. Rename the distribution (`template-python`) and import package
   (`template_python`) throughout the repository.
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

# Conda environment

The root README's `uv` or `venv` workflow is the simplest setup. Use this Conda
definition when system-level scientific packages or an existing Conda workflow
make it preferable.

Run every command from the repository root:

```bash
conda env create --file build_tools/environment.yml
conda activate template-python-paper
python -m pip install --upgrade pip
python -m pip install --editable .
python -m pip install --group dev --group analysis
python -m pytest --cov
```

The environment file intentionally contains only Python and `pip`. Package,
analysis, and development dependencies remain in `pyproject.toml`, which keeps
one authoritative dependency list for all setup methods.

To update an existing environment:

```bash
conda env update --file build_tools/environment.yml --prune
```

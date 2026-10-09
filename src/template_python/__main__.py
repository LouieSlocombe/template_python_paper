"""Allow the package to be run with ``python -m template_python``."""

from template_python.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

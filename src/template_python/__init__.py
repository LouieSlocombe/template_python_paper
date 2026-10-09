"""Public API for :mod:`template_python`."""

from importlib.metadata import PackageNotFoundError, version

from template_python.main import greeting, line, print_hello

try:
    __version__ = version("template-python")
except PackageNotFoundError:  # pragma: no cover - only used from an unpackaged tree
    __version__ = "0+unknown"

__all__ = ["__version__", "greeting", "line", "print_hello"]

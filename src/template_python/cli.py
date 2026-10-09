"""Command-line interface for the example package."""

import argparse
from collections.abc import Sequence

from template_python import __version__, greeting, line


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Run the template project's small example workflow."
    )
    parser.add_argument(
        "--name",
        default="World",
        help="name to use in the greeting (default: %(default)s)",
    )
    parser.add_argument(
        "--points",
        type=int,
        default=5,
        help="number of points in the unit interval (default: %(default)s)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return a process exit code."""
    args = build_parser().parse_args(argv)
    values = line(args.points)

    print(greeting(args.name))
    print(f"Unit interval: {values.tolist()}")
    return 0

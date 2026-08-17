"""Tests for the command-line interface."""

import runpy
import sys

import pytest

from template_python.cli import main


def test_cli_runs_the_example_workflow(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["--name", "Ada", "--points", "3"])

    assert exit_code == 0
    assert capsys.readouterr().out.splitlines() == [
        "Hello, Ada!",
        "Unit interval: [0.0, 0.5, 1.0]",
    ]


def test_package_module_runs_the_cli(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["template_python", "--points", "2"])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("template_python", run_name="__main__")

    assert exit_info.value.code == 0
    assert "Unit interval: [0.0, 1.0]" in capsys.readouterr().out

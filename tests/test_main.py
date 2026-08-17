"""Tests for the public example API."""

import numpy as np
import pytest

from template_python import greeting, line, print_hello


def test_greeting_uses_the_supplied_name() -> None:
    assert greeting("Ada") == "Hello, Ada!"


def test_print_hello_writes_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    print_hello("Grace")

    assert capsys.readouterr().out == "Hello, Grace!\n"


def test_line_spans_the_unit_interval() -> None:
    result = line(5)

    np.testing.assert_allclose(result, [0.0, 0.25, 0.5, 0.75, 1.0])
    assert result.dtype == np.dtype(np.float64)


@pytest.mark.parametrize("num_points", [1, 0, -1])
def test_line_rejects_too_few_points(num_points: int) -> None:
    with pytest.raises(ValueError, match="at least 2"):
        line(num_points)

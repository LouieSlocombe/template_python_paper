"""Small, typed example functions to replace with project-specific logic."""

import numpy as np
from numpy.typing import NDArray


def greeting(name: str = "World") -> str:
    """Return a friendly greeting.

    Args:
        name: Name to include in the greeting.

    Returns:
        A greeting ending in an exclamation mark.
    """
    return f"Hello, {name}!"


def print_hello(name: str = "World") -> None:
    """Print :func:`greeting` for ``name``."""
    print(greeting(name))


def line(num_points: int = 100) -> NDArray[np.float64]:
    """Return evenly spaced values over the closed interval ``[0, 1]``.

    Args:
        num_points: Number of samples to generate. Must be at least two.

    Raises:
        ValueError: If fewer than two points are requested.

    Returns:
        A one-dimensional, double-precision NumPy array.
    """
    if num_points < 2:
        message = "num_points must be at least 2"
        raise ValueError(message)

    return np.linspace(0.0, 1.0, num=num_points, dtype=np.float64)

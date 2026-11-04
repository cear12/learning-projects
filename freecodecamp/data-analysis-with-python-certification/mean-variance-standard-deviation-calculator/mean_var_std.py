"""Calculate column, row and overall statistics for nine numbers."""

import numpy as np


def calculate(values):
    """Return six statistics in [columns, rows, overall] order.

    Variance and standard deviation use the population definition (ddof=0).
    All returned values are native Python lists and numbers.
    """
    if len(values) != 9:
        raise ValueError("List must contain nine numbers.")

    matrix = np.array(values).reshape(3, 3)
    operations = {
        "mean": np.mean,
        "variance": np.var,
        "standard deviation": np.std,
        "max": np.max,
        "min": np.min,
        "sum": np.sum,
    }
    return {
        name: [operation(matrix, axis=0).tolist(),
               operation(matrix, axis=1).tolist(),
               operation(matrix).tolist()]
        for name, operation in operations.items()
    }

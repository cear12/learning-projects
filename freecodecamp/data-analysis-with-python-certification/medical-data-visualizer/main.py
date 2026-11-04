"""Render both figures, then run the original and additional checks."""

from pathlib import Path
import os
import unittest

PROJECT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / ".cache" / "matplotlib"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import medical_data_visualizer


def main():
    for draw in (medical_data_visualizer.draw_cat_plot, medical_data_visualizer.draw_heat_map):
        plt.close(draw())
    suite = unittest.defaultTestLoader.discover(str(PROJECT), pattern="test*.py")
    try:
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    finally:
        plt.close("all")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Render the three figures and run the complete project test suite."""

from pathlib import Path
import os
import unittest

PROJECT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / ".cache" / "matplotlib"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import time_series_visualizer


def main():
    # Keep the template's relative PNG filenames inside the project directory.
    os.chdir(PROJECT)
    for draw in (time_series_visualizer.draw_line_plot, time_series_visualizer.draw_bar_plot,
                 time_series_visualizer.draw_box_plot):
        plt.close(draw())
    suite = unittest.defaultTestLoader.discover(str(PROJECT), pattern="test*.py")
    try:
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    finally:
        plt.close("all")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

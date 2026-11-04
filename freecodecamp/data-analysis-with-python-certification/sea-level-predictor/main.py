"""Render the sea-level plot and run the complete project tests."""

from pathlib import Path
import os
import unittest

PROJECT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / ".cache" / "matplotlib"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import sea_level_predictor


def main():
    os.chdir(PROJECT)
    ax = sea_level_predictor.draw_plot()
    for line in ax.get_lines():
        print(f"2050 projection ({line.get_label()}): {line.get_ydata()[-1]:.2f} inches")
    plt.close(ax.figure)
    suite = unittest.defaultTestLoader.discover(str(PROJECT), pattern="test*.py")
    try:
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    finally:
        plt.close("all")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

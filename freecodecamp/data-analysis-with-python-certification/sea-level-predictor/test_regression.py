"""Check regression windows, projection years and independent figure creation."""

import os
from pathlib import Path
import unittest

PROJECT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / ".cache" / "matplotlib"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import sea_level_predictor as predictor


class RegressionTests(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def test_fits_use_the_correct_column_and_include_the_year_2000(self):
        frame = pd.DataFrame({"Year": [1999, 2000, 2001, 2002],
                              "CSIRO Adjusted Sea Level": [100, 10, 12, 18],
                              "NOAA Adjusted Sea Level": [np.nan] * 4})
        original = frame.copy(deep=True)
        full_fit, recent_fit = predictor.fit_trends(frame)
        # Least-squares slopes calculated directly for these four and three points.
        self.assertAlmostEqual(full_fit.slope, -24.4)
        self.assertAlmostEqual(recent_fit.slope, 4.0)
        self.assertAlmostEqual(recent_fit.intercept, (10 + 12 + 18) / 3 - 4 * 2001)
        pd.testing.assert_frame_equal(frame, original)

    def test_both_lines_reach_2050_and_start_at_the_correct_year(self):
        ax = predictor.draw_plot()
        full_line, recent_line = ax.get_lines()
        np.testing.assert_array_equal(full_line.get_xdata(), np.arange(1880, 2051))
        np.testing.assert_array_equal(recent_line.get_xdata(), np.arange(2000, 2051))

    def test_repeated_calls_create_separate_figures_without_accumulating_artists(self):
        first = predictor.draw_plot()
        second = predictor.draw_plot()
        self.assertIsNot(first.figure, second.figure)
        self.assertEqual(len(first.collections), 1)
        self.assertEqual(len(second.collections), 1)
        self.assertEqual(len(first.lines), 2)
        self.assertEqual(len(second.lines), 2)
        self.assertEqual(len(second.collections[0].get_offsets()), 134)


if __name__ == "__main__":
    unittest.main()

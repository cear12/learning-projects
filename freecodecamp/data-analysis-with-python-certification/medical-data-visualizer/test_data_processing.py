"""Verify preprocessing and filters with small, independently checked data."""

import os
from pathlib import Path
import unittest

PROJECT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / ".cache" / "matplotlib"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd

import medical_data_visualizer as visualizer


class DataProcessingTests(unittest.TestCase):
    def test_bmi_threshold_is_strictly_greater_than_25(self):
        frame = pd.DataFrame({"height": [200, 200, 200], "weight": [99, 100, 101],
                              "cholesterol": [1, 2, 3], "gluc": [3, 2, 1]})
        original = frame.copy(deep=True)
        actual = visualizer.prepare_data(frame)
        self.assertEqual(actual["overweight"].tolist(), [0, 0, 1])
        self.assertEqual(actual["cholesterol"].tolist(), [0, 1, 1])
        self.assertEqual(actual["gluc"].tolist(), [1, 1, 0])
        pd.testing.assert_frame_equal(frame, original)

    def test_category_counts_match_rows_in_each_panel(self):
        frame = pd.DataFrame({"cardio": [0, 0, 1], "active": [1, 1, 0], "alco": [0, 1, 0],
                              "cholesterol": [0, 1, 1], "gluc": [0, 0, 1],
                              "overweight": [1, 0, 1], "smoke": [0, 0, 1]})
        counts = visualizer.category_counts(frame)
        totals = counts.groupby(["cardio", "variable"])["total"].sum()
        for variable in visualizer.VARIABLES:
            self.assertEqual(totals.loc[(0, variable)], 2)
            self.assertEqual(totals.loc[(1, variable)], 1)
        indexed = counts.set_index(["cardio", "variable", "value"])["total"]
        self.assertEqual(indexed.loc[(0, "active", 1)], 2)
        self.assertEqual(indexed.loc[(1, "cholesterol", 1)], 1)
        self.assertEqual(int(counts["total"].sum()), 18)

    def test_quantile_bounds_are_inclusive_and_use_the_original_frame(self):
        # For 41 rows, 2.5% and 97.5% quantiles lie exactly at rows 1 and 39.
        frame = pd.DataFrame({"height": np.arange(100, 141), "weight": np.arange(50, 91),
                              "ap_hi": [120] * 41, "ap_lo": [80] * 41})
        frame.loc[0, "ap_lo"] = 150
        original = frame.copy(deep=True)
        cleaned = visualizer.clean_heatmap_data(frame)
        self.assertEqual(cleaned.index.tolist(), list(range(1, 40)))
        pd.testing.assert_frame_equal(frame, original)

    def test_blood_pressure_filter_allows_equal_values(self):
        frame = pd.DataFrame({"height": [170] * 3, "weight": [70] * 3,
                              "ap_hi": [120, 80, 100], "ap_lo": [80, 80, 110]})
        self.assertEqual(visualizer.clean_heatmap_data(frame).index.tolist(), [0, 1])

    def test_weight_and_height_tails_are_filtered_independently(self):
        frame = pd.DataFrame({"height": [170] * 41, "weight": np.arange(50, 91),
                              "ap_hi": [120] * 41, "ap_lo": [80] * 41})
        self.assertEqual(visualizer.clean_heatmap_data(frame).index.tolist(), list(range(1, 40)))
        frame["height"] = np.arange(150, 191)
        frame["weight"] = 70
        self.assertEqual(visualizer.clean_heatmap_data(frame).index.tolist(), list(range(1, 40)))


if __name__ == "__main__":
    unittest.main()

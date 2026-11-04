"""Check filtering and monthly aggregation independently of the example images."""

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

import time_series_visualizer as visualizer


class DataProcessingTests(unittest.TestCase):
    def test_percentile_filter_is_inclusive_and_preserves_dates(self):
        frame = pd.DataFrame({"value": range(41)}, index=pd.date_range("2020-01-01", periods=41, name="date"))
        original = frame.copy(deep=True)
        cleaned = visualizer.clean_data(frame)
        self.assertEqual(cleaned["value"].tolist(), list(range(1, 40)))
        pd.testing.assert_index_equal(cleaned.index, frame.index[1:40])
        pd.testing.assert_frame_equal(frame, original)

    def test_monthly_averages_use_daily_means_and_calendar_order(self):
        frame = pd.DataFrame({"value": [100, 10, 30, 300, 9]},
                             index=pd.to_datetime(["2019-02-01", "2019-01-01", "2019-01-02",
                                                   "2019-02-02", "2018-12-31"]))
        original = frame.copy(deep=True)
        table = visualizer.monthly_averages(frame)
        self.assertEqual(table.index.tolist(), [2018, 2019])
        self.assertEqual(table.columns.tolist(), visualizer.MONTHS)
        self.assertEqual(table.loc[2019, "January"], 20)
        self.assertEqual(table.loc[2019, "February"], 200)
        self.assertEqual(table.loc[2018, "December"], 9)
        pd.testing.assert_frame_equal(frame, original)

    def test_unobserved_months_remain_missing_instead_of_zero(self):
        frame = pd.DataFrame({"value": [10, 30]}, index=pd.to_datetime(["2019-01-01", "2019-01-02"]))
        table = visualizer.monthly_averages(frame)
        self.assertEqual(table.loc[2019, "January"], 20)
        self.assertTrue(table.loc[2019, "February":].isna().all())

    def test_plotting_preserves_the_cleaned_dataframe_and_daily_values(self):
        original = visualizer.df.copy(deep=True)
        for draw in (visualizer.draw_line_plot, visualizer.draw_bar_plot, visualizer.draw_box_plot):
            fig = draw()
            if draw is visualizer.draw_line_plot:
                np.testing.assert_array_equal(fig.axes[0].lines[0].get_ydata(), original["value"].to_numpy())
            plt.close(fig)
            pd.testing.assert_frame_equal(visualizer.df, original)


if __name__ == "__main__":
    unittest.main()

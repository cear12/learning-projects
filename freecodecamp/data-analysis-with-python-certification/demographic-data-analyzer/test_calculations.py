"""Use a small independent dataset to verify filters and denominators."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

import demographic_data_analyzer as analyzer


class CalculationTests(unittest.TestCase):
    def setUp(self):
        columns = ["age", "sex", "education", "hours-per-week", "native-country", "salary", "occupation", "race"]
        self.frame = pd.DataFrame([
            [20, "Male", "Bachelors", 1, "Big", ">50K", "Tech", "White"],
            [40, "Male", "HS-grad", 1, "Big", "<=50K", "Sales", "White"],
            [30, "Female", "Masters", 40, "Big", ">50K", "Tech", "Black"],
            [25, "Female", "Doctorate", 40, "Big", "<=50K", "Sales", "Black"],
            [50, "Female", "HS-grad", 40, "Big", ">50K", "Sales", "White"],
            [60, "Male", "HS-grad", 40, "Big", "<=50K", "Sales", "White"],
            [30, "Male", "Bachelors", 20, "India", ">50K", "Prof-specialty", "Asian-Pac-Islander"],
            [40, "Female", "HS-grad", 20, "India", ">50K", "Prof-specialty", "Asian-Pac-Islander"],
            [50, "Male", "HS-grad", 20, "India", "<=50K", "Sales", "Asian-Pac-Islander"],
            [20, "Female", "HS-grad", 20, "Zero", "<=50K", "Sales", "Other"],
        ], columns=columns)

    def analyze(self, print_data=False):
        with patch.object(analyzer.pd, "read_csv", return_value=self.frame):
            return analyzer.calculate_demographic_data(print_data=print_data)

    def test_education_percentages_use_each_groups_own_size(self):
        actual = self.analyze()
        self.assertEqual(actual["percentage_bachelors"], 20.0)
        self.assertEqual(actual["higher_education_rich"], 75.0)
        self.assertEqual(actual["lower_education_rich"], 33.3)

    def test_minimum_hours_percentage_is_limited_to_minimum_workers(self):
        actual = self.analyze()
        self.assertEqual(actual["min_work_hours"], 1)
        self.assertEqual(actual["rich_percentage"], 50.0)

    def test_country_is_chosen_by_percentage_rather_than_earner_count(self):
        actual = self.analyze()
        # Big has three high earners, India has two; their shares are 50% and 66.7%.
        self.assertEqual(actual["highest_earning_country"], "India")
        self.assertEqual(actual["highest_earning_country_percentage"], 66.7)

    def test_indian_occupation_excludes_lower_income_workers(self):
        extra = self.frame.iloc[[8, 8]].copy()
        self.frame = pd.concat([self.frame, extra], ignore_index=True)
        # Sales is now the most common Indian occupation overall; only Prof-specialty earns >50K.
        self.assertEqual(self.analyze()["top_IN_occupation"], "Prof-specialty")

    def test_average_age_and_race_counts_come_from_selected_data(self):
        actual = self.analyze()
        self.assertEqual(actual["average_age_men"], 40.0)
        self.assertIsInstance(actual["race_count"], pd.Series)
        self.assertEqual(actual["race_count"].to_dict(),
                         {"White": 4, "Asian-Pac-Islander": 3, "Black": 2, "Other": 1})

    def test_silent_mode_does_not_print_or_modify_input(self):
        original = self.frame.copy(deep=True)
        output = StringIO()
        with redirect_stdout(output):
            self.analyze(print_data=False)
        self.assertEqual(output.getvalue(), "")
        pd.testing.assert_frame_equal(self.frame, original)

    def test_print_mode_reports_results(self):
        output = StringIO()
        with redirect_stdout(output):
            self.analyze(print_data=True)
        self.assertIn("Average age of men: 40.0", output.getvalue())
        self.assertIn("Country with highest percentage of rich: India", output.getvalue())

    def test_csv_path_is_resolved_relative_to_the_module(self):
        with patch.object(analyzer.pd, "read_csv", return_value=self.frame) as read_csv:
            analyzer.calculate_demographic_data(print_data=False)
        self.assertEqual(read_csv.call_args.args[0], Path(analyzer.__file__).with_name("adult.data.csv"))


if __name__ == "__main__":
    unittest.main()

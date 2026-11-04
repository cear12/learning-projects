"""Check boundaries and arithmetic using Python's standard library."""

import json
import statistics
import unittest

from mean_var_std import calculate


class EdgeCaseTests(unittest.TestCase):
    def test_wrong_lengths_have_the_required_error_message(self):
        for size in (0, 1, 8, 10, 12):
            with self.subTest(size=size):
                with self.assertRaises(ValueError) as error:
                    calculate(list(range(size)))
                self.assertEqual(str(error.exception), "List must contain nine numbers.")

    def test_negative_and_fractional_values_match_independent_arithmetic(self):
        values = [-4.5, 2.25, 9.0, 0.0, -1.25, 6.5, 3.75, 8.0, -2.5]
        rows = [values[offset:offset + 3] for offset in (0, 3, 6)]
        columns = [values[offset::3] for offset in (0, 1, 2)]
        actual = calculate(values)
        independent = {
            "mean": statistics.mean,
            "variance": statistics.pvariance,
            "standard deviation": statistics.pstdev,
            "max": max,
            "min": min,
            "sum": sum,
        }
        for name, operation in independent.items():
            with self.subTest(statistic=name):
                for observed, group in zip(actual[name][0], columns):
                    self.assertAlmostEqual(observed, operation(group))
                for observed, group in zip(actual[name][1], rows):
                    self.assertAlmostEqual(observed, operation(group))
                self.assertAlmostEqual(actual[name][2], operation(values))

    def test_population_variance_is_used(self):
        actual = calculate(list(range(9)))
        self.assertEqual(actual["variance"][0], [6.0, 6.0, 6.0])
        self.assertEqual(actual["variance"][1], [2 / 3, 2 / 3, 2 / 3])
        self.assertAlmostEqual(actual["variance"][2], 20 / 3)

    def test_constant_values_have_zero_variance(self):
        actual = calculate([7] * 9)
        for name in ("variance", "standard deviation"):
            self.assertEqual(actual[name], [[0.0] * 3, [0.0] * 3, 0.0])
        self.assertEqual(actual["sum"], [[21] * 3, [21] * 3, 63])

    def test_input_is_preserved_and_result_has_native_python_types(self):
        values = [9, 1, 5, 3, 3, 3, 2, 9, 0]
        original = values.copy()
        result = calculate(values)
        self.assertEqual(values, original)
        self.assertEqual(set(result), {"mean", "variance", "standard deviation", "max", "min", "sum"})
        self.assertEqual(json.loads(json.dumps(result)), result)
        for statistic in result.values():
            self.assertIs(type(statistic), list)
            self.assertEqual(len(statistic), 3)
            for group in statistic[:2]:
                self.assertIs(type(group), list)
                self.assertEqual(len(group), 3)
                for number in group:
                    self.assertIn(type(number), (int, float))
            self.assertIn(type(statistic[2]), (int, float))


if __name__ == "__main__":
    unittest.main()

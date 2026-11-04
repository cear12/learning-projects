"""Print demographic statistics and run the project checks."""

from pathlib import Path
import unittest

from demographic_data_analyzer import calculate_demographic_data


def main():
    calculate_demographic_data()
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent), pattern="test*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

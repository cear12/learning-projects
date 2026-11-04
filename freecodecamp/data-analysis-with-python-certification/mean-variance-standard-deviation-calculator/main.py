"""Print an example and run the project tests."""

from pathlib import Path
from pprint import pprint
import unittest

from mean_var_std import calculate


def main():
    pprint(calculate(list(range(9))), sort_dicts=False)
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent), pattern="test*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

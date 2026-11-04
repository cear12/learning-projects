# Mean-Variance-Standard Deviation Calculator

Author: **cear12**

A solution to the [freeCodeCamp assignment](https://www.freecodecamp.org/learn/data-analysis-with-python/data-analysis-with-python-projects/mean-variance-standard-deviation-calculator), using the [official starter](https://github.com/freeCodeCamp/boilerplate-mean-variance-standard-deviation-calculator).

`calculate(values)` in [`mean_var_std.py`](mean_var_std.py) reshapes nine numbers into a 3 × 3 NumPy array and returns the mean, population variance, population standard deviation, maximum, minimum and sum.

Every result has the order **`[column statistics, row statistics, overall statistic]`**. Returned arrays and scalars are converted to native Python lists and numbers. Inputs with fewer or more than nine elements raise `ValueError("List must contain nine numbers.")`. The input list is preserved.

## Run

Use Python 3.12 with the pinned NumPy version:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

On Linux/macOS, use `.venv/bin/python`. `main.py` prints an example and runs every test, returning a failing exit code if a test fails.

To run only the original freeCodeCamp tests:

```powershell
.venv\Scripts\python.exe -m unittest test_module -v
```

To run the complete suite:

```powershell
.venv\Scripts\python.exe -m unittest discover -v
```

## Example

```python
from mean_var_std import calculate

result = calculate([0, 1, 2, 3, 4, 5, 6, 7, 8])
print(result["mean"])  # [[3.0, 4.0, 5.0], [1.0, 4.0, 7.0], 4.0]
print(result["sum"])   # [[9, 12, 15], [3, 12, 21], 36]
```

Variance and standard deviation use `ddof=0`, dividing by the population size rather than the sample-size correction.

## Verification

All **8 tests passed**, including the original three tests in `test_module.py`, which are retained unchanged. Additional tests check wrong input lengths, negative and fractional values against Python's `statistics` module, population variance, constant inputs, preservation of the input and native Python return types.

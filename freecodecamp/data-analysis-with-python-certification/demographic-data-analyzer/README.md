# Demographic Data Analyzer

Author: **cear12**

A Pandas solution to the [freeCodeCamp assignment](https://www.freecodecamp.org/learn/data-analysis-with-python/data-analysis-with-python-projects/demographic-data-analyzer), based on the [official starter](https://github.com/freeCodeCamp/boilerplate-demographic-data-analyzer).

[`calculate_demographic_data(print_data=True)`](demographic_data_analyzer.py) analyzes the supplied `adult.data.csv` and returns the ten requested results. Its original signature, returned dictionary keys, race-count Series, printing behavior and template section below the protected marker are preserved.

## Verified results

All **18 tests passed**, including all **10 unchanged official tests** and eight independent checks with a small synthetic dataset.

| Statistic in the supplied file | Result |
| --- | --- |
| Dataset rows | 32,561 |
| Average age of men | 39.4 |
| Percentage with a Bachelor's degree | 16.4% |
| Earning >50K among Bachelors/Masters/Doctorate holders | 46.5% |
| Earning >50K among other education groups | 17.4% |
| Minimum weekly working hours | 1 |
| Earning >50K among minimum-hours workers | 10.0% |
| Country with the highest within-country share earning >50K | Iran, 41.9% |
| Most common occupation among Indian records earning >50K | Prof-specialty |

Race counts are returned as a Pandas Series indexed by the source categories: White 27,816; Black 3,124; Asian-Pac-Islander 1,039; Amer-Indian-Eskimo 311; Other 271.

These are descriptive, unweighted counts and percentages of records in the supplied census file. Each education percentage uses the corresponding education group's size. Each country percentage uses that country's record count. Percentages and average age are rounded to one decimal place; the highest-earning country is chosen before rounding. The calculations use the assignment's exact category definitions and retain source records as provided.

## Run

Use Python 3.12. From this directory:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

On Linux/macOS, use `.venv/bin/python`. The entry point prints the analysis and runs all tests, returning a failing exit code if a test fails. The CSV is resolved relative to the analyzer module, so the program can also be launched from another working directory.

Run only the official checks:

```powershell
.venv\Scripts\python.exe -m unittest test_module -v
```

Run every check:

```powershell
.venv\Scripts\python.exe -m unittest discover -v
```

For a silent calculation:

```python
from demographic_data_analyzer import calculate_demographic_data

results = calculate_demographic_data(print_data=False)
print(results["higher_education_rich"])  # 46.5
```

## Dataset and checks

The [official CSV](https://github.com/freeCodeCamp/boilerplate-demographic-data-analyzer/blob/main/adult.data.csv) and original `test_module.py` are included unchanged. Dataset SHA-256: `06923b6c3b8b86739eb3854089ac35881bda073d7f40f5c92826c0ec117ca1cf`.

Additional tests verify group-specific percentage denominators, selecting a country by percentage, filtering Indian occupations to salaries above 50K, race counts, men's average age, silent and printed modes, preservation of input data and the module-relative CSV path. The results are computed from the file, without hard-coded answers.

# Book Recommendation Engine using KNN

Author: **cear12**

[Open in Google Colab](https://colab.research.google.com/github/cear12/learning-projects/blob/main/freecodecamp/machine-learning-with-python-certification/fcc_book_recommendation_knn.ipynb) · [Standalone notebook](../fcc_book_recommendation_knn.ipynb) · [Project requirements](https://www.freecodecamp.org/learn/machine-learning-with-python/machine-learning-with-python-projects/book-recommendation-engine-using-knn)

The notebook implements `get_recommends(book="")` using scikit-learn's `NearestNeighbors`, cosine distance and a sparse book-by-reader matrix. It downloads the official Book-Crossings dataset, filters infrequent users and ISBNs, builds the model, displays examples, and runs the original freeCodeCamp acceptance check.

## Verified result

The complete notebook passed the original freeCodeCamp check. All five recommendations for the check's query were verified, including independently calculated cosine distances. All **12 automated checks passed**.

| Dataset stage | Count |
| --- | ---: |
| Original book records | 271,379 |
| Original ratings | 1,149,780 |
| Ratings after frequency filters | 49,781 |
| Ratings matched to book titles | 49,517 |
| Titles in the fitted matrix | 673 |
| Readers in the fitted matrix | 888 |
| Nonzero matrix entries | 12,469 |

Measured results are saved in [`artifacts/metrics.json`](artifacts/metrics.json), with two complete queries in [`artifacts/recommendations.json`](artifacts/recommendations.json).

## Method

- Count users and ISBNs on the original ratings table. Retain users with at least 200 ratings and ISBNs with at least 100 ratings, including zero-valued ratings.
- Join titles by ISBN, combine editions under their titles, average duplicate reader/title ratings and fill missing entries with zero.
- Fit `NearestNeighbors(metric="cosine", algorithm="brute")` on a CSR matrix.
- Return exactly five other titles as `[requested_title, [[title, distance], ...]]`.
- Follow the assignment's descending-distance output order: the closest recommendation appears last. Smaller distances mean greater similarity.

Unknown titles raise `ValueError`; non-string queries raise `TypeError`. Recommendations are derived from ratings, with no hard-coded lookup table.

## Run locally

Use Python 3.12. From this directory:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts/run_notebook.py
.venv\Scripts\python.exe -m pytest -q
```

On Linux/macOS use `.venv/bin/python`. In Colab, open the notebook and run all cells; the usual data-science libraries are already installed. The notebook does not import files from this repository.

The first execution downloads approximately 26 MB. It verifies the dataset checksum and caches the archive and required CSV files. Data and local environments are excluded from Git. The executed notebook includes its outputs; `artifacts/` also contains machine-readable metrics and example recommendations.

## Rebuild the notebook

`scripts/build_notebook.py` regenerates an unexecuted notebook from readable cell definitions. It uses the unchanged final test cell from the official starter saved at `.cache/starter.ipynb`. To obtain it:

```python
from pathlib import Path
from urllib.request import urlopen
Path(".cache").mkdir(exist_ok=True)
url = "https://raw.githubusercontent.com/freeCodeCamp/boilerplate-book-recommendation-engine/main/fcc_book_recommendation_knn.ipynb"
Path(".cache/starter.ipynb").write_bytes(urlopen(url).read())
```

Run `scripts/run_notebook.py` afterward to regenerate the executed outputs.

## Sources and limits

- [Official starter notebook](https://github.com/freeCodeCamp/boilerplate-book-recommendation-engine)
- [Official dataset mirror](https://github.com/freeCodeCamp/cdn/tree/main/build/project-data/books)
- [NearestNeighbors documentation](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestNeighbors.html)

Archive SHA-256: `adc7b47afb47c8e29e5f0b70a9816569b3367c5588064ba7a916f16e3ef5d060`.

This is item-to-item collaborative filtering, without a personalized user profile. The frequency thresholds exclude less popular books. The assignment check verifies expected recommendations; it does not establish quality for unseen user preferences. Original dataset rights remain with their respective owners.

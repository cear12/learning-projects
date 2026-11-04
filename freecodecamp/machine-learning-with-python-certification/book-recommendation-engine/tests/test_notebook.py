"""Check preprocessing and recommendations independently of the full dataset."""

from pathlib import Path

import nbformat
import numpy as np
import pandas as pd
import pytest
from scipy.sparse import csr_matrix, isspmatrix_csr
from sklearn.neighbors import NearestNeighbors

PROJECT = Path(__file__).resolve().parents[1]
NOTEBOOK = PROJECT.parent / "fcc_book_recommendation_knn.ipynb"


@pytest.fixture(scope="module")
def helpers():
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    nbformat.validate(notebook)
    namespace = {"np": np, "pd": pd, "csr_matrix": csr_matrix}
    for cell in notebook.cells:
        if cell.id in {"filter-helper", "matrix-helper", "recommendation-helper"}:
            exec(compile(cell.source, f"notebook:{cell.id}", "exec"), namespace)
    return namespace


def test_frequency_thresholds_are_inclusive_and_counted_before_filtering(helpers):
    ratings = pd.DataFrame([(1, "A", 8), (1, "B", 0), (2, "A", 9),
                            (2, "C", 6), (3, "B", 5)], columns=["user", "isbn", "rating"])
    original = ratings.copy(deep=True)
    filtered = helpers["filter_ratings"](ratings, min_user_ratings=2, min_book_ratings=2)
    assert list(filtered.itertuples(index=False, name=None)) == [(1, "A", 8), (1, "B", 0), (2, "A", 9)]
    # B qualifies on the original data even though only one retained user rated it.
    assert len(filtered[filtered.isbn == "B"]) == 1
    pd.testing.assert_frame_equal(ratings, original)


def test_matrix_combines_editions_and_averages_duplicate_reader_ratings(helpers):
    books = pd.DataFrame([
        ("001", "Shared title", "First author"), ("002", "Shared title", "First author"),
        ("003", "Another title", "Second author"), ("003", "Wrong duplicate", "Other"),
    ], columns=["isbn", "title", "author"])
    ratings = pd.DataFrame([(1, "001", 8), (1, "002", 4), (2, "001", 10),
                            (2, "003", 0), (3, "missing", 7)], columns=["user", "isbn", "rating"])
    table, matrix, matched = helpers["make_book_matrix"](books, ratings)
    assert isspmatrix_csr(matrix)
    assert matched == 4
    assert table.loc["Shared title", 1] == 6
    assert table.loc["Shared title", 2] == 10
    assert table.loc["Another title", 1] == 0
    assert table.loc["Another title", 2] == 0
    assert "Wrong duplicate" not in table.index
    assert table.shape == (2, 2)


def test_matrix_rejects_unmatched_catalog(helpers):
    books = pd.DataFrame([("A", "Title", "Author")], columns=["isbn", "title", "author"])
    ratings = pd.DataFrame([(1, "B", 8)], columns=["user", "isbn", "rating"])
    with pytest.raises(ValueError, match="No rated books"):
        helpers["make_book_matrix"](books, ratings)


@pytest.fixture
def neighborhood():
    titles = pd.Index(["Query", "Twin", "Close", "Medium", "Far", "Orthogonal"])
    matrix = csr_matrix(np.array([[1, 0, 0], [1, 0, 0], [1, 0.1, 0],
                                  [1, 0.5, 0], [1, 1, 0], [0, 1, 0]], dtype=np.float64))
    return titles, matrix, NearestNeighbors(metric="cosine", algorithm="brute").fit(matrix)


def test_recommendations_exclude_only_the_query_and_preserve_zero_distance_neighbor(helpers, neighborhood):
    result = helpers["recommend_books"]("Query", *neighborhood)
    assert result[0] == "Query"
    assert [title for title, distance in result[1]] == ["Orthogonal", "Far", "Medium", "Close", "Twin"]
    expected = [1, 1 - 1 / np.sqrt(2), 1 - 1 / np.sqrt(1.25), 1 - 1 / np.sqrt(1.01), 0]
    np.testing.assert_allclose([distance for title, distance in result[1]], expected, atol=1e-12)
    assert all(isinstance(distance, float) for title, distance in result[1])


@pytest.mark.parametrize("unknown", ["", "Missing book", "query"])
def test_unknown_titles_raise_clear_errors(helpers, neighborhood, unknown):
    with pytest.raises(ValueError, match="Book not found"):
        helpers["recommend_books"](unknown, *neighborhood)


@pytest.mark.parametrize("value", [None, 42, ["Query"]])
def test_non_string_queries_are_rejected(helpers, neighborhood, value):
    with pytest.raises(TypeError, match="must be a string"):
        helpers["recommend_books"](value, *neighborhood)


def test_small_catalog_does_not_silently_return_too_few_recommendations(helpers, neighborhood):
    titles, matrix, model = neighborhood
    with pytest.raises(ValueError, match="At least six"):
        helpers["recommend_books"]("Query", titles[:5], matrix[:5], model)


def test_required_function_signature_and_python_cells(helpers):
    assert helpers["get_recommends"].__defaults__ == ("",)
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            compile(cell.source, f"notebook:{cell.id}", "exec")

"""Build the standalone book recommendation notebook."""

from pathlib import Path
import textwrap
import nbformat as nbf

PROJECT = Path(__file__).resolve().parents[1]
NOTEBOOK = PROJECT.parent / "fcc_book_recommendation_knn.ipynb"
cells = []


def markdown(identifier, source):
    cells.append(nbf.v4.new_markdown_cell(textwrap.dedent(source).strip(), id=identifier))


def code(identifier, source):
    cells.append(nbf.v4.new_code_cell(textwrap.dedent(source).strip(), id=identifier))


markdown("introduction", """
    # Book Recommendation Engine using KNN

    **Author: cear12**

    A solution to the [freeCodeCamp project](https://www.freecodecamp.org/learn/machine-learning-with-python/machine-learning-with-python-projects/book-recommendation-engine-using-knn).
    Run the cells in order in Google Colab or Jupyter. This notebook is self-contained:
    it downloads the official Book-Crossings dataset and does not import local project files.

    Books with similar reader-rating patterns are found using scikit-learn's
    `NearestNeighbors` with cosine distance. `get_recommends(book)` returns the requested
    title and five recommendations in the format required by the assignment.
""")

code("imports", """
    from pathlib import Path
    import hashlib
    import json
    import shutil
    import urllib.request
    import zipfile

    import numpy as np
    import pandas as pd
    import scipy
    from scipy.sparse import csr_matrix
    import sklearn
    from sklearn.neighbors import NearestNeighbors

    CACHE = Path(".cache")
    ARTIFACTS = Path("artifacts")
    CACHE.mkdir(exist_ok=True)
    ARTIFACTS.mkdir(exist_ok=True)
    print(f"pandas {pd.__version__}; scikit-learn {sklearn.__version__}")
""")

markdown("download-description", """
    ## 1. Download the original dataset

    Use the original freeCodeCamp CDN, with its official GitHub mirror as a fallback.
    Verify the archive's SHA-256 checksum and extract only the two required CSV files.
    Existing verified downloads are reused. The source files use semicolons and Latin-1
    encoding; ISBNs remain strings so their leading zeroes are preserved.
""")

code("download-helper", """
    DATA_URLS = (
        "https://cdn.freecodecamp.org/project-data/books/book-crossings.zip",
        "https://raw.githubusercontent.com/freeCodeCamp/cdn/main/build/project-data/books/book-crossings.zip",
    )
    DATA_SHA256 = "adc7b47afb47c8e29e5f0b70a9816569b3367c5588064ba7a916f16e3ef5d060"


    def file_sha256(path):
        digest = hashlib.sha256()
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()


    def prepare_data(cache=CACHE):
        cache = Path(cache)
        cache.mkdir(parents=True, exist_ok=True)
        archive_path = cache / "book-crossings.zip"
        if not archive_path.exists() or file_sha256(archive_path) != DATA_SHA256:
            errors = []
            for url in DATA_URLS:
                temporary = archive_path.with_suffix(".download")
                try:
                    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as out:
                        shutil.copyfileobj(response, out)
                    if file_sha256(temporary) != DATA_SHA256:
                        raise ValueError("Dataset checksum mismatch")
                    temporary.replace(archive_path)
                    break
                except (OSError, ValueError) as error:
                    temporary.unlink(missing_ok=True)
                    errors.append(f"{url}: {error}")
            else:
                raise RuntimeError("Dataset download failed:\\n" + "\\n".join(errors))
        names = ("BX-Books.csv", "BX-Book-Ratings.csv")
        with zipfile.ZipFile(archive_path) as archive:
            for name in names:
                target = cache / name
                entry = archive.getinfo(name)
                if not target.exists() or target.stat().st_size != entry.file_size:
                    with archive.open(entry) as source, target.open("wb") as out:
                        shutil.copyfileobj(source, out)
        return tuple(cache / name for name in names)
""")

code("load-data", """
    books_filename, ratings_filename = prepare_data()
    df_books = pd.read_csv(
        books_filename, encoding="ISO-8859-1", sep=";", header=0,
        names=["isbn", "title", "author"], usecols=["isbn", "title", "author"],
        dtype={"isbn": "str", "title": "str", "author": "str"})
    df_ratings = pd.read_csv(
        ratings_filename, encoding="ISO-8859-1", sep=";", header=0,
        names=["user", "isbn", "rating"], usecols=["user", "isbn", "rating"],
        dtype={"user": "int32", "isbn": "str", "rating": "float32"})
    print(f"Books: {len(df_books):,}; ratings: {len(df_ratings):,}")
    df_books.head()
""")

markdown("filter-description", """
    ## 2. Filter users and books

    Keep users with **at least 200 ratings** and ISBNs with **at least 100 ratings**.
    Both counts are calculated from the original ratings table, before either filter
    is applied. Zero-valued ratings are retained: the assignment's frequency thresholds
    include them. Do not repeatedly recalculate the thresholds on progressively smaller subsets.
""")

code("filter-helper", """
    def filter_ratings(ratings, min_user_ratings=200, min_book_ratings=100):
        user_counts = ratings["user"].value_counts()
        book_counts = ratings["isbn"].value_counts()
        users = user_counts.index[user_counts >= min_user_ratings]
        isbns = book_counts.index[book_counts >= min_book_ratings]
        return ratings.loc[ratings["user"].isin(users) & ratings["isbn"].isin(isbns)].copy()
""")

code("filter-data", """
    filtered_ratings = filter_ratings(df_ratings)
    print(f"Retained ratings: {len(filtered_ratings):,}")
    print(f"Eligible users: {filtered_ratings['user'].nunique():,}")
    print(f"Eligible ISBNs: {filtered_ratings['isbn'].nunique():,}")
""")

markdown("matrix-description", """
    ## 3. Build a sparse book-by-reader matrix

    Join ISBNs to titles and combine editions of the same title into one row.
    If a reader rated multiple editions, their ratings for that title are averaged.
    A missing rating is represented by zero. Each row is one book; each column is one reader.
    The fitted neighbor model receives a CSR sparse matrix.

    Cosine distance compares rating-vector direction: smaller values indicate more similar
    reading patterns. These distances are not star ratings or probabilities of liking a book.
""")

code("matrix-helper", """
    def make_book_matrix(books, ratings):
        catalog = books.dropna(subset=["isbn", "title"]).drop_duplicates("isbn")
        merged = ratings.merge(catalog[["isbn", "title"]], on="isbn", how="inner")
        if merged.empty:
            raise ValueError("No rated books match the catalog")
        table = merged.pivot_table(index="title", columns="user", values="rating", aggfunc="mean")
        table = table.fillna(0).astype(np.float32)
        if table.empty:
            raise ValueError("The book-rating matrix is empty")
        return table, csr_matrix(table.to_numpy()), len(merged)
""")

code("fit-model", """
    book_table, book_matrix, matched_ratings = make_book_matrix(df_books, filtered_ratings)
    model = NearestNeighbors(metric="cosine", algorithm="brute")
    model.fit(book_matrix)
    print(f"Matrix: {book_matrix.shape[0]:,} titles × {book_matrix.shape[1]:,} readers")
    print(f"Stored nonzero ratings: {book_matrix.nnz:,}")
""")

markdown("recommendation-description", """
    ## 4. Return five recommendations

    `get_recommends(book)` returns `[book, [[title, distance], ...]]`.
    Query six neighbors, remove the requested book by its row index, and return five other titles.
    The assignment lists these five in **descending distance order**, so the closest match is last.
    Titles must match the catalog exactly. An unknown title produces a clear error.
""")

code("recommendation-helper", """
    def recommend_books(book, titles, matrix, fitted_model):
        if not isinstance(book, str):
            raise TypeError("Book title must be a string")
        if book not in titles:
            raise ValueError(f"Book not found in the filtered catalog: {book!r}")
        if len(titles) < 6:
            raise ValueError("At least six books are needed to return five recommendations")
        position = titles.get_loc(book)
        distances, indices = fitted_model.kneighbors(matrix[position], n_neighbors=6)
        neighbors = [(int(index), float(distance))
                     for index, distance in zip(indices[0], distances[0]) if index != position]
        neighbors.sort(key=lambda pair: (pair[1], str(titles[pair[0]])))
        closest = neighbors[:5]
        return [book, [[str(titles[index]), distance] for index, distance in reversed(closest)]]


    def get_recommends(book=""):
        return recommend_books(book, book_table.index, book_matrix, model)
""")

code("examples", """
    example_title = "The Queen of the Damned (Vampire Chronicles (Paperback))"
    example_recommendations = get_recommends(example_title)
    print(example_title)
    pd.DataFrame(example_recommendations[1], columns=["Recommended title", "Cosine distance"])
""")

markdown("official-check-description", """
    ## 5. Run the original freeCodeCamp check

    The following cell is copied unchanged from the official starter notebook.
    Its test checks two returned recommendations. The next cell additionally checks
    the full result structure and independently verifies all five cosine distances.
""")

# Preserve the complete official test cell, including its original assertions and messages.
starter = nbf.read(PROJECT / ".cache" / "starter.ipynb", as_version=4)
code("official-test", starter.cells[-1].source)

code("result-checks", """
    requested = "Where the Heart Is (Oprah's Book Club (Paperback))"
    result = get_recommends(requested)
    assert result[0] == requested and len(result[1]) == 5
    titles = [title for title, distance in result[1]]
    distances = [distance for title, distance in result[1]]
    assert requested not in titles and len(set(titles)) == 5
    assert distances == sorted(distances, reverse=True)
    assert all(np.isfinite(distance) and 0 <= distance <= 1 for distance in distances)
    expected_titles = ["I'll Be Seeing You", "The Weight of Water", "The Surgeon",
                       "I Know This Much Is True", "The Lovely Bones: A Novel"]
    assert titles == expected_titles

    query = book_table.loc[requested].to_numpy(dtype=np.float64)
    for title, distance in result[1]:
        candidate = book_table.loc[title].to_numpy(dtype=np.float64)
        manual_distance = 1 - np.dot(query, candidate) / (np.linalg.norm(query) * np.linalg.norm(candidate))
        assert np.isclose(distance, manual_distance, atol=1e-6)

    summary = {
        "dataset_sha256": DATA_SHA256,
        "pandas_version": pd.__version__, "scikit_learn_version": sklearn.__version__,
        "raw_books": len(df_books), "raw_ratings": len(df_ratings),
        "filtered_ratings": len(filtered_ratings), "matched_ratings": matched_ratings,
        "matrix_titles": book_matrix.shape[0], "matrix_readers": book_matrix.shape[1],
        "nonzero_ratings": book_matrix.nnz, "metric": "cosine", "algorithm": "brute",
        "official_test_passed": True, "all_five_distances_verified": True,
    }
    (ARTIFACTS / "metrics.json").write_text(json.dumps(summary, indent=2) + "\\n", encoding="utf-8")
    examples = {requested: result, example_title: example_recommendations}
    (ARTIFACTS / "recommendations.json").write_text(json.dumps(examples, indent=2) + "\\n", encoding="utf-8")
    print("All five recommendations and independently computed distances verified.")
""")

markdown("limitations", """
    ## Notes

    Call `get_recommends("exact book title")` after running the previous cells.
    Search `book_table.index` to find eligible titles. Less frequently rated books are
    deliberately excluded by the assignment's thresholds. This is item-to-item collaborative
    filtering: it compares reader ratings and does not analyze book descriptions or accept
    a personal user profile. Passing the assignment check confirms the specified behavior,
    rather than measuring recommendation quality on unseen reader preferences.
""")

notebook = nbf.v4.new_notebook(cells=cells)
notebook.metadata = {
    "authors": [{"name": "cear12"}],
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python", "version": "3.12"},
}
nbf.validate(notebook)
nbf.write(notebook, NOTEBOOK)
print(f"Built {NOTEBOOK.name}: {len(cells)} cells")

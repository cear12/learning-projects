"""Check feature handling, split isolation and model persistence."""

from pathlib import Path
import os

PROJECT = Path(__file__).resolve().parents[1]
NOTEBOOK = PROJECT.parent / "fcc_predict_health_costs_with_regression.ipynb"
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / ".cache" / "matplotlib"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import nbformat
import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def helpers():
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    nbformat.validate(notebook)
    namespace = {}
    for cell in notebook.cells:
        if cell.id in {"imports", "split-helper", "encoding-helper", "model-helper"}:
            exec(compile(cell.source, f"notebook:{cell.id}", "exec"), namespace)
    return namespace


@pytest.fixture
def records():
    return pd.DataFrame([
        {"age": 25, "bmi": 22.5, "children": 0, "sex": "female", "smoker": "no", "region": "northeast"},
        {"age": 50, "bmi": 31.0, "children": 2, "sex": "male", "smoker": "yes", "region": "southwest"},
    ], index=[12, 33])


def test_split_is_reproducible_and_keeps_test_and_validation_separate(helpers):
    frame = pd.DataFrame({"row": range(100), "expenses": np.arange(100) * 100})
    training, fitting, validation, testing = helpers["split_dataset"](frame)
    assert [len(training), len(fitting), len(validation), len(testing)] == [80, 64, 16, 20]
    assert set(training.index) == set(fitting.index) | set(validation.index)
    assert set(fitting.index).isdisjoint(validation.index)
    assert set(training.index).isdisjoint(testing.index)
    assert set(training.index) | set(testing.index) == set(frame.index)
    repeated = helpers["split_dataset"](frame)
    for first, second in zip((training, fitting, validation, testing), repeated):
        pd.testing.assert_frame_equal(first, second)


def test_encoding_preserves_order_and_vocab_when_categories_are_absent(helpers, records):
    before = records.copy(deep=True)
    encoded = helpers["encode_features"](records)
    single = helpers["encode_features"](records.iloc[:1, ::-1])
    assert encoded.shape == (2, 11)
    assert single.columns.equals(encoded.columns)
    assert encoded.index.tolist() == [12, 33]
    assert all(dtype == np.float32 for dtype in encoded.dtypes)
    assert encoded.loc[12, "smoker_no"] == 1
    assert encoded.loc[12, "smoker_yes"] == 0
    assert encoded.loc[33, "region_southwest"] == 1
    assert encoded.loc[12, "bmi"] == 22.5
    pd.testing.assert_frame_equal(records, before)


@pytest.mark.parametrize("attribute,value", [("sex", "unknown"), ("smoker", "maybe"), ("region", "other")])
def test_unknown_categories_are_rejected(helpers, records, attribute, value):
    records.loc[12, attribute] = value
    with pytest.raises(ValueError, match="Unknown"):
        helpers["encode_features"](records)


@pytest.mark.parametrize("attribute,value", [("age", -1), ("bmi", np.inf), ("bmi", np.nan), ("children", -1)])
def test_invalid_numeric_values_are_rejected(helpers, records, attribute, value):
    records[attribute] = records[attribute].astype(float)
    records.loc[12, attribute] = value
    with pytest.raises(ValueError):
        helpers["encode_features"](records)


def test_target_cannot_accidentally_enter_the_features(helpers, records):
    records["expenses"] = [1000, 2000]
    with pytest.raises(ValueError, match="six input attributes"):
        helpers["encode_features"](records)


def test_missing_input_column_is_rejected(helpers, records):
    with pytest.raises(ValueError, match="six input attributes"):
        helpers["encode_features"](records.drop(columns="bmi"))


def test_model_normalization_uses_only_supplied_fitting_features_and_survives_reload(helpers, tmp_path):
    tf = helpers["tf"]
    features = np.array([[0, 2], [2, 4], [4, 6], [6, 8]], dtype=np.float32)
    labels = np.array([1000, 2000, 3000, 4000], dtype=np.float32)
    model = helpers["build_model"](features)
    np.testing.assert_allclose(model.get_layer("input_normalization").mean.numpy(), [[3, 5]])
    model.train_on_batch(features, labels)
    prediction = model(features, training=False).numpy()
    assert prediction.shape == (4, 1)
    assert np.isfinite(prediction).all() and (prediction >= 0).all()
    model.reset_metrics()
    metrics = model.test_on_batch(features, labels, return_dict=True)
    np.testing.assert_allclose(metrics["mae"], np.mean(np.abs(prediction.reshape(-1) - labels)), rtol=1e-5)
    path = tmp_path / "model.keras"
    model.save(path)
    restored = tf.keras.models.load_model(path)
    np.testing.assert_allclose(restored(features, training=False).numpy(), prediction, atol=1e-5)


def test_notebook_python_is_valid_and_author_is_set():
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    assert notebook.metadata.authors == [{"name": "cear12"}]
    for cell in notebook.cells:
        if cell.cell_type == "code":
            compile(cell.source, f"notebook:{cell.id}", "exec")

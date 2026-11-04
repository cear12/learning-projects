"""Independent checks for SMS parsing, split isolation and model behavior."""

from pathlib import Path
import os

PROJECT = Path(__file__).resolve().parents[1]
NOTEBOOK = PROJECT.parent / "fcc_sms_text_classification.ipynb"
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
    scope = {}
    selected = {"imports", "download-helper", "split-helper", "model-helper",
                "evaluation-helper", "prediction-helper"}
    for cell in notebook.cells:
        if cell.id in selected:
            exec(compile(cell.source, f"notebook:{cell.id}", "exec"), scope)
    return scope


def test_tsv_reader_keeps_literal_na_and_quoted_text(helpers, tmp_path):
    path = tmp_path / "messages.tsv"
    path.write_text('ham\tNA\nspam\tClaim "prize" now\n', encoding="utf-8")
    frame = helpers["read_messages"](path)
    assert frame["message"].tolist() == ["NA", 'Claim "prize" now']
    assert frame["target"].tolist() == [0.0, 1.0]


@pytest.mark.parametrize("text", ["other\tHello\n", "ham\t  \n"])
def test_tsv_reader_rejects_unknown_labels_and_empty_text(helpers, tmp_path, text):
    path = tmp_path / "invalid.tsv"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        helpers["read_messages"](path)


def test_duplicate_texts_are_removed_before_stratified_split(helpers):
    records = [{"label": "ham", "message": f"ordinary message {i}", "target": 0} for i in range(30)]
    records += [{"label": "spam", "message": f"advertisement {i}", "target": 1} for i in range(10)]
    records += [records[0].copy(), records[31].copy()]
    frame = pd.DataFrame(records)
    original = frame.copy(deep=True)
    unique, fitting, validation = helpers["split_training"](frame)
    assert [len(unique), len(fitting), len(validation)] == [40, 32, 8]
    assert set(fitting.message).isdisjoint(validation.message)
    assert validation.target.value_counts().to_dict() == {0: 6, 1: 2}
    for first, second in zip((unique, fitting, validation), helpers["split_training"](frame)):
        pd.testing.assert_frame_equal(first, second)
    pd.testing.assert_frame_equal(frame, original)


def test_conflicting_duplicate_labels_are_rejected(helpers):
    frame = pd.DataFrame([{"message": "same text", "label": "ham", "target": 0},
                          {"message": "same text", "label": "spam", "target": 1}])
    with pytest.raises(ValueError, match="conflicting labels"):
        helpers["split_training"](frame)


def test_metrics_match_independent_confusion_counts(helpers):
    metrics = helpers["measure_predictions"]([0, 0, 1, 1], [0.1, 0.6, 0.4, 0.9])
    assert metrics["confusion_matrix"] == [[1, 1], [1, 1]]
    assert metrics["accuracy"] == metrics["spam_precision"] == metrics["spam_recall"] == metrics["spam_f1"] == 0.5
    assert helpers["measure_predictions"]([1], [0.5])["accuracy"] == 1


@pytest.mark.parametrize("targets,scores", [([], []), ([0], [0.1, 0.2]),
    ([0], [np.nan]), ([1], [np.inf]), ([0], [-0.1]), ([1], [1.1]), ([0.2], [0.1])])
def test_invalid_metric_inputs_are_rejected(helpers, targets, scores):
    with pytest.raises(ValueError):
        helpers["measure_predictions"](targets, scores)


@pytest.mark.parametrize("score,label", [(0.1, "ham"), (0.5, "spam"), (0.9, "spam")])
def test_prediction_contract_and_threshold(helpers, score, label):
    tf = helpers["tf"]

    class FixedModel:
        def __call__(self, texts, training=False):
            assert texts.dtype == tf.string and training is False
            return tf.constant([[score]], dtype=tf.float32)

    result = helpers["classify_message"]("A message with £ and punctuation!", FixedModel())
    assert isinstance(result, list) and isinstance(result[0], float)
    assert result[0] == pytest.approx(score)
    assert result[1] == label


@pytest.mark.parametrize("text,error", [(None, TypeError), (42, TypeError), (["message"], TypeError),
                                        ("", ValueError), ("  \n", ValueError)])
def test_invalid_prediction_inputs_are_rejected_before_model_call(helpers, text, error):
    with pytest.raises(error):
        helpers["classify_message"](text, None)


def test_vocabulary_is_fit_only_on_supplied_texts_and_model_round_trips(helpers, tmp_path):
    tf = helpers["tf"]
    fitting_texts = ["meet me tomorrow", "bring some milk", "claim free reward", "win prize £100 now"]
    model = helpers["build_model"](fitting_texts, max_tokens=64)
    vocabulary = model.get_layer("text_features").get_vocabulary()
    assert "tomorrow" in vocabulary
    assert "heldoutonlytoken" not in vocabulary
    texts = tf.constant(fitting_texts)
    model.train_on_batch(texts, np.array([0, 0, 1, 1], dtype=np.float32))
    queries = tf.constant(["meet tomorrow", "heldoutonlytoken"])
    before = model(queries, training=False).numpy()
    assert before.shape == (2, 1)
    assert np.isfinite(before).all() and ((before >= 0) & (before <= 1)).all()
    checkpoint = tmp_path / "classifier.keras"
    model.save(checkpoint)
    restored = tf.keras.models.load_model(checkpoint)
    assert restored.get_layer("text_features").get_vocabulary() == vocabulary
    np.testing.assert_allclose(restored(queries, training=False).numpy(), before, atol=1e-6)


def test_notebook_cells_are_python_and_author_is_set():
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    assert notebook.metadata.authors == [{"name": "cear12"}]
    for cell in notebook.cells:
        if cell.cell_type == "code":
            compile(cell.source, f"notebook:{cell.id}", "exec")

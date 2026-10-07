"""Unit tests for Uncertainty estimation, OOD detection, Conformal intervals, and Gate 0."""

import json
from pathlib import Path
import numpy as np
import pytest

from protein_ai.config import PredictorConfig, UncertaintyConfig
from uncertainty.conformal import ConformalCalibrator
from uncertainty.ensemble import EnsembleEstimator
from uncertainty.gate0 import Gate0Report, evaluate_gate0
from uncertainty.ood import OODDetector
from uncertainty.score import CompositeUncertaintyScorer


@pytest.fixture
def synthetic_features_and_targets():
    rng = np.random.RandomState(42)
    X = rng.normal(0, 1, size=(30, 20)).astype(np.float32)
    # y with some linear and non-linear component
    y = (X[:, 0] * 1.5 + X[:, 1] * -0.8 + rng.normal(0, 0.2, size=30)).astype(np.float32)
    return X, y


def test_ensemble_estimator(synthetic_features_and_targets):
    X, y = synthetic_features_and_targets
    X_train, y_train = X[:20], y[:20]
    X_test = X[20:]

    ensemble = EnsembleEstimator(
        predictor_config=PredictorConfig(model_type="ridge"),
        uncertainty_config=UncertaintyConfig(ensemble_size=5, ensemble_subsample_ratio=0.8),
    )
    ensemble.fit(X_train, y_train)
    assert ensemble.is_fitted is True

    mean_preds, std_preds = ensemble.predict_with_disagreement(X_test)
    assert len(mean_preds) == len(X_test)
    assert len(std_preds) == len(X_test)
    assert np.all(std_preds >= 0.0)


def test_ood_detector(synthetic_features_and_targets):
    X, _ = synthetic_features_and_targets
    X_train = X[:20]
    X_in_dist = X_train[:5]
    # Perturbed out-of-distribution points far from training space
    X_out_dist = X_train[:5] + 15.0

    detector = OODDetector(config=UncertaintyConfig(ood_k_neighbors=3))
    detector.fit(X_train)

    scores_in = detector.compute_ood_scores(X_in_dist)
    scores_out = detector.compute_ood_scores(X_out_dist)

    assert np.all(scores_in >= 0.0) and np.all(scores_in <= 1.0)
    assert np.all(scores_out >= 0.0) and np.all(scores_out <= 1.0)
    # Out of distribution points must have strictly higher OOD distance
    assert np.mean(scores_out) > np.mean(scores_in)


def test_conformal_calibrator():
    calibrator = ConformalCalibrator(config=UncertaintyConfig(conformal_alpha=0.10))

    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    y_pred = np.array([1.1, 1.9, 3.2, 3.8, 5.0, 6.3, 6.9, 8.1, 9.4, 9.7])

    q = calibrator.calibrate(y_true, y_pred)
    assert calibrator.is_calibrated is True
    assert q > 0.0

    # Generate intervals on new query points
    q_test = np.array([2.0, 5.0])
    intervals = calibrator.predict_intervals(q_test)
    assert np.all(intervals.lower_bound < intervals.upper_bound)
    np.testing.assert_allclose(intervals.upper_bound - intervals.lower_bound, 2.0 * q, atol=1e-5)


def test_composite_uncertainty_scorer():
    scorer = CompositeUncertaintyScorer(
        config=UncertaintyConfig(weight_ensemble=0.5, weight_ood=0.5, weight_conformal=0.0)
    )

    ens_std = np.array([0.1, 0.5, 1.0])
    ood = np.array([0.0, 0.5, 1.0])

    composite, weights = scorer.compute_composite_score(ens_std, ood)
    assert composite.shape == (3,)
    assert 0.0 <= composite[0] < composite[1] < composite[2] <= 1.0
    assert weights["ensemble"] == 0.5
    assert weights["ood"] == 0.5


def test_gate0_evaluation_report(tmp_path):
    # Simulated test set where uncertainty tracks error
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    # Predictions with increasing error
    y_pred = np.array([1.05, 2.08, 3.15, 3.80, 5.40, 6.60, 7.80, 9.50])
    # Increasing uncertainty
    u_scores = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])

    report = evaluate_gate0(
        y_true=y_true,
        y_pred=y_pred,
        uncertainty_scores=u_scores,
        dataset_name="synthetic_test",
        split_strategy="test_split",
        is_synthetic_fixture=True,
    )

    assert isinstance(report, Gate0Report)
    assert report.n_samples == 8
    assert report.spearman_correlation is not None
    assert report.spearman_correlation > 0.80  # Strong correlation
    assert report.useful_signal is True
    assert report.high_uncertainty_mean_error > report.low_uncertainty_mean_error

    # Test saving JSON and Markdown
    json_path = tmp_path / "gate0.json"
    md_path = tmp_path / "gate0.md"
    report.save_json(json_path)
    report.save_markdown(md_path)

    assert json_path.exists()
    assert md_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["useful_signal"] is True

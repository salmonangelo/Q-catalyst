"""Unit tests for Protein-AI module: representations, mutation scoring, features, and predictors."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from protein_ai.config import ESMConfig, PredictorConfig, ProteinAIConfig
from protein_ai.embeddings import EmbeddingExtractor
from protein_ai.esm import ESMModelWrapper
from protein_ai.features import FeaturePipeline
from protein_ai.mutation_scoring import MutationScorer
from protein_ai.outputs import PREDICTION_COLUMNS, enforce_predictions_schema, save_predictions_parquet
from protein_ai.predictors import FitnessPredictor
from protein_ai.utils import compute_regression_metrics, create_synthetic_variant_dataset


@pytest.fixture
def synthetic_df():
    return create_synthetic_variant_dataset(n_records=16, random_seed=42)


def test_esm_mock_wrapper():
    config = ESMConfig(model_name="heuristic_esm_mock")
    model = ESMModelWrapper(config)
    assert model.is_mock is True
    assert model.hidden_dim == 320

    seq = "MSLEASAGPFTVRS"
    emb = model.extract_sequence_embedding(seq)
    assert isinstance(emb, np.ndarray)
    assert emb.shape == (320,)
    assert not np.isnan(emb).any()


def test_mutation_scoring():
    scorer = MutationScorer(config=ESMConfig(model_name="heuristic_esm_mock"))

    # WT score should be 0.0
    res_wt = scorer.score_variant("v_wt", "WT", parent_enzyme="IsPETase")
    assert res_wt.mutation_score == 0.0

    # Single mutation
    res_single = scorer.score_variant("v_s", "S160A", parent_enzyme="IsPETase")
    assert isinstance(res_single.mutation_score, float)
    assert res_single.mutations == "S160A"

    # Multi mutation
    res_multi = scorer.score_variant("v_m", "S160A;D206G", parent_enzyme="IsPETase")
    assert isinstance(res_multi.mutation_score, float)
    assert res_multi.mutations == "S160A;D206G"


def test_embedding_extractor_and_caching(synthetic_df, tmp_path):
    config = ESMConfig(model_name="heuristic_esm_mock", cache_dir=tmp_path / "cache")
    extractor = EmbeddingExtractor(config=config)

    matrix1, ids1 = extractor.embed_dataframe(synthetic_df)
    assert matrix1.shape == (len(synthetic_df), 320)
    assert ids1 == synthetic_df["variant_id"].tolist()

    # Second call should hit cache and yield identical results
    matrix2, ids2 = extractor.embed_dataframe(synthetic_df)
    np.testing.assert_array_almost_equal(matrix1, matrix2)


def test_feature_pipeline(synthetic_df):
    pipeline = FeaturePipeline(normalize_features=True)

    train_df = synthetic_df.iloc[:10].copy()
    test_df = synthetic_df.iloc[10:].copy()

    X_train, ids_tr = pipeline.fit_transform(train_df)
    assert pipeline.is_fitted is True
    assert X_train.shape == (10, 321)  # 320 embedding dims + 1 mutation score

    # Check zero mean and unit variance after StandardScaler
    means = np.mean(X_train, axis=0)
    np.testing.assert_allclose(means, 0.0, atol=1e-3)

    X_test, ids_te = pipeline.transform(test_df)
    assert X_test.shape == (len(test_df), 321)


def test_fitness_predictor_training_and_saving(synthetic_df, tmp_path):
    pipeline = FeaturePipeline()
    X_train, _ = pipeline.fit_transform(synthetic_df)
    y_train = synthetic_df["activity_rel_to_parent"].values

    predictor = FitnessPredictor(config=PredictorConfig(model_type="ridge", alpha=1.0))
    predictor.fit(X_train, y_train, split_strategy="test_split")

    preds = predictor.predict(X_train)
    assert preds.shape == (len(synthetic_df),)
    assert not np.isnan(preds).any()

    # Save and reload
    save_path = predictor.save(output_dir=tmp_path / "models", model_tag="test_model")
    assert save_path.exists()

    new_predictor = FitnessPredictor()
    new_predictor.load(save_path)
    new_preds = new_predictor.predict(X_train)
    np.testing.assert_array_almost_equal(preds, new_preds)


def test_predictions_schema_enforcement():
    df_raw = pd.DataFrame({
        "variant_id": ["v1", "v2"],
        "prediction": [1.2, 0.8],
        "zero_shot_score": [-0.5, 0.2],
        "esm_log_likelihood_ratio": [-0.5, 0.2],
        "model_version": ["ridge_v1", "ridge_v1"],
    })
    canonical = enforce_predictions_schema(df_raw)
    assert list(canonical.columns) == PREDICTION_COLUMNS
    assert canonical["prediction"].dtype == "float64"

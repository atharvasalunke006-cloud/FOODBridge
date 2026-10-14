"""
Unit Tests for Machine Learning Demand Forecasting
===================================================
Tests all requirements:
1. Model artifacts existence and pipeline loading
2. Prediction on valid input features
3. Input validation and rejection of invalid/corrupt features
4. Chronological train/test split verification (no future leakage)
5. Comparison against baseline: model MAE <= baseline MAE
6. Surplus food distinction statement verification
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.forecasting import (
    load_forecast_pipeline,
    validate_prediction_inputs,
    predict_demand,
    get_model_evaluation_metrics,
)


class TestForecastingPipeline(unittest.TestCase):

    def setUp(self):
        self.valid_input = {
            "location": "North Campus Hub",
            "category": "Cooked Meals",
            "date": "2026-10-20",
            "base_price": 150.0,
            "discount_percent": 10.0,
            "is_promotion": 1,
        }

    def test_pipeline_artifacts_loaded(self):
        """Verifies that the fitted joblib pipeline and metadata load successfully."""
        pipeline, metadata = load_forecast_pipeline()
        self.assertIsNotNone(pipeline, "Trained pipeline should load from models/ directory")
        self.assertIsNotNone(metadata, "Model metadata should load from models/ directory")
        self.assertTrue(hasattr(pipeline, "predict"), "Loaded pipeline must implement predict()")

    def test_valid_prediction(self):
        """Verifies prediction returns positive order count, confidence interval, and metadata."""
        result = predict_demand(self.valid_input)
        self.assertTrue(result["success"], f"Prediction failed: {result.get('error')}")
        self.assertIsInstance(result["predicted_orders"], int)
        self.assertGreater(result["predicted_orders"], 0, "Predicted orders must be positive")

        # Confidence interval
        ci = result["confidence_interval"]
        self.assertIsInstance(ci, list)
        self.assertEqual(len(ci), 2)
        self.assertLessEqual(ci[0], result["predicted_orders"])
        self.assertGreaterEqual(ci[1], result["predicted_orders"])

    def test_invalid_date_format_rejected(self):
        """Input with unparseable date string must be rejected with helpful error."""
        bad_input = dict(self.valid_input, date="invalid-date-string")
        is_valid, error, _ = validate_prediction_inputs(bad_input)
        self.assertFalse(is_valid)
        self.assertIn("Invalid date format", error)

    def test_negative_discount_rejected(self):
        """Input with negative discount percentage must be rejected."""
        bad_input = dict(self.valid_input, discount_percent=-15.0)
        is_valid, error, _ = validate_prediction_inputs(bad_input)
        self.assertFalse(is_valid)
        self.assertIn("Discount percentage must be between", error)

    def test_negative_base_price_rejected(self):
        """Input with zero or negative base price must be rejected."""
        bad_input = dict(self.valid_input, base_price=-50.0)
        is_valid, error, _ = validate_prediction_inputs(bad_input)
        self.assertFalse(is_valid)
        self.assertIn("Base price must be greater than zero", error)

    def test_missing_location_rejected(self):
        """Input with empty or missing location must be rejected."""
        bad_input = dict(self.valid_input, location="")
        is_valid, error, _ = validate_prediction_inputs(bad_input)
        self.assertFalse(is_valid)
        self.assertIn("Missing or blank 'location'", error)

    def test_chronological_split_verified(self):
        """Verifies that the train date range strictly precedes the test date range in metadata."""
        metrics = get_model_evaluation_metrics()
        train_range = metrics.get("train_date_range", [])
        test_range = metrics.get("test_date_range", [])
        self.assertEqual(len(train_range), 2)
        self.assertEqual(len(test_range), 2)
        # Train end date must be before test start date
        self.assertLessEqual(train_range[1], test_range[0], "Train period must strictly precede test period to avoid leakage")

    def test_model_beats_baseline_mae(self):
        """Verifies that the trained regression model achieves a lower MAE than the simple mean baseline."""
        metrics = get_model_evaluation_metrics()
        perf = metrics.get("metrics", {})
        model_mae = perf.get("model_mae")
        baseline_mae = perf.get("baseline_mae")
        self.assertIsNotNone(model_mae)
        self.assertIsNotNone(baseline_mae)
        self.assertLess(model_mae, baseline_mae, "Trained RandomForest model must outperform Dummy baseline")
        self.assertGreater(perf.get("improvement_pct", 0), 0)

    def test_surplus_distinction_disclaimer(self):
        """Verifies that prediction output includes an explicit disclaimer distinguishing demand from surplus."""
        result = predict_demand(self.valid_input)
        self.assertTrue(result["success"])
        disclaimer = result.get("surplus_distinction")
        self.assertIsNotNone(disclaimer)
        self.assertIn("Predicted meal orders measure anticipated customer consumption", disclaimer)
        self.assertIn("Surplus food occurs only when prepared meal volume exceeds this demand", disclaimer)


if __name__ == "__main__":
    unittest.main()

"""
FoodBridge AI - Machine Learning Demand Forecasting Module
===========================================================
This module provides machine learning inference, input validation, and model
evaluation metrics for meal order demand forecasting.

Key Design Elements:
1. Supervised RandomForest Regression Pipeline (preprocessor + estimator)
2. Strict feature validation and rejection of corrupt/out-of-bounds inputs
3. Chronologically evaluated test metrics (MAE, RMSE, R²) against baseline
4. Critical academic disclaimer: Predicted orders measure customer consumption
   demand, NOT available surplus food.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from src.data_manager import load_demand_history

# Paths anchored to project root
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
MODEL_FILE = MODELS_DIR / "demand_forecast_model.joblib"
METADATA_FILE = MODELS_DIR / "model_metadata.json"

# Cached pipeline instance and metadata to avoid reloading on every query
_CACHED_PIPELINE = None
_CACHED_METADATA = None

EXPECTED_FEATURE_COLUMNS = [
    "location",
    "category",
    "day_of_week",
    "is_weekend",
    "month",
    "base_price",
    "discount_percent",
    "is_promotion",
]

KNOWN_LOCATIONS = [
    "North Campus Hub",
    "Downtown Station",
    "Tech Corridor Gate 2",
    "East Wing Plaza",
    "West Market Hub",
    "South City Center",
]

KNOWN_CATEGORIES = [
    "Cooked Meals",
    "Bakery",
    "Fresh Produce",
    "Packaged Goods",
    "Dairy",
]


def load_forecast_pipeline() -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
    """
    Loads the serialized scikit-learn pipeline and training metadata.
    Caches artifacts in memory for fast inference in Streamlit.
    """
    global _CACHED_PIPELINE, _CACHED_METADATA

    if _CACHED_PIPELINE is not None and _CACHED_METADATA is not None:
        return _CACHED_PIPELINE, _CACHED_METADATA

    if not MODEL_FILE.exists() or not METADATA_FILE.exists():
        # Fallback: auto-train model if deployed on a fresh instance without joblib artifact
        try:
            from train_model import train_demand_forecast_model
            train_demand_forecast_model()
        except Exception as e:
            print(f"Model file missing and auto-training failed: {e}")
            return None, None

    try:
        _CACHED_PIPELINE = joblib.load(MODEL_FILE)
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            _CACHED_METADATA = json.load(f)
        return _CACHED_PIPELINE, _CACHED_METADATA
    except Exception as e:
        print(f"Error loading trained forecast pipeline: {e}")
        return None, None


def validate_prediction_inputs(
    inputs: Dict[str, Any]
) -> Tuple[bool, Optional[str], Optional[pd.DataFrame]]:
    """
    Validates user/API inputs for meal demand prediction.

    Checks:
    1. Required fields presence: location, category, date (or day_of_week/month).
    2. Date format: YYYY-MM-DD, automatically computing day_of_week, is_weekend, and month.
    3. Location: non-empty string.
    4. Category: non-empty string.
    5. base_price: strictly positive number (> 0).
    6. discount_percent: 0.0 <= discount_percent <= 100.0.
    7. is_promotion: boolean or 0/1.

    Returns:
        Tuple[bool, Optional[str], Optional[pd.DataFrame]]: (is_valid, error_msg, validated_df)
    """
    if not isinstance(inputs, dict):
        return False, "Prediction inputs must be provided as a dictionary.", None

    # Check 1: Location validation
    location = inputs.get("location")
    if not location or not str(location).strip():
        return False, "Missing or blank 'location'. Please select a valid campus/city zone.", None
    location_str = str(location).strip()

    # Check 2: Category validation
    category = inputs.get("category")
    if not category or not str(category).strip():
        return False, "Missing or blank 'category'. Please select a valid food category.", None
    category_str = str(category).strip()

    # Check 3: Date & Calendar feature extraction
    date_val = inputs.get("date")
    if date_val is not None:
        try:
            if isinstance(date_val, str):
                dt = datetime.strptime(date_val.strip(), "%Y-%m-%d")
            elif isinstance(date_val, datetime):
                dt = date_val
            elif hasattr(date_val, "strftime"):
                dt = datetime.strptime(date_val.strftime("%Y-%m-%d"), "%Y-%m-%d")
            else:
                return False, f"Invalid date type '{type(date_val).__name__}'. Expected 'YYYY-MM-DD' string.", None

            day_of_week = dt.weekday()
            is_weekend = 1 if day_of_week in (5, 6) else 0
            month = dt.month
        except ValueError:
            return False, f"Invalid date format '{date_val}'. Expected format is 'YYYY-MM-DD'.", None
    else:
        # Fallback to direct numeric day/month if date is not passed
        try:
            day_of_week = int(inputs.get("day_of_week", 0))
            if not (0 <= day_of_week <= 6):
                return False, f"Invalid 'day_of_week' ({day_of_week}). Must be between 0 (Mon) and 6 (Sun).", None
            is_weekend = 1 if day_of_week in (5, 6) else 0
            month = int(inputs.get("month", 10))
            if not (1 <= month <= 12):
                return False, f"Invalid 'month' ({month}). Must be between 1 and 12.", None
        except (ValueError, TypeError):
            return False, "Missing valid 'date' or numeric calendar features.", None

    # Check 4: Base price validation
    base_price = inputs.get("base_price", 120.0)
    try:
        base_price_val = float(base_price)
        if base_price_val <= 0:
            return False, f"Base price must be greater than zero. Received: {base_price_val}", None
    except (ValueError, TypeError):
        return False, f"Invalid base price '{base_price}'. Must be a positive numeric value.", None

    # Check 5: Discount percentage validation
    discount_pct = inputs.get("discount_percent", 0.0)
    try:
        discount_val = float(discount_pct)
        if discount_val < 0.0 or discount_val > 100.0:
            return False, f"Discount percentage must be between 0.0 and 100.0. Received: {discount_val}%", None
    except (ValueError, TypeError):
        return False, f"Invalid discount percentage '{discount_pct}'. Must be a valid number.", None

    # Check 6: Promotion flag validation
    is_promo = inputs.get("is_promotion", 0)
    try:
        if isinstance(is_promo, bool):
            promo_val = 1 if is_promo else 0
        else:
            promo_val = int(is_promo)
            if promo_val not in (0, 1):
                return False, f"Invalid 'is_promotion' ({is_promo}). Must be 0, 1, or boolean.", None
    except (ValueError, TypeError):
        return False, f"Invalid 'is_promotion' value '{is_promo}'. Expected 0, 1, or boolean.", None

    # Construct validated DataFrame matching pipeline input schema
    row_dict = {
        "location": location_str,
        "category": category_str,
        "day_of_week": int(day_of_week),
        "is_weekend": int(is_weekend),
        "month": int(month),
        "base_price": float(base_price_val),
        "discount_percent": float(discount_val),
        "is_promotion": int(promo_val),
    }

    df_validated = pd.DataFrame([row_dict], columns=EXPECTED_FEATURE_COLUMNS)
    return True, None, df_validated


def predict_demand(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predicts expected meal orders for a specific canteen/hub scenario using
    the fitted scikit-learn RandomForest regression pipeline.

    Returns:
        dict:
            - success (bool)
            - error (str or None)
            - predicted_orders (int)
            - confidence_interval (Tuple[int, int])
            - input_summary (dict)
            - metrics (dict)
            - surplus_distinction (str)
    """
    is_valid, error_msg, df_input = validate_prediction_inputs(inputs)
    if not is_valid:
        return {
            "success": False,
            "error": error_msg,
            "predicted_orders": None,
            "confidence_interval": None,
            "surplus_distinction": None,
        }

    pipeline, metadata = load_forecast_pipeline()
    if pipeline is None:
        return {
            "success": False,
            "error": "Trained ML model not found. Please run 'python train_model.py' to fit the model.",
            "predicted_orders": None,
            "confidence_interval": None,
            "surplus_distinction": None,
        }

    try:
        raw_pred = pipeline.predict(df_input)[0]
        predicted_orders = int(max(0, round(raw_pred)))

        # Use test RMSE or MAE from metadata for prediction uncertainty intervals
        metrics = metadata.get("metrics", {}) if metadata else {}
        rmse = float(metrics.get("test_rmse", 12.8))
        mae = float(metrics.get("model_mae", 10.3))

        lower_bound = int(max(0, round(predicted_orders - (1.96 * rmse))))
        upper_bound = int(round(predicted_orders + (1.96 * rmse)))

        return {
            "success": True,
            "error": None,
            "predicted_orders": predicted_orders,
            "confidence_interval": [lower_bound, upper_bound],
            "estimated_uncertainty_mae": round(mae, 1),
            "input_features": df_input.iloc[0].to_dict(),
            "model_metadata": {
                "model_name": metadata.get("model_name", "RandomForestRegressor"),
                "dataset_type": metadata.get("dataset_type", "Synthetic Development Dataset"),
                "model_mae": metrics.get("model_mae"),
                "baseline_mae": metrics.get("baseline_mae"),
                "improvement_pct": metrics.get("improvement_pct"),
            },
            "surplus_distinction": (
                "CRITICAL DISTINCTION: Predicted meal orders measure anticipated customer consumption. "
                "Surplus food occurs only when prepared meal volume exceeds this demand (Surplus = max(0, Prepared - Consumed))."
            ),
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Model inference error: {str(e)}",
            "predicted_orders": None,
            "confidence_interval": None,
            "surplus_distinction": None,
        }


def get_model_evaluation_metrics() -> Dict[str, Any]:
    """
    Returns stored model performance metrics and chronological test comparison points.
    """
    _, metadata = load_forecast_pipeline()
    if metadata:
        return metadata

    return {
        "model_name": "Not Trained",
        "dataset_type": "N/A",
        "metrics": {
            "model_mae": None,
            "baseline_mae": None,
            "improvement_pct": None,
        },
        "daily_test_comparison": [],
        "limitations": [
            "Model artifacts not found in models/ directory. Run train_model.py to initialize."
        ],
    }


# -----------------------------------------------------------------------------
# BACKWARDS-COMPATIBILITY ADAPTERS (Preserves existing UI and basic tests)
# -----------------------------------------------------------------------------
def get_historical_demand_summary() -> Dict[str, Any]:
    """
    Computes overall demand metrics from data/demand_history.csv.
    """
    df = load_demand_history()
    if df.empty:
        return {
            "total_meals_demanded": 0,
            "total_meals_supplied": 0,
            "fulfillment_rate": 0.0,
            "top_demand_zone": "N/A",
            "historical_df": df,
        }

    total_demanded = int(df["meals_demanded"].sum())
    total_supplied = int(df["meals_supplied"].sum())
    fulfillment_rate = round((total_supplied / total_demanded * 100), 1) if total_demanded > 0 else 0.0

    zone_sums = df.groupby("location")["meals_demanded"].sum().sort_values(ascending=False)
    top_zone = zone_sums.index[0] if not zone_sums.empty else "N/A"

    return {
        "total_meals_demanded": total_demanded,
        "total_meals_supplied": total_supplied,
        "fulfillment_rate": fulfillment_rate,
        "top_demand_zone": top_zone,
        "historical_df": df,
    }


def generate_placeholder_forecast(horizon_days: int = 7) -> pd.DataFrame:
    """
    Generates a simple 7-day projected baseline for visualization.
    Maintained for backwards-compatibility with test_basic.py.
    """
    df = load_demand_history()

    if not df.empty and "date" in df.columns:
        last_date = pd.to_datetime(df["date"]).max()
        if pd.isna(last_date):
            last_date = datetime.now()
    else:
        last_date = datetime.now()

    if not df.empty and "meals_demanded" in df.columns:
        daily_grouped = df.groupby("date")["meals_demanded"].sum()
        baseline_avg = float(daily_grouped.mean()) if not daily_grouped.empty else 250.0
    else:
        baseline_avg = 250.0

    future_dates = [(last_date + timedelta(days=i + 1)).strftime("%Y-%m-%d") for i in range(horizon_days)]

    np.random.seed(42)
    projections = []
    for i, date_str in enumerate(future_dates):
        variation = int(np.sin(i) * 20) + int(np.random.randint(-15, 15))
        predicted = max(100, int(baseline_avg + variation))
        lower_bound = max(50, predicted - 25)
        upper_bound = predicted + 30

        projections.append({
            "forecast_date": date_str,
            "predicted_demand_meals": predicted,
            "lower_bound_estimate": lower_bound,
            "upper_bound_estimate": upper_bound,
            "model_type": "Baseline Average",
        })

    return pd.DataFrame(projections)


def get_forecasting_model_status() -> Dict[str, Any]:
    """
    Returns updated metadata about the active ML model.
    """
    pipeline, metadata = load_forecast_pipeline()
    if pipeline is not None and metadata is not None:
        return {
            "status": "TRAINED_MODEL_ACTIVE",
            "model_name": metadata.get("model_name"),
            "dataset_type": metadata.get("dataset_type"),
            "model_mae": metadata.get("metrics", {}).get("model_mae"),
            "baseline_mae": metadata.get("metrics", {}).get("baseline_mae"),
            "improvement_pct": metadata.get("metrics", {}).get("improvement_pct"),
            "test_r2": metadata.get("metrics", {}).get("test_r2"),
            "features": metadata.get("features"),
        }

    return {
        "status": "MODEL_PENDING",
        "notice": "Run 'python train_model.py' to fit the regression model.",
    }

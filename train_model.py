"""
FoodBridge AI - Machine Learning Model Training Pipeline
=========================================================
Trains a supervised regression pipeline to forecast meal demand (num_orders)
using historical patterns, calendar features, pricing, and location baselines.

Key Engineering Features:
1. Chronological Train/Test Split (prevents future-to-past data leakage).
2. Transparent Baseline Comparison (evaluates against scikit-learn DummyRegressor).
3. End-to-end ColumnTransformer + Regressor Pipeline saved via joblib.
4. Support for public benchmark datasets if provided, with clearly labeled synthetic fallback.
5. Strict academic disclaimer: predicted orders represent demand, NOT food surplus.

Usage:
------
    python train_model.py
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Resolve paths relative to project root
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

PUBLIC_DATASET_FILE = DATA_DIR / "food_demand_public.csv"
SYNTHETIC_DATASET_FILE = DATA_DIR / "synthetic_food_demand.csv"
MODEL_OUTPUT_FILE = MODELS_DIR / "demand_forecast_model.joblib"
METADATA_OUTPUT_FILE = MODELS_DIR / "model_metadata.json"

CATEGORICAL_FEATURES = ["location", "category"]
NUMERICAL_FEATURES = [
    "day_of_week",
    "is_weekend",
    "month",
    "base_price",
    "discount_percent",
    "is_promotion",
]
ALL_FEATURES = CATEGORICAL_FEATURES + NUMERICAL_FEATURES
TARGET_COLUMN = "num_orders"


def generate_synthetic_demand_dataset(output_path: Path) -> pd.DataFrame:
    """
    Generates a realistic, clearly documented synthetic dataset simulating
    daily campus food demand across 14 months (2025-08-01 to 2026-10-14).

    Documented Patterns:
    - Weekly Seasonality: Weekdays see high campus traffic; weekends drop ~45%.
    - Location Heterogeneity: North Campus Hub and Downtown have higher base footfall.
    - Price & Promotion Elasticity: Discounts and promotions boost order volume.
    - Category Dynamics: Cooked meals represent high-volume staples.
    """
    print("Generating synthetic food demand dataset for development...")
    np.random.seed(42)

    locations = [
        ("North Campus Hub", 60),
        ("Downtown Station", 40),
        ("Tech Corridor Gate 2", 30),
        ("East Wing Plaza", 10),
        ("West Market Hub", -10),
        ("South City Center", -20),
    ]

    categories = [
        ("Cooked Meals", 65, 150.0),
        ("Bakery", 25, 90.0),
        ("Fresh Produce", 10, 110.0),
        ("Packaged Goods", -10, 80.0),
        ("Dairy", -5, 70.0),
    ]

    start_date = datetime(2025, 8, 1)
    end_date = datetime(2026, 10, 14)
    num_days = (end_date - start_date).days + 1

    records = []
    record_id = 10001

    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")
        day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
        is_weekend = 1 if day_of_week in (5, 6) else 0
        month = current_date.month
        week = current_date.isocalendar()[1]

        # Day of week multiplier (Mid-week peak Tue-Thu, weekend drop)
        dow_factor = {0: 1.05, 1: 1.15, 2: 1.20, 3: 1.15, 4: 1.10, 5: 0.55, 6: 0.50}[day_of_week]

        for loc_name, loc_boost in locations:
            for cat_name, cat_boost, base_p in categories:
                # Promotion occurs randomly ~15% of the time
                is_promo = 1 if np.random.rand() < 0.15 else 0
                discount_pct = float(np.random.choice([0.0, 5.0, 10.0, 15.0, 20.0, 25.0]) if is_promo else 0.0)

                # Base demand baseline calculation
                base_demand = 130.0 + loc_boost + cat_boost
                demand = base_demand * dow_factor

                # Promotional elasticity
                if is_promo:
                    demand *= (1.0 + (discount_pct * 0.012) + 0.15)

                # Gaussian noise
                noise = np.random.normal(0, 12)
                final_orders = int(max(15, round(demand + noise)))

                records.append({
                    "record_id": record_id,
                    "date": date_str,
                    "week": week,
                    "month": month,
                    "day_of_week": day_of_week,
                    "is_weekend": is_weekend,
                    "location": loc_name,
                    "category": cat_name,
                    "base_price": base_p,
                    "discount_percent": discount_pct,
                    "is_promotion": is_promo,
                    "num_orders": final_orders,
                })
                record_id += 1

    df = pd.DataFrame(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Synthetic dataset created successfully: {len(df):,} records saved to {output_path}")
    return df


def load_training_data() -> Tuple[pd.DataFrame, str]:
    """
    Inspects and loads dataset.
    Prioritizes real public benchmark if present, otherwise uses synthetic dataset.
    """
    if PUBLIC_DATASET_FILE.exists():
        print(f"Found real public dataset at: {PUBLIC_DATASET_FILE}")
        df = pd.read_csv(PUBLIC_DATASET_FILE, encoding="utf-8")
        dataset_type = "Public Benchmark Dataset"
    elif SYNTHETIC_DATASET_FILE.exists():
        print(f"Loading existing synthetic dataset from: {SYNTHETIC_DATASET_FILE}")
        df = pd.read_csv(SYNTHETIC_DATASET_FILE, encoding="utf-8")
        dataset_type = "Synthetic Development Dataset"
    else:
        print("No existing dataset found. Creating synthetic dataset...")
        df = generate_synthetic_demand_dataset(SYNTHETIC_DATASET_FILE)
        dataset_type = "Synthetic Development Dataset"

    # Standardize column naming if meals_demanded was used
    if TARGET_COLUMN not in df.columns and "meals_demanded" in df.columns:
        df[TARGET_COLUMN] = df["meals_demanded"]

    # Ensure required feature columns exist
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        if "day_of_week" not in df.columns:
            df["day_of_week"] = df["date"].dt.dayofweek
        if "is_weekend" not in df.columns:
            df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
        if "month" not in df.columns:
            df["month"] = df["date"].dt.month

    for col in NUMERICAL_FEATURES:
        if col not in df.columns:
            df[col] = 0.0

    return df, dataset_type


def train_demand_forecast_model() -> Dict[str, Any]:
    """
    Executes the training and validation workflow:
    1. Loads data.
    2. Sorts chronologically and splits into Train (earlier 80%) and Test (later 20%).
    3. Fits a scikit-learn Pipeline (OneHotEncoder + StandardScaler + RandomForestRegressor).
    4. Evaluates against a scikit-learn DummyRegressor baseline.
    5. Saves pipeline to models/demand_forecast_model.joblib.
    6. Saves metadata to models/model_metadata.json.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    df, dataset_type = load_training_data()

    # 1. Sort strictly by date to preserve temporal causality
    if "date" in df.columns:
        df = df.sort_values(by="date").reset_index(drop=True)

    # 2. Chronological Train/Test Split (80% train, 20% test)
    # Strictly avoiding random shuffle to prevent future data leakage
    split_idx = int(len(df) * 0.80)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    X_train = train_df[ALL_FEATURES]
    y_train = train_df[TARGET_COLUMN].values

    X_test = test_df[ALL_FEATURES]
    y_test = test_df[TARGET_COLUMN].values

    train_start_date = str(train_df["date"].min().strftime("%Y-%m-%d")) if "date" in train_df.columns else "N/A"
    train_end_date = str(train_df["date"].max().strftime("%Y-%m-%d")) if "date" in train_df.columns else "N/A"
    test_start_date = str(test_df["date"].min().strftime("%Y-%m-%d")) if "date" in test_df.columns else "N/A"
    test_end_date = str(test_df["date"].max().strftime("%Y-%m-%d")) if "date" in test_df.columns else "N/A"

    print(f"\n--- Chronological Split Overview ---")
    print(f"Train Set: {len(X_train):,} samples ({train_start_date} to {train_end_date})")
    print(f"Test Set:  {len(X_test):,} samples ({test_start_date} to {test_end_date})")

    # 3. Build scikit-learn Preprocessing & Modeling Pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
            ("num", StandardScaler(), NUMERICAL_FEATURES),
        ]
    )

    rf_regressor = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", rf_regressor),
        ]
    )

    # 4. Train Dummy Baseline Model
    baseline_model = DummyRegressor(strategy="mean")
    baseline_model.fit(X_train, y_train)
    y_baseline_pred = baseline_model.predict(X_test)
    baseline_mae = float(mean_absolute_error(y_test, y_baseline_pred))

    # 5. Train Supervised ML Pipeline
    print("\nFitting RandomForest regression pipeline on training data...")
    pipeline.fit(X_train, y_train)
    y_model_pred = pipeline.predict(X_test)

    # 6. Evaluation Metrics on Held-Out Test Data
    model_mae = float(mean_absolute_error(y_test, y_model_pred))
    model_rmse = float(np.sqrt(mean_squared_error(y_test, y_model_pred)))
    model_r2 = float(r2_score(y_test, y_model_pred))
    improvement_pct = round(((baseline_mae - model_mae) / baseline_mae) * 100.0, 2)

    print("\n================ EVALUATION RESULTS ================")
    print(f"Dataset Provenance:   {dataset_type}")
    print(f"Baseline MAE (Mean):  {baseline_mae:.2f} orders")
    print(f"RandomForest MAE:     {model_mae:.2f} orders")
    print(f"Error Reduction:      {improvement_pct:.2f}% better than baseline")
    print(f"Test RMSE:            {model_rmse:.2f} orders")
    print(f"Test R² Score:        {model_r2:.4f}")
    print("====================================================")

    # 7. Serialize Pipeline Artifacts
    joblib.dump(pipeline, MODEL_OUTPUT_FILE)
    print(f"\nSaved trained pipeline to: {MODEL_OUTPUT_FILE}")

    # 8. Prepare Test Comparison Points for UI Plotly Chart
    # Sample daily aggregate comparison on test set
    test_eval_df = test_df.copy()
    test_eval_df["predicted_num_orders"] = np.round(y_model_pred).astype(int)

    # Group daily totals for charting
    daily_comparison = (
        test_eval_df.groupby("date")[["num_orders", "predicted_num_orders"]]
        .sum()
        .reset_index()
    )
    daily_comparison["date"] = daily_comparison["date"].dt.strftime("%Y-%m-%d")

    # Prepare metadata dictionary
    metadata = {
        "model_name": "RandomForestRegressor_FoodDemand",
        "training_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_type": dataset_type,
        "dataset_provenance": (
            "Public Benchmark Dataset"
            if dataset_type == "Public Benchmark Dataset"
            else "Generated synthetic simulation modeling campus food service demand patterns."
        ),
        "target_variable": TARGET_COLUMN,
        "features": ALL_FEATURES,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "train_date_range": [train_start_date, train_end_date],
        "test_date_range": [test_start_date, test_end_date],
        "metrics": {
            "model_mae": round(model_mae, 2),
            "baseline_mae": round(baseline_mae, 2),
            "improvement_pct": improvement_pct,
            "test_rmse": round(model_rmse, 2),
            "test_r2": round(model_r2, 4),
        },
        "daily_test_comparison": daily_comparison.to_dict(orient="records"),
        "limitations": [
            "Dataset is synthetic: real-world demand includes unmodeled external shocks (e.g., campus strikes, heavy storms).",
            "Predicted orders represent consumption demand, NOT available surplus food.",
            "Surplus food occurs only when prepared meal volume exceeds actual consumption demand.",
        ],
    }

    with open(METADATA_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved model metadata to: {METADATA_OUTPUT_FILE}")
    return metadata


if __name__ == "__main__":
    train_demand_forecast_model()

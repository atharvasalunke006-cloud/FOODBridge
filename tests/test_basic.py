"""
Basic tests for FoodBridge AI core modules.
Verifies data loading, metrics calculation, matching placeholder, and forecast generator.
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path for robust imports across all operating systems
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd

from src.data_manager import (
    load_donations,
    load_recipients,
    load_demand_history,
    get_summary_metrics,
    save_donation,
)
from src.matching import get_available_recipients, rule_based_candidate_filter
from src.forecasting import get_historical_demand_summary, generate_placeholder_forecast


class TestFoodBridgeCore(unittest.TestCase):

    def test_load_donations(self):
        df = load_donations()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty, "Donations dataset should not be empty")
        self.assertIn("donation_id", df.columns)
        self.assertIn("quantity_meals", df.columns)

    def test_load_recipients(self):
        df = load_recipients()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty, "Recipients dataset should not be empty")
        self.assertIn("recipient_id", df.columns)
        self.assertIn("needed_meals", df.columns)

    def test_load_demand_history(self):
        df = load_demand_history()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty, "Demand history dataset should not be empty")
        self.assertIn("meals_demanded", df.columns)

    def test_summary_metrics(self):
        metrics = get_summary_metrics()
        self.assertIn("total_donations", metrics)
        self.assertIn("total_meals", metrics)
        self.assertIn("meals_matched", metrics)
        self.assertIn("pending_donations", metrics)
        self.assertGreater(metrics["total_donations"], 0)
        self.assertGreater(metrics["total_meals"], 0)

    def test_save_donation_validation(self):
        # Blank donor name should fail
        success, msg = save_donation("", "Bread", "Bakery", 20, "Downtown", "2026-10-14 10:00", "2026-10-14 12:00")
        self.assertFalse(success)
        self.assertIn("Donor name", msg)

        # Non-positive meals should fail
        success, msg = save_donation("Test Cafe", "Bread", "Bakery", 0, "Downtown", "2026-10-14 10:00", "2026-10-14 12:00")
        self.assertFalse(success)
        self.assertIn("greater than 0", msg)

    def test_matching_prototype(self):
        recipients = get_available_recipients()
        self.assertFalse(recipients.empty)
        candidates = rule_based_candidate_filter("Cooked Meals", "Downtown Station", 50)
        self.assertIsInstance(candidates, pd.DataFrame)
        self.assertFalse(candidates.empty)

    def test_forecasting_prototype(self):
        summary = get_historical_demand_summary()
        self.assertGreater(summary["total_meals_demanded"], 0)
        forecast = generate_placeholder_forecast(7)
        self.assertEqual(len(forecast), 7)
        self.assertIn("predicted_demand_meals", forecast.columns)

    def test_plotly_palettes(self):
        import plotly.express as px
        # Verify that color palettes used in app.py exist without AttributeError
        self.assertTrue(hasattr(px.colors.sequential, "Tealgrn"))
        self.assertTrue(hasattr(px.colors.qualitative, "Prism"))


if __name__ == "__main__":
    unittest.main()

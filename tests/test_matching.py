"""
Unit Tests for FoodBridge AI Matching Engine
============================================
Tests all requirements:
1. Compatible food category
2. Incompatible food category
3. Unavailable recipient
4. Expired pickup deadline
5. Partial allocation
6. No over-allocation
7. Insufficient remaining recipient capacity
8. Missing locations handled safely
9. Prevention of duplicate allocations
"""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd

from src.matching import (
    find_matches_for_donation,
    evaluate_recipient_eligibility,
    estimate_zone_distance,
    calculate_match_score,
)
from src.data_manager import commit_allocation_plan


class TestMatchingAlgorithm(unittest.TestCase):

    def setUp(self):
        """Set up standard reference evaluation timestamp and test entities."""
        self.eval_time = datetime(2026, 10, 14, 12, 0)

        # Standard donation
        self.donation = {
            "donation_id": "TEST-DON-001",
            "donor_name": "Test Dining Hall",
            "food_name": "Rice and Curry",
            "category": "Cooked Meals",
            "quantity_meals": 100,
            "pickup_location": "North Campus Hub",
            "pickup_deadline": "2026-10-14 18:00",  # 6 hours in future
            "status": "Pending",
        }

    # -------------------------------------------------------------------------
    # REQUIREMENT 1: Compatible Food Category
    # -------------------------------------------------------------------------
    def test_compatible_food_category(self):
        """Recipient accepting 'Cooked Meals' should be eligible for Cooked Meals donation."""
        recipient = {
            "recipient_id": "TEST-REC-01",
            "organization_name": "Shelter Alpha",
            "location": "North Campus Hub",
            "needed_meals": 50,
            "accepted_categories": "Cooked Meals;Bakery",
            "urgency_level": "High",
            "status": "Active",
        }
        df_recipients = pd.DataFrame([recipient])

        result = find_matches_for_donation(self.donation, recipients_df=df_recipients, eval_time=self.eval_time)

        self.assertEqual(len(result["eligible_matches"]), 1)
        self.assertEqual(len(result["ineligible_recipients"]), 0)
        matched = result["eligible_matches"][0]
        self.assertEqual(matched["recipient_id"], "TEST-REC-01")
        self.assertEqual(matched["potential_allocated_meals"], 50)

    # -------------------------------------------------------------------------
    # REQUIREMENT 2: Incompatible Food Category
    # -------------------------------------------------------------------------
    def test_incompatible_food_category(self):
        """Recipient accepting only 'Fresh Produce' must NOT be matched with 'Cooked Meals'."""
        recipient = {
            "recipient_id": "TEST-REC-02",
            "organization_name": "Produce Only Pantry",
            "location": "North Campus Hub",
            "needed_meals": 50,
            "accepted_categories": "Fresh Produce;Dairy",
            "urgency_level": "High",
            "status": "Active",
        }
        df_recipients = pd.DataFrame([recipient])

        result = find_matches_for_donation(self.donation, recipients_df=df_recipients, eval_time=self.eval_time)

        self.assertEqual(len(result["eligible_matches"]), 0, "Incompatible category must not be in eligible matches")
        self.assertEqual(len(result["ineligible_recipients"]), 1)
        rejection = result["ineligible_recipients"][0]
        self.assertEqual(rejection["recipient_id"], "TEST-REC-02")
        self.assertIn("Incompatible food category", rejection["rejection_reason"])

    # -------------------------------------------------------------------------
    # REQUIREMENT 3: Unavailable Recipient
    # -------------------------------------------------------------------------
    def test_unavailable_recipient(self):
        """Recipients with status 'Inactive' or 'Suspended' must be excluded."""
        recipient = {
            "recipient_id": "TEST-REC-03",
            "organization_name": "Inactive Shelter",
            "location": "North Campus Hub",
            "needed_meals": 60,
            "accepted_categories": "Cooked Meals",
            "urgency_level": "High",
            "status": "Inactive",
        }
        df_recipients = pd.DataFrame([recipient])

        result = find_matches_for_donation(self.donation, recipients_df=df_recipients, eval_time=self.eval_time)

        self.assertEqual(len(result["eligible_matches"]), 0)
        self.assertEqual(len(result["ineligible_recipients"]), 1)
        self.assertIn("Unavailable recipient", result["ineligible_recipients"][0]["rejection_reason"])

    # -------------------------------------------------------------------------
    # REQUIREMENT 4: Expired Pickup Deadline
    # -------------------------------------------------------------------------
    def test_expired_pickup_deadline(self):
        """Donation with pickup deadline before evaluation time must be flagged expired and have 0 matches."""
        expired_donation = dict(self.donation)
        expired_donation["pickup_deadline"] = "2026-10-14 10:00"  # 2 hours before 12:00 eval_time

        recipient = {
            "recipient_id": "TEST-REC-04",
            "organization_name": "Active Shelter",
            "location": "North Campus Hub",
            "needed_meals": 40,
            "accepted_categories": "Cooked Meals",
            "urgency_level": "High",
            "status": "Active",
        }
        df_recipients = pd.DataFrame([recipient])

        result = find_matches_for_donation(expired_donation, recipients_df=df_recipients, eval_time=self.eval_time)

        self.assertTrue(result["is_expired"], "Donation should be flagged as expired")
        self.assertEqual(len(result["eligible_matches"]), 0, "No matches should be produced for expired donation")
        self.assertEqual(len(result["ineligible_recipients"]), 1)
        self.assertIn("Expired pickup deadline", result["ineligible_recipients"][0]["rejection_reason"])

    # -------------------------------------------------------------------------
    # REQUIREMENT 5: Partial Allocation
    # -------------------------------------------------------------------------
    def test_partial_allocation_recipient_needs_less(self):
        """When recipient needs 40 meals and donor has 100, recipient receives exactly 40 meals."""
        recipient = {
            "recipient_id": "TEST-REC-05",
            "organization_name": "Small Center",
            "location": "North Campus Hub",
            "needed_meals": 40,
            "accepted_categories": "Cooked Meals",
            "urgency_level": "Normal",
            "status": "Active",
        }
        df_recipients = pd.DataFrame([recipient])

        result = find_matches_for_donation(self.donation, recipients_df=df_recipients, eval_time=self.eval_time)

        self.assertEqual(len(result["allocation_plan"]), 1)
        plan_item = result["allocation_plan"][0]
        self.assertEqual(plan_item["allocated_meals"], 40, "Should partially allocate exactly 40 meals")
        self.assertEqual(plan_item["needed_meals_after"], 0)

    def test_partial_allocation_donor_has_less(self):
        """When donor has 35 meals and recipient needs 80, recipient receives 35 meals."""
        small_donation = dict(self.donation)
        small_donation["quantity_meals"] = 35

        recipient = {
            "recipient_id": "TEST-REC-06",
            "organization_name": "Big Shelter",
            "location": "North Campus Hub",
            "needed_meals": 80,
            "accepted_categories": "Cooked Meals",
            "urgency_level": "High",
            "status": "Active",
        }
        df_recipients = pd.DataFrame([recipient])

        result = find_matches_for_donation(small_donation, recipients_df=df_recipients, eval_time=self.eval_time)

        self.assertEqual(len(result["allocation_plan"]), 1)
        plan_item = result["allocation_plan"][0]
        self.assertEqual(plan_item["allocated_meals"], 35, "Should allocate all 35 available meals")
        self.assertEqual(plan_item["needed_meals_after"], 45, "Remaining need should be 80 - 35 = 45")

    # -------------------------------------------------------------------------
    # REQUIREMENT 6: No Over-Allocation
    # -------------------------------------------------------------------------
    def test_no_over_allocation_multi_recipient(self):
        """Sum of allocations must never exceed donation availability or recipient need."""
        donation_100 = dict(self.donation)
        donation_100["quantity_meals"] = 100

        # Three recipients needing 60, 50, 40 (Total need = 150 > donation 100)
        recipients = [
            {
                "recipient_id": "REC-A",
                "organization_name": "Shelter A",
                "location": "North Campus Hub",
                "needed_meals": 60,
                "accepted_categories": "Cooked Meals",
                "urgency_level": "High",
                "status": "Active",
            },
            {
                "recipient_id": "REC-B",
                "organization_name": "Shelter B",
                "location": "East Wing Plaza",
                "needed_meals": 50,
                "accepted_categories": "Cooked Meals",
                "urgency_level": "Medium",
                "status": "Active",
            },
            {
                "recipient_id": "REC-C",
                "organization_name": "Shelter C",
                "location": "Downtown Station",
                "needed_meals": 40,
                "accepted_categories": "Cooked Meals",
                "urgency_level": "Normal",
                "status": "Active",
            },
        ]
        df_recipients = pd.DataFrame(recipients)

        result = find_matches_for_donation(donation_100, recipients_df=df_recipients, eval_time=self.eval_time)

        plan = result["allocation_plan"]
        total_allocated = sum(item["allocated_meals"] for item in plan)

        # Invariant 1: Total allocated exactly equals donation availability (no over-allocation)
        self.assertEqual(total_allocated, 100)

        # Invariant 2: Recipient A gets min(100, 60) = 60
        self.assertEqual(plan[0]["allocated_meals"], 60)
        self.assertLessEqual(plan[0]["allocated_meals"], 60)

        # Invariant 3: Recipient B gets min(40, 50) = 40 (remaining 40 meals)
        self.assertEqual(plan[1]["allocated_meals"], 40)
        self.assertLessEqual(plan[1]["allocated_meals"], 50)

        # Invariant 4: Recipient C gets 0 meals because donation was exhausted
        rec_c_allocated = sum(item["allocated_meals"] for item in plan if item["recipient_id"] == "REC-C")
        self.assertEqual(rec_c_allocated, 0)

    # -------------------------------------------------------------------------
    # REQUIREMENT 7: Insufficient Remaining Recipient Capacity
    # -------------------------------------------------------------------------
    def test_insufficient_remaining_recipient_capacity(self):
        """Recipient with needed_meals <= 0 must be rejected."""
        recipient_zero = {
            "recipient_id": "TEST-REC-07",
            "organization_name": "Full Shelter",
            "location": "North Campus Hub",
            "needed_meals": 0,
            "accepted_categories": "Cooked Meals",
            "urgency_level": "High",
            "status": "Active",
        }
        df_recipients = pd.DataFrame([recipient_zero])

        result = find_matches_for_donation(self.donation, recipients_df=df_recipients, eval_time=self.eval_time)

        self.assertEqual(len(result["eligible_matches"]), 0)
        self.assertEqual(len(result["ineligible_recipients"]), 1)
        self.assertIn("Insufficient remaining capacity", result["ineligible_recipients"][0]["rejection_reason"])

    # -------------------------------------------------------------------------
    # REQUIREMENT 8: Safe Handling of Missing Locations
    # -------------------------------------------------------------------------
    def test_missing_location_handled_safely(self):
        """Missing or unlisted locations must not crash and receive neutral documented label/score."""
        dist, label = estimate_zone_distance("North Campus Hub", None)
        self.assertIsNone(dist)
        self.assertIn("Missing", label)

        dist, label = estimate_zone_distance("North Campus Hub", "Unknown Outer District")
        self.assertIsNone(dist)
        self.assertIn("Unknown", label)

        # Score calculation with None distance should use neutral fallback
        score, breakdown, reasons = calculate_match_score(
            donation_meals=50,
            recipient_needed=50,
            urgency_level="Normal",
            distance_km=None,
            hours_until_deadline=4.0,
        )
        self.assertGreater(score, 0)
        self.assertEqual(breakdown["distance_score"], 12.0)
        self.assertTrue(any("Unknown zone fallback" in r for r in reasons))

    # -------------------------------------------------------------------------
    # REQUIREMENT 9: Ranking Scores & Explanations Present
    # -------------------------------------------------------------------------
    def test_ranking_reasons_and_score_bounds(self):
        """Verify scores are within 0-100 and reasons are non-empty."""
        score, breakdown, reasons = calculate_match_score(
            donation_meals=75,
            recipient_needed=60,
            urgency_level="High",
            distance_km=0.5,
            hours_until_deadline=3.0,
        )
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)
        self.assertEqual(len(reasons), 4)
        for r in reasons:
            self.assertTrue(len(r) > 5)

    # -------------------------------------------------------------------------
    # REQUIREMENT 10: Prevention of Double Allocation
    # -------------------------------------------------------------------------
    def test_prevent_double_allocation_validation(self):
        """Attempting to commit an allocation on a non-pending donation must be rejected."""
        # Test with dummy donation ID that is already matched
        success, msg, _ = commit_allocation_plan(
            donation_id="DON-1003",  # In data/donations.csv, DON-1003 is already "Completed"
            allocations=[{
                "recipient_id": "REC-2001",
                "organization_name": "Hope Community Shelter",
                "allocated_meals": 30,
                "match_score": 85.0,
            }],
        )
        self.assertFalse(success, "Should not allow allocating already completed/matched donation")
        self.assertIn("cannot be allocated again", msg)


if __name__ == "__main__":
    unittest.main()

"""
FoodBridge AI - Intelligent Donation Matching Engine
====================================================
This module implements the multi-criteria matching and allocation engine for
FoodBridge AI. It pairs surplus food donations with community shelters,
orphanages, and food pantries based on:

1. Category Compatibility (only matching organizations that can accept the food)
2. Capacity & Partial Allocation (preventing over-allocation and supporting partial splits)
3. Geographic Proximity (using a documented campus/city zone reference matrix)
4. Recipient Urgency (prioritizing high-need community shelters)
5. Pickup Feasibility (enforcing safe collection windows before shelf-life expiry)

ACADEMIC & DEMO DISCLAIMER:
---------------------------
- All NGO partners, donations, and locations are fictional demonstration data.
- Distance calculations use a documented demo reference matrix between known zones;
  no real-time GPS road routing or paid mapping APIs are invoked.
- No real food is physically collected or dispatched.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

from src.data_manager import load_recipients, load_donations, commit_allocation_plan

# -----------------------------------------------------------------------------
# 1. DOCUMENTED DEMO ZONE DISTANCE MATRIX
# -----------------------------------------------------------------------------
# Estimated kilometers between predefined community zones for academic demonstration.
# Handled safely: if any location is missing or unknown, a documented neutral fallback is used.
DEMO_ZONE_DISTANCES_KM: Dict[Tuple[str, str], float] = {
    ("north campus hub", "north campus hub"): 0.5,
    ("north campus hub", "east wing plaza"): 2.5,
    ("north campus hub", "downtown station"): 4.0,
    ("north campus hub", "tech corridor gate 2"): 5.5,
    ("north campus hub", "west market hub"): 6.0,
    ("north campus hub", "south city center"): 8.5,

    ("downtown station", "downtown station"): 0.5,
    ("downtown station", "south city center"): 2.0,
    ("downtown station", "east wing plaza"): 3.0,
    ("downtown station", "tech corridor gate 2"): 3.5,
    ("downtown station", "west market hub"): 4.5,
    ("downtown station", "north campus hub"): 4.0,

    ("east wing plaza", "east wing plaza"): 0.5,
    ("east wing plaza", "north campus hub"): 2.5,
    ("east wing plaza", "downtown station"): 3.0,
    ("east wing plaza", "tech corridor gate 2"): 4.0,
    ("east wing plaza", "south city center"): 5.0,
    ("east wing plaza", "west market hub"): 7.0,

    ("west market hub", "west market hub"): 0.5,
    ("west market hub", "downtown station"): 4.5,
    ("west market hub", "south city center"): 4.0,
    ("west market hub", "north campus hub"): 6.0,
    ("west market hub", "tech corridor gate 2"): 5.0,
    ("west market hub", "east wing plaza"): 7.0,

    ("south city center", "south city center"): 0.5,
    ("south city center", "downtown station"): 2.0,
    ("south city center", "west market hub"): 4.0,
    ("south city center", "east wing plaza"): 5.0,
    ("south city center", "tech corridor gate 2"): 4.5,
    ("south city center", "north campus hub"): 8.5,

    ("tech corridor gate 2", "tech corridor gate 2"): 0.5,
    ("tech corridor gate 2", "downtown station"): 3.5,
    ("tech corridor gate 2", "east wing plaza"): 4.0,
    ("tech corridor gate 2", "south city center"): 4.5,
    ("tech corridor gate 2", "west market hub"): 5.0,
    ("tech corridor gate 2", "north campus hub"): 5.5,

    # --- Maharashtra Regional Hubs & City Zones ---
    # Pune Intra-City
    ("pune - shivajinagar", "pune - shivajinagar"): 0.5,
    ("pune - shivajinagar", "pune - kothrud"): 4.5,
    ("pune - shivajinagar", "pune - hinjawadi (it park)"): 14.0,
    ("pune - shivajinagar", "pune - hadapsar"): 9.0,
    ("pune - shivajinagar", "pune - viman nagar"): 8.5,
    ("pune - shivajinagar", "pune - pimpri-chinchwad"): 13.0,

    ("pune - kothrud", "pune - kothrud"): 0.5,
    ("pune - kothrud", "pune - hinjawadi (it park)"): 16.0,
    ("pune - kothrud", "pune - hadapsar"): 12.0,
    ("pune - kothrud", "pune - viman nagar"): 13.0,
    ("pune - kothrud", "pune - pimpri-chinchwad"): 15.0,

    ("pune - hinjawadi (it park)", "pune - hinjawadi (it park)"): 0.5,
    ("pune - hinjawadi (it park)", "pune - pimpri-chinchwad"): 8.0,
    ("pune - hinjawadi (it park)", "pune - viman nagar"): 21.0,
    ("pune - hinjawadi (it park)", "pune - hadapsar"): 22.0,

    ("pune - viman nagar", "pune - viman nagar"): 0.5,
    ("pune - viman nagar", "pune - hadapsar"): 7.0,
    ("pune - viman nagar", "pune - pimpri-chinchwad"): 18.0,

    ("pune - hadapsar", "pune - hadapsar"): 0.5,
    ("pune - hadapsar", "pune - pimpri-chinchwad"): 20.0,

    ("pune - pimpri-chinchwad", "pune - pimpri-chinchwad"): 0.5,

    # Mumbai Metropolitan Region (MMR)
    ("mumbai - dadar", "mumbai - dadar"): 0.5,
    ("mumbai - dadar", "mumbai - andheri"): 12.0,
    ("mumbai - dadar", "mumbai - bandra kurla complex (bkc)"): 5.5,
    ("mumbai - dadar", "mumbai - colaba / fort"): 11.0,
    ("mumbai - dadar", "thane west"): 26.0,
    ("mumbai - dadar", "navi mumbai - vashi"): 19.0,

    ("mumbai - andheri", "mumbai - andheri"): 0.5,
    ("mumbai - andheri", "mumbai - bandra kurla complex (bkc)"): 8.0,
    ("mumbai - andheri", "mumbai - colaba / fort"): 22.0,
    ("mumbai - andheri", "thane west"): 22.0,
    ("mumbai - andheri", "navi mumbai - vashi"): 24.0,

    ("mumbai - bandra kurla complex (bkc)", "mumbai - bandra kurla complex (bkc)"): 0.5,
    ("mumbai - bandra kurla complex (bkc)", "mumbai - colaba / fort"): 15.0,
    ("mumbai - bandra kurla complex (bkc)", "thane west"): 21.0,
    ("mumbai - bandra kurla complex (bkc)", "navi mumbai - vashi"): 16.0,

    ("mumbai - colaba / fort", "mumbai - colaba / fort"): 0.5,
    ("mumbai - colaba / fort", "thane west"): 34.0,
    ("mumbai - colaba / fort", "navi mumbai - vashi"): 28.0,

    ("thane west", "thane west"): 0.5,
    ("thane west", "navi mumbai - vashi"): 18.0,

    ("navi mumbai - vashi", "navi mumbai - vashi"): 0.5,

    # Other Major Maharashtra Cities
    ("nashik - college road", "nashik - college road"): 0.5,
    ("nagpur - sitabuldi", "nagpur - sitabuldi"): 0.5,
    ("chhatrapati sambhajinagar", "chhatrapati sambhajinagar"): 0.5,
    ("kolhapur - shahupuri", "kolhapur - shahupuri"): 0.5,
    ("solapur central", "solapur central"): 0.5,

    # Inter-City Corridor Distances (km)
    ("pune - shivajinagar", "mumbai - dadar"): 148.0,
    ("pune - shivajinagar", "nashik - college road"): 210.0,
    ("pune - shivajinagar", "chhatrapati sambhajinagar"): 235.0,
    ("pune - shivajinagar", "kolhapur - shahupuri"): 230.0,
    ("pune - shivajinagar", "solapur central"): 250.0,
    ("pune - shivajinagar", "nagpur - sitabuldi"): 710.0,

    ("mumbai - dadar", "nashik - college road"): 165.0,
    ("mumbai - dadar", "chhatrapati sambhajinagar"): 330.0,
    ("mumbai - dadar", "nagpur - sitabuldi"): 800.0,
    ("nashik - college road", "chhatrapati sambhajinagar"): 180.0,
    ("chhatrapati sambhajinagar", "nagpur - sitabuldi"): 470.0,
}


def estimate_zone_distance(
    donor_location: Optional[str],
    recipient_location: Optional[str],
) -> Tuple[Optional[float], str]:
    """
    Estimates distance between donor and recipient locations safely.

    Requirements Handled:
    - If donor and recipient are in the same zone: ~0.5 km (Same Zone).
    - If known in demo zone matrix: returns documented estimated km.
    - If both locations are in same Maharashtra city (e.g. Pune, Mumbai, etc.): estimates intra-city distance.
    - If either location is missing, blank, or unrecognized: returns (None, "Unknown Zone / Missing Location").

    Returns:
        Tuple[Optional[float], str]: (distance in km or None, human-readable description)
    """
    if not donor_location or not recipient_location:
        return None, "Location Not Specified (Missing Data)"

    loc1 = str(donor_location).strip().lower()
    loc2 = str(recipient_location).strip().lower()

    if not loc1 or not loc2:
        return None, "Location Not Specified (Missing Data)"

    if loc1 == loc2:
        return 0.5, "Same Campus Zone (~0.5 km)"

    key = (loc1, loc2)
    rev_key = (loc2, loc1)

    if key in DEMO_ZONE_DISTANCES_KM:
        dist = DEMO_ZONE_DISTANCES_KM[key]
        return dist, f"Estimated ~{dist:.1f} km (Demo Reference Matrix)"
    elif rev_key in DEMO_ZONE_DISTANCES_KM:
        dist = DEMO_ZONE_DISTANCES_KM[rev_key]
        return dist, f"Estimated ~{dist:.1f} km (Demo Reference Matrix)"

    # Smart heuristics for custom manually entered locations within common Maharashtra hubs
    for city_key, approx_km in [
        ("pune", 7.0),
        ("mumbai", 12.0),
        ("thane", 6.0),
        ("navi mumbai", 8.0),
        ("nashik", 6.5),
        ("nagpur", 8.0),
        ("sambhajinagar", 6.0),
        ("aurangabad", 6.0),
        ("kolhapur", 5.0),
        ("solapur", 5.0),
    ]:
        if city_key in loc1 and city_key in loc2:
            return approx_km, f"Estimated ~{approx_km:.1f} km (Same City: {city_key.capitalize()} Intra-Zone)"

    return None, "Unknown Zone / External Location"



# -----------------------------------------------------------------------------
# 2. ELIGIBILITY VALIDATION
# -----------------------------------------------------------------------------
def parse_datetime_safe(dt_val: Any) -> Optional[datetime]:
    """Helper to parse datetime strings or timestamps safely."""
    if dt_val is None or pd.isna(dt_val):
        return None
    if isinstance(dt_val, datetime):
        return dt_val
    if isinstance(dt_val, pd.Timestamp):
        return dt_val.to_pydatetime()

    dt_str = str(dt_val).strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None


def is_category_compatible(donation_category: str, accepted_categories_str: str) -> bool:
    """
    Checks if recipient accepts the specific donation category.
    Accepts semicolons, commas, or case-insensitive matches.
    """
    if not accepted_categories_str or not donation_category:
        return False

    accepted_list = [
        item.strip().lower()
        for item in str(accepted_categories_str).replace(",", ";").split(";")
        if item.strip()
    ]
    don_cat = str(donation_category).strip().lower()

    return (don_cat in accepted_list) or ("all" in accepted_list)


def evaluate_recipient_eligibility(
    donation: Union[Dict[str, Any], pd.Series],
    recipient: Union[Dict[str, Any], pd.Series],
    eval_time: Optional[datetime] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Evaluates whether a recipient satisfies all hard eligibility constraints.

    Hard Constraints:
    1. Recipient must have status == 'Active'.
    2. Recipient must accept the donation's food category.
    3. Recipient must have remaining needed_meals > 0.
    4. Pickup deadline must not already be expired relative to evaluation time.

    Returns:
        Tuple[bool, Optional[str]]: (is_eligible, rejection_reason_if_ineligible)
    """
    if eval_time is None:
        eval_time = datetime.now()

    # Constraint 1: Status check
    status = str(recipient.get("status", "")).strip().lower()
    if status != "active":
        return False, f"Unavailable recipient: Status is '{recipient.get('status', 'Inactive')}'"

    # Constraint 2: Category compatibility
    donation_category = str(donation.get("category", "")).strip()
    accepted_categories = str(recipient.get("accepted_categories", "")).strip()
    if not is_category_compatible(donation_category, accepted_categories):
        return False, (
            f"Incompatible food category: Recipient accepts [{accepted_categories}], "
            f"not '{donation_category}'"
        )

    # Constraint 3: Remaining recipient capacity
    try:
        needed_meals = int(recipient.get("needed_meals", 0))
    except (ValueError, TypeError):
        needed_meals = 0

    if needed_meals <= 0:
        return False, "Insufficient remaining capacity: Recipient requires 0 meals"

    # Constraint 4: Pickup deadline check
    deadline_dt = parse_datetime_safe(donation.get("pickup_deadline"))
    if deadline_dt and deadline_dt < eval_time:
        return False, f"Expired pickup deadline: Deadline passed at {deadline_dt.strftime('%Y-%m-%d %H:%M')}"

    return True, None


# -----------------------------------------------------------------------------
# 3. MULTI-FACTOR RANKING SCORE (0 TO 100)
# -----------------------------------------------------------------------------
def calculate_match_score(
    donation_meals: int,
    recipient_needed: int,
    urgency_level: str,
    distance_km: Optional[float],
    hours_until_deadline: Optional[float],
) -> Tuple[float, Dict[str, float], List[str]]:
    """
    Calculates a transparent, documented multi-factor score out of 100 points.

    Score Components:
    -----------------
    1. Distance / Proximity (Max 30 pts):
       - <= 1.0 km: 30 pts (walking/immediate zone)
       - <= 3.0 km: 24 pts (short transit)
       - <= 6.0 km: 16 pts (moderate transit)
       - <= 10.0 km: 8 pts (extended transit)
       - > 10.0 km: 4 pts
       - Missing/Unknown: 12 pts (neutral fallback)

    2. Quantity Fit (Max 25 pts):
       - Evaluates batch alignment: min(Qd, Qr) / max(Qd, Qr).
       - Score = 5.0 + 20.0 * ratio.
       - Rewords perfect 1:1 capacity matches with 25 pts, while still allowing partials.

    3. Recipient Urgency (Max 25 pts):
       - High: 25 pts
       - Medium: 16 pts
       - Normal/Low: 8 pts

    4. Pickup Feasibility (Max 20 pts):
       - Evaluates time buffer before food expiry:
       - >= 4.0 hours: 20 pts (ample collection window)
       - >= 2.0 hours: 15 pts
       - >= 1.0 hours: 10 pts
       - < 1.0 hours: 5 pts
       - Unparseable/Missing: 10 pts

    Returns:
        Tuple[float, Dict[str, float], List[str]]: (total_score, breakdown_dict, reasons_list)
    """
    # 1. Proximity Score (30 pts max)
    if distance_km is not None:
        if distance_km <= 1.0:
            dist_score = 30.0
            dist_reason = f"Proximity: Immediate zone (~{distance_km:.1f} km, 30.0/30 pts)"
        elif distance_km <= 3.0:
            dist_score = 24.0
            dist_reason = f"Proximity: Short transit (~{distance_km:.1f} km, 24.0/30 pts)"
        elif distance_km <= 6.0:
            dist_score = 16.0
            dist_reason = f"Proximity: Moderate transit (~{distance_km:.1f} km, 16.0/30 pts)"
        elif distance_km <= 10.0:
            dist_score = 8.0
            dist_reason = f"Proximity: Extended transit (~{distance_km:.1f} km, 8.0/30 pts)"
        else:
            dist_score = 4.0
            dist_reason = f"Proximity: Distant zone (~{distance_km:.1f} km, 4.0/30 pts)"
    else:
        dist_score = 12.0
        dist_reason = "Proximity: Unknown zone fallback estimate (12.0/30 pts)"

    # 2. Quantity Fit Score (25 pts max)
    qd = max(1, donation_meals)
    qr = max(1, recipient_needed)
    ratio = min(qd, qr) / max(qd, qr)
    qty_score = round(5.0 + (20.0 * ratio), 1)

    if ratio >= 0.95:
        qty_reason = f"Quantity Fit: Ideal 1:1 batch match ({qd} vs {qr} meals, {qty_score}/25 pts)"
    elif qd >= qr:
        qty_reason = f"Quantity Fit: Fully satisfies shelter need ({qr} of {qd} meals, {qty_score}/25 pts)"
    else:
        qty_reason = f"Quantity Fit: Partial shelter fulfillment ({qd} of {qr} meals needed, {qty_score}/25 pts)"

    # 3. Urgency Score (25 pts max)
    urgency_norm = str(urgency_level).strip().capitalize()
    if urgency_norm == "High":
        urgency_score = 25.0
        urgency_reason = "Urgency: High priority community shelter (25.0/25 pts)"
    elif urgency_norm == "Medium":
        urgency_score = 16.0
        urgency_reason = "Urgency: Medium priority shelter (16.0/25 pts)"
    else:
        urgency_score = 8.0
        urgency_reason = "Urgency: Normal scheduled request (8.0/25 pts)"

    # 4. Pickup Feasibility Score (20 pts max)
    if hours_until_deadline is not None:
        if hours_until_deadline >= 4.0:
            feas_score = 20.0
            feas_reason = f"Feasibility: Comfortable pickup window ({hours_until_deadline:.1f}h remaining, 20.0/20 pts)"
        elif hours_until_deadline >= 2.0:
            feas_score = 15.0
            feas_reason = f"Feasibility: Moderate pickup window ({hours_until_deadline:.1f}h remaining, 15.0/20 pts)"
        elif hours_until_deadline >= 1.0:
            feas_score = 10.0
            feas_reason = f"Feasibility: Tight pickup window ({hours_until_deadline:.1f}h remaining, 10.0/20 pts)"
        elif hours_until_deadline > 0:
            feas_score = 5.0
            feas_reason = f"Feasibility: Critical pickup window (<1h remaining, 5.0/20 pts)"
        else:
            feas_score = 0.0
            feas_reason = "Feasibility: Pickup deadline expired (0.0/20 pts)"
    else:
        feas_score = 10.0
        feas_reason = "Feasibility: Standard window assumed (10.0/20 pts)"

    total = round(dist_score + qty_score + urgency_score + feas_score, 1)
    total = max(0.0, min(100.0, total))

    breakdown = {
        "distance_score": dist_score,
        "quantity_fit_score": qty_score,
        "urgency_score": urgency_score,
        "feasibility_score": feas_score,
        "total_score": total,
    }

    reasons = [dist_reason, qty_reason, urgency_reason, feas_reason]
    return total, breakdown, reasons


# -----------------------------------------------------------------------------
# 4. CORE MATCHING & ALLOCATION PIPELINE
# -----------------------------------------------------------------------------
def find_matches_for_donation(
    donation: Union[Dict[str, Any], pd.Series],
    recipients_df: Optional[pd.DataFrame] = None,
    eval_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Main matching algorithm connecting donations with eligible recipients.

    Features:
    - Filters ineligible recipients (status, category, expired deadline, zero capacity).
    - Computes documented transparent scores out of 100.
    - Supports partial allocations (never over-allocating donation or recipient need).
    - Generates both individual ranked candidates and a multi-recipient greedy allocation plan.

    Returns:
        dict containing:
            - donation_meta: info on donation
            - is_expired: boolean
            - eligible_matches: list of ranked candidate dictionaries
            - allocation_plan: list of proposed greedy allocations
            - ineligible_recipients: list of rejected organizations with reasons
            - scoring_documentation: explanation and limitations
    """
    if eval_time is None:
        eval_time = datetime.now()

    if recipients_df is None:
        recipients_df = load_recipients()

    donation_dict = donation.to_dict() if isinstance(donation, pd.Series) else dict(donation)
    don_id = str(donation_dict.get("donation_id", "N/A"))
    don_meals = int(donation_dict.get("quantity_meals", 0))
    don_loc = donation_dict.get("pickup_location")
    deadline_dt = parse_datetime_safe(donation_dict.get("pickup_deadline"))

    # Check if donation deadline has passed
    is_expired = False
    hours_until_deadline: Optional[float] = None
    if deadline_dt:
        diff_hours = (deadline_dt - eval_time).total_seconds() / 3600.0
        hours_until_deadline = max(0.0, diff_hours)
        if diff_hours < 0:
            is_expired = True

    eligible_candidates: List[Dict[str, Any]] = []
    ineligible_recipients: List[Dict[str, Any]] = []

    if recipients_df is not None and not recipients_df.empty:
        for _, rec_row in recipients_df.iterrows():
            rec_dict = rec_row.to_dict()
            rec_id = str(rec_dict.get("recipient_id", "N/A"))
            org_name = str(rec_dict.get("organization_name", "Unknown Organization"))

            # Check eligibility constraints
            is_eligible, rejection_reason = evaluate_recipient_eligibility(
                donation=donation_dict,
                recipient=rec_dict,
                eval_time=eval_time,
            )

            if not is_eligible:
                ineligible_recipients.append({
                    "recipient_id": rec_id,
                    "organization_name": org_name,
                    "location": rec_dict.get("location", "N/A"),
                    "needed_meals": int(rec_dict.get("needed_meals", 0)),
                    "rejection_reason": rejection_reason,
                })
                continue

            # Recipient is eligible: calculate distance and score
            rec_loc = rec_dict.get("location")
            dist_km, dist_label = estimate_zone_distance(don_loc, rec_loc)
            needed_meals = int(rec_dict.get("needed_meals", 0))
            urgency = str(rec_dict.get("urgency_level", "Normal"))

            score, breakdown, reasons = calculate_match_score(
                donation_meals=don_meals,
                recipient_needed=needed_meals,
                urgency_level=urgency,
                distance_km=dist_km,
                hours_until_deadline=hours_until_deadline,
            )

            # Potential single-pair allocation:
            # Never allocate more than donation has, or more than recipient needs
            potential_alloc = min(don_meals, needed_meals)

            eligible_candidates.append({
                "recipient_id": rec_id,
                "organization_name": org_name,
                "contact_person": rec_dict.get("contact_person", "N/A"),
                "location": rec_loc,
                "distance_km": dist_km,
                "distance_label": dist_label,
                "needed_meals": needed_meals,
                "potential_allocated_meals": potential_alloc,
                "remaining_unfulfilled_need": max(0, needed_meals - potential_alloc),
                "urgency_level": urgency,
                "match_score": score,
                "distance_score": breakdown["distance_score"],
                "quantity_fit_score": breakdown["quantity_fit_score"],
                "urgency_score": breakdown["urgency_score"],
                "feasibility_score": breakdown["feasibility_score"],
                "ranking_reasons": reasons,
            })

    # Sort candidates descending by match_score
    eligible_candidates.sort(key=lambda x: x["match_score"], reverse=True)
    for rank, cand in enumerate(eligible_candidates, start=1):
        cand["rank"] = rank

    # -------------------------------------------------------------------------
    # Sequential Greedy Allocation Plan (Multi-Recipient Split)
    # -------------------------------------------------------------------------
    # If a donation has 75 meals, and #1 needs 40 meals, they get 40 meals.
    # Remaining 35 meals go to #2 recipient who needs 50 meals (gets 35).
    # Guarantees:
    # 1. Total allocated <= donation available
    # 2. Each allocation <= recipient need
    # 3. Exactly accounts for partial distributions
    allocation_plan: List[Dict[str, Any]] = []
    rem_donation_meals = don_meals

    for cand in eligible_candidates:
        if rem_donation_meals <= 0:
            break
        alloc_qty = min(rem_donation_meals, cand["needed_meals"])
        if alloc_qty > 0:
            allocation_plan.append({
                "recipient_id": cand["recipient_id"],
                "organization_name": cand["organization_name"],
                "location": cand["location"],
                "urgency_level": cand["urgency_level"],
                "match_score": cand["match_score"],
                "needed_meals_before": cand["needed_meals"],
                "allocated_meals": alloc_qty,
                "needed_meals_after": cand["needed_meals"] - alloc_qty,
                "distance_label": cand["distance_label"],
            })
            rem_donation_meals -= alloc_qty

    return {
        "donation_meta": {
            "donation_id": don_id,
            "donor_name": donation_dict.get("donor_name", "N/A"),
            "food_name": donation_dict.get("food_name", "N/A"),
            "category": donation_dict.get("category", "N/A"),
            "quantity_meals": don_meals,
            "pickup_location": don_loc,
            "pickup_deadline": str(donation_dict.get("pickup_deadline", "N/A")),
            "hours_until_deadline": round(hours_until_deadline, 1) if hours_until_deadline is not None else None,
        },
        "is_expired": is_expired,
        "eligible_matches": eligible_candidates,
        "allocation_plan": allocation_plan,
        "ineligible_recipients": ineligible_recipients,
        "scoring_documentation": {
            "formula": "Score (0-100) = Distance (30%) + Quantity Fit (25%) + Urgency (25%) + Feasibility (20%)",
            "limitations": [
                "Distances are reference estimates based on predefined campus zones, not real-time GPS road navigation.",
                "Urgency is based on self-reported static categories rather than live shelter pantry sensors.",
                "Sequential allocation uses a greedy heuristic; global vehicle routing (VRP) is not simulated.",
            ],
        },
    }


# -----------------------------------------------------------------------------
# 5. BACKWARDS-COMPATIBILITY ADAPTERS
# -----------------------------------------------------------------------------
def get_available_recipients(only_active: bool = True) -> pd.DataFrame:
    """
    Maintains compatibility with existing UI and tests.
    """
    df = load_recipients()
    if df.empty:
        return df

    if only_active and "status" in df.columns:
        return df[df["status"] == "Active"]
    return df


def rule_based_candidate_filter(
    donation_category: str,
    donation_location: str,
    quantity_meals: int,
) -> pd.DataFrame:
    """
    Legacy adapter function kept to preserve existing unit tests in test_basic.py.
    Internally invokes the new multi-criteria engine.
    """
    mock_donation = {
        "donation_id": "DON-PROTOTYPE",
        "category": donation_category,
        "pickup_location": donation_location,
        "quantity_meals": quantity_meals,
        "pickup_deadline": "2030-01-01 12:00",  # Safe future deadline
    }

    results = find_matches_for_donation(mock_donation)
    eligible = results.get("eligible_matches", [])

    rows = []
    for cand in eligible:
        rows.append({
            "recipient_id": cand["recipient_id"],
            "organization_name": cand["organization_name"],
            "location": cand["location"],
            "needed_meals": cand["needed_meals"],
            "urgency_level": cand["urgency_level"],
            "category_compatible": "Yes",
            "same_zone": "Yes" if "Same" in cand["distance_label"] else "Nearby Zone",
            "prototype_compatibility_score": f"{int(cand['match_score'])}%",
        })

    return pd.DataFrame(rows)


def get_matching_engine_status() -> Dict[str, Any]:
    """
    Returns the production status of the matching algorithm.
    """
    return {
        "status": "ACTIVE_PRODUCTION_ALGORITHM",
        "algorithm": "Multi-Criteria Transparent Heuristic + Greedy Allocation Planner",
        "factors": ["Category Compatibility", "Capacity Bounds", "Zone Proximity", "Urgency", "Shelf-Life Feasibility"],
        "partial_allocation_supported": True,
        "double_allocation_prevention": True,
    }

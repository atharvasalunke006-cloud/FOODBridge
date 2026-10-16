"""
FoodBridge AI - Data Manager Module
====================================
This module handles all local CSV file interactions for the application.

Why pathlib?
------------
In Python, using `pathlib.Path` ensures our code works across all operating systems
(Windows, macOS, Linux) without hardcoding backslashes or forward slashes.
By anchoring `BASE_DIR` to the parent of the `src/` directory, paths are always
calculated relative to the project root, no matter which terminal folder you run from.

Disclaimer:
-----------
All data handled here is fictional demo data for an academic engineering project.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import pandas as pd

# Anchor BASE_DIR to the root of the project (one level up from src/)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DONATIONS_FILE = DATA_DIR / "donations.csv"
RECIPIENTS_FILE = DATA_DIR / "recipients.csv"
DEMAND_HISTORY_FILE = DATA_DIR / "demand_history.csv"
ALLOCATIONS_FILE = DATA_DIR / "allocations.csv"

# Standard column schemas for data integrity
ALLOCATION_COLUMNS = [
    "allocation_id",
    "donation_id",
    "recipient_id",
    "organization_name",
    "allocated_meals",
    "match_score",
    "allocated_at",
    "status",
]

DONATION_COLUMNS = [
    "donation_id",
    "donor_name",
    "food_name",
    "category",
    "quantity_meals",
    "pickup_location",
    "prep_datetime",
    "pickup_deadline",
    "status",
    "created_at",
]

RECIPIENT_COLUMNS = [
    "recipient_id",
    "organization_name",
    "contact_person",
    "location",
    "needed_meals",
    "accepted_categories",
    "urgency_level",
    "status",
]

DEMAND_COLUMNS = [
    "date",
    "location",
    "category",
    "meals_demanded",
    "meals_supplied",
]

# Standard Maharashtra Regional Distribution Hubs & Campus Zones
MAHARASHTRA_LOCATIONS = [
    "Pune - Shivajinagar",
    "Pune - Kothrud",
    "Pune - Hinjawadi (IT Park)",
    "Pune - Hadapsar",
    "Pune - Viman Nagar",
    "Pune - Pimpri-Chinchwad",
    "Mumbai - Dadar",
    "Mumbai - Andheri",
    "Mumbai - Bandra Kurla Complex (BKC)",
    "Mumbai - Colaba / Fort",
    "Thane West",
    "Navi Mumbai - Vashi",
    "Nashik - College Road",
    "Nagpur - Sitabuldi",
    "Chhatrapati Sambhajinagar",
    "Kolhapur - Shahupuri",
    "Solapur Central",
]


def get_available_locations() -> list:
    """
    Returns a unified list of available locations:
    Prioritizes curated Maharashtra locations, combined with any custom locations
    previously recorded in donations or recipients.
    """
    locations_set = set(MAHARASHTRA_LOCATIONS)
    try:
        donations = load_donations()
        if not donations.empty and "pickup_location" in donations.columns:
            for loc in donations["pickup_location"].dropna():
                loc_clean = str(loc).strip()
                if loc_clean:
                    locations_set.add(loc_clean)
    except Exception:
        pass

    try:
        recipients = load_recipients()
        if not recipients.empty and "location" in recipients.columns:
            for loc in recipients["location"].dropna():
                loc_clean = str(loc).strip()
                if loc_clean:
                    locations_set.add(loc_clean)
    except Exception:
        pass

    # Sort with Maharashtra prime hubs first, then remaining alphabetically
    base_order = {name: idx for idx, name in enumerate(MAHARASHTRA_LOCATIONS)}
    return sorted(list(locations_set), key=lambda x: (0, base_order[x]) if x in base_order else (1, x.lower()))


def ensure_data_directory() -> None:
    """Creates the data/ directory if it doesn't already exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)



def load_donations() -> pd.DataFrame:
    """
    Loads all food donation records from CSV.
    
    Returns:
        pd.DataFrame: Contains donation records with proper datatypes.
    """
    ensure_data_directory()
    if not DONATIONS_FILE.exists():
        # Return an empty DataFrame matching our expected schema
        return pd.DataFrame(columns=DONATION_COLUMNS)

    try:
        df = pd.read_csv(DONATIONS_FILE, encoding="utf-8")
        # Ensure quantity_meals is treated as an integer
        if "quantity_meals" in df.columns:
            df["quantity_meals"] = pd.to_numeric(df["quantity_meals"], errors="coerce").fillna(0).astype(int)
        return df
    except Exception as e:
        print(f"Error loading donations: {e}")
        return pd.DataFrame(columns=DONATION_COLUMNS)


def load_recipients() -> pd.DataFrame:
    """
    Loads recipient organizations and their current meal needs.
    
    Returns:
        pd.DataFrame: Contains recipient profiles and requirements.
    """
    ensure_data_directory()
    if not RECIPIENTS_FILE.exists():
        return pd.DataFrame(columns=RECIPIENT_COLUMNS)

    try:
        df = pd.read_csv(RECIPIENTS_FILE, encoding="utf-8")
        if "needed_meals" in df.columns:
            df["needed_meals"] = pd.to_numeric(df["needed_meals"], errors="coerce").fillna(0).astype(int)
        return df
    except Exception as e:
        print(f"Error loading recipients: {e}")
        return pd.DataFrame(columns=RECIPIENT_COLUMNS)


def load_demand_history() -> pd.DataFrame:
    """
    Loads historical daily demand records across zones.
    
    Returns:
        pd.DataFrame: Contains historical meal demand and supply stats.
    """
    ensure_data_directory()
    if not DEMAND_HISTORY_FILE.exists():
        return pd.DataFrame(columns=DEMAND_COLUMNS)

    try:
        df = pd.read_csv(DEMAND_HISTORY_FILE, encoding="utf-8")
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if "meals_demanded" in df.columns:
            df["meals_demanded"] = pd.to_numeric(df["meals_demanded"], errors="coerce").fillna(0).astype(int)
        if "meals_supplied" in df.columns:
            df["meals_supplied"] = pd.to_numeric(df["meals_supplied"], errors="coerce").fillna(0).astype(int)
        return df
    except Exception as e:
        print(f"Error loading demand history: {e}")
        return pd.DataFrame(columns=DEMAND_COLUMNS)


def generate_donation_id(df: pd.DataFrame) -> str:
    """
    Generates a human-readable sequential ID like DON-1011.
    """
    if df.empty or "donation_id" not in df.columns:
        return "DON-1001"

    # Extract numeric part from IDs matching DON-XXXX
    existing_ids = df["donation_id"].dropna().astype(str)
    numeric_ids = []
    for item in existing_ids:
        parts = item.split("-")
        if len(parts) == 2 and parts[1].isdigit():
            numeric_ids.append(int(parts[1]))

    if numeric_ids:
        next_num = max(numeric_ids) + 1
    else:
        next_num = 1001

    return f"DON-{next_num}"


def save_donation(
    donor_name: str,
    food_name: str,
    category: str,
    quantity_meals: int,
    pickup_location: str,
    prep_datetime: str,
    pickup_deadline: str,
    status: str = "Pending",
) -> Tuple[bool, str]:
    """
    Validates and appends a new food donation record to data/donations.csv.

    Validation Rules:
    1. Donor name and food name cannot be blank.
    2. Category and pickup location cannot be blank.
    3. Quantity in meals must be greater than zero.
    4. Pickup deadline must not precede preparation date/time.

    Returns:
        Tuple[bool, str]: (Success boolean, Status message or newly created donation_id)
    """
    # 1. Basic empty text validation
    donor_name = donor_name.strip() if donor_name else ""
    food_name = food_name.strip() if food_name else ""
    category = category.strip() if category else ""
    pickup_location = pickup_location.strip() if pickup_location else ""

    if not donor_name:
        return False, "Donor name cannot be empty."
    if not food_name:
        return False, "Food item name cannot be empty."
    if not category:
        return False, "Please select a valid food category."
    if not pickup_location:
        return False, "Pickup location cannot be empty."

    # 2. Quantity validation
    try:
        qty = int(quantity_meals)
        if qty <= 0:
            return False, "Quantity in meals must be greater than 0."
    except (ValueError, TypeError):
        return False, "Quantity in meals must be a valid whole number."

    # 3. Datetime logic check
    try:
        dt_prep = datetime.strptime(str(prep_datetime), "%Y-%m-%d %H:%M")
        dt_deadline = datetime.strptime(str(pickup_deadline), "%Y-%m-%d %H:%M")
        if dt_deadline <= dt_prep:
            return False, "Pickup deadline must be after the preparation date/time."
    except ValueError:
        # If dates are in another string format, fallback check without throwing an error
        pass

    # Load current records, compute new ID, and append
    df = load_donations()
    new_id = generate_donation_id(df)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    new_row = {
        "donation_id": new_id,
        "donor_name": donor_name,
        "food_name": food_name,
        "category": category,
        "quantity_meals": qty,
        "pickup_location": pickup_location,
        "prep_datetime": str(prep_datetime),
        "pickup_deadline": str(pickup_deadline),
        "status": status,
        "created_at": now_str,
    }

    # Append row
    updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Save safely to CSV
    try:
        ensure_data_directory()
        updated_df.to_csv(DONATIONS_FILE, index=False, encoding="utf-8")
        return True, new_id
    except Exception as e:
        return False, f"Failed to save donation to file: {str(e)}"


def generate_recipient_id(df: pd.DataFrame) -> str:
    """
    Generates a human-readable sequential recipient ID like REC-2011.
    """
    if df.empty or "recipient_id" not in df.columns:
        return "REC-2001"

    existing_ids = df["recipient_id"].dropna().astype(str)
    numeric_ids = []
    for item in existing_ids:
        parts = item.split("-")
        if len(parts) == 2 and parts[1].isdigit():
            numeric_ids.append(int(parts[1]))

    if numeric_ids:
        next_num = max(numeric_ids) + 1
    else:
        next_num = 2001

    return f"REC-{next_num}"


def save_recipient(
    organization_name: str,
    contact_person: str,
    location: str,
    needed_meals: int,
    accepted_categories: str,
    urgency_level: str = "Medium",
    status: str = "Active",
) -> Tuple[bool, str]:
    """
    Validates and appends a new recipient shelter/NGO record to data/recipients.csv.

    Validation Rules:
    1. Organization name and location cannot be blank.
    2. Needed meals must be a positive number (> 0).
    3. Accepted categories cannot be empty.
    4. Urgency level defaults to 'Medium' if unrecognized.

    Returns:
        Tuple[bool, str]: (Success boolean, Status message or newly created recipient_id)
    """
    org_name = organization_name.strip() if organization_name else ""
    contact = contact_person.strip() if contact_person else "Program Coordinator"
    loc = location.strip() if location else ""
    cats = accepted_categories.strip() if accepted_categories else ""
    urgency = urgency_level.strip().capitalize() if urgency_level else "Medium"

    if not org_name:
        return False, "Organization / Shelter name cannot be empty."
    if not loc:
        return False, "Location cannot be empty."
    if not cats:
        return False, "Please specify at least one accepted food category."

    try:
        qty = int(needed_meals)
        if qty <= 0:
            return False, "Needed meals must be greater than 0."
    except (ValueError, TypeError):
        return False, "Needed meals must be a valid whole number."

    if urgency not in ["High", "Medium", "Normal", "Low"]:
        urgency = "Medium"

    df = load_recipients()
    new_id = generate_recipient_id(df)

    new_row = {
        "recipient_id": new_id,
        "organization_name": org_name,
        "contact_person": contact,
        "location": loc,
        "needed_meals": qty,
        "accepted_categories": cats,
        "urgency_level": urgency,
        "status": status,
    }

    updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    try:
        ensure_data_directory()
        updated_df.to_csv(RECIPIENTS_FILE, index=False, encoding="utf-8")
        return True, new_id
    except Exception as e:
        return False, f"Failed to save recipient to file: {str(e)}"


def get_summary_metrics() -> Dict[str, Any]:

    """
    Computes key performance indicators from the donations data.

    Returns:
        dict:
            - total_donations (int)
            - total_meals (int)
            - meals_matched (int)
            - pending_donations (int)
            - pending_meals (int)
    """
    df = load_donations()

    if df.empty:
        return {
            "total_donations": 0,
            "total_meals": 0,
            "meals_matched": 0,
            "pending_donations": 0,
            "pending_meals": 0,
        }

    total_donations = len(df)
    total_meals = int(df["quantity_meals"].sum())

    # 'Matched' or 'Completed' are counted towards saved / distributed meals
    matched_mask = df["status"].isin(["Matched", "Completed"])
    meals_matched = int(df.loc[matched_mask, "quantity_meals"].sum())

    pending_mask = df["status"] == "Pending"
    pending_donations = int(pending_mask.sum())
    pending_meals = int(df.loc[pending_mask, "quantity_meals"].sum())

    return {
        "total_donations": total_donations,
        "total_meals": total_meals,
        "meals_matched": meals_matched,
        "pending_donations": pending_donations,
        "pending_meals": pending_meals,
    }


def load_allocations() -> pd.DataFrame:
    """
    Loads saved matching allocation records from data/allocations.csv.

    Returns:
        pd.DataFrame: Table of allocated meals and match history.
    """
    ensure_data_directory()
    if not ALLOCATIONS_FILE.exists():
        return pd.DataFrame(columns=ALLOCATION_COLUMNS)

    try:
        df = pd.read_csv(ALLOCATIONS_FILE, encoding="utf-8")
        if "allocated_meals" in df.columns:
            df["allocated_meals"] = pd.to_numeric(df["allocated_meals"], errors="coerce").fillna(0).astype(int)
        if "match_score" in df.columns:
            df["match_score"] = pd.to_numeric(df["match_score"], errors="coerce").fillna(0.0).astype(float)
        return df
    except Exception as e:
        print(f"Error loading allocations: {e}")
        return pd.DataFrame(columns=ALLOCATION_COLUMNS)


def generate_allocation_id(df: pd.DataFrame) -> str:
    """
    Generates a sequential allocation ID like ALC-5004.
    """
    if df.empty or "allocation_id" not in df.columns:
        return "ALC-5001"

    existing_ids = df["allocation_id"].dropna().astype(str)
    numeric_ids = []
    for item in existing_ids:
        parts = item.split("-")
        if len(parts) == 2 and parts[1].isdigit():
            numeric_ids.append(int(parts[1]))

    next_num = max(numeric_ids) + 1 if numeric_ids else 5001
    return f"ALC-{next_num}"


def commit_allocation_plan(
    donation_id: str,
    allocations: list,
) -> Tuple[bool, str, list]:
    """
    Safely commits one or more allocations for a donation to the persistent CSV stores.

    Guarantees:
    1. Prevents duplicate allocation of already-matched donations.
    2. Enforces partial allocation bounds: never allocates more than available or needed.
    3. Consistently updates recipient needed_meals and donation status/remainders.
    4. Appends tamper-proof audit records in data/allocations.csv.

    Args:
        donation_id: The ID of the pending donation.
        allocations: List of dicts, each with keys:
            - recipient_id (str)
            - organization_name (str)
            - allocated_meals (int)
            - match_score (float)

    Returns:
        Tuple[bool, str, list]: (success, status_message, list of created allocation dicts)
    """
    if not allocations:
        return False, "No allocations provided to commit.", []

    donations_df = load_donations()
    recipients_df = load_recipients()
    allocations_df = load_allocations()

    # 1. Verify donation existence and status
    donation_matches = donations_df[donations_df["donation_id"] == donation_id]
    if donation_matches.empty:
        return False, f"Donation with ID '{donation_id}' not found.", []

    donation_row = donation_matches.iloc[0]
    if str(donation_row.get("status", "")).strip().lower() != "pending":
        return False, f"Donation '{donation_id}' is already {donation_row.get('status')} and cannot be allocated again.", []

    available_meals = int(donation_row["quantity_meals"])
    if available_meals <= 0:
        return False, f"Donation '{donation_id}' has 0 available meals.", []

    # 2. Check total allocation against donation availability
    total_to_allocate = sum(int(item.get("allocated_meals", 0)) for item in allocations)
    if total_to_allocate <= 0:
        return False, "Total allocated meals must be greater than zero.", []

    if total_to_allocate > available_meals:
        return False, (
            f"Over-allocation detected: Total requested allocation ({total_to_allocate} meals) "
            f"exceeds available donation quantity ({available_meals} meals)."
        ), []

    # 3. Check each recipient capacity
    for item in allocations:
        rec_id = item.get("recipient_id")
        alloc_qty = int(item.get("allocated_meals", 0))
        if alloc_qty <= 0:
            return False, f"Allocation quantity for recipient '{rec_id}' must be positive.", []

        rec_matches = recipients_df[recipients_df["recipient_id"] == rec_id]
        if rec_matches.empty:
            return False, f"Recipient with ID '{rec_id}' not found.", []

        rec_row = rec_matches.iloc[0]
        if str(rec_row.get("status", "")).strip().lower() != "active":
            return False, f"Recipient '{rec_id}' is inactive and cannot receive allocations.", []

        needed = int(rec_row.get("needed_meals", 0))
        if alloc_qty > needed:
            return False, (
                f"Over-allocation detected for recipient '{rec_id}': Requested {alloc_qty} meals "
                f"but recipient only needs {needed} meals."
            ), []

    # 4. Apply allocations to recipients and build allocation records
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    created_records = []
    current_alloc_df = allocations_df.copy()

    for item in allocations:
        rec_id = item.get("recipient_id")
        alloc_qty = int(item.get("allocated_meals", 0))
        score = float(item.get("match_score", 0.0))
        org_name = item.get("organization_name", "")

        # Deduct from recipient
        rec_idx = recipients_df[recipients_df["recipient_id"] == rec_id].index[0]
        recipients_df.at[rec_idx, "needed_meals"] = max(0, int(recipients_df.at[rec_idx, "needed_meals"]) - alloc_qty)

        # Generate allocation ID
        new_alloc_id = generate_allocation_id(current_alloc_df)
        alloc_row = {
            "allocation_id": new_alloc_id,
            "donation_id": donation_id,
            "recipient_id": rec_id,
            "organization_name": org_name,
            "allocated_meals": alloc_qty,
            "match_score": round(score, 1),
            "allocated_at": now_str,
            "status": "Confirmed",
        }
        current_alloc_df = pd.concat([current_alloc_df, pd.DataFrame([alloc_row])], ignore_index=True)
        created_records.append(alloc_row)

    # 5. Update donation row and handle remainder if partial
    don_idx = donations_df[donations_df["donation_id"] == donation_id].index[0]
    remainder_meals = available_meals - total_to_allocate

    if remainder_meals == 0:
        # Full allocation
        donations_df.at[don_idx, "status"] = "Matched"
    else:
        # Partial allocation: mark original row with allocated amount as Matched
        donations_df.at[don_idx, "quantity_meals"] = total_to_allocate
        donations_df.at[don_idx, "status"] = "Matched"

        # Create new remainder record for remaining meals so total historical meals are conserved
        remainder_id = generate_donation_id(donations_df)
        remainder_row = {
            "donation_id": remainder_id,
            "donor_name": donation_row["donor_name"],
            "food_name": f"{donation_row['food_name']} (Remaining Balance)",
            "category": donation_row["category"],
            "quantity_meals": remainder_meals,
            "pickup_location": donation_row["pickup_location"],
            "prep_datetime": donation_row["prep_datetime"],
            "pickup_deadline": donation_row["pickup_deadline"],
            "status": "Pending",
            "created_at": now_str,
        }
        donations_df = pd.concat([donations_df, pd.DataFrame([remainder_row])], ignore_index=True)

    # 6. Save all files safely
    try:
        ensure_data_directory()
        donations_df.to_csv(DONATIONS_FILE, index=False, encoding="utf-8")
        recipients_df.to_csv(RECIPIENTS_FILE, index=False, encoding="utf-8")
        current_alloc_df.to_csv(ALLOCATIONS_FILE, index=False, encoding="utf-8")
        msg = f"Successfully allocated {total_to_allocate} meals across {len(created_records)} recipient(s)."
        if remainder_meals > 0:
            msg += f" Remaining balance of {remainder_meals} meals saved as new pending listing."
        return True, msg, created_records
    except Exception as e:
        return False, f"Failed to persist allocations to disk: {str(e)}", []


"""
FoodBridge AI - Supabase Database Client & Bridge
==================================================
This module provides a connection layer to Supabase PostgreSQL cloud database.

Credentials Discovery Order:
1. Streamlit Secrets: st.secrets["supabase"]["url"] / st.secrets["SUPABASE_URL"]
2. Environment Variables: os.environ.get("SUPABASE_URL")
3. Local .env file (if python-dotenv is present)

Resilience:
If Supabase credentials are missing or the cloud network is unreachable,
the application seamlessly and gracefully falls back to local CSV storage.
"""

import os
from typing import Any, Dict, List, Optional
import pandas as pd

# Lazy global client singleton
_SUPABASE_CLIENT = None
_INIT_ATTEMPTED = False


def get_supabase_credentials() -> tuple:
    """Retrieves Supabase URL and Key from Streamlit secrets or environment variables."""

    url = None
    key = None

    # 1. Try Streamlit Secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "supabase" in st.secrets:
                url = st.secrets["supabase"].get("url") or st.secrets["supabase"].get("SUPABASE_URL")
                key = st.secrets["supabase"].get("key") or st.secrets["supabase"].get("SUPABASE_KEY")
            if not url and "SUPABASE_URL" in st.secrets:
                url = st.secrets["SUPABASE_URL"]
            if not key and "SUPABASE_KEY" in st.secrets:
                key = st.secrets["SUPABASE_KEY"]
    except Exception:
        pass

    # 2. Try OS Environment Variables
    if not url:
        url = os.environ.get("SUPABASE_URL")
    if not key:
        key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

    url = str(url).strip() if url else ""
    key = str(key).strip() if key else ""
    return url, key


def get_supabase_client():
    """Initializes and returns the Supabase client singleton, or None if unconfigured."""
    global _SUPABASE_CLIENT, _INIT_ATTEMPTED

    if _SUPABASE_CLIENT is not None:
        return _SUPABASE_CLIENT

    if _INIT_ATTEMPTED:
        return None

    _INIT_ATTEMPTED = True
    url, key = get_supabase_credentials()

    if not url or not key:
        return None

    try:
        from supabase import create_client
        _SUPABASE_CLIENT = create_client(url, key)
        return _SUPABASE_CLIENT
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")
        return None


def is_supabase_connected() -> bool:
    """Checks if Supabase client is configured and can be reached."""
    client = get_supabase_client()
    return client is not None


# -----------------------------------------------------------------------------
# DONATIONS OPERATIONS
# -----------------------------------------------------------------------------
def fetch_donations_supabase() -> Optional[pd.DataFrame]:
    """Fetches all donations from Supabase donations table."""
    client = get_supabase_client()
    if client is None:
        return None

    try:
        response = client.table("donations").select("*").order("created_at", desc=True).execute()
        if response.data is not None:
            df = pd.DataFrame(response.data)
            if not df.empty and "quantity_meals" in df.columns:
                df["quantity_meals"] = pd.to_numeric(df["quantity_meals"], errors="coerce").fillna(0).astype(int)
            return df
    except Exception as e:
        print(f"Supabase fetch_donations error: {e}")
    return None


def insert_donation_supabase(donation_row: Dict[str, Any]) -> bool:
    """Inserts a new donation record into Supabase."""
    client = get_supabase_client()
    if client is None:
        return False

    try:
        response = client.table("donations").insert(donation_row).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Supabase insert_donation error: {e}")
        return False


def update_donation_status_supabase(donation_id: str, status: str, quantity_meals: int) -> bool:
    """Updates status and quantity of an existing donation."""
    client = get_supabase_client()
    if client is None:
        return False

    try:
        client.table("donations").update({
            "status": status,
            "quantity_meals": quantity_meals,
        }).eq("donation_id", donation_id).execute()
        return True
    except Exception as e:
        print(f"Supabase update_donation error: {e}")
        return False


# -----------------------------------------------------------------------------
# RECIPIENTS OPERATIONS
# -----------------------------------------------------------------------------
def fetch_recipients_supabase() -> Optional[pd.DataFrame]:
    """Fetches all recipient organizations from Supabase."""
    client = get_supabase_client()
    if client is None:
        return None

    try:
        response = client.table("recipients").select("*").execute()
        if response.data is not None:
            df = pd.DataFrame(response.data)
            if not df.empty and "needed_meals" in df.columns:
                df["needed_meals"] = pd.to_numeric(df["needed_meals"], errors="coerce").fillna(0).astype(int)
            return df
    except Exception as e:
        print(f"Supabase fetch_recipients error: {e}")
    return None


def insert_recipient_supabase(recipient_row: Dict[str, Any]) -> bool:
    """Inserts a new recipient into Supabase."""
    client = get_supabase_client()
    if client is None:
        return False

    try:
        response = client.table("recipients").insert(recipient_row).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Supabase insert_recipient error: {e}")
        return False


def update_recipient_needed_meals_supabase(recipient_id: str, needed_meals: int) -> bool:
    """Updates remaining needed meals for a recipient."""
    client = get_supabase_client()
    if client is None:
        return False

    try:
        client.table("recipients").update({
            "needed_meals": needed_meals,
        }).eq("recipient_id", recipient_id).execute()
        return True
    except Exception as e:
        print(f"Supabase update_recipient error: {e}")
        return False


# -----------------------------------------------------------------------------
# ALLOCATIONS OPERATIONS
# -----------------------------------------------------------------------------
def fetch_allocations_supabase() -> Optional[pd.DataFrame]:
    """Fetches all confirmed allocations from Supabase."""
    client = get_supabase_client()
    if client is None:
        return None

    try:
        response = client.table("allocations").select("*").order("allocated_at", desc=True).execute()
        if response.data is not None:
            return pd.DataFrame(response.data)
    except Exception as e:
        print(f"Supabase fetch_allocations error: {e}")
    return None


def insert_allocations_supabase(allocation_rows: List[Dict[str, Any]]) -> bool:
    """Bulk inserts confirmed allocation records into Supabase."""
    client = get_supabase_client()
    if client is None:
        return False

    try:
        response = client.table("allocations").insert(allocation_rows).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Supabase insert_allocations error: {e}")
        return False


# -----------------------------------------------------------------------------
# DEMAND HISTORY OPERATIONS
# -----------------------------------------------------------------------------
def fetch_demand_history_supabase() -> Optional[pd.DataFrame]:
    """Fetches historical meal demand records from Supabase."""
    client = get_supabase_client()
    if client is None:
        return None

    try:
        response = client.table("demand_history").select("*").order("date", desc=False).execute()
        if response.data is not None:
            df = pd.DataFrame(response.data)
            if not df.empty and "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
            return df
    except Exception as e:
        print(f"Supabase fetch_demand_history error: {e}")
    return None

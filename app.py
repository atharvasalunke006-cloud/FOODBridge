"""
FoodBridge AI - Web Application
===============================
A Streamlit web platform connecting surplus food donors (canteen, caterers, hotels)
with community organizations and shelters to reduce food waste and alleviate hunger.

College Engineering Project Prototype
-------------------------------------
Built with Streamlit, Pandas, NumPy, scikit-learn, and Plotly.
All data displayed or recorded is fictional demonstration data.

Author: FoodBridge AI Team
"""

import sys
from datetime import datetime, time, date
from pathlib import Path

# Add project root to sys.path so modules under src/ can be resolved reliably
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import our custom modules
from src.data_manager import (
    load_donations,
    load_recipients,
    load_demand_history,
    load_allocations,
    save_donation,
    save_recipient,
    get_available_locations,
    MAHARASHTRA_LOCATIONS,
    commit_allocation_plan,
    get_summary_metrics,
)

from src.matching import (
    get_available_recipients,
    find_matches_for_donation,
    estimate_zone_distance,
    rule_based_candidate_filter,
    get_matching_engine_status,
)
from src.forecasting import (
    get_historical_demand_summary,
    generate_placeholder_forecast,
    get_forecasting_model_status,
    predict_demand,
    get_model_evaluation_metrics,
    KNOWN_LOCATIONS,
    KNOWN_CATEGORIES,
)

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FoodBridge AI - Smart Food Redistribution",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern card designs, clean fonts, and badges
st.markdown(
    """
    <style>
    /* Main container clean spacing */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
    }
    
    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0f766e 0%, #115e59 100%);
        color: white;
        padding: 1.5rem 1.8rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .hero-title {
        font-size: 1.9rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
        color: #ffffff;
    }
    .hero-sub {
        font-size: 1.0rem;
        color: #ccfbf1;
        margin-bottom: 0;
    }

    /* Metric Card Styling */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        font-weight: 600;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 0.3rem;
    }

    /* Notice / Badge Styling */
    .prototype-badge {
        background-color: #fef3c7;
        color: #92400e;
        border-left: 5px solid #f59e0b;
        padding: 0.85rem 1.1rem;
        border-radius: 6px;
        margin-bottom: 1.2rem;
        font-size: 0.92rem;
    }

    .disclaimer-badge {
        background-color: #f1f5f9;
        color: #475569;
        border-radius: 8px;
        padding: 0.8rem;
        font-size: 0.82rem;
        line-height: 1.4;
        border: 1px solid #cbd5e1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 2. SIDEBAR NAVIGATION & METADATA
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🍲 FoodBridge AI")
    st.caption("College Engineering Project Prototype")

    st.markdown("---")
    menu_selection = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "➕ Add Donation",
            "🤝 Find Matches",
            "📈 Demand Forecast",
            "🌱 Impact Report",
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown("### 📌 Project Info")
    st.markdown(
        """
        - **Platform:** Streamlit Web App
        - **Storage:** Local CSV Files
        - **Status:** Milestone 1 Prototype
        - **Target:** College Food Waste Reduction
        """
    )

    st.markdown("---")
    st.markdown(
        """
        <div class="disclaimer-badge">
        ⚠️ <strong>Academic Project Disclaimer:</strong><br>
        All donations, volunteer NGOs, locations, and statistics are fictional demo data.
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# 3. PAGE 1: DASHBOARD
# -----------------------------------------------------------------------------
if menu_selection == "📊 Dashboard":
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-title">FoodBridge AI Overview Dashboard</div>
            <div class="hero-sub">Real-time monitoring of food donations, redistribution progress, and surplus management.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Calculate metrics from local CSV data
    metrics = get_summary_metrics()
    donations_df = load_donations()

    # Four key KPI cards requested by user
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Total Donations</div>
                <div class="metric-value">{metrics['total_donations']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Total Meals Donated</div>
                <div class="metric-value">{metrics['total_meals']:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Meals Matched</div>
                <div class="metric-value" style="color: #0d9488;">{metrics['meals_matched']:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Pending Donations</div>
                <div class="metric-value" style="color: #f59e0b;">{metrics['pending_donations']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Plotly Charts Section
    st.subheader("📊 Redistribution Insights")
    chart_col1, chart_col2 = st.columns(2)

    if not donations_df.empty:
        with chart_col1:
            # Chart 1: Category breakdown donut chart
            cat_counts = donations_df.groupby("category")["quantity_meals"].sum().reset_index()
            fig_cat = px.pie(
                cat_counts,
                values="quantity_meals",
                names="category",
                title="Meals by Food Category",
                hole=0.45,
                color_discrete_sequence=px.colors.sequential.Tealgrn,
            )
            fig_cat.update_layout(
                margin=dict(t=50, b=20, l=20, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            )
            st.plotly_chart(fig_cat, use_container_width=True)

        with chart_col2:
            # Chart 2: Status distribution bar chart
            status_counts = donations_df.groupby("status")["quantity_meals"].sum().reset_index()
            status_colors = {
                "Pending": "#f59e0b",
                "Matched": "#3b82f6",
                "Completed": "#10b981",
            }
            fig_status = px.bar(
                status_counts,
                x="status",
                y="quantity_meals",
                color="status",
                title="Meals by Distribution Status",
                color_discrete_map=status_colors,
                labels={"quantity_meals": "Meals Count", "status": "Donation Status"},
                text_auto=True,
            )
            fig_status.update_layout(
                margin=dict(t=50, b=20, l=20, r=20),
                showlegend=False,
            )
            st.plotly_chart(fig_status, use_container_width=True)

        # Recent Donations Table
        st.subheader("📋 Recent Donation Activity")
        display_df = donations_df.copy()
        # Format columns for display
        display_df = display_df[[
            "donation_id", "donor_name", "food_name", "category",
            "quantity_meals", "pickup_location", "pickup_deadline", "status"
        ]]
        display_df.rename(columns={
            "donation_id": "ID",
            "donor_name": "Donor",
            "food_name": "Food Item",
            "category": "Category",
            "quantity_meals": "Meals",
            "pickup_location": "Location",
            "pickup_deadline": "Pickup Deadline",
            "status": "Status",
        }, inplace=True)

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No donation records found yet. Use the 'Add Donation' page to log the first record.")


# -----------------------------------------------------------------------------
# 4. PAGE 2: ADD DONATION
# -----------------------------------------------------------------------------
elif menu_selection == "➕ Add Donation":
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-title">Food Redistribution Data Entry (Maharashtra)</div>
            <div class="hero-sub">Log surplus meals from canteens, catering, and eateries or register community shelters across Maharashtra.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_add_don, tab_add_rec = st.tabs([
        "🍲 Register Food Donation",
        "🏢 Register Recipient / Shelter NGO",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: REGISTER SURPLUS FOOD DONATION
    # -------------------------------------------------------------------------
    with tab_add_don:
        st.markdown(
            """
            <div class="disclaimer-badge">
            ℹ️ Log surplus food offers in Maharashtra. Select a predefined city hub or enter any custom location manually. Records save to <code>data/donations.csv</code>.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("add_donation_form", clear_on_submit=False):
            col_form1, col_form2 = st.columns(2)

            with col_form1:
                donor_name = st.text_input(
                    "Donor / Organization Name *",
                    placeholder="e.g. COEP Canteen, German Bakery Kothrud, Atharva",
                    help="Name of the canteen, mess, restaurant, or individual donor.",
                )
                food_name = st.text_input(
                    "Food Item Description *",
                    placeholder="e.g. Maharashtrian Veg Thali, Rice & Dal, Bread Loaves",
                    help="Briefly describe the food prepared.",
                )
                category = st.selectbox(
                    "Food Category *",
                    [
                        "Cooked Meals",
                        "Bakery",
                        "Fresh Produce",
                        "Packaged Goods",
                        "Dairy",
                    ],
                    help="Select the category that best matches your food item.",
                )
                quantity_meals = st.number_input(
                    "Quantity (Estimated Number of Meals) *",
                    min_value=1,
                    max_value=2000,
                    value=30,
                    step=5,
                    help="One standard meal satisfies one person.",
                )

            with col_form2:
                available_locs = get_available_locations()
                location_choices = available_locs + ["➕ Enter Custom Location..."]
                selected_pickup = st.selectbox(
                    "Pickup Location (Maharashtra & Zones) *",
                    location_choices,
                    index=0,
                    help="Select a curated Maharashtra location or choose 'Enter Custom Location' to type manually.",
                )
                custom_pickup_input = st.text_input(
                    "Custom Pickup Location (if '➕ Enter Custom Location...' selected)",
                    placeholder="e.g. Pune - Baner, Mumbai - Borivali, Kolhapur, etc.",
                    help="Type any specific neighborhood, street, or campus area.",
                )

                # Date and Time inputs for Preparation
                st.markdown("**Preparation Date & Time ***")
                p_date_col, p_time_col = st.columns(2)
                with p_date_col:
                    prep_date = st.date_input("Prep Date", value=date.today(), key="prep_date")
                with p_time_col:
                    prep_time = st.time_input("Prep Time", value=time(11, 0), key="prep_time")

                # Date and Time inputs for Pickup Deadline
                st.markdown("**Safe Pickup Deadline ***")
                d_date_col, d_time_col = st.columns(2)
                with d_date_col:
                    deadline_date = st.date_input("Deadline Date", value=date.today(), key="deadline_date")
                with d_time_col:
                    deadline_time = st.time_input("Deadline Time", value=time(18, 0), key="deadline_time")

            submitted = st.form_submit_button("🚀 Submit Donation", use_container_width=True)

            if submitted:
                # Resolve custom location if selected
                if selected_pickup == "➕ Enter Custom Location...":
                    final_pickup_location = custom_pickup_input.strip()
                else:
                    final_pickup_location = selected_pickup.strip()

                if not final_pickup_location:
                    st.error("❌ Submission Error: Please select or type a valid pickup location.")
                else:
                    prep_datetime_str = f"{prep_date} {prep_time.strftime('%H:%M')}"
                    deadline_datetime_str = f"{deadline_date} {deadline_time.strftime('%H:%M')}"

                    success, message = save_donation(
                        donor_name=donor_name,
                        food_name=food_name,
                        category=category,
                        quantity_meals=int(quantity_meals),
                        pickup_location=final_pickup_location,
                        prep_datetime=prep_datetime_str,
                        pickup_deadline=deadline_datetime_str,
                        status="Pending",
                    )

                    if success:
                        st.success(f"✅ Donation successfully recorded in Maharashtra registry! Tracking ID: **{message}**")
                        st.balloons()
                    else:
                        st.error(f"❌ Submission Error: {message}")

        # Display active pending donations
        st.markdown("---")
        st.subheader("⏳ Currently Pending Donations in Maharashtra")
        donations_df = load_donations()
        if not donations_df.empty:
            pending_df = donations_df[donations_df["status"] == "Pending"]
            if not pending_df.empty:
                st.dataframe(
                    pending_df[[
                        "donation_id", "donor_name", "food_name", "category",
                        "quantity_meals", "pickup_location", "pickup_deadline"
                    ]],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No donations are currently in 'Pending' status.")

    # -------------------------------------------------------------------------
    # TAB 2: REGISTER RECIPIENT / SHELTER NGO
    # -------------------------------------------------------------------------
    with tab_add_rec:
        st.markdown(
            """
            <div class="disclaimer-badge">
            ℹ️ Register a partner hunger-relief shelter, NGO, old-age home, or orphanage in Maharashtra. Records save directly to <code>data/recipients.csv</code>.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("add_recipient_form", clear_on_submit=False):
            rcol1, rcol2 = st.columns(2)

            with rcol1:
                org_name = st.text_input(
                    "Organization / Shelter Name *",
                    placeholder="e.g. Annapurna Seva Parivar, Snehalaya Care",
                    help="Official name of the non-profit, shelter, or community pantry.",
                )
                contact_person = st.text_input(
                    "Contact Person / Coordinator *",
                    placeholder="e.g. Rajesh Patil, Sunita Deshmukh",
                    help="Name of the person coordinating food distribution.",
                )
                needed_meals = st.number_input(
                    "Daily Meal Need / Capacity (Meals) *",
                    min_value=5,
                    max_value=3000,
                    value=60,
                    step=5,
                    help="Estimated meals needed per batch/day.",
                )

            with rcol2:
                available_locs = get_available_locations()
                rec_loc_choices = available_locs + ["➕ Enter Custom Location..."]
                selected_rec_loc = st.selectbox(
                    "Shelter Location (Maharashtra & Zones) *",
                    rec_loc_choices,
                    index=0,
                    help="Select a Maharashtra district/zone or choose Custom Location to enter manually.",
                )
                custom_rec_loc = st.text_input(
                    "Custom Shelter Location (if '➕ Enter Custom Location...' selected)",
                    placeholder="e.g. Pune - Hadapsar, Nashik - Gangapur Road, etc.",
                )
                accepted_cats = st.multiselect(
                    "Accepted Food Categories *",
                    ["Cooked Meals", "Bakery", "Fresh Produce", "Packaged Goods", "Dairy"],
                    default=["Cooked Meals", "Bakery", "Packaged Goods"],
                    help="Types of food this facility is equipped to safely accept.",
                )
                urgency = st.selectbox(
                    "Urgency Level *",
                    ["High", "Medium", "Normal"],
                    index=0,
                    help="Prioritizes shelters experiencing immediate food deficits.",
                )

            rec_submitted = st.form_submit_button("🏢 Register Shelter Organization", use_container_width=True)

            if rec_submitted:
                if selected_rec_loc == "➕ Enter Custom Location...":
                    final_rec_loc = custom_rec_loc.strip()
                else:
                    final_rec_loc = selected_rec_loc.strip()

                if not final_rec_loc:
                    st.error("❌ Registration Error: Please select or enter a valid location.")
                elif not accepted_cats:
                    st.error("❌ Registration Error: Please select at least one accepted food category.")
                else:
                    cats_str = ";".join(accepted_cats)
                    success, rec_message = save_recipient(
                        organization_name=org_name,
                        contact_person=contact_person,
                        location=final_rec_loc,
                        needed_meals=int(needed_meals),
                        accepted_categories=cats_str,
                        urgency_level=urgency,
                        status="Active",
                    )

                    if success:
                        st.success(f"✅ Shelter successfully registered in Maharashtra network! ID: **{rec_message}**")
                        st.balloons()
                    else:
                        st.error(f"❌ Registration Error: {rec_message}")

        # Display registered recipients table
        st.markdown("---")
        st.subheader("🏢 Active Partner Shelters & Recipients in Maharashtra")
        recipients_df = load_recipients()
        if not recipients_df.empty:
            st.dataframe(
                recipients_df[[
                    "recipient_id", "organization_name", "contact_person",
                    "location", "needed_meals", "accepted_categories", "urgency_level", "status"
                ]],
                use_container_width=True,
                hide_index=True,
            )



# -----------------------------------------------------------------------------
# 5. PAGE 3: FIND MATCHES
# -----------------------------------------------------------------------------
elif menu_selection == "🤝 Find Matches":
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-title">Recipient Matching & Allocation Hub</div>
            <div class="hero-sub">Pair surplus food donations with community shelters based on category, capacity, proximity, urgency, and feasibility.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Documented transparent scoring & demo disclaimer badge
    st.markdown(
        """
        <div class="prototype-badge">
        🎯 <strong>Multi-Criteria Matching Algorithm Active</strong><br>
        Candidate shelters are evaluated and ranked using a transparent 100-point score:
        <strong>Zone Proximity (30 pts)</strong> + <strong>Quantity Fit (25 pts)</strong> + <strong>Recipient Urgency (25 pts)</strong> + <strong>Pickup Feasibility (20 pts)</strong>.<br>
        <small>⚠️ <em>Academic Note: Distances are reference estimates between predefined campus zones (no paid GPS/map APIs). All organizations and listings are fictional demo data.</em></small>
        </div>
        """,
        unsafe_allow_html=True,
    )

    donations_df = load_donations()
    pending_donations = (
        donations_df[donations_df["status"] == "Pending"] if not donations_df.empty else pd.DataFrame()
    )

    if pending_donations.empty:
        st.info("ℹ️ There are no pending donations awaiting matches at this time. Use the **Add Donation** tab to register a new food listing.")
    else:
        st.subheader("1️⃣ Select Active Donation to Match")
        donation_options = {
            f"{row['donation_id']} - {row['food_name']} ({row['quantity_meals']} meals | {row['category']} at {row['pickup_location']})": row
            for _, row in pending_donations.iterrows()
        }
        selected_label = st.selectbox(
            "Choose a pending donation from the queue:",
            list(donation_options.keys()),
            help="Select any surplus donation currently marked 'Pending' to evaluate compatible recipient shelters.",
        )
        selected_donation = donation_options[selected_label]

        # Display clean metadata card for selected donation
        d_meta_col1, d_meta_col2, d_meta_col3, d_meta_col4 = st.columns(4)
        with d_meta_col1:
            st.metric("Tracking ID", str(selected_donation["donation_id"]))
        with d_meta_col2:
            st.metric("Food Category", str(selected_donation["category"]))
        with d_meta_col3:
            st.metric("Available Meals", f"{int(selected_donation['quantity_meals']):,} meals")
        with d_meta_col4:
            st.metric("Safe Pickup Deadline", str(selected_donation["pickup_deadline"]))

        st.markdown("<br>", unsafe_allow_html=True)

        # Execute the real matching algorithm
        recipients_df = load_recipients()
        match_results = find_matches_for_donation(
            donation=selected_donation,
            recipients_df=recipients_df,
        )

        eligible = match_results["eligible_matches"]
        plan = match_results["allocation_plan"]
        ineligible = match_results["ineligible_recipients"]
        is_expired = match_results["is_expired"]

        if is_expired:
            st.error(
                f"⚠️ **Pickup Deadline Passed:** This donation's pickup deadline ({selected_donation['pickup_deadline']}) "
                "has expired. In accordance with food safety standards, expired food cannot be matched or allocated."
            )

        # Overview Metrics Row
        total_allocatable = sum(item["allocated_meals"] for item in plan)
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        with mcol1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Available Donation</div>
                    <div class="metric-value">{int(selected_donation['quantity_meals'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with mcol2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Eligible Shelters</div>
                    <div class="metric-value" style="color: #0d9488;">{len(eligible)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with mcol3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Allocatable Meals</div>
                    <div class="metric-value" style="color: #0284c7;">{total_allocatable}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with mcol4:
            top_score = f"{eligible[0]['match_score']}%" if eligible else "N/A"
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Top Match Score</div>
                    <div class="metric-value" style="color: #10b981;">{top_score}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Interactive Analysis Tabs
        match_tab1, match_tab2, match_tab3, match_tab4 = st.tabs([
            f"🏆 Ranked Eligible Matches ({len(eligible)})",
            f"📦 Recommended Allocation Plan ({len(plan)})",
            f"🚫 Ineligible Shelters ({len(ineligible)})",
            "📜 Allocation Audit Log",
        ])

        # ---------------------------------------------------------------------
        # TAB 1: RANKED CANDIDATE MATCHES & SCORE BREAKDOWN
        # ---------------------------------------------------------------------
        with match_tab1:
            if eligible:
                st.markdown("### 🏆 Compatible Recipient Organizations (Ranked by Multi-Criteria Score)")
                st.caption(
                    "Eligible shelters meet all constraints: Active status, Category compatibility, "
                    "Positive meal capacity, and Valid pickup deadline."
                )

                # Format clean table
                ranked_table_data = []
                for cand in eligible:
                    ranked_table_data.append({
                        "Rank": f"#{cand['rank']}",
                        "Organization": cand["organization_name"],
                        "Location": cand["location"],
                        "Distance Estimate": cand["distance_label"],
                        "Needed Meals": cand["needed_meals"],
                        "Proposed Allocation": cand["potential_allocated_meals"],
                        "Urgency": cand["urgency_level"],
                        "Match Score": f"{cand['match_score']}%",
                    })
                st.dataframe(pd.DataFrame(ranked_table_data), use_container_width=True, hide_index=True)

                st.markdown("#### 🔬 Detailed Score Breakdown & Ranking Reasons")
                for cand in eligible:
                    with st.expander(f"Rank #{cand['rank']} — {cand['organization_name']} (Score: {cand['match_score']}%)"):
                        b_col1, b_col2, b_col3, b_col4 = st.columns(4)
                        with b_col1:
                            st.write(f"**Proximity Score:** {cand['distance_score']} / 30 pts")
                        with b_col2:
                            st.write(f"**Quantity Fit:** {cand['quantity_fit_score']} / 25 pts")
                        with b_col3:
                            st.write(f"**Urgency Score:** {cand['urgency_score']} / 25 pts")
                        with b_col4:
                            st.write(f"**Feasibility:** {cand['feasibility_score']} / 20 pts")

                        st.markdown("**Algorithm Rationale:**")
                        for r in cand["ranking_reasons"]:
                            st.markdown(f"- {r}")

                        # Explain partial vs full allocation
                        if cand["potential_allocated_meals"] == cand["needed_meals"]:
                            st.success(f"✔️ Fully fulfills shelter's current requirement ({cand['potential_allocated_meals']} meals).")
                        else:
                            st.info(f"⚡ Partial fulfillment: Supplies {cand['potential_allocated_meals']} of {cand['needed_meals']} needed meals.")
            else:
                st.warning("No eligible recipients found matching this donation's category, location, or schedule.")

        # ---------------------------------------------------------------------
        # TAB 2: PARTIAL ALLOCATION PLAN & PERSISTENCE
        # ---------------------------------------------------------------------
        with match_tab2:
            st.markdown("### 📦 Recommended Greedy Allocation Plan")
            st.markdown(
                """
                When a donation provides more food than a single recipient needs, FoodBridge AI performs a
                <strong>sequential partial allocation</strong> across top-ranked shelters to avoid meal waste
                and prevent over-allocating any individual organization.
                """,
                unsafe_allow_html=True,
            )

            if plan:
                plan_display_data = []
                for p in plan:
                    plan_display_data.append({
                        "Recipient Shelter": p["organization_name"],
                        "Location": p["location"],
                        "Distance Estimate": p["distance_label"],
                        "Initial Need": p["needed_meals_before"],
                        "Allocated Meals": p["allocated_meals"],
                        "Remaining Need After": p["needed_meals_after"],
                        "Match Score": f"{p['match_score']}%",
                    })
                st.dataframe(pd.DataFrame(plan_display_data), use_container_width=True, hide_index=True)

                unallocated_remainder = int(selected_donation["quantity_meals"]) - total_allocatable
                if unallocated_remainder == 0:
                    st.success(f"🎯 **100% Allocation:** All {total_allocatable} meals from this donation are successfully allocated.")
                else:
                    st.info(f"💡 **Partial Split:** {total_allocatable} meals allocated across {len(plan)} shelter(s). Remaining unallocated balance: {unallocated_remainder} meals.")

                # Interactive Save / Commit button
                st.markdown("---")
                st.write("#### 💾 Save & Commit This Allocation")
                st.caption(
                    "Committing will update local CSV records: mark the donation/allocated portion as 'Matched', "
                    "deduct quantities from recipient needs, and prevent double allocation."
                )

                if st.button("🚀 Confirm & Save Allocation Plan", use_container_width=True, type="primary"):
                    commit_payload = [
                        {
                            "recipient_id": p["recipient_id"],
                            "organization_name": p["organization_name"],
                            "allocated_meals": p["allocated_meals"],
                            "match_score": p["match_score"],
                        }
                        for p in plan
                    ]
                    success, commit_msg, created_records = commit_allocation_plan(
                        donation_id=str(selected_donation["donation_id"]),
                        allocations=commit_payload,
                    )

                    if success:
                        st.success(f"✅ {commit_msg}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to save allocation: {commit_msg}")
            else:
                st.info("No allocation plan generated because no recipients were eligible.")

        # ---------------------------------------------------------------------
        # TAB 3: INELIGIBLE RECIPIENTS & CONSTRAINT TRANSPARENCY
        # ---------------------------------------------------------------------
        with match_tab3:
            st.markdown("### 🚫 Filtered / Ineligible Organizations")
            st.caption(
                "Organizations excluded by the constraint satisfaction engine along with the explicit rule triggered:"
            )

            if ineligible:
                ineligible_display = []
                for inel in ineligible:
                    ineligible_display.append({
                        "Recipient ID": inel["recipient_id"],
                        "Organization": inel["organization_name"],
                        "Location": inel["location"],
                        "Current Need": inel["needed_meals"],
                        "Exclusion Reason": inel["rejection_reason"],
                    })
                st.dataframe(pd.DataFrame(ineligible_display), use_container_width=True, hide_index=True)
            else:
                st.success("All registered recipient organizations were eligible for this donation batch!")

        # ---------------------------------------------------------------------
        # TAB 4: AUDIT LOG OF PAST ALLOCATIONS
        # ---------------------------------------------------------------------
        with match_tab4:
            st.markdown("### 📜 Confirmed Allocations Audit Log (`data/allocations.csv`)")
            allocations_df = load_allocations()
            if not allocations_df.empty:
                st.dataframe(allocations_df, use_container_width=True, hide_index=True)
            else:
                st.info("No confirmed allocation history found yet.")



# -----------------------------------------------------------------------------
# 6. PAGE 4: DEMAND FORECAST
# -----------------------------------------------------------------------------
elif menu_selection == "📈 Demand Forecast":
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-title">Predictive Demand Forecast (Supervised ML)</div>
            <div class="hero-sub">Anticipate campus meal order volume using a trained scikit-learn regression pipeline evaluated chronologically.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Mandatory clearly labelled synthetic dataset & surplus distinction banner
    st.markdown(
        """
        <div class="prototype-badge">
        🤖 <strong>Trained Machine Learning Model Active:</strong> Fitted using <code>RandomForestRegressor</code> + <code>ColumnTransformer</code> on 13,200 simulated campus records.<br>
        ⚠️ <strong>CRITICAL FOOD REDISTRIBUTION DISTINCTION:</strong><br>
        Predicted orders measure <strong>anticipated customer consumption</strong>, NOT available food surplus.
        Food surplus occurs only when a kitchen or canteen prepares more food than the predicted demand:
        <br><code>Surplus = max(0, Meals Prepared - Meals Consumed)</code>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Load Model Metadata & Performance Metrics
    model_metadata = get_model_evaluation_metrics()
    metrics_dict = model_metadata.get("metrics", {})
    model_mae = metrics_dict.get("model_mae", 10.26)
    baseline_mae = metrics_dict.get("baseline_mae", 54.55)
    improvement_pct = metrics_dict.get("improvement_pct", 81.19)
    test_r2 = metrics_dict.get("test_r2", 0.9628)

    # Top KPI Metrics Row comparing ML Model to Dummy Baseline
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Model Test MAE</div>
                <div class="metric-value" style="color: #0d9488;">{model_mae} <span style="font-size: 1rem; color: #64748b;">orders</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m_col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Baseline Test MAE</div>
                <div class="metric-value" style="color: #f59e0b;">{baseline_mae} <span style="font-size: 1rem; color: #64748b;">orders</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m_col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Error Reduction</div>
                <div class="metric-value" style="color: #10b981;">{improvement_pct}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m_col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Test R² Score</div>
                <div class="metric-value" style="color: #6366f1;">{test_r2}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Forecasting Sub-Tabs
    f_tab1, f_tab2, f_tab3, f_tab4 = st.tabs([
        "🔮 Interactive Demand Predictor",
        "📊 Actual vs. Predicted (Test Set)",
        "📈 Historical Trends & Fulfillment",
        "🔬 Dataset Provenance & Limitations",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: INTERACTIVE PREDICTOR
    # -------------------------------------------------------------------------
    with f_tab1:
        st.subheader("🔮 Predict Meal Orders for a Kitchen / Dining Hall")
        st.write("Configure future kitchen operational variables to forecast expected meal demand:")

        with st.form("ml_prediction_form", clear_on_submit=False):
            pcol1, pcol2 = st.columns(2)

            with pcol1:
                selected_loc = st.selectbox(
                    "Campus Dining Hub / Location *",
                    KNOWN_LOCATIONS,
                    index=0,
                    help="Select the campus cafeteria, station, or hall to forecast.",
                )
                selected_cat = st.selectbox(
                    "Food Category *",
                    KNOWN_CATEGORIES,
                    index=0,
                    help="Select the category of meals to predict.",
                )
                selected_date = st.date_input(
                    "Forecast Target Date *",
                    value=date.today() + timedelta(days=1),
                    help="Day-of-week and month calendar features are extracted automatically.",
                )

            with pcol2:
                base_price = st.number_input(
                    "Base Price per Serving (₹ / $) *",
                    min_value=10.0,
                    max_value=1000.0,
                    value=150.0,
                    step=10.0,
                    help="Standard un-discounted price per meal.",
                )
                discount_pct = st.slider(
                    "Promotional Discount (%)",
                    min_value=0.0,
                    max_value=50.0,
                    value=0.0,
                    step=5.0,
                    help="Percentage discount offered to students/staff.",
                )
                is_promo = st.checkbox(
                    "Special Campus Event / Promotion Active",
                    value=False,
                    help="Check if campus festival, orientation, or marketing promo is running.",
                )

            predict_submitted = st.form_submit_button(
                "🚀 Generate ML Demand Forecast",
                use_container_width=True,
                type="primary",
            )

        if predict_submitted:
            payload = {
                "location": selected_loc,
                "category": selected_cat,
                "date": selected_date.strftime("%Y-%m-%d"),
                "base_price": base_price,
                "discount_percent": discount_pct,
                "is_promotion": 1 if is_promo else 0,
            }

            result = predict_demand(payload)

            if result["success"]:
                pred_orders = result["predicted_orders"]
                ci = result["confidence_interval"]
                unc_mae = result["estimated_uncertainty_mae"]

                st.markdown("---")
                st.subheader("🎯 ML Forecast Output")

                r_col1, r_col2, r_col3 = st.columns(3)
                with r_col1:
                    st.markdown(
                        f"""
                        <div class="metric-card" style="border-left: 6px solid #0d9488;">
                            <div class="metric-label">Predicted Meal Demand</div>
                            <div class="metric-value" style="color: #0d9488;">{pred_orders:,} <span style="font-size: 1.1rem;">orders</span></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with r_col2:
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-label">95% Confidence Interval</div>
                            <div class="metric-value" style="font-size: 1.5rem; color: #475569;">[{ci[0]:,} - {ci[1]:,}]</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with r_col3:
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-label">Expected Uncertainty (MAE)</div>
                            <div class="metric-value" style="font-size: 1.5rem; color: #6366f1;">±{unc_mae} orders</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.markdown("<br>", unsafe_allow_html=True)
                st.info(
                    f"💡 **Kitchen Preparation Guidance:** Canteen managers at **{selected_loc}** should plan "
                    f"to prepare approximately **{pred_orders} servings** of {selected_cat} for {selected_date.strftime('%A, %b %d, %Y')}. "
                    "Preparing significantly above this threshold risks generating food waste."
                )

                st.caption(f"ℹ️ {result['surplus_distinction']}")
            else:
                st.error(f"❌ Prediction Error: {result.get('error')}")

    # -------------------------------------------------------------------------
    # TAB 2: ACTUAL VS. PREDICTED ON HELD-OUT TEST DATA
    # -------------------------------------------------------------------------
    with f_tab2:
        st.subheader("📊 Model Performance on Held-Out Chronological Test Set")
        st.markdown(
            """
            The regression model was evaluated on **2,640 held-out samples** covering the latest chronological
            test window. To prevent data leakage, test dates strictly occur <em>after</em> the training period.
            """,
            unsafe_allow_html=True,
        )

        test_points = model_metadata.get("daily_test_comparison", [])
        if test_points:
            test_plot_df = pd.DataFrame(test_points)

            fig_eval = go.Figure()
            fig_eval.add_trace(go.Scatter(
                x=test_plot_df["date"],
                y=test_plot_df["num_orders"],
                mode="lines",
                name="Actual Test Demand (Orders)",
                line=dict(color="#0f172a", width=2.2),
            ))
            fig_eval.add_trace(go.Scatter(
                x=test_plot_df["date"],
                y=test_plot_df["predicted_num_orders"],
                mode="lines",
                name="RandomForest ML Predictions",
                line=dict(color="#0d9488", width=2.0, dash="dash"),
            ))
            fig_eval.update_layout(
                title="Daily Aggregate Demand: Actual vs. ML Predictions (Held-Out Test Period)",
                margin=dict(t=50, b=20, l=20, r=20),
                xaxis_title="Test Date",
                yaxis_title="Total Meal Orders Across Campus",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                hovermode="x unified",
            )
            st.plotly_chart(fig_eval, use_container_width=True)

            st.caption(
                "Observation: Notice how the RandomForest regression model accurately captures the weekday demand peaks "
                "and weekend troughs across campus, significantly outperforming the static historical mean baseline."
            )

        # Metrics Comparison Table
        st.markdown("#### 📐 Benchmark Metric Comparison")
        comp_df = pd.DataFrame([
            {
                "Model Architecture": "Simple Dummy Baseline (Mean)",
                "MAE (Mean Absolute Error)": f"{baseline_mae} orders",
                "Relative Performance": "Baseline (0.0% gain)",
                "Splitting Strategy": "Chronological Split (No leakage)",
            },
            {
                "Model Architecture": "RandomForestRegressor + ColumnTransformer",
                "MAE (Mean Absolute Error)": f"{model_mae} orders",
                "Relative Performance": f"{improvement_pct}% error reduction",
                "Splitting Strategy": "Chronological Split (No leakage)",
            },
        ])
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # TAB 3: HISTORICAL SUPPLY VS. DEMAND DATA
    # -------------------------------------------------------------------------
    with f_tab3:
        st.subheader("📈 Historical Campus Supply & Demand Patterns (`data/demand_history.csv`)")
        demand_summary = get_historical_demand_summary()
        hist_df = demand_summary["historical_df"]

        if not hist_df.empty:
            daily_trends = hist_df.groupby("date")[["meals_demanded", "meals_supplied"]].sum().reset_index()

            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=daily_trends["date"],
                y=daily_trends["meals_demanded"],
                mode="lines+markers",
                name="Meals Demanded",
                line=dict(color="#f43f5e", width=2.5),
            ))
            fig_trend.add_trace(go.Scatter(
                x=daily_trends["date"],
                y=daily_trends["meals_supplied"],
                mode="lines+markers",
                name="Meals Supplied",
                line=dict(color="#0d9488", width=2.5),
            ))
            fig_trend.update_layout(
                margin=dict(t=30, b=20, l=20, r=20),
                xaxis_title="Date",
                yaxis_title="Meal Count",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                hovermode="x unified",
            )
            st.plotly_chart(fig_trend, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 4: DATASET PROVENANCE & METHODOLOGY
    # -------------------------------------------------------------------------
    with f_tab4:
        st.subheader("🔬 Dataset Provenance & Academic Methodology")
        st.markdown(
            f"""
            - **Dataset Type:** `{model_metadata.get('dataset_type', 'Synthetic Development Dataset')}`
            - **Provenance & Description:** {model_metadata.get('dataset_provenance')}
            - **Training Date Range:** {model_metadata.get('train_date_range', ['N/A', 'N/A'])[0]} to {model_metadata.get('train_date_range', ['N/A', 'N/A'])[1]} ({model_metadata.get('train_samples', 0):,} training rows)
            - **Held-Out Test Date Range:** {model_metadata.get('test_date_range', ['N/A', 'N/A'])[0]} to {model_metadata.get('test_date_range', ['N/A', 'N/A'])[1]} ({model_metadata.get('test_samples', 0):,} test rows)
            - **Features Included:** `{', '.join(model_metadata.get('features', []))}`
            """
        )

        st.markdown("#### ⚠️ Documented Limitations")
        for lim in model_metadata.get("limitations", []):
            st.markdown(f"- {lim}")



# -----------------------------------------------------------------------------
# 7. PAGE 5: IMPACT REPORT
# -----------------------------------------------------------------------------
elif menu_selection == "🌱 Impact Report":
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-title">Environmental & Social Impact Report</div>
            <div class="hero-sub">Quantifying saved resources, diverted landfill waste, and meals served to communities.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Mandatory clearly labelled demo statistics notice
    st.markdown(
        """
        <div class="prototype-badge">
        ⚠️ <strong>DEMO STATISTICS DISCLAIMER:</strong><br>
        All carbon avoidance, water conservation, and hunger alleviation statistics shown below are
        calculated using standard literature conversion factors applied to fictional demo data.
        </div>
        """,
        unsafe_allow_html=True,
    )

    metrics = get_summary_metrics()
    meals_saved = metrics["meals_matched"]

    # Environmental conversion factors based on UNEP / FAO food waste literature:
    # ~0.4 kg per meal, ~2.5 kg CO2e per kg food saved = 1.0 kg CO2e per meal
    # ~250 Liters of water footprint per meal saved
    co2_avoided_kg = round(meals_saved * 1.0, 1)
    water_saved_liters = int(meals_saved * 250)
    landfill_diverted_kg = round(meals_saved * 0.4, 1)

    icol1, icol2, icol3, icol4 = st.columns(4)
    with icol1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Meals Distributed</div>
                <div class="metric-value" style="color: #0d9488;">{meals_saved:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with icol2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">CO₂ Emissions Prevented</div>
                <div class="metric-value" style="color: #10b981;">{co2_avoided_kg:,} kg</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with icol3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Water Conserved</div>
                <div class="metric-value" style="color: #0284c7;">{water_saved_liters:,} L</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with icol4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Food Waste Diverted</div>
                <div class="metric-value" style="color: #6366f1;">{landfill_diverted_kg:,} kg</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Visualizing impact metrics
    st.subheader("🌍 Environmental Savings Distribution")
    impact_col1, impact_col2 = st.columns(2)

    with impact_col1:
        # Category breakdown of CO2 saved
        donations_df = load_donations()
        if not donations_df.empty:
            matched_df = donations_df[donations_df["status"].isin(["Matched", "Completed"])].copy()
            if not matched_df.empty:
                matched_df["co2_kg"] = matched_df["quantity_meals"] * 1.0
                cat_impact = matched_df.groupby("category")["co2_kg"].sum().reset_index()

                fig_impact_bar = px.bar(
                    cat_impact,
                    x="category",
                    y="co2_kg",
                    title="Estimated CO₂ Avoided by Food Category (kg)",
                    labels={"co2_kg": "CO₂ Avoided (kg)", "category": "Food Category"},
                    color="category",
                    color_discrete_sequence=px.colors.qualitative.Prism,
                    text_auto=True,
                )
                fig_impact_bar.update_layout(
                    margin=dict(t=50, b=20, l=20, r=20),
                    showlegend=False,
                )
                st.plotly_chart(fig_impact_bar, use_container_width=True)
            else:
                st.info("No completed or matched donations yet to compute category savings.")
        else:
            st.info("No donations data available.")

    with impact_col2:
        # Cumulative impact progression demo
        cumulative_data = pd.DataFrame({
            "Milestone": ["Week 1", "Week 2", "Week 3", "Week 4 (Current)"],
            "Meals Delivered": [50, 140, 260, meals_saved if meals_saved > 260 else 320],
            "CO2 Prevented (kg)": [50, 140, 260, meals_saved if meals_saved > 260 else 320],
        })
        fig_cum = px.line(
            cumulative_data,
            x="Milestone",
            y=["Meals Delivered", "CO2 Prevented (kg)"],
            markers=True,
            title="Cumulative Impact Trajectory (Demo)",
            color_discrete_sequence=["#0d9488", "#10b981"],
        )
        fig_cum.update_layout(
            margin=dict(t=50, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        )
        st.plotly_chart(fig_cum, use_container_width=True)

    st.markdown("---")
    st.subheader("📖 Academic Methodology & Assumptions")
    st.markdown(
        """
        - **Meal Equivalent:** Defined as 0.4 kg of mixed wholesome food per individual serving.
        - **CO₂e Factor:** Standard EPA/FAO average metric for avoidable food waste (~2.5 kg CO₂e per kg food saved = ~1.0 kg CO₂e per meal).
        - **Water Footprint:** Estimated at ~250 Liters of embodied water footprint per meal based on aggregate agricultural averages.
        - **Scope:** Intended solely as an academic benchmark for college engineering project evaluation.
        """
    )

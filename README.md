# 🍲 FoodBridge AI

> **College Engineering Project Prototype**  
> An intelligent food surplus redistribution platform connecting campus cafeterias, canteens, bakeries, and caterers with community shelters and hunger-relief organizations.

---

## 📌 Project Overview

FoodBridge AI is designed to solve a critical campus and community challenge: **food waste juxtaposed with food insecurity**. 

In this initial phase (**Milestone 1**), FoodBridge AI provides a fully functional, modern Streamlit web application that:
- Manages and logs food donation offers with validation.
- Tracks active community recipient requests and needs.
- Previews matching compatibility between donors and shelters.
- Visualizes historical meal demand trends with baseline forecasting.
- Quantifies environmental savings (CO₂ emissions prevented, water conserved).

---

## 🏗️ Project Architecture & Folder Structure

```text
D:\FoodBridgeAi\
├── .venv\                  # Python virtual environment (pre-installed)
├── data\                   # Local CSV storage for demo datasets
│   ├── demand_history.csv  # Historical meal demand and supply stats
│   ├── donations.csv       # Active and past food donation listings
│   └── recipients.csv      # Registered partner shelters and community needs
├── models\                 # Directory for serialized ML models (.joblib / .pkl)
│   └── README.md
├── src\                    # Core application backend modules
│   ├── __init__.py
│   ├── data_manager.py     # CSV operations, input validation, pathlib paths
│   ├── forecasting.py      # Demand summaries & baseline projection generator
│   └── matching.py         # Recipient queries & prototype candidate filtering
├── tests\                  # Automated unit test suite
│   ├── __init__.py
│   └── test_basic.py       # Unit tests for data loading, validation, and metrics
├── app.py                  # Main Streamlit web application
├── requirements.txt        # Python dependency manifest
└── README.md               # Project guide and documentation
```

---

## 🚀 How to Run the Application (Windows)

All commands should be executed from your project directory `D:\FoodBridgeAi`.

### 1. Open PowerShell or Command Prompt
Navigate to your project folder:
```powershell
cd D:\FoodBridgeAi
```

### 2. Activate the Virtual Environment
Activate your existing `.venv` environment:
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

Or, you can run directly without activating:
```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

### 3. Open in Browser
Streamlit will launch the web application at:
```text
http://localhost:8501
```

---

## 🧭 Application Pages

1. **📊 Dashboard**
   - High-level KPIs: Total Donations, Total Meals Donated, Meals Matched, and Pending Donations.
   - Interactive Plotly visualizations for food categories and donation status.
   - Recent donation log table.

2. **➕ Add Donation**
   - Safe input form to register surplus meals (Donor name, food description, category, meal count, pickup location, preparation date/time, and pickup deadline).
   - Server-side data validation (non-empty fields, positive meals, deadline after preparation).
   - Real-time updates saved directly to `data/donations.csv`.

3. **🤝 Find Matches**
   - Multi-criteria candidate ranking algorithm scoring shelters on:
     - **Zone Proximity (30%)**: Documented demo zone distance matrix.
     - **Quantity Fit (25%)**: Capacity alignment ratio $\min(Q_d, Q_r) / \max(Q_d, Q_r)$.
     - **Recipient Urgency (25%)**: Prioritizing high-need community shelters.
     - **Pickup Feasibility (20%)**: Collection buffer before food expiration.
   - Transparent constraint enforcement: filters out inactive shelters, category mismatches, zero capacity, and expired deadlines.
   - Sequential greedy partial allocation planner preventing over-allocation and double allocation.
   - Audit logging to `data/allocations.csv`.

4. **📈 Demand Forecast**
   - Supervised Machine Learning regression pipeline (`ColumnTransformer` + `RandomForestRegressor`) trained on campus food service demand patterns.
   - Evaluated chronologically (Train: 10,560 samples, Held-out Test: 2,640 samples) to prevent future data leakage.
   - Transparent performance metrics:
     - **RandomForest MAE:** $10.26\text{ orders}$ vs. **Baseline MAE:** $54.55\text{ orders}$ ($81.19\%$ error reduction).
     - **Test $R^2$:** $0.9628$.
   - Interactive prediction tool with 95% confidence intervals and input validation.
   - Visual comparison chart showing Actual vs. Predicted orders on held-out test data.
   - *Explicit educational distinction: Predicted orders represent consumer demand, not food surplus.*

5. **🌱 Impact Report**
   - Estimates environmental and social impact metrics:
     - Equivalent CO₂ emissions prevented ($~1.0\text{ kg CO}_2\text{e}$ per meal).
     - Embodied water footprint conserved ($~250\text{ L}$ per meal).
     - Food waste diverted from landfills ($~0.4\text{ kg}$ per meal).
   - Category-wise breakdown and cumulative impact trajectory.

---

## 🤖 Training the Machine Learning Model

To train (or retrain) the scikit-learn forecasting pipeline:

```powershell
.\.venv\Scripts\python.exe train_model.py
```
This script evaluates the model chronologically against a `DummyRegressor` baseline, reports MAE and $R^2$, and exports artifacts to `models/demand_forecast_model.joblib` and `models/model_metadata.json`.

---

## 🧪 Running Automated Tests

To run the full unit test suite (basic data tests + matching engine tests + ML forecasting tests):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

To run individual test modules:

```powershell
# Matching algorithm unit tests
.\.venv\Scripts\python.exe tests\test_matching.py

# Machine learning forecasting unit tests
.\.venv\Scripts\python.exe tests\test_forecasting.py
```

---

## 🌐 Online Deployment Guide

FoodBridge AI is pre-configured for free cloud hosting on **Streamlit Community Cloud**, **Hugging Face Spaces**, or **Render**.

### Recommended: Deploying to Streamlit Community Cloud (Free)

#### Step 1: Initialize Git and Push to GitHub
1. Open PowerShell or Command Prompt in `D:\FoodBridgeAi`:
   ```powershell
   cd D:\FoodBridgeAi
   git init
   git add .
   git commit -m "Initial release of FoodBridge AI"
   ```
   *(Note: The included `.gitignore` automatically prevents `.venv/` and temporary cache files from being uploaded.)*

2. Create a new repository on [GitHub](https://github.com/new) named `FoodBridgeAi`.
3. Link your local repository and push:
   ```powershell
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/FoodBridgeAi.git
   git branch -M main
   git push -u origin main
   ```

#### Step 2: Launch on Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with your GitHub account.
2. Click the **"New app"** button.
3. Select your repository: `<YOUR_GITHUB_USERNAME>/FoodBridgeAi`.
4. Set **Branch:** `main` and **Main file path:** `app.py`.
5. Click **"Deploy!"**.
6. Streamlit Cloud will read `requirements.txt`, launch the container, and provide a public URL (e.g., `https://foodbridge-ai.streamlit.app`).

---

## ⚠️ Known Production Limitations (Honest Disclosure)

1. **Ephemeral Local Storage on Free Cloud Hosts:**
   - On free platforms like Streamlit Community Cloud or Render, new donations saved to `data/donations.csv` or `data/allocations.csv` are stored in ephemeral container memory. When the cloud container reboots or redeploys, files revert to the git repository baseline. For persistent production, an external database (e.g. Supabase, PostgreSQL) should be connected.
2. **Pre-Trained ML Model File Size:**
   - The serialized model file (`models/demand_forecast_model.joblib`) is approximately $14.7\text{ MB}$, well within GitHub's $100\text{ MB}$ limit. In addition, `src/forecasting.py` includes automatic self-healing code to re-train the model on-the-fly if the binary file is ever missing.
3. **Synthetic Training Data:**
   - The demand regression model is trained on a synthetic simulation of campus canteen ordering dynamics. While it models day-of-week seasonality, location variance, and promotional elasticity, it does not capture unmodeled real-world shocks (e.g. extreme storms, campus holidays).
4. **Distance Approximations:**
   - Geographic proximity relies on a predefined demo campus zone distance matrix to avoid paid external mapping APIs (such as Google Maps API).

---

## ⚠️ Academic Disclaimer

FoodBridge AI is developed as an academic engineering demonstration. All recipient organizations, donor names, locations, pickup listings, and impact figures are fictional demo records created solely for educational and evaluation purposes.


"# FOODBridge" 

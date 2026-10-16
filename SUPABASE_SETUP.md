# ⚡ Connecting FoodBridge AI to Supabase

FoodBridge AI includes a hybrid cloud database bridge:
- **With Supabase:** Real-time PostgreSQL cloud persistence across all devices and deployed instances.
- **Without Supabase:** Seamless local CSV fallback (`data/` directory) so development and testing never break.

---

## 🛠️ Step-by-Step Setup Guide (5 Minutes)

### Step 1: Create a Free Supabase Project
1. Go to **[supabase.com](https://supabase.com)** and sign in (or create a free account).
2. Click **"New project"**.
3. Choose an organization, enter a name (e.g. `foodbridge-ai`), set a database password, and choose a region (e.g., `Mumbai / India` or `Singapore`).
4. Click **Create new project** and wait ~1-2 minutes for Supabase to provision your database.

---

### Step 2: Create Tables & Seed Data (1-Click SQL)
1. In your Supabase dashboard, open the **SQL Editor** (icon `>_` on the left sidebar).
2. Click **New query**.
3. Open the file [`supabase_schema.sql`](supabase_schema.sql) in your FoodBridge AI project and copy all of its contents.
4. Paste the SQL into the Supabase SQL Editor and click **Run** (or press <kbd>Ctrl</kbd> + <kbd>Enter</kbd>).
5. You will see:
   - Tables created: `donations`, `recipients`, `allocations`, `demand_history`
   - Row Level Security (RLS) policies enabled with public read/write for the app
   - Pre-populated Maharashtra NGOs and sample donations!

---

### Step 3: Connect Credentials to FoodBridge AI

1. In Supabase, go to **Project Settings** (gear icon ⚙️ at bottom left) ➔ **API**.
2. Find:
   - **Project URL:** `https://xxxxxxxxxxxxxxxx.supabase.co`
   - **Project API Keys:** `anon` / `public`
3. In your project, create or open the file [`.streamlit/secrets.toml`](.streamlit/secrets.toml) and add:

```toml
[supabase]
url = "https://your-project-id.supabase.co"
key = "your-anon-public-key"
```

*(Note: `.streamlit/secrets.toml` is already listed in your `.gitignore` so your private API keys will never be accidentally committed to GitHub!)*

---

### Step 4: Verify Connection
1. Run or refresh your local Streamlit app:
   ```powershell
   .\.venv\Scripts\streamlit.exe run app.py
   ```
2. Look at the left sidebar under **System Info**:
   - You will see: **🟢 Database: Supabase Cloud (Live)**
3. Any food donation or shelter registered will now automatically save directly to your Supabase PostgreSQL cloud database!

---

### 🚀 Deploying to Streamlit Community Cloud with Supabase
When you deploy on **[share.streamlit.io](https://share.streamlit.io)**:
1. Open your deployed app settings ➔ **Secrets**.
2. Paste the exact same block:
   ```toml
   [supabase]
   url = "https://your-project-id.supabase.co"
   key = "your-anon-public-key"
   ```
3. Click **Save**. Your deployed cloud app will instantly connect to Supabase!

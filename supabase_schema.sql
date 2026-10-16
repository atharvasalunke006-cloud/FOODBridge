-- =============================================================================
-- FoodBridge AI - Supabase Database Schema & Initial Seed Data
-- =============================================================================
-- Instructions:
-- 1. Go to your Supabase project dashboard (https://supabase.com).
-- 2. Open the "SQL Editor" from the left sidebar.
-- 3. Click "New Query", paste this entire script, and click "Run".
-- =============================================================================

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- 1. TABLE: DONATIONS
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.donations (
    donation_id TEXT PRIMARY KEY,
    donor_name TEXT NOT NULL,
    food_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity_meals INTEGER NOT NULL CHECK (quantity_meals > 0),
    pickup_location TEXT NOT NULL,
    prep_datetime TEXT NOT NULL,
    pickup_deadline TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending',
    created_at TEXT NOT NULL
);

-- -----------------------------------------------------------------------------
-- 2. TABLE: RECIPIENTS (SHELTERS & NGOS)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.recipients (
    recipient_id TEXT PRIMARY KEY,
    organization_name TEXT NOT NULL,
    contact_person TEXT NOT NULL,
    location TEXT NOT NULL,
    needed_meals INTEGER NOT NULL CHECK (needed_meals >= 0),
    accepted_categories TEXT NOT NULL,
    urgency_level TEXT NOT NULL DEFAULT 'Medium',
    status TEXT NOT NULL DEFAULT 'Active'
);

-- -----------------------------------------------------------------------------
-- 3. TABLE: ALLOCATIONS (MATCH AUDIT TRAIL)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.allocations (
    allocation_id TEXT PRIMARY KEY,
    donation_id TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    organization_name TEXT NOT NULL,
    allocated_meals INTEGER NOT NULL CHECK (allocated_meals > 0),
    match_score NUMERIC NOT NULL,
    allocated_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Confirmed'
);

-- -----------------------------------------------------------------------------
-- 4. TABLE: DEMAND_HISTORY (PREDICTIVE ANALYTICS)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.demand_history (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    location TEXT NOT NULL,
    category TEXT NOT NULL,
    meals_demanded INTEGER NOT NULL,
    meals_supplied INTEGER NOT NULL
);

-- -----------------------------------------------------------------------------
-- 5. ROW LEVEL SECURITY (RLS) POLICIES
-- Allows anonymous read and write access for development & prototype usage
-- -----------------------------------------------------------------------------
ALTER TABLE public.donations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recipients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.demand_history ENABLE ROW LEVEL SECURITY;

-- Allow public read/write access for prototype demo
DROP POLICY IF EXISTS "Public access for donations" ON public.donations;
CREATE POLICY "Public access for donations" ON public.donations
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Public access for recipients" ON public.recipients;
CREATE POLICY "Public access for recipients" ON public.recipients
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Public access for allocations" ON public.allocations;
CREATE POLICY "Public access for allocations" ON public.allocations
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Public access for demand_history" ON public.demand_history;
CREATE POLICY "Public access for demand_history" ON public.demand_history
    FOR ALL USING (true) WITH CHECK (true);

-- -----------------------------------------------------------------------------
-- 6. SEED DATA (MAHARASHTRA NETWORK)
-- -----------------------------------------------------------------------------
INSERT INTO public.recipients (recipient_id, organization_name, contact_person, location, needed_meals, accepted_categories, urgency_level, status)
VALUES
    ('REC-2001', 'Annapurna Seva Parivar', 'Rajendra Pawar', 'Pune - Shivajinagar', 65, 'Cooked Meals;Bakery;Packaged Goods', 'High', 'Active'),
    ('REC-2002', 'Maher Ashram Children Home', 'Sister Lucy Kurien', 'Pune - Viman Nagar', 80, 'Cooked Meals;Dairy;Fresh Produce', 'High', 'Active'),
    ('REC-2003', 'Snehalaya Care Center', 'Dr. Girish Kulkarni', 'Pune - Kothrud', 50, 'Cooked Meals;Dairy;Bakery', 'Medium', 'Active'),
    ('REC-2004', 'Akshaya Chaitanya Food Mission', 'Vikram Joshi', 'Mumbai - Dadar', 120, 'Cooked Meals;Fresh Produce;Bakery', 'High', 'Active'),
    ('REC-2005', 'Robin Hood Army Mumbai Chapter', 'Pooja Mehta', 'Mumbai - Andheri', 75, 'Cooked Meals;Bakery;Packaged Goods', 'High', 'Active'),
    ('REC-2006', 'Samarpan Old Age Care', 'Anjali Deshmukh', 'Thane West', 45, 'Cooked Meals;Dairy', 'Medium', 'Active'),
    ('REC-2007', 'Vashi Community Night Shelter', 'Ramesh Shinde', 'Navi Mumbai - Vashi', 60, 'Cooked Meals;Packaged Goods', 'Normal', 'Active'),
    ('REC-2008', 'Matoshree Orphanage', 'Sunita Patil', 'Nashik - College Road', 55, 'Cooked Meals;Fresh Produce;Packaged Goods', 'Medium', 'Active'),
    ('REC-2009', 'Nagpur Hunger Relief Mission', 'Amit Deshpande', 'Nagpur - Sitabuldi', 70, 'Cooked Meals;Bakery', 'High', 'Active'),
    ('REC-2010', 'Chhatrapati Seva Samiti', 'Sachin Kadam', 'Chhatrapati Sambhajinagar', 50, 'Cooked Meals;Dairy', 'Normal', 'Active'),
    ('REC-2011', 'Hinjawadi Labor Support Pantry', 'Nilesh Gaikwad', 'Pune - Hinjawadi (IT Park)', 60, 'Cooked Meals;Fresh Produce;Packaged Goods', 'Medium', 'Active')
ON CONFLICT (recipient_id) DO NOTHING;

INSERT INTO public.donations (donation_id, donor_name, food_name, category, quantity_meals, pickup_location, prep_datetime, pickup_deadline, status, created_at)
VALUES
    ('DON-1001', 'COEP Central Mess', 'Rice & Dal Tadka with Mix Veg', 'Cooked Meals', 75, 'Pune - Shivajinagar', '2026-10-16 09:30', '2026-10-17 18:00', 'Pending', '2026-10-16 09:45'),
    ('DON-1002', 'Kayani Bakery Camp', 'Assorted Whole Wheat Bread & Buns', 'Bakery', 40, 'Pune - Shivajinagar', '2026-10-16 07:00', '2026-10-17 20:00', 'Pending', '2026-10-16 07:30'),
    ('DON-1003', 'Grand Sheraton Banquet', 'Paneer Butter Masala & Pulao', 'Cooked Meals', 120, 'Pune - Shivajinagar', '2026-10-15 21:00', '2026-10-16 04:00', 'Completed', '2026-10-15 21:30'),
    ('DON-1004', 'Reliance Fresh Dadar', 'Apples Oranges and Bananas', 'Fresh Produce', 60, 'Mumbai - Dadar', '2026-10-16 08:00', '2026-10-18 18:00', 'Pending', '2026-10-16 08:15'),
    ('DON-1005', 'Taj President Caterers', 'Breakfast Croissants & Fruit Tarts', 'Bakery', 35, 'Mumbai - Colaba / Fort', '2026-10-16 10:30', '2026-10-17 17:00', 'Pending', '2026-10-16 10:45'),
    ('DON-1006', 'Infosys Hinjawadi Food Court', 'Vegetable Biryani & Raita', 'Cooked Meals', 90, 'Pune - Hinjawadi (IT Park)', '2026-10-15 13:00', '2026-10-15 17:00', 'Completed', '2026-10-15 13:10'),
    ('DON-1007', 'Chitale Bandhu Dairy', 'Fresh Milk Packets & Curd', 'Dairy', 50, 'Pune - Kothrud', '2026-10-16 08:00', '2026-10-18 08:00', 'Pending', '2026-10-16 08:20'),
    ('DON-1008', 'Andheri Sports Club Kitchen', 'Pav Bhaji & Bun Packs', 'Cooked Meals', 45, 'Mumbai - Andheri', '2026-10-15 22:00', '2026-10-16 08:00', 'Completed', '2026-10-15 22:15'),
    ('DON-1009', 'MIT World Peace Mess', 'Palak Paneer & Phulka Roti', 'Cooked Meals', 85, 'Pune - Kothrud', '2026-10-16 11:00', '2026-10-17 18:00', 'Pending', '2026-10-16 11:15'),
    ('DON-1010', 'D-Mart Vashi Superstore', 'Canned Pulses & Whole Grain Packs', 'Packaged Goods', 110, 'Navi Mumbai - Vashi', '2026-10-15 10:00', '2026-10-25 18:00', 'Completed', '2026-10-15 10:30'),
    ('DON-1011', 'Atharva', 'Special Maharashtrian Veg Thali', 'Cooked Meals', 35, 'Pune - Shivajinagar', '2026-10-16 11:00', '2026-10-17 19:00', 'Pending', '2026-10-16 12:31')
ON CONFLICT (donation_id) DO NOTHING;

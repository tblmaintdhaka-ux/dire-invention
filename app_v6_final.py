import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib # For basic password hashing
import io 

# --- CONFIGURATION & DATABASE SETUP ---
DB_FILE = "tracker_2026.db"

# --- SECURITY FUNCTIONS (Basic Hashing) ---
def make_hashes(password):
    """Returns a SHA256 hash of the password."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """Checks if the entered password matches the stored hash."""
    return make_hashes(password) == hashed_text

def init_db():
    """Initializes the SQL database with all necessary tables."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Table 1: Budget Configuration (Cost Center)
    c.execute('''CREATE TABLE IF NOT EXISTS budget_heads (
                    id INTEGER PRIMARY KEY,
                    department TEXT,
                    cost_area TEXT UNIQUE,
                    total_budget REAL
                )''')
    
    # Table 2: Maintenance Notifications / Requests (UPDATED SCHEMA)
    c.execute('''CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mn_number TEXT,
                    mn_issue_date TEXT, 
                    date_logged TEXT,
                    requester TEXT,
                    cost_area TEXT,
                    estimated_cost REAL,
                    status TEXT DEFAULT 'Pending',
                    mn_particulars TEXT,
                    mn_category TEXT,
                    department TEXT,
                    location TEXT,
                    supplier_vendor TEXT,
                    supplier_type TEXT,
                    currency TEXT,
                    foreign_spare_cost REAL,
                    freight_fca_charges REAL,
                    customs_duty_rate REAL, 
                    local_cost_wo_vat_ait REAL,
                    vat_ait REAL,
                    landed_total_cost REAL,
                    date_sent_ho TEXT,
                    plant_remarks TEXT,
                    FOREIGN KEY(cost_area) REFERENCES budget_heads(cost_area)
                )''')
                
    # Table 3: User Management
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    role TEXT -- 'administrator' or 'user'
                )''')

    # Table 4: Exchange Rate and Duty Configuration (NEW TABLE)
    c.execute('''CREATE TABLE IF NOT EXISTS exchange_config (
                    key TEXT PRIMARY KEY,
                    value REAL
                )''')

    # Initialize default configuration values if not present
    default_config = {
        'USD_rate': 110.00, 'EUR_rate': 120.00, 'GBP_rate': 130.00, 
        'INR_rate': 1.50, 'OTHER_rate': 100.00, 'CustomsDuty_pct': 0.05
    }
    for key, value in default_config.items():
        c.execute("INSERT OR IGNORE INTO exchange_config (key, value) VALUES (?, ?)", (key, value))
        
    conn.commit()
    
    # Create a default admin user if none exists
    c.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if c.fetchone()[0] == 0:
        admin_password_hash = make_hashes("admin123") # Default password for admin is 'admin123'
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                  ('admin', admin_password_hash, 'administrator'))
        conn.commit()
    
    conn.close()

# --- DATABASE INTERACTION FUNCTIONS ---
def load_data(query):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

# --- CORE FUNCTION: Budget vs. Cost Status Calculation ---
def calculate_status():
    """Merges budget and request data to show current status."""
    budgets = load_data("SELECT * FROM budget_heads")
    requests = load_data("SELECT * FROM requests")

    if budgets.empty:
        return pd.DataFrame(), 0, 0, 0 

    budgets['total_budget'] = pd.to_numeric(budgets['total_budget'], errors='coerce').fillna(0)
    
    if not requests.empty:
        # Use landed_total_cost for tracking against budget
        requests['landed_total_cost'] = pd.to_numeric(requests['landed_total_cost'], errors='coerce').fillna(0)
        
        spent_by_area = requests.groupby('cost_area')['landed_total_cost'].sum().reset_index()
        merged = pd.merge(budgets, spent_by_area, on='cost_area', how='left').fillna(0)
    else:
        merged = budgets.copy()
        merged['landed_total_cost'] = 0
            
    merged.rename(columns={'landed_total_cost': 'Total Utilized Cost'}, inplace=True)
    
    merged['Remaining Balance'] = merged['total_budget'] - merged['Total Utilized Cost']
    
    total_budget = merged['total_budget'].sum()
    total_spent = merged['Total Utilized Cost'].sum()
    remaining = total_budget - total_spent

    merged['Utilization %'] = merged.apply(
        lambda row: (row['Total Utilized Cost'] / row['total_budget']) * 100 
                    if row['total_budget'] > 0 else 0, 
        axis=1
    )
    
    return merged, total_budget, total_spent, remaining

# --- APP LAYOUT ---
st.set_page_config(page_title="Org Budget Tracker 2026", layout="wide")
init_db()

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

# --- LOGIN PAGE ---
def login_page():
    st.sidebar.subheader("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type='password')
    
    if st.sidebar.button("Login"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT password_hash, role FROM users WHERE username = ?', (username,))
        user_data = c.fetchone()
        conn.close()

        if user_data:
            stored_hash, role = user_data
            if check_hashes(password, stored_hash):
                st.session_state['logged_in'] = True
                st.session_state['role'] = role
                st.session_state['username'] = username
                st.success(f"Logged in as {role}!")
                st.rerun() 
            else:
                st.sidebar.error("Incorrect Password")
        else:
            st.sidebar.error("User not found")

    st.sidebar.markdown("---")
    st.sidebar.info("Default Admin: **admin** / **admin123**")

# --- LOGOUT FUNCTION ---
def logout():
    st.session_state['logged_in'] = False
    st.session_state['role'] = None
    st.session_state['username'] = None
    st.rerun()

# --- MAIN APPLICATION LOGIC ---
if not st.session_state['logged_in']:
    login_page()
    st.title("Organizational Tracker 2026 - Please Log In")
else:
    # Sidebar Navigation and Logout Button
    st.sidebar.markdown(f"**Logged in as:** **{st.session_state['username']}** ({st.session_state['role'].title()})")
    if st.sidebar.button("Logout"):
        logout()
        
    menu = ["View & Filter Requests", "New Request (MN)"]
    if st.session_state['role'] == 'administrator':
        menu.append("Budget Balance Sheet") 
        menu.append("Budget Setup & Import")
        menu.append("Users & Access Control")
        
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Go to", menu)
    st.sidebar.markdown("---")

    # --- TAB 1: VIEW & FILTER REQUESTS ---
    if page == "View & Filter Requests":
        st.title("🔍 Existing Entries & Tracking Status")
        
        # Display Core Metrics (Budget Status)
        df_status, total_budget, total_spent, remaining = calculate_status()
        
        if not df_status.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Budget 2026 (BDT)", f"{total_budget:,.2f}")
            col2.metric("Total Utilized Cost", f"{total_spent:,.2f}")
            col3.metric("Remaining Balance", f"{remaining:,.2f}")
            st.markdown("---")

        # Load all requests for filtering
        requests_df = load_data("SELECT * FROM requests")
        
        if requests_df.empty:
            st.info("No requests found.")
        else:
            st.subheader("Filter Requests")
            
            # Smart Filters
            col_filter_1, col_filter_2, col_filter_3 = st.columns(3)
            
            with col_filter_1:
                selected_status = st.multiselect("Filter by Status", requests_df['status'].unique(), default=[])
            with col_filter_2:
                selected_area = st.multiselect("Filter by Cost Center", requests_df['cost_area'].unique(), default=[])
            with col_filter_3:
                selected_requester = st.multiselect("Filter by Requester", requests_df['requester'].unique(), default=[])

            # Apply Filters
            filtered_df = requests_df.copy()
            if selected_status:
                filtered_df = filtered_df[filtered_df['status'].isin(selected_status)]
            if selected_area:
                filtered_df = filtered_df[filtered_df['cost_area'].isin(selected_area)]
            if selected_requester:
                filtered_df = filtered_df[filtered_df['requester'].isin(selected_requester)]

            # --- STATUS UPDATE FEATURE (ADMIN ONLY) ---
            st.markdown("---")
            if st.session_state['role'] == 'administrator':
                st.subheader("🛠️ Update Request Status (Admin Access)")
                
                # Filter out rejected/completed requests from the update list for clarity
                update_df = requests_df[~requests_df['status'].isin(["Rejected", "Completed"])].sort_values(by='date_logged', ascending=False)
                
                # Define common workflow statuses 
                workflow_statuses = ["Pending", "Approved by SRPM", "Approved by AD", "Finance Approved", "Rejected", "PO Issued", "Completed"]
                
                with st.form("status_update_form", clear_on_submit=True):
                    col_u1, col_u2 = st.columns(2)
                    with col_u1:
                        # Dropdown showing ID and MN Number for easier selection
                        display_options = [f"ID {row['id']} - MN: {row['mn_number']} ({row['status']})" for index, row in update_df.iterrows()]
                        selected_display = st.selectbox("Select Request to Update", options=display_options)
                        
                        # Extract the actual ID from the display string
                        selected_id = None
                        if selected_display:
                            try:
                                selected_id = int(selected_display.split(' - ')[0].replace('ID ', ''))
                            except ValueError:
                                selected_id = None
                        
                    with col_u2:
                        # Pre-select the current status of the chosen MN if possible
                        current_status = update_df[update_df['id'] == selected_id]['status'].iloc[0] if selected_id and not update_df[update_df['id'] == selected_id].empty else "Pending"
                        new_status = st.selectbox("New Status", workflow_statuses, index=workflow_statuses.index(current_status) if current_status in workflow_statuses else 0)
                        
                    if st.form_submit_button("Apply Status Change"):
                        if selected_id:
                            execute_query("UPDATE requests SET status = ? WHERE id = ?", (new_status, selected_id))
                            st.success(f"Status for Request ID {selected_id} updated to **{new_status}**.")
                            st.rerun()
                        else:
                            st.warning("Please select a request.")
            
            st.markdown("---")
            st.subheader("All Request Fields")
            
            # Display the filtered data
            st.dataframe(
                filtered_df,
                use_container_width=True
            )
            
            # Download CSV option
            st.download_button(
                label="Download Filtered Requests CSV",
                data=filtered_df.to_csv(index=False).encode('utf-8'),
                file_name='filtered_requests.csv',
                mime='text/csv',
                key='download_requests'
            )

# --- TAB 2: NEW REQUEST (MN) (REVISED AND DEBUGGED) ---
    elif page == "New Request (MN)":
        st.title("📝 Create New Maintenance Notification")
        
        # Load data needed for configuration and calculation
        budgets = load_data("SELECT cost_area, department FROM budget_heads")
        config_data = load_data("SELECT key, value FROM exchange_config")
        config_dict = config_data.set_index('key')['value'].to_dict()
        
        # Define FX rates and Duty Percentage
        fx_rates = {
            "BDT": 1.0, 
            "USD": config_dict.get('USD_rate', 110.00), 
            "EUR": config_dict.get('EUR_rate', 120.00),
            "GBP": config_dict.get('GBP_rate', 130.00),
            "INR": config_dict.get('INR_rate', 1.50),
            "Other": config_dict.get('OTHER_rate', 100.00)
        }
        customs_duty_pct = config_dict.get('CustomsDuty_pct', 0.05) # Default 5%

        if budgets.empty:
            st.warning("No Department or Cost Area data found. Please set up budgets first.")
            st.stop()
        
        departments = sorted(budgets['department'].unique().tolist())
        
        
        # 1. GENERAL & CATEGORIZATION (Moved outside form for dynamic area update)
        st.subheader("1. General & Categorization")
        col1, col2, col3 = st.columns(3)
        with col1:
            mn_issue_date = st.date_input("MN Issue Date *", value=datetime.now(), help="Date the MN was officially issued.")
            requester = st.text_input("Requester Name", value=st.session_state['username'], disabled=True)
            mn_category = st.selectbox("MN Category *", ["R&M (Repair & Maintenance)", "C&C (Chemicals & Consumables)"], index=None)
        with col2:
            mn_no = st.text_input("MN Number * (e.g., DHK/001/26)")
            # Department selection is OUTSIDE the form to trigger reruns
            selected_department = st.selectbox("Department *", departments, index=None, key="mn_dept_select", help="Selecting a Department will filter the Cost Area list.")
        with col3:
            # DYNAMIC DROPDOWN LOGIC (Runs on every rerun)
            cost_areas_filtered = []
            if selected_department:
                cost_areas_filtered = budgets[budgets['department'] == selected_department]['cost_area'].unique().tolist()
                
            # Cost Area selection is OUTSIDE the form
            area = st.selectbox("Cost Area *", sorted(cost_areas_filtered), index=None, key="mn_area_select", help="The specific Cost Center being charged.")
            location = st.text_input("Location *")
        
        mn_particulars = st.text_area("MN Particulars/Detailed Description of Work * (Max 200 chars)", max_chars=200)

        
        # 2. FINANCIAL & PROCUREMENT DETAILS (Moved outside form for live calculation)
        st.subheader("2. Financial & Procurement Details")
        
        col_supp, col_curr, col_cost1, col_cost2 = st.columns(4)
        
        with col_supp:
            supplier_vendor = st.text_input("Supplier/Vendor *")
            supplier_type = st.selectbox("Supplier Type *", ["Local", "Foreign"], index=None)
        
        with col_curr:
            currency = st.selectbox("Currency *", list(fx_rates.keys()), index=0)
            st.info(f"Rate: 1 {currency} = **{fx_rates.get(currency):.4f} BDT**")
        
        with col_cost1:
            foreign_spare_cost = st.number_input("Foreign Spare Cost *", min_value=0.0, format="%.2f", value=0.0, key="mn_fsc")
            freight_fca_charges = st.number_input("Freight & FCA Charges *", min_value=0.0, format="%.2f", value=0.0, key="mn_ffc")
            
        with col_cost2:
            local_cost_wo_vat_ait = st.number_input("Local Cost without VAT & AIT *", min_value=0.0, format="%.2f", value=0.0, key="mn_lcwa")
            vat_ait = st.number_input("VAT & AIT *", min_value=0.0, format="%.2f", value=0.0, key="mn_va")
            
            # --- LIVE CALCULATION OF LANDED TOTAL COST (BDT) ---
            exchange_rate = fx_rates.get(currency, 1.0)
            
            landed_total_cost = (
                (foreign_spare_cost * (1 + customs_duty_pct)) + 
                freight_fca_charges
            ) * exchange_rate + local_cost_wo_vat_ait + vat_ait
            
            st.markdown(f"**Calculated Landed Total Cost (BDT):**")
            st.markdown(f"## {landed_total_cost:,.2f}")
            st.caption(f"*(Based on Duty Rate: {customs_duty_pct:.2%} and {currency} Rate: {exchange_rate:.4f} BDT)*")


        # 3. TIMELINE & REMARKS (Moved outside form)
        st.subheader("3. Timeline & Remarks")
        col_date, col_remarks = st.columns([1, 2])
        with col_date:
            date_sent_ho = st.date_input("Date of Sending To HO *", value=datetime.now())
        with col_remarks:
            plant_remarks = st.text_area("Plant Remarks/Notes") # NOT mandatory
        
        st.markdown("---")


        # --- SUBMISSION LOGIC (Inside a form for one-click action) ---
        with st.form("mn_submission_form", clear_on_submit=True):
            st.markdown("*Fields marked with a **\*** are mandatory.")
            submitted = st.form_submit_button("Submit Request")
            
            if submitted:
                
                # --- MANDATORY FIELD CHECK ---
                # Retrieve current state of all fields
                # Check for None, empty string, or zero (for cost fields) where not allowed
                
                is_valid = True
                
                # Check for None/empty strings
                if not all([mn_no, mn_category, selected_department, area, location, supplier_vendor, supplier_type, currency, mn_particulars]):
                    is_valid = False

                # Check for non-negative/non-zero costs
                if not all(c >= 0 for c in [foreign_spare_cost, freight_fca_charges, local_cost_wo_vat_ait, vat_ait]) or landed_total_cost <= 0:
                    is_valid = False
                
                if not is_valid:
                    st.error("⚠️ Please fill in all mandatory fields (*) and ensure the calculated cost is greater than 0.")
                    # Use st.stop() to prevent budget check on invalid data
                    st.stop() 
                
                # --- BUDGET CHECK & SUBMISSION ---
                df_status, _, _, _ = calculate_status()
                target_area = df_status[df_status['cost_area'] == area]
                
                if target_area.empty:
                    st.error("Could not find budget data for the selected Cost Center.")
                    st.stop()

                curr_remaining = target_area['Remaining Balance'].iloc[0]
                
                if landed_total_cost > curr_remaining:
                    st.error(f"⚠️ Budget Exceeded! Cost Area **'{area}'** only has **{curr_remaining:,.2f} BDT** remaining. Please contact an administrator.")
                    st.stop()

                # All checks passed, proceed to DB insertion
                date_issue_str = mn_issue_date.strftime("%Y-%m-%d")
                date_ho_str = date_sent_ho.strftime("%Y-%m-%d")

                query = '''INSERT INTO requests (
                        mn_number, mn_issue_date, date_logged, requester, cost_area, estimated_cost, status,
                        mn_particulars, mn_category, department, location, supplier_vendor, 
                        supplier_type, currency, foreign_spare_cost, freight_fca_charges, customs_duty_rate, 
                        local_cost_wo_vat_ait, vat_ait, landed_total_cost, date_sent_ho, plant_remarks
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
                
                params = (
                    mn_no, date_issue_str, datetime.now().strftime("%Y-%m-%d"), requester, area, landed_total_cost, "Pending",
                    mn_particulars, mn_category, selected_department, location, supplier_vendor, 
                    supplier_type, currency, foreign_spare_cost, freight_fca_charges, customs_duty_pct, 
                    local_cost_wo_vat_ait, vat_ait, landed_total_cost, date_ho_str, plant_remarks
                )
                
                execute_query(query, params)
                st.success("✅ Request Submitted Successfully! Form cleared.")
                # We don't need st.rerun() here as clear_on_submit=True handles the form clearing
                # but a manual rerun might be needed if the success message disappears too fast
                # Let's keep the success message and rely on the next interaction to trigger rerun.

    # --- TAB 3: BUDGET BALANCE SHEET ---
    elif page == "Budget Balance Sheet":
        st.title("📊 Budget Balance Sheet (Departmental Subtotals)")
        
        # 1. Get the base status data
        df_status, total_budget, total_spent, remaining = calculate_status()

        if df_status.empty:
            st.info("No budget data found. Please set up budgets in the 'Budget Setup & Import' tab.")
            st.stop()

        # Rename columns for clarity as requested by the user
        df_status = df_status.rename(columns={
            'total_budget': 'Total Budget',
            'Total Utilized Cost': 'MN_issued',
            'Remaining Balance': 'Remaining Budget'
        })
        
        # 2. Define the Columns to Display (Corrected case: 'department')
        display_cols = ['department', 'cost_area', 'Total Budget', 'MN_issued', 'Remaining Budget']
        df_display = df_status[display_cols].copy()

        # 3. Calculate Subtotals (Grouping by Department)
        df_subtotal = df_display.groupby('department', as_index=False)[['Total Budget', 'MN_issued', 'Remaining Budget']].sum()
        df_subtotal['cost_area'] = '--- SUBTOTAL ---' # Identifier for subtotal row
        
        # 4. Combine and Sort the DataFrames
        final_df = pd.concat([df_display, df_subtotal], ignore_index=True)
        final_df = final_df.sort_values(by=['department', 'cost_area'], ascending=[True, True])
        
        # Rename the column back to title case for display only
        final_df = final_df.rename(columns={'department': 'Department'})
        
        # 5. Format the Table Appearance
        def style_balance_sheet(row):
            if row['cost_area'] == '--- SUBTOTAL ---':
                return ['font-weight: bold; background-color: #f0f2f6'] * len(row)
            return [''] * len(row)
        
        # Apply the styling to rows
        styled_df = final_df.style.apply(style_balance_sheet, axis=1).format({
            'Total Budget': 'BDT {:,.2f}',
            'MN_issued': 'BDT {:,.2f}',
            'Remaining Budget': 'BDT {:,.2f}'
        })

        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Download CSV option (uses the unstyled final_df)
        st.download_button(
            label="Download Balance Sheet CSV",
            data=final_df.to_csv(index=False).encode('utf-8'),
            file_name='budget_balance_sheet.csv',
            mime='text/csv',
            key='download_balance'
        )

        # 6. Display Grand Totals
        st.markdown("---")
        col_g1, col_g2, col_g3 = st.columns(3)
        col_g1.metric("Grand Total Budget", f"BDT {total_budget:,.2f}")
        col_g2.metric("Grand Total MN Issued", f"BDT {total_spent:,.2f}")
        col_g3.metric("Grand Total Remaining", f"BDT {remaining:,.2f}")

    # --- TAB 4: BUDGET SETUP & IMPORT (ADMIN ONLY) ---
    elif page == "Budget Setup & Import":
        if st.session_state['role'] != 'administrator':
            st.error("🚫 Access Denied: Only Administrators can access Budget Setup.")
            st.stop()

        st.title("⚙️ Budget Configuration & Import 2026")
        
        st.header("1. Import Budget from File")
        st.markdown("**Expected Columns:** `Department`, `Cost Area`, `Total Budget`")
        
        uploaded_file = st.file_uploader("Upload Budget File (CSV or XLSX)", type=['csv', 'xlsx'])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    budget_df = pd.read_csv(uploaded_file)
                else:
                    budget_df = pd.read_excel(uploaded_file, engine='openpyxl')
                    
                budget_df.columns = [col.strip().replace(' ', '_').replace('.', '_').lower() for col in budget_df.columns]
                required_cols = ['department', 'cost_area', 'total_budget']

                if not all(col in budget_df.columns for col in required_cols):
                    st.error(f"Error: Missing required columns: {', '.join([col for col in required_cols if col not in budget_df.columns])}.")
                else:
                    st.subheader("Preview of Data to Import:")
                    st.dataframe(budget_df[required_cols])
                    
                    if st.button("Confirm and Import/Update Budgets"):
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        rows_imported = 0
                        for index, row in budget_df.iterrows():
                            # UPSERT command: INSERT OR REPLACE
                            c.execute('''
                                INSERT OR REPLACE INTO budget_heads (cost_area, department, total_budget) 
                                VALUES (?, ?, ?)
                            ''', (row['cost_area'], row['department'], row['total_budget']))
                            rows_imported += 1
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Successfully imported/updated {rows_imported} budget heads.")
                        st.rerun()
            except Exception as e:
                st.error(f"An unexpected error occurred during file processing: {e}")

        # --- MANUAL ENTRY OPTION ---
        st.header("2. Manual Budget Entry")
        st.markdown("Use this form to add a new budget or quickly adjust an existing one.")
        
        # Manual Entry Form 
        with st.form("manual_budget_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                dept = st.text_input("Department (e.g., Production)")
            with col2:
                area = st.text_input("Cost Area Name (e.g., Line-1, Generator)")
            with col3:
                amount = st.number_input("Approved Budget 2026 (BDT)", min_value=0.0, format="%.2f")
            
            submit_budget = st.form_submit_button("Manually Add/Update Budget Head")
            
            if submit_budget:
                if dept and area and amount > 0:
                    try:
                        execute_query("INSERT OR REPLACE INTO budget_heads (cost_area, department, total_budget) VALUES (?, ?, ?)",
                                      (area, dept, amount))
                        st.success(f"Added/Updated {area} with budget {amount:,.2f}")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Database error. Please check the Cost Area name.")
                else:
                    st.warning("Please fill all manual entry fields.")

        # Display current budget allocations
        st.subheader("Current Master Budget Data")
        current_budget_df = load_data("SELECT * FROM budget_heads")
        st.dataframe(current_budget_df, use_container_width=True)
        
        # Download CSV option
        st.download_button(
            label="Download Budget Data CSV",
            data=current_budget_df.to_csv(index=False).encode('utf-8'),
            file_name='master_budget_data.csv',
            mime='text/csv',
            key='download_budget_data'
        )

        # --- CLEAR BUDGET DATA OPTION ---
        st.markdown("---")
        st.header("3. Danger Zone (Clear Data)")
        st.markdown("Use this to clear all existing budget allocations to start fresh for a new fiscal year. **This does NOT delete request history.**")
        
        if st.button("🔴 CLEAR ALL BUDGET DATA", help="This action cannot be undone!", type="secondary"):
            execute_query("DELETE FROM budget_heads")
            st.warning("🗑️ All budget data has been cleared!")
            st.rerun()


    # --- TAB 5: USERS & ACCESS CONTROL (ADMIN ONLY) ---
    elif page == "Users & Access Control":
        if st.session_state['role'] != 'administrator':
            st.error("🚫 Access Denied: Only Administrators can access User and Configuration settings.")
            st.stop()
            
        st.title("👥 User Creation & Access Management")
        
        # --- CONFIGURATION FORM ---
        st.header("1. Financial Configuration (Admin Only)")
        config_data = load_data("SELECT key, value FROM exchange_config")
        config_dict = config_data.set_index('key')['value'].to_dict()
        
        with st.form("financial_config_form"):
            st.subheader("Currency Exchange Rates (1 Unit = BDT)")
            col_rates = st.columns(5)
            # Fetch existing rates or use defaults
            usd = col_rates[0].number_input("USD Rate", value=config_dict.get('USD_rate', 110.00), min_value=0.01)
            eur = col_rates[1].number_input("EUR Rate", value=config_dict.get('EUR_rate', 120.00), min_value=0.01)
            gbp = col_rates[2].number_input("GBP Rate", value=config_dict.get('GBP_rate', 130.00), min_value=0.01)
            inr = col_rates[3].number_input("INR Rate", value=config_dict.get('INR_rate', 1.50), min_value=0.01)
            other = col_rates[4].number_input("Other Currency Rate", value=config_dict.get('OTHER_rate', 100.00), min_value=0.01)

            st.subheader("Customs Duty")
            # Customs Duty is in percentage (0.05 for 5%)
            duty = st.number_input("Customs Duty % (e.g., input 0.05 for 5%)", 
                                   value=config_dict.get('CustomsDuty_pct', 0.05), 
                                   min_value=0.00, 
                                   max_value=1.0,
                                   format="%.4f")
            
            if st.form_submit_button("Save Configuration"):
                updates = [
                    ('USD_rate', usd), ('EUR_rate', eur), ('GBP_rate', gbp), 
                    ('INR_rate', inr), ('OTHER_rate', other), ('CustomsDuty_pct', duty)
                ]
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                for key, value in updates:
                    c.execute("INSERT OR REPLACE INTO exchange_config (key, value) VALUES (?, ?)", (key, value))
                conn.commit()
                conn.close()
                st.success("Financial configuration updated successfully!")
                st.rerun()

        st.markdown("---")
        st.header("2. Create New User")
        with st.form("new_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type='password')
            with col2:
                new_role = st.selectbox("Role", ["user", "administrator"])
            
            if st.form_submit_button("Create User"):
                if new_username and new_password:
                    try:
                        hashed_pwd = make_hashes(new_password)
                        execute_query("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                                      (new_username, hashed_pwd, new_role))
                        st.success(f"User **{new_username}** created with role **{new_role}**.")
                        st.rerun() 
                    except sqlite3.IntegrityError:
                        st.error("Username already exists. Please choose a different name.")
                else:
                    st.warning("Username and Password cannot be empty.")
        
        st.subheader("3. Existing Users")
        users_df = load_data("SELECT id, username, role FROM users")
        st.dataframe(users_df, use_container_width=True)
        
        # Download CSV option
        st.download_button(
            label="Download User List CSV",
            data=users_df.to_csv(index=False).encode('utf-8'),
            file_name='user_list.csv',
            mime='text/csv',
            key='download_users'
        )

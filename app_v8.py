import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import hashlib 
import io 

# --- CUSTOM CSS FOR PROFESSIONAL LOOK & BUTTON NAVIGATION ---
PRIMARY_COLOR = "#007A8A"  # Dark Teal/Professional Blue-Green
SECONDARY_BACKGROUND = "#F5F5F5" # Light Gray
# UPDATED PEPSI LOGO URL
PEPSI_LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/e/ea/Pepsi_2023.svg"

st.markdown(f"""
<style>
/* Global Background Color */
.stApp {{
    background-color: white;
}}
/* Sidebar Background Color */
.st-emotion-cache-12fmw5b {{ /* Target sidebar container */
    background-color: {SECONDARY_BACKGROUND}; 
}}

/* 1. Target the specific radio input containers in the sidebar */
.st-emotion-cache-1xt5sqs {{ /* This targets the outer container of the radio buttons */
    padding: 0;
}}
/* 2. Style the radio option labels to look like buttons */
.st-emotion-cache-1627u5h {{ /* This targets the label wrapper for each radio option */
    padding: 0;
}}
div.stRadio > label {{
    /* Style the labels to look like buttons */
    background-color: #E0E0E0; /* Slightly darker than background for contrast */
    color: #0e1117; /* Dark text */
    border-radius: 5px; 
    border: 1px solid #ccc;
    margin: 5px 0; /* Vertical spacing between "buttons" */
    padding: 10px 15px; /* Internal padding */
    width: 100%; /* Ensure full width of the sidebar */
    transition: all 0.2s ease-in-out;
    display: block; /* Important to make the whole area clickable */
    font-weight: bold;
    cursor: pointer;
    box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
}}
/* 3. Style the selected (checked) button */
div.stRadio > label:has(input:checked) {{
    background-color: {PRIMARY_COLOR}; /* Primary Teal for selected */
    color: white; 
    border-color: {PRIMARY_COLOR};
}}
/* 4. Style hover effect */
div.stRadio > label:hover:not(:has(input:checked)) {{
    background-color: #D3D3D3; /* Slightly darker gray on hover */
    border-color: #bbb;
}}
/* 5. Hide the actual radio circle input element */
div.stRadio > label > div > div > div > input[type="radio"] {{
    position: absolute; /* Take out of flow */
    opacity: 0; /* Make invisible */
}}
/* 6. Ensure the text content is centered or nicely aligned */
div.stRadio > label > div > div {{
    display: flex;
    align-items: center;
    justify-content: flex-start; /* Align text to the left */
    gap: 10px; /* Space between icon/radio element and text */
}}
/* 7. Style the app title/header */
.st-emotion-cache-10trblm {{
    color: {PRIMARY_COLOR};
    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}}
/* Custom class for the logo to control its size */
.pepsi-logo {{
    max-width: 150px;
    height: auto;
    display: block;
    margin: 0 auto 20px auto; /* Center the image */
}}
</style>
""", unsafe_allow_html=True)
# --- END CUSTOM CSS ---


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
    
    # Table 2: Maintenance Notifications / Requests 
    c.execute('''CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mn_number TEXT UNIQUE, -- Added UNIQUE constraint
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

    # Table 4: Exchange Rate and Duty Configuration
    c.execute('''CREATE TABLE IF NOT EXISTS exchange_config (
                    key TEXT PRIMARY KEY,
                    value REAL
                )''')
                
    # Table 5: Event Log
    c.execute('''CREATE TABLE IF NOT EXISTS event_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    username TEXT,
                    action_type TEXT, -- e.g., 'BUDGET_UPDATE', 'USER_CREATE', 'MN_STATUS_CHANGE'
                    description TEXT
                )''')
                
    # Table 6: LC/PO and Payment Tracker (NEW)
    c.execute('''
        CREATE TABLE IF NOT EXISTS lc_po_tracker (
            mn_number TEXT PRIMARY KEY,
            lc_po_nr TEXT,
            lc_po_date TEXT,
            eta_shipment_delivery TEXT,
            delivery_completed TEXT, -- 'Yes' or 'No'
            date_of_delivery TEXT,
            commercial_store_remarks TEXT,
            delay_days INTEGER,
            bill_submitted_vendor TEXT, -- Local Supplier Only field
            bill_tracking_id TEXT,
            date_bill_submit_acc TEXT,
            date_bill_submit_ho TEXT,
            bill_paid TEXT, -- 'Yes' or 'No'
            actual_lc_costing REAL, -- Foreign Supplier Only field
            FOREIGN KEY(mn_number) REFERENCES requests(mn_number)
        )
    ''')


    # Initialize default configuration values if not present
    default_config = {
        'USD_rate': 110.00, 'EUR_rate': 120.00, 'GBP_rate': 130.00, 
        'INR_rate': 1.50, 'OTHER_rate': 100.00, 'CustomsDuty_pct': 0.05
    }
    for key, value in default_config.items():
        c.execute("INSERT OR IGNORE INTO exchange_config (key, value) VALUES (?, ?)", (key, value))
        
    conn.commit()
    
    # Create a default admin user if none exists or update password if it exists
    admin_username = 'admin'
    admin_new_password_hash = make_hashes("admin1024098") # Updated default password
    
    c.execute("SELECT COUNT(*) FROM users WHERE username=?", (admin_username,))
    if c.fetchone()[0] == 0:
        # Insert new admin
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                  (admin_username, admin_new_password_hash, 'administrator'))
    else:
        # Update existing admin password to the new default
        c.execute("UPDATE users SET password_hash = ? WHERE username = ?",
                  (admin_new_password_hash, admin_username))
                  
    conn.commit()
    
    conn.close()

# --- DATABASE INTERACTION FUNCTIONS ---
def load_data(query, params=()):
    """
    Loads data from the SQL database using a query and optional parameters.
    """
    conn = sqlite3.connect(DB_FILE)
    if params:
        df = pd.read_sql(query, conn, params=params)
    else:
        df = pd.read_sql(query, conn)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

# --- LOGGING FUNCTIONS ---
def log_event(action_type, description):
    """Records an event into the event_log table."""
    username = st.session_state.get('username', 'SYSTEM')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_query('''INSERT INTO event_log (timestamp, username, action_type, description)
                     VALUES (?, ?, ?, ?)''', 
                     (timestamp, username, action_type, description))
    
def get_event_logs():
    """Retrieves all event logs."""
    return load_data("SELECT * FROM event_log ORDER BY timestamp DESC")

# --- CORE FUNCTION: Budget vs. Cost Status Calculation ---
@st.cache_data
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
st.set_page_config(page_title="TBL R&M Tracker 2026", layout="wide")
init_db()

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
# New session state for persistent submission message
if 'mn_submission_result' not in st.session_state:
    st.session_state['mn_submission_result'] = None
if 'mn_submission_status' not in st.session_state:
    st.session_state['mn_submission_status'] = None
# New session state for LC/PO Tracker details visibility
if 'show_mn_details' not in st.session_state:
    st.session_state['show_mn_details'] = False


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
                # Invalidate cache to fetch new data after login
                calculate_status.clear()
                st.rerun() 
            else:
                st.sidebar.error("Incorrect Password")
        else:
            st.sidebar.error("User not found")

    st.sidebar.markdown("---")
    
    # --- DISPLAY USERS ---
    st.sidebar.subheader("Registered Users")
    users_df = load_data("SELECT username, role FROM users ORDER BY username")
    if not users_df.empty:
        # Mark the currently logged-in user as 'Active' for clarity (though this list is in the sidebar for all)
        users_df['Status'] = users_df['username'].apply(
            lambda x: 'Active' if x == st.session_state.get('username') and st.session_state['logged_in'] else 'Inactive'
        )
        
        # Format the display slightly
        users_df.rename(columns={'username': 'Username', 'role': 'Role'}, inplace=True)
        st.sidebar.dataframe(users_df[['Username', 'Role', 'Status']], use_container_width=True, hide_index=True)
    else:
        st.sidebar.info("No users registered.")
    
# --- LOGOUT FUNCTION ---
def logout():
    st.session_state['logged_in'] = False
    st.session_state['role'] = None
    st.session_state['username'] = None
    # Clear the submission message on logout
    st.session_state['mn_submission_result'] = None
    st.session_state['mn_submission_status'] = None
    st.session_state['show_mn_details'] = False # Reset tracker visibility
    st.rerun()

# --- MAIN APPLICATION LOGIC ---
if not st.session_state['logged_in']:
    # Display Pepsi Logo
    st.markdown(f'<img src="{PEPSI_LOGO_URL}" class="pepsi-logo">', unsafe_allow_html=True)
    
    login_page()
    st.title("TBL R&M Tracker 2026 - Please Log In")
else:
    # Sidebar Navigation and Logout Button
    st.sidebar.markdown(f"**Logged in as:** **{st.session_state['username']}** ({st.session_state['role'].title()})")
    if st.sidebar.button("Logout"):
        logout()
        
    # --- MENU ITEMS WITH EMOJIS ---
    menu = ["🔎 View & Filter Requests", "📝 New Request (MN)"]
    if st.session_state['role'] == 'administrator':
        menu.append("📊 Budget Balance Sheet") 
        menu.append("💰 LC/PO & Payment Tracker") # NEW TAB
        menu.append("⚙️ Budget Setup & Import")
        menu.append("👥 Users & Access Control")
        menu.append("📜 Event Log")
        
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Go to", menu)
    st.sidebar.markdown("---")
    
    # Remove the icon for the page title display to keep the title cleaner
    page_name = page.split(' ', 1)[-1].strip()

    # --- TAB 1: VIEW & FILTER REQUESTS ---
    if page_name == "View & Filter Requests":
        # Clear any old submission message when changing tabs
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False

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
                # Filter by Supplier Type
                selected_supplier_type = st.multiselect("Filter by Supplier Type", requests_df['supplier_type'].unique(), default=[])

            # Apply Filters
            filtered_df = requests_df.copy()
            if selected_status:
                filtered_df = filtered_df[filtered_df['status'].isin(selected_status)]
            if selected_area:
                filtered_df = filtered_df[filtered_df['cost_area'].isin(selected_area)]
            if selected_supplier_type:
                filtered_df = filtered_df[filtered_df['supplier_type'].isin(selected_supplier_type)]
            
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
                    
                    display_options = [f"ID {row['id']} - MN: {row['mn_number']} ({row['status']})" for index, row in update_df.iterrows()]
                    selected_display = col_u1.selectbox("Select Request to Update", options=display_options)
                    
                    selected_id = None
                    current_status = "Pending"
                    if selected_display:
                        try:
                            selected_id = int(selected_display.split(' - ')[0].replace('ID ', ''))
                            current_status = update_df[update_df['id'] == selected_id]['status'].iloc[0]
                        except Exception:
                            pass
                    
                    new_status = col_u2.selectbox("New Status", workflow_statuses, index=workflow_statuses.index(current_status) if current_status in workflow_statuses else 0)
                        
                    if st.form_submit_button("Apply Status Change"):
                        if selected_id:
                            execute_query("UPDATE requests SET status = ? WHERE id = ?", (new_status, selected_id))
                            # LOGGING STATUS CHANGE
                            log_event("MN_STATUS_CHANGE", f"MN ID {selected_id} status changed from {current_status} to {new_status}.")
                            calculate_status.clear()
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

    # --- TAB 2: NEW REQUEST (MN) ---
    elif page_name == "New Request (MN)":
        # Clear any old submission message when changing tabs
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False

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
        
        
        # 1. GENERAL & CATEGORIZATION 
        st.subheader("1. General & Categorization")
        col1, col2, col3 = st.columns(3)
        with col1:
            mn_issue_date = st.date_input("MN Issue Date *", value=datetime.now(), help="Date the MN was officially issued.")
            requester = st.text_input("Requester Name", value=st.session_state['username'], disabled=True)
            mn_category = st.selectbox("MN Category *", ["R&M (Repair & Maintenance)", "C&C (Chemicals & Consumables)"], index=None)
        with col2:
            mn_no = st.text_input("MN Number * (e.g., DHK/001/26)")
            selected_department = st.selectbox("Department *", departments, index=None, key="mn_dept_select", help="Selecting a Department will filter the Cost Area list.")
        with col3:
            # DYNAMIC DROPDOWN LOGIC
            cost_areas_filtered = []
            if selected_department:
                cost_areas_filtered = budgets[budgets['department'] == selected_department]['cost_area'].unique().tolist()
                
            area = st.selectbox("Cost Area *", sorted(cost_areas_filtered), index=None, key="mn_area_select", help="The specific Cost Center being charged.")
            location = st.text_input("Location *")
        
        mn_particulars = st.text_area("MN Particulars/Detailed Description of Work * (Max 200 chars)", max_chars=200)

        
        # 2. FINANCIAL & PROCUREMENT DETAILS 
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
            st.caption(f"*(Duty Rate: {customs_duty_pct:.2%} | {currency} Rate: {exchange_rate:.4f} BDT)*")


        # 3. TIMELINE & REMARKS
        st.subheader("3. Timeline & Remarks")
        col_date, col_remarks = st.columns([1, 2])
        with col_date:
            date_sent_ho = st.date_input("Date of Sending To HO *", value=datetime.now())
        with col_remarks:
            plant_remarks = st.text_area("Plant Remarks/Notes") # NOT mandatory
        
        st.markdown("---")


        # --- SUBMISSION LOGIC (UPDATED MESSAGE POSITION) ---
        with st.form("mn_submission_form"):
            st.markdown("*Fields marked with a **\*** are mandatory.")
            
            # --- MESSAGE CONTAINER MOVED HERE ---
            message_container = st.empty()
            
            # Display the stored submission message if available
            if st.session_state['mn_submission_result']:
                if st.session_state['mn_submission_status'] == 'success':
                    message_container.success(st.session_state['mn_submission_result'])
                elif st.session_state['mn_submission_status'] == 'error':
                    message_container.error(st.session_state['mn_submission_result'])
                # Clear the message so it doesn't persist forever, but stays until next input
                st.session_state['mn_submission_result'] = None
                st.session_state['mn_submission_status'] = None

            submitted = st.form_submit_button("Submit Request")
            
            if submitted:
                # Reset container placeholder to clear previous message during processing
                message_container.empty()

                # --- MANDATORY FIELD CHECK ---
                required_fields = [
                    (mn_no, "MN Number"), (mn_category, "MN Category"), (selected_department, "Department"), (area, "Cost Area"), 
                    (location, "Location"), (supplier_vendor, "Supplier/Vendor"), (supplier_type, "Supplier Type"), (currency, "Currency"),
                    (mn_particulars, "MN Particulars"), (date_sent_ho, "Date of Sending To HO")
                ]
                required_costs = [foreign_spare_cost, freight_fca_charges, local_cost_wo_vat_ait, vat_ait]
                
                missing_fields = [label for value, label in required_fields if value is None or (isinstance(value, str) and not value.strip())]
                cost_invalid = any(c < 0 for c in required_costs) or landed_total_cost <= 0
                
                if missing_fields or cost_invalid:
                    error_msg = "⚠️ Please fill in all mandatory fields (*)."
                    if missing_fields:
                        error_msg += f" Missing: {', '.join(missing_fields)}."
                    if cost_invalid:
                        error_msg += " Landed Total Cost must be greater than 0."
                    message_container.error(error_msg)
                    st.stop() 

                # --- DUPLICATE CHECK ---
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT mn_number FROM requests WHERE mn_number = ?", (mn_no,))
                if c.fetchone():
                    conn.close()
                    message_container.error(f"❌ Duplicate Submission Error: An MN request with number **{mn_no}** already exists. Please check the MN Number or the existing requests list.")
                    st.stop()
                conn.close()
                
                # --- BUDGET CHECK ---
                df_status, _, _, _ = calculate_status()
                target_area = df_status[df_status['cost_area'] == area]
                
                if target_area.empty:
                    message_container.error("Could not find budget data for the selected Cost Center.")
                    st.stop()

                curr_remaining = target_area['Remaining Balance'].iloc[0]
                
                if landed_total_cost > curr_remaining:
                    message_container.error(f"⚠️ Budget Exceeded! Cost Area **'{area}'** only has **{curr_remaining:,.2f} BDT** remaining. Submission aborted.")
                    st.stop()

                # --- DB INSERTION ---
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
                # Invalidate cache to reflect new utilized cost
                calculate_status.clear()

                # Set session state flags for successful message display on RERUN
                st.session_state['mn_submission_result'] = f"✅ Request **{mn_no}** submitted successfully! Input fields cleared for a new entry."
                st.session_state['mn_submission_status'] = 'success'
                
                # Force rerun to clear all inputs outside the form and display the persistent message
                st.rerun() 


    # --- TAB 3: BUDGET BALANCE SHEET ---
    elif page_name == "Budget Balance Sheet":
        # Clear any old submission message when changing tabs
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False

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

    # --- TAB 4: LC/PO & PAYMENT TRACKER (FIXED) ---
    elif page_name == "LC/PO & Payment Tracker":
        # Clear any old submission message when changing tabs
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None

        if st.session_state['role'] != 'administrator':
            st.error("🚫 Access Denied: Only Administrators can access the LC/PO Tracker.")
            st.stop()
            
        st.title("💰 LC/PO & Payment Tracker")
        st.markdown("Track the procurement and payment progress for **Finance Approved** MN Requests.")
        
        # 1. Fetch Finance Approved Requests
        approved_requests = load_data("""
            SELECT mn_number, mn_particulars, cost_area, supplier_vendor, date_sent_ho, supplier_type
            FROM requests 
            WHERE status IN ('Finance Approved', 'PO Issued') 
            ORDER BY date_sent_ho DESC
        """)
        
        if approved_requests.empty:
            st.info("No MN requests are currently at the 'Finance Approved' or 'PO Issued' stage for tracking.")
            st.session_state['show_mn_details'] = False # Ensure details are hidden if no data exists
            st.stop()
            
        # Add a blank option to force selection
        mn_options = ['--- Select an MN Reference ID ---'] + approved_requests['mn_number'].tolist()
        
        # 2. MN Selection Form
        with st.form("mn_tracker_select_form"):
            col_select, col_button = st.columns([3, 1])
            selected_mn = col_select.selectbox("Select MN Reference ID to Track/Update *", mn_options, index=0, key="tracker_mn_select")
            
            is_mn_selected = selected_mn != '--- Select an MN Reference ID ---'
            
            # Button to trigger details visibility
            if col_button.form_submit_button("Show Details", type="primary"):
                if is_mn_selected:
                    st.session_state['show_mn_details'] = True
                else:
                    st.session_state['show_mn_details'] = False
                    st.error("Please select a valid MN Reference ID.")
            
            # Only proceed with complex fetching and rendering if the MN is selected AND the details flag is set
            if st.session_state['show_mn_details'] and is_mn_selected:
                
                # Fetch existing tracker data or initialize empty
                tracker_df = load_data("SELECT * FROM lc_po_tracker WHERE mn_number = ?", (selected_mn,))
                tracker_data = {}
                if not tracker_df.empty:
                    tracker_data = tracker_df.iloc[0].to_dict()
                
                request_data = approved_requests[approved_requests['mn_number'] == selected_mn].iloc[0].to_dict()
                
                # Helper function to safely convert DB string date to date object
                def safe_date_input(key, default_date_str=None):
                    if tracker_data.get(key):
                        try:
                            # Use default value if parsing fails
                            return datetime.strptime(tracker_data[key], "%Y-%m-%d").date()
                        except ValueError:
                            pass
                    
                    # Use today's date if no default string is provided and conversion failed
                    if default_date_str == str(date.today()):
                        return date.today()
                        
                    return None
                    
                # --- START DISPLAYING DETAILS AND INPUT FIELDS ---
                st.markdown("---")
                st.subheader("Selected MN Details")
                
                col_d1, col_d2, col_d3 = st.columns(3)
                col_d1.info(f"**Cost Area:** {request_data.get('cost_area')}")
                col_d2.info(f"**Supplier:** {request_data.get('supplier_vendor')}")
                col_d3.info(f"**Supplier Type:** {request_data.get('supplier_type')}")
                st.markdown(f"**MN Particulars:** *{request_data.get('mn_particulars')}*")

                st.markdown("---")
                st.subheader("Procurement & Payment Inputs")
                
                # --- INPUT FIELDS ---
                col1, col2 = st.columns(2)
                
                # Procurement/LC Details
                lc_po_nr = col1.text_input("LC Nr. / PO Nr.", value=tracker_data.get('lc_po_nr', ''))
                lc_po_date_val = safe_date_input('lc_po_date')
                lc_po_date = col2.date_input("Date of LC/PO", value=lc_po_date_val, key="lc_po_date", disabled=not is_mn_selected)
                
                col3, col4 = st.columns(2)
                eta_shipment_val = safe_date_input('eta_shipment_delivery')
                eta_shipment = col3.date_input("ETA Shipment/Delivery Date", value=eta_shipment_val, key="mn_eta", disabled=not is_mn_selected)
                
                delivery_completed = col4.selectbox("Delivery Completed?", 
                                                    options=['No', 'Yes'], 
                                                    index=['No', 'Yes'].index(tracker_data.get('delivery_completed', 'No')),
                                                    key="delivery_completed_select", disabled=not is_mn_selected)
                
                date_of_delivery_val = safe_date_input('date_of_delivery')
                date_of_delivery = st.date_input("Date of Delivery", value=date_of_delivery_val, key="mn_delivery_date", disabled=not is_mn_selected)
                
                commercial_remarks = st.text_area("Commercial / Store Remarks", value=tracker_data.get('commercial_store_remarks', ''), disabled=not is_mn_selected)
                
                st.markdown("---")
                
                # Delay Calculation (LC/PO Date - Date Sent HO)
                delay_days = 0
                date_ho = datetime.strptime(request_data['date_sent_ho'], "%Y-%m-%d").date()
                if lc_po_date:
                    delay_days = (lc_po_date - date_ho).days
                    st.info(f"Calculated Delay: **{delay_days} days** (LC/PO Date to Date Sent HO)")
                else:
                    st.info("Delay will be calculated once the LC/PO Date is entered.")

                st.markdown("---")
                
                # Payment Details
                st.subheader("Bill & Payment Tracking")
                
                col5, col6 = st.columns(2)
                
                # Local Supplier Specific Field
                bill_submitted_vendor = tracker_data.get('bill_submitted_vendor', '')
                if request_data.get('supplier_type') == 'Local':
                    bill_submitted_vendor = col5.text_input("Bill Submitted by Vendor (Local Supplier)", value=bill_submitted_vendor, disabled=not is_mn_selected)
                
                bill_tracking_id = col6.text_input("Bill Tracking ID", value=tracker_data.get('bill_tracking_id', ''), disabled=not is_mn_selected)
                
                col7, col8, col9 = st.columns(3)
                date_bill_acc_val = safe_date_input('date_bill_submit_acc')
                date_bill_acc = col7.date_input("Date of Bill Submit to Acc.", value=date_bill_acc_val, key="mn_bill_acc_date", disabled=not is_mn_selected)
                
                date_bill_ho_val = safe_date_input('date_bill_submit_ho')
                date_bill_ho = col8.date_input("Date of Bill Submit to HO", value=date_bill_ho_val, key="mn_bill_ho_date", disabled=not is_mn_selected)
                
                bill_paid = col9.selectbox("Bill Paid?", 
                                           options=['No', 'Yes'], 
                                           index=['No', 'Yes'].index(tracker_data.get('bill_paid', 'No')),
                                           key="bill_paid_select", disabled=not is_mn_selected)
                
                # Foreign Supplier Specific Field
                actual_lc_costing = tracker_data.get('actual_lc_costing', 0.0)
                if request_data.get('supplier_type') == 'Foreign':
                    actual_lc_costing = st.number_input("Actual LC Costing (Foreign Supplier)", min_value=0.0, format="%.2f", value=float(actual_lc_costing), disabled=not is_mn_selected)
                
                st.markdown("---")
            
            # --- SUBMIT BUTTON ---
            submitted = st.form_submit_button("Update LC/PO & Payment Data")
            
            if submitted:
                if not is_mn_selected:
                    st.error("Please select an MN Reference ID before submitting.")
                elif not st.session_state['show_mn_details']:
                    st.error("Please click 'Show Details' first to load the data for the selected MN.")
                else:
                    # Logic runs only if MN is selected and details were shown/updated
                    # Ensure date fields are formatted as strings for storage
                    # Check if date inputs are not None before calling strftime
                    lc_po_date_str = lc_po_date.strftime("%Y-%m-%d") if lc_po_date else None
                    eta_shipment_str = eta_shipment.strftime("%Y-%m-%d") if eta_shipment else None
                    date_of_delivery_str = date_of_delivery.strftime("%Y-%m-%d") if date_of_delivery else None
                    date_bill_acc_str = date_bill_acc.strftime("%Y-%m-%d") if date_bill_acc else None
                    date_bill_ho_str = date_bill_ho.strftime("%Y-%m-%d") if date_bill_ho else None
                    
                    # Update requests table status if PO number is entered and status is 'Finance Approved'
                    status_df = load_data("SELECT status FROM requests WHERE mn_number = ?", (selected_mn,))
                    current_mn_status = status_df.iloc[0]['status'] if not status_df.empty else None

                    if lc_po_nr and current_mn_status == 'Finance Approved':
                        execute_query("UPDATE requests SET status = 'PO Issued' WHERE mn_number = ?", (selected_mn,))
                        log_event("MN_STATUS_CHANGE", f"MN {selected_mn} status changed to 'PO Issued' by LC/PO entry.")
                    
                    # UPSERT (Insert or Update) logic
                    query = """
                        INSERT INTO lc_po_tracker (
                            mn_number, lc_po_nr, lc_po_date, eta_shipment_delivery, delivery_completed, date_of_delivery, 
                            commercial_store_remarks, delay_days, bill_submitted_vendor, bill_tracking_id, 
                            date_bill_submit_acc, date_bill_submit_ho, bill_paid, actual_lc_costing
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(mn_number) DO UPDATE SET
                            lc_po_nr=excluded.lc_po_nr, lc_po_date=excluded.lc_po_date, 
                            eta_shipment_delivery=excluded.eta_shipment_delivery, delivery_completed=excluded.delivery_completed, 
                            date_of_delivery=excluded.date_of_delivery, commercial_store_remarks=excluded.commercial_store_remarks, 
                            delay_days=excluded.delay_days, bill_submitted_vendor=excluded.bill_submitted_vendor, 
                            bill_tracking_id=excluded.bill_tracking_id, date_bill_submit_acc=excluded.date_bill_submit_acc, 
                            date_bill_submit_ho=excluded.date_bill_submit_ho, bill_paid=excluded.bill_paid, 
                            actual_lc_costing=excluded.actual_lc_costing
                    """
                    params = (
                        selected_mn, lc_po_nr, lc_po_date_str, eta_shipment_str, delivery_completed, date_of_delivery_str, 
                        commercial_remarks, delay_days, bill_submitted_vendor, bill_tracking_id, 
                        date_bill_acc_str, date_bill_ho_str, bill_paid, actual_lc_costing
                    )
                    
                    execute_query(query, params)
                    log_event("LC_PO_UPDATE", f"Updated LC/PO tracker for MN {selected_mn}. LC/PO: {lc_po_nr}.")
                    st.success(f"Successfully updated tracking data for MN **{selected_mn}**.")
                    st.session_state['show_mn_details'] = False # Hide details after update
                    st.rerun()

        st.markdown("---")
        # 3. Display Updated Tracking Table
        st.header("LC/PO Tracking Data")
        
        # Join requests and lc_po_tracker for a complete view
        tracker_display_df = load_data("""
            SELECT
                r.mn_number,
                r.mn_particulars,
                r.cost_area,
                r.supplier_vendor,
                r.supplier_type,
                r.status,
                t.lc_po_nr,
                t.lc_po_date,
                t.eta_shipment_delivery,
                t.delivery_completed,
                t.date_of_delivery,
                t.delay_days,
                t.bill_tracking_id,
                t.bill_paid
            FROM requests r
            INNER JOIN lc_po_tracker t ON r.mn_number = t.mn_number
        """)
        
        if tracker_display_df.empty:
            st.info("No tracking entries have been created yet.")
        else:
            # Smart Filtering for the Display Table
            st.subheader("Filter Tracking Table")
            
            col_t1, col_t2, col_t3 = st.columns(3)
            
            filter_po = col_t1.text_input("Filter by LC/PO Number")
            filter_delivery = col_t2.multiselect("Filter by Delivery Status", tracker_display_df['delivery_completed'].unique(), default=[])
            filter_paid = col_t3.multiselect("Filter by Bill Paid Status", tracker_display_df['bill_paid'].unique(), default=[])
            
            filtered_tracker = tracker_display_df.copy()
            if filter_po:
                filtered_tracker = filtered_tracker[filtered_tracker['lc_po_nr'].str.contains(filter_po, case=False, na=False)]
            if filter_delivery:
                filtered_tracker = filtered_tracker[filtered_tracker['delivery_completed'].isin(filter_delivery)]
            if filter_paid:
                filtered_tracker = filtered_tracker[filtered_tracker['bill_paid'].isin(filter_paid)]
                
            st.dataframe(filtered_tracker, use_container_width=True)
            
            st.download_button(
                label="Download Tracking Data CSV",
                data=filtered_tracker.to_csv(index=False).encode('utf-8'),
                file_name='lc_po_tracker_data.csv',
                mime='text/csv',
                key='download_tracker_data'
            )


    # --- TAB 5: BUDGET SETUP & IMPORT ---
    elif page_name == "Budget Setup & Import":
        # Clear any old submission message when changing tabs
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False

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
                        # LOGGING BUDGET IMPORT
                        log_event("BUDGET_IMPORT", f"Imported/updated {rows_imported} budget heads via file upload.")
                        calculate_status.clear()
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
                        # LOGGING MANUAL BUDGET UPDATE
                        log_event("BUDGET_UPDATE", f"Manually updated/added budget for {area} to {amount:,.2f} BDT.")
                        calculate_status.clear()
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
            # LOGGING BUDGET CLEAR
            log_event("BUDGET_CLEAR", "Cleared ALL data from the budget_heads table.")
            calculate_status.clear()
            st.warning("🗑️ All budget data has been cleared!")
            st.rerun()


    # --- TAB 6: USERS & ACCESS CONTROL ---
    elif page_name == "Users & Access Control":
        # Clear any old submission message when changing tabs
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False

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
                # LOGGING CONFIG UPDATE
                log_event("CONFIG_UPDATE", f"Updated Financial Config: Duty={duty:.2%}, Rates=USD:{usd}, EUR:{eur}, GBP:{gbp}, INR:{inr}, OTHER:{other}.")
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
                        # LOGGING USER CREATION
                        log_event("USER_CREATE", f"Created new user '{new_username}' with role '{new_role}'.")
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

    # --- TAB 7: EVENT LOG ---
    elif page_name == "Event Log":
        # Clear any old submission message when changing tabs
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False
        
        if st.session_state['role'] != 'administrator':
            st.error("🚫 Access Denied: Only Administrators can view the Event Log.")
            st.stop()
            
        st.title("📜 Application Event Log (Admin Audit)")
        st.markdown("Displays critical actions performed by users and the system.")
        
        df_logs = get_event_logs()
        
        if df_logs.empty:
            st.info("No events have been logged yet.")
        else:
            # Reorder and rename columns for display
            df_logs = df_logs[['timestamp', 'username', 'action_type', 'description']]
            df_logs.rename(columns={
                'timestamp': 'Time',
                'username': 'User',
                'action_type': 'Action Type',
                'description': 'Details'
            }, inplace=True)
            
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
            
            # Download CSV option
            st.download_button(
                label="Download Event Log CSV",
                data=df_logs.to_csv(index=False).encode('utf-8'),
                file_name='application_event_log.csv',
                mime='text/csv',
                key='download_event_log'
            )

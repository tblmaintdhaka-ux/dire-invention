import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, date
import hashlib 
import io 
import re

main_logo = "https://tbl.com.bd/frontend/img/products/3.png"
icon_logo = "https://tbl.com.bd/frontend/img/products/3.png" 

st.logo(main_logo, icon_image=icon_logo)
with st.sidebar:
    # Use st.image for more direct control
    st.image("https://tbl.com.bd/frontend/img/products/3.png", width=90)
    st.markdown("---") # Adds a nice divider line
    
# Custom CSS to define specific icon size
st.markdown(
    """
    <style>
        /* 1. Target the logo container and remove standard height restrictions */
        [data-testid="stLogo"] {
            height: 100px !important; 
            max-height: 100px !important; /* Ensure max-height isn't capping it at 48px */
            width: auto !important;
        }

        /* 2. Target the image inside the container */
        [data-testid="stLogo"] img {
            height: 100px !important; 
            width: auto !important;
            max-width: 100% !important;
            object-fit: contain; /* Prevents stretching */
        }
        
        /* 3. Adjust sidebar navigation padding to prevent the logo from overlapping items */
        [data-testid="stSidebarNav"] {
            padding-top: 120px !important; /* Increase this to match your logo height */
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- CUSTOM CSS FOR PROFESSIONAL LOOK & BUTTON NAVIGATION ---
PRIMARY_COLOR = "#007A8A"  # Dark Teal/Professional Blue-Green
SECONDARY_BACKGROUND = "#F5F5F5" # Light Gray
PEPSI_LOGO_URL = "https://tbl.com.bd/tbl/img/tbl.png"

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
    max-width: 300px;
    height: auto;
    display: block;
    margin: 0 0 20px 0; /* Left align the image */
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
                    mn_number TEXT UNIQUE, 
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

    # Table 4: Message Board
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
                
    # Table 6: LC/PO and Payment Tracker
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

    # Table 7: Indent Purchase Record (Main Record Header)
    c.execute('''
        CREATE TABLE IF NOT EXISTS indent_purchase_record (
            bill_no TEXT PRIMARY KEY, 
            indent_no TEXT,
            grn_no TEXT,
            supplier TEXT,
            bill_date TEXT,
            payment_mode TEXT,
            total_bill_amount REAL,
            remarks TEXT
        )
    ''')

    # Table 8: Indent Goods Details (Line Items)
    c.execute('''
        CREATE TABLE IF NOT EXISTS indent_goods_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_no TEXT, -- Stores the bill_no from the header table
            description TEXT,
            quantity REAL,
            unit TEXT,
            rate REAL,
            amount REAL,
            FOREIGN KEY(bill_no) REFERENCES indent_purchase_record(bill_no)
        )
    ''')

    # Updated Table 9: Independent Indent Records (Standalone)
    c.execute('''CREATE TABLE IF NOT EXISTS standalone_indents (
                    indent_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    indent_number TEXT,
                    item_description TEXT,
                    quantity REAL,
                    unit TEXT,
                    rate REAL,
                    total_amount REAL,
                    indent_date TEXT,
                    supplier TEXT,
                    status TEXT DEFAULT 'Not Purchased'
                )''')
    
        # Migration: Add status column if it doesn't exist in older DB versions
    try:
        c.execute("ALTER TABLE standalone_indents ADD COLUMN status TEXT DEFAULT 'Not Purchased'")
    except sqlite3.OperationalError:
        pass # Column already exists

    # Initialize default configuration values if not present
    default_config = {
        'USD_rate': 110.00, 'EUR_rate': 120.00, 'GBP_rate': 130.00, 
        'INR_rate': 1.50, 'OTHER_rate': 100.00, 'CustomsDuty_pct': 0.05
    }

    # This loop MUST be indented inside the function
    for key, value in default_config.items():
        c.execute("INSERT OR IGNORE INTO exchange_config (key, value) VALUES (?, ?)", (key, value))
    
    conn.commit()

    # Create a default admin user
    admin_username = 'admin'
    admin_new_password_hash = make_hashes("admin1024098")

    c.execute("SELECT COUNT(*) FROM users WHERE username=?", (admin_username,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                (admin_username, admin_new_password_hash, 'administrator'))
    else:
        c.execute("UPDATE users SET password_hash = ? WHERE username = ?",
                (admin_new_password_hash, admin_username))
                
    conn.commit()
    conn.close() # Close connection only at the very end of the function

# --- DATABASE INTERACTION FUNCTIONS ---
def load_data(query, params=()):
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
    username = st.session_state.get('username', 'SYSTEM')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_query('''INSERT INTO event_log (timestamp, username, action_type, description)
                     VALUES (?, ?, ?, ?)''', 
                     (timestamp, username, action_type, description))
    
def get_event_logs():
    return load_data("SELECT * FROM event_log ORDER BY timestamp DESC")

# --- CORE FUNCTION: Budget vs. Cost Status Calculation ---
@st.cache_data
def calculate_status():
    budgets = load_data("SELECT * FROM budget_heads")
    requests = load_data("SELECT * FROM requests")

    if budgets.empty:
        return pd.DataFrame(), 0, 0, 0 

    budgets['total_budget'] = pd.to_numeric(budgets['total_budget'], errors='coerce').fillna(0)
    
    if not requests.empty:
        requests['landed_total_cost'] = pd.to_numeric(requests['landed_total_cost'], errors='coerce').fillna(0)
        
        # 1. Calculate Total Utilized (MN_issued) - All except Rejected
        spent_by_area = requests[requests['status'] != 'Rejected'].groupby('cost_area')['landed_total_cost'].sum().reset_index()
        
        # 2. NEW: Calculate MN_approved (Criteria: Finance Approved, PO Issued, Completed)
        approved_statuses = ["Finance Approved", "PO Issued", "Completed"]
        approved_by_area = requests[requests['status'].isin(approved_statuses)].groupby('cost_area')['landed_total_cost'].sum().reset_index()
        approved_by_area.rename(columns={'landed_total_cost': 'MN_approved'}, inplace=True)
        
        # Merge data
        merged = pd.merge(budgets, spent_by_area, on='cost_area', how='left').fillna(0)
        merged = pd.merge(merged, approved_by_area, on='cost_area', how='left').fillna(0)
    else:
        merged = budgets.copy()
        merged['landed_total_cost'] = 0
        merged['MN_approved'] = 0
            
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


def message_board():
    st.title("📋 Community Message Board")
    
    # Message Input Section
    with st.form("message_form", clear_on_submit=True):
        user_msg = st.text_area("Post a message for all users:", placeholder="Type your update here...")
        submit = st.form_submit_button("Post Message")
        
        if submit and user_msg.strip():
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO messages (username, message) VALUES (?, ?)", 
                      (st.session_state['username'], user_msg))
            conn.commit()
            conn.close()
            st.success("Message posted!")
            st.rerun()

    st.markdown("---")
    
    # Display Messages Section
    messages_df = load_data("SELECT username, message, timestamp FROM messages ORDER BY timestamp DESC LIMIT 50")
    
    if not messages_df.empty:
        for index, row in messages_df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.markdown(f"**{row['username']}**")
                    st.caption(f"{row['timestamp']}")
                with col2:
                    st.write(row['message'])
    else:
        st.info("No messages yet. Be the first to post!")

# --- APP LAYOUT ---
st.set_page_config(page_title="TBL R&M Tracker 2026", layout="wide")
init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'current_goods_data' not in st.session_state:
    st.session_state['current_goods_data'] = []
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'mn_submission_result' not in st.session_state:
    st.session_state['mn_submission_result'] = None
if 'mn_submission_status' not in st.session_state:
    st.session_state['mn_submission_status'] = None
if 'show_mn_details' not in st.session_state:
    st.session_state['show_mn_details'] = False
if 'show_admin_edit' not in st.session_state:
    st.session_state['show_admin_edit'] = False
if 'edit_mn_id' not in st.session_state:
    st.session_state['edit_mn_id'] = None


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
                calculate_status.clear()
                st.rerun() 
            else:
                st.sidebar.error("Incorrect Password")
        else:
            st.sidebar.error("User not found")

    st.sidebar.markdown("---")
    
    st.sidebar.subheader("Registered Users")
    users_df = load_data("SELECT username, role FROM users ORDER BY username")
    if not users_df.empty:
        users_df['Status'] = users_df['username'].apply(
            lambda x: 'Active' if x == st.session_state.get('username') and st.session_state['logged_in'] else 'Inactive'
        )
        users_df.rename(columns={'username': 'Username', 'role': 'Role'}, inplace=True)
        st.sidebar.dataframe(users_df[['Username', 'Role', 'Status']], width='stretch', hide_index=True)
    else:
        st.sidebar.info("No users registered.")
    
# --- LOGOUT FUNCTION ---
def logout():
    st.session_state['logged_in'] = False
    st.session_state['role'] = None
    st.session_state['username'] = None
    st.session_state['mn_submission_result'] = None
    st.session_state['mn_submission_status'] = None
    st.session_state['show_mn_details'] = False
    st.session_state['show_admin_edit'] = False
    st.session_state['edit_mn_id'] = None
    st.rerun()

# --- MAIN APPLICATION LOGIC ---
if not st.session_state['logged_in']:
    st.markdown(f'<img src="{PEPSI_LOGO_URL}" class="pepsi-logo">', unsafe_allow_html=True)
    login_page()
    st.title("TBL R&M Tracker 2026 - Please Log In")
else:
# --- MAIN APPLICATION LOGIC ---
    # ... (login check) ...
    st.sidebar.markdown(f"**Logged in as:** **{st.session_state['username']}** ({st.session_state['role'].title()})")
    if st.sidebar.button("Logout"):
        logout()
        
    # --- NEW DYNAMIC MENU LOGIC ---
    role = st.session_state['role']
    
    # Define available pages for each role
    # User: Requests (View), Balance Sheet, Tracker, Indent
    if role == 'user':
        menu = ["🔎 View & Filter Requests", "📝 New Request (MN)", "📊 Budget Balance Sheet", "📋 Message Board", "💰 LC/PO & Payment Tracker", "🛒 Indent & Purchase Record"]
    
    # Super: All accept "Users & Access Control" & "Budget Setup & Import"
    elif role == 'super':
        menu = [
            "🔎 View & Filter Requests", 
            "📝 New Request (MN)", 
            "📊 Budget Balance Sheet", 
            "📋 Message Board",
            "💰 LC/PO & Payment Tracker", 
            "🛒 Indent & Purchase Record", 
            "📜 Event Log"
        ]
        
    # Administrator: All pages
    else: # administrator
        menu = [
            "🔎 View & Filter Requests", 
            "📝 New Request (MN)", 
            "📊 Budget Balance Sheet", 
            "📋 Message Board",
            "💰 LC/PO & Payment Tracker", 
            "🛒 Indent & Purchase Record", 
            "⚙️ Budget Setup & Import",
            "👥 Users & Access Control",
            "📜 Event Log"
        ]
        
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Go to", menu)
    st.sidebar.markdown("---")
    page_name = page.split(' ', 1)[-1].strip()

    if page_name == "View & Filter Requests":
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False
        
        st.title("🔍 Existing Entries & Tracking Status")
        
        budgets = load_data("SELECT cost_area, department FROM budget_heads")
        config_data = load_data("SELECT key, value FROM exchange_config")
        config_dict = config_data.set_index('key')['value'].to_dict()
        
        fx_rates = {
            "BDT": 1.0, 
            "USD": config_dict.get('USD_rate', 110.00), 
            "EUR": config_dict.get('EUR_rate', 120.00),
            "GBP": config_dict.get('GBP_rate', 130.00),
            "INR": config_dict.get('INR_rate', 1.50),
            "Other": config_dict.get('OTHER_rate', 100.00)
        }
        customs_duty_pct = config_dict.get('CustomsDuty_pct', 0.05)
        
        df_status, total_budget, total_spent, remaining = calculate_status()
        
        if not df_status.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Budget 2026 (BDT)", f"{total_budget:,.2f}")
            col2.metric("Total Utilized Cost", f"{total_spent:,.2f}")
            col3.metric("Remaining Balance", f"{remaining:,.2f}")
            st.markdown("---")

        requests_df = load_data("SELECT * FROM requests")
        
        if requests_df.empty:
            st.info("No requests found.")
        else:
            st.subheader("🛠️ Admin Tools (Edit & Status Update)")
            action_df = requests_df.sort_values(by='date_logged', ascending=False)
            action_options = ['--- Select a Request ID to Action ---'] + [
                f"ID {row['id']} - MN: {row['mn_number']} ({row['status']})" 
                for index, row in action_df.iterrows()
            ]

            col_a1, col_a2 = st.columns(2)
            selected_action_display = col_a1.selectbox("Select Request for Action", options=action_options, key="admin_action_select")
            
            selected_id = None
            if selected_action_display != '--- Select a Request ID to Action ---':
                try:
                    selected_id = int(selected_action_display.split(' - ')[0].replace('ID ', ''))
                except Exception:
                    pass
            
            if st.session_state['role'] == 'administrator':
                workflow_statuses = ["Pending", "Approved by SRPM", "Approved by AD", "Finance Approved", "Rejected", "PO Issued", "Completed"]
                
                with col_a2.form("status_update_form", clear_on_submit=True):
                    current_status = action_df[action_df['id'] == selected_id]['status'].iloc[0] if selected_id else "Pending"
                    new_status = st.selectbox("New Status", workflow_statuses, 
                                              index=workflow_statuses.index(current_status) if current_status in workflow_statuses else 0,
                                              key="new_status_select")
                        
                    if st.form_submit_button("Apply Status Change"):
                        if selected_id:
                            execute_query("UPDATE requests SET status = ? WHERE id = ?", (new_status, selected_id))
                            log_event("MN_STATUS_CHANGE", f"MN ID {selected_id} status changed from {current_status} to {new_status}.")
                            calculate_status.clear()
                            st.success(f"Status for Request ID {selected_id} updated to **{new_status}**.")
                            st.rerun()
                        else:
                            st.warning("Please select a request.")
                            
                if selected_id and col_a1.button(f"✏️ Edit ID {selected_id} Details", type="secondary"):
                    st.session_state['show_admin_edit'] = True
                    st.session_state['edit_mn_id'] = selected_id
                    st.rerun()
            
            st.markdown("---")
            
            if st.session_state['show_admin_edit'] and st.session_state['edit_mn_id']:
                edit_id = st.session_state['edit_mn_id']
                record_to_edit_df = load_data("SELECT * FROM requests WHERE id = ?", (edit_id,))
                if record_to_edit_df.empty:
                    st.error(f"Could not find request with ID {edit_id}.")
                    st.session_state['show_admin_edit'] = False
                    st.session_state['edit_mn_id'] = None
                    st.stop()
                
                original_data = record_to_edit_df.iloc[0].to_dict()
                original_landed_cost = original_data['landed_total_cost']
                original_cost_area = original_data['cost_area']
                st.header(f"✏️ Editing Request ID: {edit_id} (MN: {original_data['mn_number']})")
                departments = sorted(budgets['department'].unique().tolist())
                
                with st.form("admin_edit_form"):
                    st.subheader("1. General & Categorization")
                    col1, col2, col3 = st.columns(3)
                    issue_date_val = datetime.strptime(original_data['mn_issue_date'], "%Y-%m-%d").date()
                    date_ho_val = datetime.strptime(original_data['date_sent_ho'], "%Y-%m-%d").date()
                    
                    with col1:
                        mn_issue_date = st.date_input("MN Issue Date *", value=issue_date_val)
                        st.text_input("Requester Name (Read-Only)", value=original_data['requester'], disabled=True)
                        mn_category = st.selectbox("MN Category *", ["R&M (Repair & Maintenance)", "C&C (Chemicals & Consumables)"], 
                                                   index=["R&M (Repair & Maintenance)", "C&C (Chemicals & Consumables)"].index(original_data['mn_category']))
                    with col2:
                        mn_no_new = st.text_input("MN Number * (e.g., DHK/001/26)", value=original_data['mn_number'])
                        selected_department = st.selectbox("Department *", departments, 
                                                           index=departments.index(original_data['department']))
                    with col3:
                        cost_areas_filtered = budgets[budgets['department'] == selected_department]['cost_area'].unique().tolist()
                        area = st.selectbox("Cost Area *", sorted(cost_areas_filtered), 
                                            index=sorted(cost_areas_filtered).index(original_data['cost_area']))
                        location = st.text_input("Location *", value=original_data['location'])
                    
                    mn_particulars = st.text_area("MN Particulars/Detailed Description of Work * (Max 200 chars)", 
                                                  max_chars=200, value=original_data['mn_particulars'])

                    st.subheader("2. Financial & Procurement Details")
                    col_supp, col_curr, col_cost1, col_cost2 = st.columns(4)
                    with col_supp:
                        supplier_vendor = st.text_input("Supplier/Vendor *", value=original_data['supplier_vendor'])
                        supplier_type = st.selectbox("Supplier Type *", ["Local", "Foreign"], 
                                                     index=["Local", "Foreign"].index(original_data['supplier_type']))
                    currency_list = list(fx_rates.keys())
                    currency = col_curr.selectbox("Currency *", currency_list, index=currency_list.index(original_data['currency']))
                    col_curr.info(f"Rate: 1 {currency} = **{fx_rates.get(currency):.4f} BDT**")
                    with col_cost1:
                        foreign_spare_cost = st.number_input("Foreign Spare Cost *", min_value=0.0, format="%.2f", 
                                                             value=original_data['foreign_spare_cost'], key="edit_mn_fsc")
                        freight_fca_charges = st.number_input("Freight & FCA Charges *", min_value=0.0, format="%.2f", 
                                                              value=original_data['freight_fca_charges'], key="edit_mn_ffc")
                    with col_cost2:
                        local_cost_wo_vat_ait = st.number_input("Local Cost without VAT & AIT *", min_value=0.0, format="%.2f", 
                                                                value=original_data['local_cost_wo_vat_ait'], key="edit_mn_lcwa")
                        vat_ait = st.number_input("VAT & AIT *", min_value=0.0, format="%.2f", 
                                                  value=original_data['vat_ait'], key="edit_mn_va")
                        exchange_rate = fx_rates.get(currency, 1.0)
                        landed_total_cost_new = (
                            (foreign_spare_cost * (1 + customs_duty_pct)) + 
                            freight_fca_charges
                        ) * exchange_rate + local_cost_wo_vat_ait + vat_ait
                        st.markdown(f"**New Landed Total Cost (BDT):**")
                        st.markdown(f"## {landed_total_cost_new:,.2f}")
                        
                    st.subheader("3. Timeline & Remarks")
                    col_date, col_remarks = st.columns([1, 2])
                    with col_date:
                        date_sent_ho = st.date_input("Date of Sending To HO *", value=date_ho_val)
                    with col_remarks:
                        plant_remarks = st.text_area("Plant Remarks/Notes", value=original_data['plant_remarks'])

                    st.markdown("---")
                    col_save, col_cancel = st.columns(2)
                    save_button = col_save.form_submit_button("💾 Save Edited Request", type="primary")
                    cancel_button = col_cancel.form_submit_button("❌ Cancel Edit", type="secondary")
                    
                    if cancel_button:
                        st.session_state['show_admin_edit'] = False
                        st.session_state['edit_mn_id'] = None
                        st.rerun()

                    if save_button:
                        required_fields = [
                            (mn_no_new, "MN Number"), (mn_category, "MN Category"), (selected_department, "Department"), (area, "Cost Area"), 
                            (location, "Location"), (supplier_vendor, "Supplier/Vendor"), (supplier_type, "Supplier Type"), (currency, "Currency"),
                            (mn_particulars, "MN Particulars"), (date_sent_ho, "Date of Sending To HO")
                        ]
                        missing_fields = [label for value, label in required_fields if value is None or (isinstance(value, str) and not value.strip())]
                        if missing_fields or landed_total_cost_new <= 0:
                            error_msg = "⚠️ Please fill in all mandatory fields (*)."
                            if missing_fields: error_msg += f" Missing: {', '.join(missing_fields)}."
                            if landed_total_cost_new <= 0: error_msg += " Landed Total Cost must be greater than 0."
                            st.error(error_msg)
                            st.stop() 

                        if mn_no_new != original_data['mn_number']:
                            conn = sqlite3.connect(DB_FILE)
                            c = conn.cursor()
                            c.execute("SELECT mn_number FROM requests WHERE mn_number = ?", (mn_no_new,))
                            if c.fetchone():
                                conn.close()
                                st.error(f"❌ Duplicate MN Error: An MN request with number **{mn_no_new}** already exists.")
                                st.stop()
                            conn.close()
                            
                        df_status, _, _, _ = calculate_status()
                        old_area_status = df_status[df_status['cost_area'] == original_cost_area]
                        if area != original_cost_area:
                            new_area_status = df_status[df_status['cost_area'] == area]
                            new_area_remaining = new_area_status['Remaining Balance'].iloc[0]
                            if landed_total_cost_new > new_area_remaining:
                                st.error(f"⚠️ Budget Exceeded in new Cost Area! '{area}' only has **{new_area_remaining:,.2f} BDT** remaining.")
                                st.stop()
                        else:
                            current_remaining = old_area_status['Remaining Balance'].iloc[0]
                            available_after_removal = current_remaining + original_landed_cost
                            if landed_total_cost_new > available_after_removal:
                                st.error(f"⚠️ Budget Exceeded! '{area}' can only support an updated cost of up to **{available_after_removal:,.2f} BDT**.")
                                st.stop()

                        date_issue_str = mn_issue_date.strftime("%Y-%m-%d")
                        date_ho_str = date_sent_ho.strftime("%Y-%m-%d")
                        update_query = '''UPDATE requests SET
                                mn_number = ?, mn_issue_date = ?, cost_area = ?, estimated_cost = ?,
                                mn_particulars = ?, mn_category = ?, department = ?, location = ?, 
                                supplier_vendor = ?, supplier_type = ?, currency = ?, foreign_spare_cost = ?, 
                                freight_fca_charges = ?, customs_duty_rate = ?, local_cost_wo_vat_ait = ?, 
                                vat_ait = ?, landed_total_cost = ?, date_sent_ho = ?, plant_remarks = ?
                            WHERE id = ?'''
                        params = (
                            mn_no_new, date_issue_str, area, landed_total_cost_new,
                            mn_particulars, mn_category, selected_department, location,
                            supplier_vendor, supplier_type, currency, foreign_spare_cost,
                            freight_fca_charges, customs_duty_pct, local_cost_wo_vat_ait,
                            vat_ait, landed_total_cost_new, date_ho_str, plant_remarks,
                            edit_id
                        )
                        execute_query(update_query, params)
                        calculate_status.clear()
                        log_event("MN_ADMIN_EDIT", f"Request ID {edit_id} (MN: {mn_no_new}) was edited by admin.")
                        st.success(f"✅ Request ID **{edit_id}** (MN: {mn_no_new}) updated successfully!")
                        st.session_state['show_admin_edit'] = False
                        st.session_state['edit_mn_id'] = None
                        st.rerun()

            st.subheader("Filter Requests")
            col_filter_1, col_filter_2, col_filter_3 = st.columns(3)
            with col_filter_1:
                selected_status = st.multiselect("Filter by Status", requests_df['status'].unique(), default=[])
            with col_filter_2:
                selected_area = st.multiselect("Filter by Cost Center", requests_df['cost_area'].unique(), default=[])
            with col_filter_3:
                selected_supplier_type = st.multiselect("Filter by Supplier Type", requests_df['supplier_type'].unique(), default=[])

            filtered_df = requests_df.copy()
            if selected_status: filtered_df = filtered_df[filtered_df['status'].isin(selected_status)]
            if selected_area: filtered_df = filtered_df[filtered_df['cost_area'].isin(selected_area)]
            if selected_supplier_type: filtered_df = filtered_df[filtered_df['supplier_type'].isin(selected_supplier_type)]
            
            st.markdown("---")
            st.subheader("All Request Fields")
            st.dataframe(filtered_df, width='stretch')
            st.download_button(
                label="Download Filtered Requests CSV",
                data=filtered_df.to_csv(index=False).encode('utf-8'),
                file_name='filtered_requests.csv',
                mime='text/csv',
                key='download_requests'
            )

    # --- TAB 2: NEW REQUEST (MN) ---
    elif page_name == "New Request (MN)":

        st.session_state['show_mn_details'] = False
        st.session_state['show_admin_edit'] = False
        st.session_state['edit_mn_id'] = None
        st.title("📝 Create New Management Notification")

        budgets = load_data("SELECT cost_area, department FROM budget_heads")
        config_data = load_data("SELECT key, value FROM exchange_config")
        config_dict = config_data.set_index('key')['value'].to_dict()
        
        fx_rates = {
            "BDT": 1.0, 
            "USD": config_dict.get('USD_rate', 110.00), 
            "EUR": config_dict.get('EUR_rate', 120.00),
            "GBP": config_dict.get('GBP_rate', 130.00),
            "INR": config_dict.get('INR_rate', 1.50),
            "Other": config_dict.get('OTHER_rate', 100.00)
        }
        customs_duty_pct = config_dict.get('CustomsDuty_pct', 0.05)

        if budgets.empty:
            st.warning("No Department or Cost Area data found. Please set up budgets first.")
            st.stop()
        
        departments = sorted(budgets['department'].unique().tolist())

        # Display persistent success/error message
        if st.session_state['mn_submission_result']:
            if st.session_state['mn_submission_status'] == 'success':
                st.success(st.session_state['mn_submission_result'])
            elif st.session_state['mn_submission_status'] == 'error':
                st.error(st.session_state['mn_submission_result'])
            # We no longer clear it immediately here to allow it to be visible after the rerun
        
        st.subheader("1. General & Categorization")
        col1, col2, col3 = st.columns(3)
        with col1:
            mn_issue_date = st.date_input("MN Issue Date *", value=datetime.now())
            requester = st.text_input("Requester Name", value=st.session_state['username'], disabled=True)
            mn_category = st.selectbox("MN Category *", ["R&M (Repair & Maintenance)", "C&C (Chemicals & Consumables)"], index=None)
        with col2:
            mn_no = st.text_input("MN Number * (Format: DHK/001/2026)")
            selected_department = st.selectbox("Department *", departments, index=None, key="mn_dept_select")
        with col3:
            cost_areas_filtered = []
            if selected_department:
                cost_areas_filtered = budgets[budgets['department'] == selected_department]['cost_area'].unique().tolist()
            area = st.selectbox("Cost Area *", sorted(cost_areas_filtered), index=None, key="mn_area_select")
            location = st.text_input("Location *")
        mn_particulars = st.text_area("MN Particulars/Detailed Description of Work * (Max 200 chars)", max_chars=200)

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
            exchange_rate = fx_rates.get(currency, 1.0)
            landed_total_cost = (
                (foreign_spare_cost * (1 + customs_duty_pct)) + 
                freight_fca_charges
            ) * exchange_rate + local_cost_wo_vat_ait + vat_ait
            st.markdown(f"**Calculated Landed Total Cost (BDT):**")
            st.markdown(f"## {landed_total_cost:,.2f}")
            st.caption(f"*(Duty Rate: {customs_duty_pct:.2%} | {currency} Rate: {exchange_rate:.4f} BDT)*")

        st.subheader("3. Timeline & Remarks")
        col_date, col_remarks = st.columns([1, 2])
        with col_date:
            date_sent_ho = st.date_input("Date of Sending To HO *", value=datetime.now())
        with col_remarks:
            plant_remarks = st.text_area("Plant Remarks/Notes")
        st.markdown("---")

        with st.form("mn_submission_form"):
            st.markdown("*Fields marked with a * or ** are mandatory.")
            submitted = st.form_submit_button("Submit Request")
            if st.session_state['mn_submission_result']:
                if st.session_state['mn_submission_status'] == 'success':
                    st.success(st.session_state['mn_submission_result'])
                elif st.session_state['mn_submission_status'] == 'error':
                    st.error(st.session_state['mn_submission_result'])            
            if submitted:
                # 1. MN Number Regex Validation
                # Pattern explains: 3 uppercase letters / 3 digits / 4 digits
                mn_pattern = r"^[A-Z]{3}/\d{3}/\d{4}$"
                
                if not mn_no:
                    st.error("MN Number is required.")
                elif not re.match(mn_pattern, mn_no):
                    st.error("❌ Invalid MN Number format! Please use 'AAA/000/0000' (e.g., DHK/001/2026).")
                else:
                    # 2. Existing validation for other fields
                    required_fields = [
                        (mn_no, "MN Number"), (mn_category, "MN Category"), (selected_department, "Department"), 
                        (area, "Cost Area"), (location, "Location"), (supplier_vendor, "Supplier/Vendor"), 
                        (supplier_type, "Supplier Type"), (currency, "Currency"), (mn_particulars, "MN Particulars"), 
                        (date_sent_ho, "Date of Sending To HO")
                    ]
                missing_fields = [label for value, label in required_fields if value is None or (isinstance(value, str) and not value.strip())]
                
                # Reset previous result on new attempt
                st.session_state['mn_submission_result'] = None
                st.session_state['mn_submission_status'] = None

                if missing_fields or landed_total_cost <= 0:
                    error_msg = "⚠️ Please fill in all mandatory fields (*)."
                    if missing_fields: error_msg += f" Missing: {', '.join(missing_fields)}."
                    if landed_total_cost <= 0: error_msg += " Landed Total Cost must be greater than 0."
                    st.session_state['mn_submission_result'] = error_msg
                    st.session_state['mn_submission_status'] = 'error'
                    st.rerun()
                
                # Check for Duplicate MN Request
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT mn_number FROM requests WHERE mn_number = ?", (mn_no,))
                if c.fetchone():
                    conn.close()
                    st.session_state['mn_submission_result'] = f"❌ Duplicate Submission Error: MN {mn_no} already exists."
                    st.session_state['mn_submission_status'] = 'error'
                    st.rerun()
                conn.close()

                df_status, _, _, _ = calculate_status()
                target_area = df_status[df_status['cost_area'] == area]
                curr_remaining = target_area['Remaining Balance'].iloc[0]
                if landed_total_cost > curr_remaining:
                    st.session_state['mn_submission_result'] = f"⚠️ Budget Exceeded! '{area}' only has **{curr_remaining:,.2f} BDT** remaining."
                    st.session_state['mn_submission_status'] = 'error'
                    st.rerun()

                date_issue_str = mn_issue_date.strftime("%Y-%m-%d")
                date_ho_str = date_sent_ho.strftime("%Y-%m-%d")
                query = '''INSERT INTO requests (
                            mn_number, mn_issue_date, date_logged, requester, cost_area, estimated_cost, 
                            status, mn_particulars, mn_category, department, location, 
                            supplier_vendor, supplier_type, currency, foreign_spare_cost, 
                            freight_fca_charges, customs_duty_rate, local_cost_wo_vat_ait, 
                            vat_ait, landed_total_cost, date_sent_ho, plant_remarks
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
                
                params = (
                    mn_no, date_issue_str, datetime.now().strftime("%Y-%m-%d"), 
                    requester, area, landed_total_cost, "Pending", 
                    mn_particulars, mn_category, selected_department, location, 
                    supplier_vendor, supplier_type, currency, foreign_spare_cost, 
                    freight_fca_charges, customs_duty_pct, local_cost_wo_vat_ait, 
                    vat_ait, landed_total_cost, date_ho_str, plant_remarks
                )
                execute_query(query, params)
                calculate_status.clear()
                st.session_state['mn_submission_result'] = f"✅ MN Request Successful: Request **{mn_no}** submitted successfully!"
                st.session_state['mn_submission_status'] = 'success'
                st.rerun()

    # --- TAB 3: BUDGET BALANCE SHEET ---
    elif page_name == "Budget Balance Sheet":
        # Reset unrelated session states
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False
        st.session_state['show_admin_edit'] = False
        st.session_state['edit_mn_id'] = None

        # Initialize local session states for drill-down
        if 'bb_selected_status' not in st.session_state:
            st.session_state.bb_selected_status = None
        if 'bb_selected_mn' not in st.session_state:
            st.session_state.bb_selected_mn = None

        st.title("📊 Budget Balance Sheet (Departmental Subtotals)")
        
        # Fetch data
        df_status, total_budget, total_spent, remaining = calculate_status()
    
        if df_status.empty:
            st.info("No budget data found.")
            st.stop()

        # --- 1. FINANCIAL BAR CHART ---
        st.subheader("Budget vs. Expenditure Overview")
        total_approved = df_status['MN_approved'].sum()
        chart_df = pd.DataFrame({
            "Metric": ["Total Budget", "MN Issued (Utilized)", "MN Approved", "Remaining Budget"],
            "Amount (BDT)": [total_budget, total_spent, total_approved, remaining]
        })
        
        fig_bar = px.bar(
            chart_df, 
            x="Metric", 
            y="Amount (BDT)", 
            color="Metric",
            text="Amount (BDT)",
            color_discrete_map={
                "Total Budget": "#008080", 
                "MN Issued (Utilized)": "#FFA500", 
                "MN Approved": "#2ECC71", 
                "Remaining Budget": "#E74C3C"
            }
        )
        fig_bar.update_traces(texttemplate='%{text:,.2s}', textposition='outside')
        fig_bar.update_layout(showlegend=False, height=450, margin=dict(t=30))
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

        # --- 2. MN REQUEST STATUS SUMMARY & DRILL-DOWN ---
        st.subheader("MN Request Status Summary")
        status_raw = load_data("SELECT status, mn_number FROM requests")
        
        if not status_raw.empty:
            counts = status_raw['status'].value_counts().reset_index()
            counts.columns = ['Status', 'Count']
            
            sc1, sc2 = st.columns([1, 1])
            
            with sc1:
                # Pie Chart
                fig_pie = px.pie(
                    counts, 
                    values='Count', 
                    names='Status', 
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
                st.plotly_chart(fig_pie, use_container_width=True)

            with sc2:
                # Metrics with "link-like" buttons
                st.write("**Click a number to view MNs:**")
                for _, row in counts.iterrows():
                    # Display metric and a button for drill-down
                    col_m, col_b = st.columns([2, 3])
                    col_m.metric(row['Status'], row['Count'])
                    if col_b.button(f"List {row['Status']} MNs", key=f"drill_{row['Status']}"):
                        st.session_state.bb_selected_status = row['Status']
                        st.session_state.bb_selected_mn = None # Reset MN choice

            # Drill-down view
            if st.session_state.bb_selected_status:
                st.markdown(f"### MNs for Status: `{st.session_state.bb_selected_status}`")
                mn_list = status_raw[status_raw['status'] == st.session_state.bb_selected_status]['mn_number'].tolist()
                
                sel_mn = st.selectbox("Select an MN number for overview", ["-- Select --"] + mn_list)
                if sel_mn != "-- Select --":
                    mn_full = load_data(f"SELECT * FROM requests WHERE mn_number = '{sel_mn}'")
                    if not mn_full.empty:
                        d = mn_full.iloc[0]
                        with st.container(border=True):
                            st.markdown(f"#### Overview: {sel_mn}")
                            c_a, c_b = st.columns(2)
                            c_a.write(f"**Requester:** {d['requester']}")
                            c_a.write(f"**Dept:** {d['department']}")
                            c_a.write(f"**Cost Area:** {d['cost_area']}")
                            c_b.write(f"**Est. Cost:** BDT {d['estimated_cost']:,.2f}")
                            c_b.write(f"**Date Logged:** {d['date_logged']}")
                            c_b.write(f"**Category:** {d['mn_category']}")
                            st.write(f"**Particulars:** {d['mn_particulars']}")
                
                if st.button("Close Drill-down"):
                    st.session_state.bb_selected_status = None
                    st.rerun()

        else:
            st.info("No MN requests recorded yet.")

        st.markdown("---")

        # --- 3. DETAILED BREAKDOWN TABLE ---
        st.subheader("Detailed Departmental Breakdown")
        df_status = df_status.rename(columns={
            'total_budget': 'Total Budget',
            'Total Utilized Cost': 'MN_issued',
            'Remaining Balance': 'Remaining Budget'
        })

        display_cols = ['department', 'cost_area', 'Total Budget', 'MN_issued', 'MN_approved', 'Remaining Budget']
        df_display = df_status[display_cols].copy()

        val_cols = ['Total Budget', 'MN_issued', 'MN_approved', 'Remaining Budget']
        df_subtotal = df_display.groupby('department', as_index=False)[val_cols].sum()
        df_subtotal['cost_area'] = '--- SUBTOTAL ---'

        final_df = pd.concat([df_display, df_subtotal], ignore_index=True)
        final_df = final_df.sort_values(by=['department', 'cost_area'], ascending=[True, True])
        final_df = final_df.rename(columns={'department': 'Department'})

        def style_balance_sheet(row):
            if row['cost_area'] == '--- SUBTOTAL ---':
                return ['font-weight: bold; background-color: #f0f2f6'] * len(row)
            return [''] * len(row)

        styled_df = final_df.style.apply(style_balance_sheet, axis=1).format({
            'Total Budget': 'BDT {:,.2f}',
            'MN_issued': 'BDT {:,.2f}',
            'MN_approved': 'BDT {:,.2f}',
            'Remaining Budget': 'BDT {:,.2f}'
        })

        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        st.download_button(
            label="Download Balance Sheet CSV",
            data=final_df.to_csv(index=False).encode('utf-8'),
            file_name='budget_balance_sheet.csv',
            mime='text/csv'
        )
    elif page_name == "Message Board":
        message_board()
    elif page_name == "LC/PO & Payment Tracker":
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_admin_edit'] = False
        st.session_state['edit_mn_id'] = None
            
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
                # CHANGED: "Bill Submitted by Vendor" is now a Yes/No option for Local Suppliers
                bill_submitted_vendor = tracker_data.get('bill_submitted_vendor', 'No')
                if request_data.get('supplier_type') == 'Local':
                    bill_submitted_vendor = col5.selectbox("Bill Submitted by Vendor (Local Supplier)?", ["No", "Yes"], 
                                                           index=["No", "Yes"].index(bill_submitted_vendor) if bill_submitted_vendor in ["No", "Yes"] else 0,
                                                           disabled=not is_mn_selected)
                else:
                    bill_submitted_vendor = col5.text_input("Bill Submitted by Vendor (Foreign Supplier)", 
                                                           value=bill_submitted_vendor, disabled=not is_mn_selected)
                
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
            
            # CHANGED: Added supplier_type to the filtering options
            col_t1, col_t2, col_t3, col_t4 = st.columns(4)
            
            filter_po = col_t1.text_input("Filter by LC/PO Number")
            filter_supp_type = col_t2.multiselect("Filter by Supplier Type", tracker_display_df['supplier_type'].unique(), default=[])
            filter_delivery = col_t3.multiselect("Filter by Delivery Status", tracker_display_df['delivery_completed'].unique(), default=[])
            filter_paid = col_t4.multiselect("Filter by Bill Paid Status", tracker_display_df['bill_paid'].unique(), default=[])
            
            filtered_tracker = tracker_display_df.copy()
            if filter_po:
                filtered_tracker = filtered_tracker[filtered_tracker['lc_po_nr'].str.contains(filter_po, case=False, na=False)]
            if filter_supp_type:
                filtered_tracker = filtered_tracker[filtered_tracker['supplier_type'].isin(filter_supp_type)]
            if filter_delivery:
                filtered_tracker = filtered_tracker[filtered_tracker['delivery_completed'].isin(filter_delivery)]
            if filter_paid:
                filtered_tracker = filtered_tracker[filtered_tracker['bill_paid'].isin(filter_paid)]
                
            st.dataframe(filtered_tracker, width='stretch')
            
            st.download_button(
                label="Download Tracking Data CSV",
                data=filtered_tracker.to_csv(index=False).encode('utf-8'),
                file_name='lc_po_tracker_data.csv',
                mime='text/csv',
                key='download_tracker_data'
            )


    # --- TAB 5: BUDGET SETUP & IMPORT ---
    elif page_name == "Budget Setup & Import":
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False
        st.session_state['show_admin_edit'] = False
        st.session_state['edit_mn_id'] = None

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
            st.markdown("---") # Adds a nice divider 
            
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
        st.dataframe(current_budget_df, width='stretch')
        
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
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False
        st.session_state['show_admin_edit'] = False
        st.session_state['edit_mn_id'] = None

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
                new_role = st.selectbox("Role", ["user", "super", "administrator"])
            
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
        st.dataframe(users_df, width='stretch')
        st.subheader("Manage Registered Users")
    
        # Load users from the database
        users_df = load_data("SELECT id, username, role FROM users ORDER BY username")
    
        if not users_df.empty:
            # Create a selection box to choose a user to delete
            # Exclude the currently logged-in admin to prevent self-deletion
            other_users = users_df[users_df['username'] != st.session_state['username']]
        
            if not other_users.empty:
                user_to_delete = st.selectbox(
                    "Select User to Remove", 
                    options=other_users['username'].tolist(),
                    help="Warning: This action cannot be undone."
                )

                if st.button("❌ Delete Selected User", type="primary"):
                    # Database execution to delete the user
                    execute_query("DELETE FROM users WHERE username = ?", (user_to_delete,))
                
                    # Log the event
                    log_event("USER_DELETE", f"Admin deleted user: {user_to_delete}")
                
                    st.success(f"User '{user_to_delete}' has been permanently removed.")
                    st.rerun() # Refresh the page to update the user list
            else:
                st.info("No other users available to delete.")
            
            # Display the current user table for reference
            st.dataframe(users_df[['username', 'role']], width='stretch', hide_index=True)
        else:
            st.warning("No users found in the database.")
        
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
        # Guard: Super & Admin can access
        if st.session_state['role'] not in ['administrator', 'super']:
            st.error("🚫 Access Denied.")
            st.stop()
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False
        st.session_state['show_admin_edit'] = False
        st.session_state['edit_mn_id'] = None
            
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
            
            st.dataframe(df_logs, width='stretch', hide_index=True)
            
            # Download CSV option
            st.download_button(
                label="Download Event Log CSV",
                data=df_logs.to_csv(index=False).encode('utf-8'),
                file_name='application_event_log.csv',
                mime='text/csv',
                key='download_event_log'
            )

    elif page_name == "Indent & Purchase Record":

        st.title("🛒 Indent & Purchase Management")

        # Initialize Session States for Billing
        if 'temp_bill_items' not in st.session_state:
            st.session_state['temp_bill_items'] = []

        # 1. Add Items to Indent Registry
        st.header("1. Add Items to Indent Registry")
        with st.form("add_indent_registry_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                reg_indent_no = st.text_input("Indent Number *")
                reg_date = st.date_input("Indent Date", value=date.today())
            with col2:
                reg_desc = st.text_input("Goods Description *")
                reg_unit = st.selectbox("Unit", ["Nos", "Sets", "Kg", "Ltr", "Mtr", "Pkt", "Roll", "Box"])
            with col3:
                reg_qty = st.number_input("Quantity *", min_value=0.0, step=1.0)
                reg_rate = st.number_input("Rate (Optional)", min_value=0.0, step=0.01)
            
            if st.form_submit_button("Add to Indent Registry", type="primary"):
                if reg_indent_no and reg_desc and reg_qty > 0:
                    execute_query('''INSERT INTO standalone_indents 
                                   (indent_number, indent_date, item_description, quantity, unit, rate, total_amount, status) 
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                   (reg_indent_no, reg_date.strftime("%Y-%m-%d"), reg_desc, reg_qty, reg_unit, reg_rate, reg_qty*reg_rate, "Not Purchased"))
                    st.success(f"Added item '{reg_desc}' to Indent {reg_indent_no}")
                    st.rerun()

        # 4. Indent Registry Status
        st.header("4. Indent Registry Status")
        registry_df = load_data("SELECT indent_id, indent_number, indent_date, item_description, quantity, unit, rate, status FROM standalone_indents ORDER BY indent_id DESC")
        st.dataframe(registry_df, width='stretch', hide_index=True)

        st.markdown("---")

        # 3. Generate Bill from Indent Registry
        st.header("3. Generate Bill from Indent Registry")
        
        # 4.1 Select Multiple Indents from Registry
        # Fetch only 'Not Purchased' items to avoid double billing
        indent_list_query = "SELECT DISTINCT indent_number FROM standalone_indents WHERE status = 'Not Purchased' ORDER BY indent_date DESC"
        indent_list_df = load_data(indent_list_query)
        
        if not indent_list_df.empty:
            selected_indents = st.multiselect("Select Indent Number(s)", indent_list_df['indent_number'].tolist())
            
            if selected_indents:
                # 4.2 Fetch all items for the selected indents
                placeholders = ', '.join(['?'] * len(selected_indents))
                items_query = f"""
                    SELECT indent_id, indent_number, item_description, quantity, unit, rate 
                    FROM standalone_indents 
                    WHERE indent_number IN ({placeholders}) AND status = 'Not Purchased'
                """
                
                # Fetching data with parameters for safety
                conn = sqlite3.connect(DB_FILE)
                available_items_df = pd.read_sql_query(items_query, conn, params=selected_indents)
                conn.close()

                if not available_items_df.empty:
                    st.write("Select specific items to include in this bill:")
                    
                    # Add selection column for checkbox
                    available_items_df.insert(0, "Select", True)
                    
                    # Use data_editor to allow checkbox selection and quantity/rate adjustments
                    edited_items_df = st.data_editor(
                        available_items_df,
                        column_config={
                            "Select": st.column_config.CheckboxColumn("Select", default=True),
                            "indent_id": None, # Hide ID from user
                            "indent_number": st.column_config.TextColumn("Indent No", disabled=True),
                            "item_description": "Item Name",
                            "quantity": st.column_config.NumberColumn("Qty", min_value=0.0),
                            "rate": st.column_config.NumberColumn("Rate", min_value=0.0),
                        },
                        disabled=["indent_number"],
                        hide_index=True,
                        key="multi_bill_editor"
                    )

                    # Filter for only selected items
                    selected_items_to_bill = edited_items_df[edited_items_df["Select"] == True].copy()
                    
                    if not selected_items_to_bill.empty:
                        # Calculate totals
                        selected_items_to_bill['amount'] = selected_items_to_bill['quantity'] * selected_items_to_bill['rate']
                        total_bill_amt = selected_items_to_bill['amount'].sum()
                        st.info(f"Total Amount for Selected Items: {total_bill_amt:,.2f} BDT")

                        # 4.3 Bill Header Information Form
                        with st.form("multi_indent_bill_form"):
                            c1, c2, c3 = st.columns(3)
                            new_bill_no = c1.text_input("Bill No *")
                            new_bill_date = c2.date_input("Bill Date", value=date.today())
                            new_supplier = c3.text_input("Supplier Name *")
                            
                            c4, c5 = st.columns(2)
                            new_grn = c4.text_input("GRN No (Optional)")
                            new_pay_mode = c5.selectbox("Payment Mode", ["Cash", "Bank Transfer", "Cheque", "Credit"])
                            new_remarks = st.text_area("Remarks")

                            submit_bill = st.form_submit_button("Generate & Save Bill")

                        if submit_bill:
                            if not new_bill_no or not new_supplier:
                                st.error("Bill No and Supplier Name are required.")
                            else:
                                try:
                                    conn = sqlite3.connect(DB_FILE)
                                    cursor = conn.cursor()
                                    
                                    # Create a summary string of indents for the header
                                    indents_summary = ", ".join(selected_indents)
                                    
                                    # 1. Insert into indent_purchase_record (Header)
                                    cursor.execute("""
                                        INSERT INTO indent_purchase_record 
                                        (bill_no, indent_no, grn_no, supplier, bill_date, payment_mode, total_bill_amount, remarks)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (new_bill_no, indents_summary, new_grn, new_supplier, str(new_bill_date), new_pay_mode, total_bill_amt, new_remarks))
                                    
                                    # 2. Insert into indent_goods_details (Line Items) and Update Registry Status
                                    for _, row in selected_items_to_bill.iterrows():
                                        cursor.execute("""
                                            INSERT INTO indent_goods_details 
                                            (bill_no, description, quantity, unit, rate, amount)
                                            VALUES (?, ?, ?, ?, ?, ?)
                                        """, (new_bill_no, row['item_description'], row['quantity'], row['unit'], row['rate'], row['amount']))
                                        
                                        # Update the specific item in registry as 'Purchased'
                                        cursor.execute("UPDATE standalone_indents SET status = 'Purchased' WHERE indent_id = ?", (row['indent_id'],))
                                    
                                    conn.commit()
                                    conn.close()
                                    st.success(f"Bill {new_bill_no} successfully generated for Indents: {indents_summary}")
                                    st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error("Error: This Bill No already exists.")
                                except Exception as e:
                                    st.error(f"Unexpected Error: {e}")
                    else:
                        st.warning("Please select at least one item from the table above to generate a bill.")
            else:
                st.info("Please select one or more Indent Numbers from the list.")
        else:
            st.warning("No pending (Not Purchased) indents found in the registry.")
        # C. Temporary Display Section
        if st.session_state['temp_bill_items']:
            st.subheader("📋 Temporary Display (Items to be Billed)")
            temp_df = pd.DataFrame(st.session_state['temp_bill_items'])
            st.table(temp_df[['desc', 'qty', 'unit', 'rate', 'amount']])
            total_val = temp_df['amount'].sum()
            st.metric("Calculated Bill Total", f"{total_val:,.2f} BDT")

        st.markdown("---")

        # 5. View Saved Bills
        st.header("5. View Saved Bills")
        view_query = """
            SELECT r.bill_no, r.bill_date, r.supplier, r.total_bill_amount, 
                   d.description, d.quantity, d.unit, d.rate, d.amount as item_amount, 
                   r.indent_no, r.grn_no, r.payment_mode, r.remarks
            FROM indent_purchase_record r
            JOIN indent_goods_details d ON r.bill_no = d.bill_no
            ORDER BY r.bill_date DESC
        """
        bills_df = load_data(view_query)
        if not bills_df.empty:
            # Filters
            f1, f2, f3 = st.columns(3)
            with f1: search = st.text_input("Search Bill/Indent No")
            with f2: sel_sup = st.multiselect("Filter Supplier", bills_df['supplier'].unique())
            with f3: sel_pay = st.multiselect("Filter Payment Mode", bills_df['payment_mode'].unique())
            
            # Apply Filters
            filtered = bills_df.copy()
            if search: filtered = filtered[filtered['bill_no'].astype(str).str.contains(search) | filtered['indent_no'].astype(str).str.contains(search)]
            if sel_sup: filtered = filtered[filtered['supplier'].isin(sel_sup)]
            if sel_pay: filtered = filtered[filtered['payment_mode'].isin(sel_pay)]
            
            st.dataframe(filtered, width='stretch', hide_index=True)
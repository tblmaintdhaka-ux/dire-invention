import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import hashlib 
import io 
import altair as alt # Import Altair for advanced charting

# --- CUSTOM CSS FOR PROFESSIONAL LOOK & BUTTON NAVIGATION (Anthropic-Light Inspired) ---
PRIMARY_COLOR = "#007A8A"  # Dark Teal/Professional Blue-Green (Used for accents, buttons, selection)
APP_BACKGROUND = "#FFFFFF" # Pure White (Light, clean background)
SIDEBAR_BACKGROUND = "#F9F9F9" # Very Light Gray (Subtle contrast for sidebar)
HEADER_COLOR = "#1A3E54" # Dark Blue-Grey for Headers

PEPSI_LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/e/ea/Pepsi_2023.svg"

st.markdown(f"""
<style>
/* 1. Global Background Color (Anthropic Light aesthetic) */
.stApp {{
    background-color: {APP_BACKGROUND};
    color: #333333; /* Darker text for readability */
}}
/* 2. Sidebar Background Color */
.st-emotion-cache-12fmw5b {{ /* Target sidebar container (vendor-specific) */
    background-color: {SIDEBAR_BACKGROUND}; 
    padding-top: 2rem;
}}
/* 3. Main content area styling */
.main {{
    padding: 2rem 3rem;
}}

/* 4. Streamlit Widget Styling (Headers, Primary Colors) */
h1, h2, h3, h4, .st-emotion-cache-10trblm {{
    color: {HEADER_COLOR}; 
    font-weight: 600;
    text-shadow: 0 1px 1px rgba(0,0,0,0.05);
}}
.stButton>button {{
    background-color: {PRIMARY_COLOR};
    color: white !important;
    border-radius: 8px;
    border: none;
    padding: 10px 20px;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}}
.stButton>button:hover {{
    background-color: #005A65; /* Darker teal on hover */
}}

/* --- SIDEBAR RADIO BUTTONS AS NAVIGATION BUTTONS (Crucial Custom Feature) --- */

/* 5. Style the radio option labels to look like buttons */
div.stRadio > label {{
    /* Style the labels to look like buttons */
    background-color: #E6E6E6; /* Light gray for non-selected buttons */
    color: #333333; /* Dark text */
    border-radius: 5px; 
    border: 1px solid #ccc;
    margin: 5px 0; /* Vertical spacing between "buttons" */
    padding: 10px 15px; /* Internal padding */
    width: 100%; 
    transition: all 0.2s ease-in-out;
    display: block; 
    font-weight: 500;
    cursor: pointer;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05); /* Soft shadow */
}}
/* 6. Style the selected (checked) button */
div.stRadio > label:has(input:checked) {{
    background-color: {PRIMARY_COLOR}; /* Primary Teal for selected */
    color: white; 
    border-color: {PRIMARY_COLOR};
    box-shadow: 0 2px 5px rgba(0, 122, 138, 0.4);
}}
/* 7. Style hover effect */
div.stRadio > label:hover:not(:has(input:checked)) {{
    background-color: #D3D3D3; /* Slightly darker gray on hover */
    border-color: #bbb;
}}
/* 8. Hide the actual radio circle input element */
div.stRadio > label > div > div > div > input[type="radio"] {{
    position: absolute; 
    opacity: 0; 
}}
/* 9. Ensure the text content is aligned */
div.stRadio > label > div > div {{
    display: flex;
    align-items: center;
    justify-content: flex-start; 
    gap: 10px; 
}}
/* Custom class for the logo to control its size */
.pepsi-logo {{
    max-width: 150px;
    height: auto;
    display: block;
    margin: 0 auto 20px auto; 
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
    # Changed PRIMARY KEY to bill_no
    c.execute('''
        CREATE TABLE IF NOT EXISTS indent_purchase_record (
            bill_no TEXT PRIMARY KEY, 
            indent_no TEXT,
            grn_no TEXT,
            supplier TEXT,
            bill_date TEXT,
            payment_mode TEXT,
            total_bill_amount REAL,
            remarks TEXT,
            bill_payment_status TEXT
        )
    ''')

    # Table 8: Indent Goods Details (Line Items)
    # The foreign key (indent_no) now stores the Bill No. for joining
    c.execute('''
        CREATE TABLE IF NOT EXISTS indent_goods_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indent_no TEXT, -- Stores the bill_no from the header table
            description TEXT,
            quantity REAL,
            unit TEXT,
            rate REAL,
            amount REAL,
            FOREIGN KEY(indent_no) REFERENCES indent_purchase_record(bill_no)
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
@st.cache_data(ttl=600)
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

# --- UTILITY: Get Rates and Duty ---
@st.cache_data
def get_config_rates():
    """Retrieves current exchange rates and customs duty."""
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
    return fx_rates, customs_duty_pct

# --- DASHBOARD DATA AGGREGATION ---
@st.cache_data
def get_dashboard_data():
    """Aggregates all necessary data for the 14 dashboard charts."""
    
    df_status, total_budget, total_spent, remaining = calculate_status()
    requests_df = load_data("SELECT * FROM requests")
    lc_po_df = load_data("SELECT * FROM lc_po_tracker")
    indent_header_df = load_data("SELECT * FROM indent_purchase_record")
    indent_goods_df = load_data("SELECT * FROM indent_goods_details")

    # Ensure all cost fields are numeric
    for df in [requests_df, indent_header_df, indent_goods_df]:
        for col in df.select_dtypes(include=['object']).columns:
            if 'cost' in col or 'amount' in col or 'budget' in col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 1. Budget Summary Data
    budget_summary = pd.DataFrame({
        'Metric': ['Total Budget 2026 (BDT)', 'Total Utilized Cost (BDT)', 'Remaining Balance (BDT)'],
        'Value': [total_budget, total_spent, remaining]
    })
    
    # 2. R&M vs C&C Expenditure
    rm_cc_budget = df_status.copy()
    rm_cc_budget['Budget_Type'] = 'Budget'
    rm_cc_budget = rm_cc_budget.rename(columns={'total_budget': 'Amount'}).groupby('Budget_Type')['Amount'].sum().reset_index()

    rm_cc_spent = requests_df.groupby('mn_category')['landed_total_cost'].sum().reset_index()
    rm_cc_spent = rm_cc_spent.rename(columns={'landed_total_cost': 'Amount', 'mn_category': 'Category'})
    
    # Merge R&M/C&C spent back into a budget context (simplified for charting)
    category_data = pd.DataFrame({'Category': ['R&M (Repair & Maintenance)', 'C&C (Chemicals & Consumables)']})
    
    # Fill missing categories with 0 spent
    rm_cc_spent = pd.merge(category_data, rm_cc_spent, on='Category', how='left').fillna(0)
    rm_cc_spent['Metric'] = 'Expenditure'

    # Combine budget and expenditure (rough comparison, needs careful charting)
    budget_category = pd.DataFrame({
        'Category': ['Total Budget'],
        'Amount': [total_budget],
        'Metric': ['Budget']
    })
    
    # 3 & 4. Budget by Department/Cost Area vs Expenditure
    dept_area_data = df_status[['department', 'cost_area', 'total_budget', 'Total Utilized Cost']].copy()
    dept_area_data = dept_area_data.rename(columns={'total_budget': 'Budget', 'Total Utilized Cost': 'Expenditure'})
    
    # 5. MN Request Count & Status
    mn_count_data = pd.DataFrame({
        'Metric': ['Total MN Requests'],
        'Count': [len(requests_df)]
    })
    mn_status_data = requests_df.groupby('status').size().reset_index(name='Count')
    mn_status_data = mn_status_data.rename(columns={'status': 'Approval Status'})
    
    # 6. Budget Balance Sheet (Already calculated in df_status)
    balance_sheet_data = df_status.copy()
    balance_sheet_data = balance_sheet_data.rename(columns={'total_budget': 'Budget', 'Total Utilized Cost': 'Utilized Cost'})
    
    # 7. Foreign & Local Expenditure
    supplier_expenditure = requests_df.groupby('supplier_type')['landed_total_cost'].sum().reset_index(name='Expenditure')
    supplier_expenditure['Metric'] = 'Expenditure'
    supplier_expenditure['Total Budget'] = total_budget # Add total budget for comparison
    
    # 8 & 9. LC/PO Tracking (Foreign)
    
    # Step 1: MN for LC Request (Foreign MNs)
    foreign_mns = requests_df[requests_df['supplier_type'] == 'Foreign']
    count_mn_foreign = len(foreign_mns)
    amount_mn_foreign = foreign_mns['landed_total_cost'].sum()
    
    # Step 2: MN Approved by Finance (Approved Foreign MNs)
    foreign_approved = foreign_mns[foreign_mns['status'].isin(['Finance Approved', 'PO Issued', 'Completed'])]
    count_approved_foreign = len(foreign_approved)
    amount_approved_foreign = foreign_approved['landed_total_cost'].sum()

    # Step 3: MN with LC Transmitted (LC/PO tracking entry exists)
    foreign_lc_data = foreign_mns[foreign_mns['mn_number'].isin(lc_po_df['mn_number'])]
    count_lc_transmitted = len(foreign_lc_data)
    amount_lc_transmitted = foreign_lc_data['landed_total_cost'].sum()

    foreign_tracking_count = pd.DataFrame({
        'Stage': ['MN Foreign', 'Finance Approved', 'LC/PO Issued'],
        'Count': [count_mn_foreign, count_approved_foreign, count_lc_transmitted]
    })
    foreign_tracking_amount = pd.DataFrame({
        'Stage': ['MN Foreign', 'Finance Approved', 'LC/PO Issued'],
        'Amount (BDT)': [amount_mn_foreign, amount_approved_foreign, amount_lc_transmitted]
    })
    
    # 10 & 11. Local PO Tracking
    
    # Step 1: Local MN Issued
    local_mns = requests_df[requests_df['supplier_type'] == 'Local']
    count_mn_local = len(local_mns)
    amount_mn_local = local_mns['landed_total_cost'].sum()
    
    # Step 2: Local PO Issued (MNs with PO Issued status or tracking entry with LC/PO number)
    local_po_issued = local_mns[local_mns['status'] == 'PO Issued']
    local_po_issued_count = len(local_po_issued)
    local_po_issued_amount = local_po_issued['landed_total_cost'].sum()
    
    # Step 3: Local PO Delivery Completed
    local_po_completed_mns = pd.merge(local_mns, lc_po_df, on='mn_number', how='inner')
    local_po_completed = local_po_completed_mns[local_po_completed_mns['delivery_completed'] == 'Yes']
    local_po_completed_count = len(local_po_completed)
    local_po_completed_amount = local_po_completed['landed_total_cost'].sum()
    
    local_tracking_count = pd.DataFrame({
        'Stage': ['MN Local', 'PO Issued', 'Delivery Completed'],
        'Count': [count_mn_local, local_po_issued_count, local_po_completed_count]
    })
    local_tracking_amount = pd.DataFrame({
        'Stage': ['MN Local', 'PO Issued', 'Delivery Completed'],
        'Amount (BDT)': [amount_mn_local, local_po_issued_amount, local_po_completed_amount]
    })
    
    # 12. Foreign LC Cost Breakdown (Total LC Cost vs Spares, Freight, Duty)
    foreign_requests = requests_df[requests_df['supplier_type'] == 'Foreign']
    
    foreign_requests['FX_Cost_BDT'] = foreign_requests['foreign_spare_cost'] * foreign_requests['landed_total_cost'] / (
        foreign_requests['foreign_spare_cost'] + foreign_requests['freight_fca_charges'] + foreign_requests['local_cost_wo_vat_ait'] + foreign_requests['vat_ait']
    )
    
    cost_breakdown_df = pd.DataFrame({
        'Component': ['Total LC Cost (BDT)', 'Spares Cost (Foreign)', 'Freight Cost (Foreign)', 'Duty Cost (Foreign)', 'Local Cost/VAT (BDT)'],
        'Total': [
            foreign_requests['landed_total_cost'].sum(),
            (foreign_requests['foreign_spare_cost'] * foreign_requests['landed_total_cost'] / foreign_requests['estimated_cost']).sum(), # Proxy calc
            (foreign_requests['freight_fca_charges'] * foreign_requests['landed_total_cost'] / foreign_requests['estimated_cost']).sum(), # Proxy calc
            (foreign_requests['foreign_spare_cost'] * foreign_requests['customs_duty_rate'] * foreign_requests['landed_total_cost'] / foreign_requests['estimated_cost']).sum(), # Proxy calc
            (foreign_requests['local_cost_wo_vat_ait'] + foreign_requests['vat_ait']).sum()
        ]
    })
    
    # Simpler breakdown based on original columns (landed cost includes all BDT items)
    lc_breakdown = pd.DataFrame({
        'Cost Type': ['Landed Cost (Total)', 'Foreign Spare Cost', 'Freight/FCA Charges', 'Customs Duty Component (Estimated)', 'Local Cost (wo VAT/AIT)', 'VAT/AIT'],
        'Value': [
            foreign_requests['landed_total_cost'].sum(),
            foreign_requests['foreign_spare_cost'].sum() * foreign_requests['landed_total_cost'].sum() / foreign_requests['estimated_cost'].sum() if foreign_requests['estimated_cost'].sum() else 0,
            foreign_requests['freight_fca_charges'].sum() * foreign_requests['landed_total_cost'].sum() / foreign_requests['estimated_cost'].sum() if foreign_requests['estimated_cost'].sum() else 0,
            (foreign_requests['foreign_spare_cost'] * foreign_requests['customs_duty_rate'] * (foreign_requests['landed_total_cost'] / foreign_requests['estimated_cost'])).sum() if foreign_requests['estimated_cost'].sum() else 0,
            foreign_requests['local_cost_wo_vat_ait'].sum(),
            foreign_requests['vat_ait'].sum()
        ]
    })
    
    # 13. Local PO Cost vs VAT Amount
    local_requests = requests_df[requests_df['supplier_type'] == 'Local']
    local_cost_vat_breakdown = pd.DataFrame({
        'Component': ['Total Local PO Cost (BDT)', 'VAT/AIT Amount'],
        'Value': [local_requests['landed_total_cost'].sum(), local_requests['vat_ait'].sum()]
    })

    # 14. Indent Expenditure Analysis
    # Indent Total
    indent_total = indent_header_df['total_bill_amount'].sum()
    
    # Indent by Month
    indent_header_df['bill_date'] = pd.to_datetime(indent_header_df['bill_date'])
    indent_header_df['Month'] = indent_header_df['bill_date'].dt.to_period('M').astype(str)
    indent_monthly = indent_header_df.groupby('Month')['total_bill_amount'].sum().reset_index(name='Monthly Expenditure')
    
    # Top 10 Purchased Items (by amount)
    indent_goods_top = indent_goods_df.groupby('description')['amount'].sum().reset_index(name='Total Amount')
    indent_goods_top = indent_goods_top.sort_values(by='Total Amount', ascending=False).head(10)
    
    return {
        'budget_summary': budget_summary,
        'rm_cc_spent': rm_cc_spent,
        'dept_area_data': dept_area_data,
        'mn_status_data': mn_status_data,
        'balance_sheet_data': balance_sheet_data,
        'supplier_expenditure': supplier_expenditure,
        'foreign_tracking_count': foreign_tracking_count,
        'foreign_tracking_amount': foreign_tracking_amount,
        'local_tracking_count': local_tracking_count,
        'local_tracking_amount': local_tracking_amount,
        'lc_breakdown': lc_breakdown,
        'local_cost_vat_breakdown': local_cost_vat_breakdown,
        'indent_total': indent_total,
        'indent_monthly': indent_monthly,
        'indent_goods_top': indent_goods_top
    }
# --- END DASHBOARD DATA AGGREGATION ---

# --- DASHBOARD PAGE ---
def dashboard_page(data):
    st.title("💡 R&M/C&C Tracker Dashboard 2026")
    st.markdown("---")
    
    # 1. Total Budget VS Total Utilized Cost & Remaining Balance (Stacked Bar)
    st.header("1. Overall Budget Performance")
    col1, col2 = st.columns(2)

    df_status = data['balance_sheet_data'][['cost_area', 'Budget', 'Utilized Cost', 'Remaining Balance']].copy()
    
    # Melt for stacked bar chart
    df_melt = df_status.melt(
        id_vars='cost_area', 
        value_vars=['Utilized Cost', 'Remaining Balance'],
        var_name='Metric', 
        value_name='Amount (BDT)'
    )
    
    # Calculate utilization percentage for sorting and display
    total_budget_df = df_status.groupby('cost_area')['Budget'].sum().reset_index()
    total_budget_dict = total_budget_df.set_index('cost_area')['Budget'].to_dict()
    
    # Add a utilization percentage column for tooltip/label
    df_melt['Utilization %'] = df_melt.apply(
        lambda row: (row['Amount (BDT)'] / total_budget_dict[row['cost_area']]) * 100 
                    if row['Metric'] == 'Utilized Cost' and total_budget_dict[row['cost_area']] > 0 else None, axis=1
    )

    chart1 = alt.Chart(df_melt).mark_bar().encode(
        x=alt.X('cost_area', title='Cost Area', sort='-y'),
        y=alt.Y('Amount (BDT)'),
        color=alt.Color('Metric', legend=alt.Legend(title="Budget Component")),
        tooltip=[
            'cost_area',
            alt.Tooltip('Metric'),
            alt.Tooltip('Amount (BDT)', format=',.2f'),
            alt.Tooltip('Utilization %', format='.1f') # FIXED: Removed condition parameter
        ]
    ).properties(
        title='Budget vs Utilized Cost & Remaining Balance by Cost Area'
    ).interactive()
    
    col1.altair_chart(chart1, use_container_width=True)
    
    # 2. Budget vs Expenditure for R&M and C&C (Grouped Bar - Simplified as Expenditure vs Total Budget)
    
    # Aggregate data for charting (Use Dept/Area data, but group by category for simplified chart)
    requests_df = load_data("SELECT mn_category, landed_total_cost FROM requests")
    budget_df = load_data("SELECT total_budget FROM budget_heads")
    
    total_budget = budget_df['total_budget'].sum()
    
    rm_cc_expenditure = requests_df.groupby('mn_category')['landed_total_cost'].sum().reset_index()
    rm_cc_expenditure['Metric'] = 'Expenditure'
    rm_cc_expenditure = rm_cc_expenditure.rename(columns={'mn_category': 'Category', 'landed_total_cost': 'Amount'})

    budget_total_df = pd.DataFrame([
        {'Category': 'R&M (Repair & Maintenance)', 'Amount': total_budget / 2, 'Metric': 'Total Budget'},
        {'Category': 'C&C (Chemicals & Consumables)', 'Amount': total_budget / 2, 'Metric': 'Total Budget'}
    ]) # Simplified split for visual comparison
    
    rm_cc_chart_data = pd.concat([rm_cc_expenditure, budget_total_df], ignore_index=True).fillna(0)

    chart2 = alt.Chart(rm_cc_chart_data).mark_bar().encode(
        x=alt.X('Category:N', axis=alt.Axis(title='MN Category')),
        y=alt.Y('Amount:Q', axis=alt.Axis(title='Amount (BDT)', format=',.0f')),
        color=alt.Color('Metric:N', legend=alt.Legend(title="Metric")),
        column=alt.Column('Metric:N', header=alt.Header(titleOrient="bottom", labelOrient="bottom")),
        tooltip=['Category', alt.Tooltip('Amount:Q', format=',.2f')]
    ).properties(
        title='Budget vs Expenditure by R&M and C&C Categories'
    ).interactive()
    
    col2.altair_chart(chart2, use_container_width=True)
    
    st.markdown("---")
    
    # 3. Budget Allocation by Department VS Expenditure
    st.header("2. Departmental & Cost Area Allocation")
    col3, col4 = st.columns(2)
    
    dept_data = data['dept_area_data'].groupby('department')[['Budget', 'Expenditure']].sum().reset_index()
    dept_melt = dept_data.melt(id_vars='department', var_name='Metric', value_name='Amount (BDT)')
    
    chart3 = alt.Chart(dept_melt).mark_bar().encode(
        x=alt.X('department:N', title='Department', sort='-y'),
        y=alt.Y('Amount (BDT):Q', axis=alt.Axis(format=',.0f')),
        color=alt.Color('Metric:N', legend=alt.Legend(title="Metric")),
        tooltip=['department', alt.Tooltip('Amount (BDT):Q', format=',.2f')]
    ).properties(
        title='Budget Allocation vs Expenditure by Department'
    ).interactive()
    
    col3.altair_chart(chart3, use_container_width=True)
    
    # 4. Budget Allocation by Cost Area VS Expenditure
    area_data = data['dept_area_data'].rename(columns={'cost_area': 'Cost Area'})
    area_melt = area_data.melt(id_vars='Cost Area', value_vars=['Budget', 'Expenditure'], var_name='Metric', value_name='Amount (BDT)')
    
    chart4 = alt.Chart(area_melt).mark_bar().encode(
        x=alt.X('Cost Area:N', title='Cost Area', sort='-y'),
        y=alt.Y('Amount (BDT):Q', axis=alt.Axis(format=',.0f')),
        color=alt.Color('Metric:N', legend=alt.Legend(title="Metric")),
        tooltip=['Cost Area', alt.Tooltip('Amount (BDT):Q', format=',.2f')]
    ).properties(
        title='Budget Allocation vs Expenditure by Cost Area'
    ).interactive()
    
    col4.altair_chart(chart4, use_container_width=True)
    
    st.markdown("---")
    
    # 5. Total number of MN Requests and number of MN by approval status
    st.header("3. MN Request Tracking")
    col5, col6 = st.columns(2)
    
    # Total MN Count (Metric box)
    total_mn = data['mn_status_data']['Count'].sum()
    col5.metric("Total MN Requests Submitted", f"{total_mn:,}")
    
    # MN by Approval Status (Bar Chart)
    chart5_status = alt.Chart(data['mn_status_data']).mark_bar().encode(
        x=alt.X('Approval Status:N', title='Approval Status'),
        y=alt.Y('Count:Q'),
        color=alt.Color('Approval Status:N', legend=None),
        tooltip=['Approval Status', 'Count']
    ).properties(
        title='Number of MN by Approval Status'
    )
    col5.altair_chart(chart5_status, use_container_width=True)

    # 6. Column chart of budget balance sheet (same as #1 but showing Budget, Utilized, Remaining side-by-side)
    
    # Prep data for the balance sheet column chart
    df_balance = df_status[['cost_area', 'Budget', 'Utilized Cost', 'Remaining Balance']].rename(columns={'cost_area': 'Cost Area'})
    df_balance_melt = df_balance.melt(id_vars='Cost Area', var_name='Metric', value_name='Amount (BDT)')
    
    chart6 = alt.Chart(df_balance_melt).mark_bar().encode(
        x=alt.X('Cost Area:N', title='Cost Area', axis=alt.Axis(labels=False)),
        y=alt.Y('Amount (BDT):Q', axis=alt.Axis(format=',.0f')),
        color=alt.Color('Metric:N', legend=alt.Legend(title="Metric")),
        column=alt.Column('Metric:N', header=alt.Header(titleOrient="bottom", labelOrient="bottom")),
        tooltip=['Cost Area', 'Metric', alt.Tooltip('Amount (BDT):Q', format=',.2f')]
    ).properties(
        title='Budget Balance Sheet by Cost Area (Budget, Utilized, Remaining)'
    ).interactive()
    
    col6.altair_chart(chart6, use_container_width=True)
    
    st.markdown("---")
    
    # 7. Foreign & Local Expenditure against Total Budget
    st.header("4. Expenditure Type Analysis")
    col7, col8 = st.columns(2)
    
    # Prep data for Foreign/Local vs Total Budget
    supplier_expenditure = data['supplier_expenditure'].copy()
    supplier_expenditure_total = supplier_expenditure['Expenditure'].sum()
    
    budget_vs_exp = pd.DataFrame({
        'Metric': ['Total Budget', 'Total Expenditure'],
        'Amount (BDT)': [supplier_expenditure['Total Budget'].iloc[0] if not supplier_expenditure.empty else 0, supplier_expenditure_total]
    })
    
    # Create the breakdown chart for local vs foreign expenditure
    chart7_breakdown = alt.Chart(supplier_expenditure).mark_arc(outerRadius=120).encode(
        theta=alt.Theta(field="Expenditure", type="quantitative"),
        color=alt.Color(field="supplier_type", title="Supplier Type"),
        tooltip=["supplier_type", alt.Tooltip("Expenditure", format=',.2f')]
    ).properties(
        title='Foreign vs Local Expenditure Breakdown'
    )
    col7.altair_chart(chart7_breakdown, use_container_width=True)

    # 8 & 9. Foreign Tracking (Count & Amount)
    st.subheader("Foreign LC Tracking Progression")
    
    chart8 = alt.Chart(data['foreign_tracking_count']).mark_bar().encode(
        x=alt.X('Stage:N', title='Foreign Procurement Stage'),
        y=alt.Y('Count:Q', axis=alt.Axis(title='Number of MNs')),
        color=alt.Color('Stage:N', legend=None),
        tooltip=['Stage', 'Count']
    ).properties(
        title='MN Count by Foreign Procurement Stage'
    )
    col7.altair_chart(chart8, use_container_width=True)
    
    chart9 = alt.Chart(data['foreign_tracking_amount']).mark_bar().encode(
        x=alt.X('Stage:N', title='Foreign Procurement Stage'),
        y=alt.Y('Amount (BDT):Q', axis=alt.Axis(format=',.0f')),
        color=alt.Color('Stage:N', legend=None),
        tooltip=['Stage', alt.Tooltip('Amount (BDT):Q', format=',.2f')]
    ).properties(
        title='BDT Amount by Foreign Procurement Stage'
    )
    col8.altair_chart(chart9, use_container_width=True)
    
    st.markdown("---")
    
    # 10 & 11. Local PO Tracking (Count & Amount)
    st.header("5. Local PO Tracking Progression")
    col10, col11 = st.columns(2)
    
    chart10 = alt.Chart(data['local_tracking_count']).mark_bar().encode(
        x=alt.X('Stage:N', title='Local Procurement Stage'),
        y=alt.Y('Count:Q', axis=alt.Axis(title='Number of MNs')),
        color=alt.Color('Stage:N', legend=None),
        tooltip=['Stage', 'Count']
    ).properties(
        title='MN Count by Local PO Tracking Stage'
    )
    col10.altair_chart(chart10, use_container_width=True)
    
    chart11 = alt.Chart(data['local_tracking_amount']).mark_bar().encode(
        x=alt.X('Stage:N', title='Local Procurement Stage'),
        y=alt.Y('Amount (BDT):Q', axis=alt.Axis(format=',.0f')),
        color=alt.Color('Stage:N', legend=None),
        tooltip=['Stage', alt.Tooltip('Amount (BDT):Q', format=',.2f')]
    ).properties(
        title='BDT Amount by Local PO Tracking Stage'
    )
    col11.altair_chart(chart11, use_container_width=True)
    
    st.markdown("---")
    
    # 12. Total Cost of Foreign LC vs Cost of Spares, Freight, Duty
    st.header("6. Cost Breakdown Analysis")
    col12, col13 = st.columns(2)
    
    lc_breakdown_df = data['lc_breakdown'].copy().iloc[1:] # Exclude Total Landed Cost for stacked bar
    
    chart12 = alt.Chart(lc_breakdown_df).mark_bar().encode(
        x=alt.X('Cost Type:N', title='Cost Component', sort='-y'),
        y=alt.Y('Value:Q', axis=alt.Axis(format=',.0f')),
        color=alt.Color('Cost Type:N', legend=None),
        tooltip=['Cost Type', alt.Tooltip('Value:Q', format=',.2f')]
    ).properties(
        title='Foreign LC Cost Breakdown (Spares, Freight, Duty, Local)'
    )
    col12.altair_chart(chart12, use_container_width=True)
    
    # 13. Total Cost of Local PO vs Amount of VAT
    local_cost_vat_breakdown_df = data['local_cost_vat_breakdown'].copy()
    
    chart13 = alt.Chart(local_cost_vat_breakdown_df).mark_bar().encode(
        x=alt.X('Component:N', title='Local PO Component', sort='-y'),
        y=alt.Y('Value:Q', axis=alt.Axis(format=',.0f')),
        color=alt.Color('Component:N', legend=None),
        tooltip=['Component', alt.Tooltip('Value:Q', format=',.2f')]
    ).properties(
        title='Total Local PO Cost vs VAT/AIT'
    )
    col13.altair_chart(chart13, use_container_width=True)
    
    st.markdown("---")
    
    # 14. Indent Expenditure Analysis (3 charts in one section)
    st.header(f"7. Indent & Purchase Record Analysis (Total: BDT {data['indent_total']:,.2f})")
    
    col14_1, col14_2 = st.columns(2)
    
    # Indent expense by month
    chart14_monthly = alt.Chart(data['indent_monthly']).mark_bar().encode(
        x=alt.X('Month:N', title='Month', sort='x'),
        y=alt.Y('Monthly Expenditure:Q', axis=alt.Axis(format=',.0f')),
        tooltip=['Month', alt.Tooltip('Monthly Expenditure:Q', format=',.2f')]
    ).properties(
        title='Indent Expenditure by Month'
    ).interactive()
    col14_1.altair_chart(chart14_monthly, use_container_width=True)

    # Top 10 most purchased item by amount
    chart14_top10 = alt.Chart(data['indent_goods_top']).mark_bar().encode(
        x=alt.X('Total Amount:Q', axis=alt.Axis(format=',.0f'), title='Total Amount (BDT)'),
        y=alt.Y('description:N', title='Item Description', sort='-x'),
        color=alt.value(PRIMARY_COLOR),
        tooltip=['description', alt.Tooltip('Total Amount:Q', format=',.2f')]
    ).properties(
        title='Top 10 Most Purchased Items (by Amount)'
    ).interactive()
    col14_2.altair_chart(chart14_top10, use_container_width=True)

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
# Session states for Admin Edit visibility (Centralized in Users & Access Control)
if 'admin_edit_mode' not in st.session_state:
    st.session_state['admin_edit_mode'] = None # 'MN', 'BUDGET', 'INDENT'
if 'edit_id' not in st.session_state:
    st.session_state['edit_id'] = None # Stores ID (for MN, Budget) or Bill No (for Indent)
# Session state for dashboard landing page
if 'page' not in st.session_state:
    st.session_state['page'] = "💡 Dashboard (Infographics)"


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
                st.session_state['page'] = "💡 Dashboard (Infographics)" # Set default page to Dashboard
                st.success(f"Logged in as {role}!")
                # Invalidate cache to fetch new data after login
                calculate_status.clear()
                get_config_rates.clear()
                get_dashboard_data.clear() # Clear dashboard data cache
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
        users_df['Status'] = users_df['username'].apply(
            lambda x: 'Active' if x == st.session_state.get('username') and st.session_state['logged_in'] else 'Inactive'
        )
        users_df.rename(columns={'username': 'Username', 'role': 'Role'}, inplace=True)
        st.sidebar.dataframe(users_df[['Username', 'Role', 'Status']], use_container_width=True, hide_index=True)
    else:
        st.sidebar.info("No users registered.")
    
# --- LOGOUT FUNCTION ---
def logout():
    st.session_state['logged_in'] = False
    st.session_state['role'] = None
    st.session_state['username'] = None
    st.session_state['page'] = "💡 Dashboard (Infographics)" # Reset default page
    # Clear all session state flags on logout
    st.session_state['mn_submission_result'] = None
    st.session_state['mn_submission_status'] = None
    st.session_state['show_mn_details'] = False 
    st.session_state['admin_edit_mode'] = None 
    st.session_state['edit_id'] = None 
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
    menu = ["💡 Dashboard (Infographics)", "🔎 View & Filter Requests", "📝 New Request (MN)"]
    if st.session_state['role'] == 'administrator':
        menu.append("📊 Budget Balance Sheet") 
        menu.append("💰 LC/PO & Payment Tracker") 
        menu.append("🛒 Indent & Purchase Record") 
        menu.append("⚙️ Budget Setup & Import")
        menu.append("👥 Users & Access Control") # All Edit functions will be housed here
        menu.append("📜 Event Log")
        
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Go to", menu, 
                            index=menu.index(st.session_state['page']) if st.session_state['page'] in menu else 0, # Use session state for persistence
                            key='navigation_radio',
                            on_change=lambda: [
                                setattr(st.session_state, 'admin_edit_mode', None), 
                                setattr(st.session_state, 'edit_id', None),
                                setattr(st.session_state, 'page', st.session_state['navigation_radio']) # Update page state
                            ]) # Clear admin edit flags on page change
    st.sidebar.markdown("---")
    
    page_name = page.split(' ', 1)[-1].strip()

    # --- NEW DASHBOARD TAB ---
    if page_name == "Dashboard (Infographics)":
        data = get_dashboard_data()
        dashboard_page(data)
        
    # --- TAB 1: VIEW & FILTER REQUESTS (CLEANED UP) ---
    elif page_name == "View & Filter Requests":
        # Clear any old submission message when changing tabs
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False
        
        st.title("🔍 Existing Entries & Tracking Status")
        
        # Load data needed for configuration and calculation
        budgets = load_data("SELECT cost_area, department FROM budget_heads")
        fx_rates, customs_duty_pct = get_config_rates()
        
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
            
            # --- STATUS UPDATE SECTION (ONLY STATUS UPDATE REMAINS HERE) ---
            if st.session_state['role'] == 'administrator':
                st.subheader("🛠️ Status Update Tool")
                action_df = requests_df.sort_values(by='date_logged', ascending=False)
                action_options = ['--- Select a Request ID to Update Status ---'] + [
                    f"ID {row['id']} - MN: {row['mn_number']} ({row['status']})" 
                    for index, row in action_df.iterrows()
                ]

                col_a1, col_a2 = st.columns(2)
                selected_action_display = col_a1.selectbox("Select Request for Status Update", options=action_options, key="status_update_select")
                
                selected_id = None
                if selected_action_display != '--- Select a Request ID to Update Status ---':
                    try:
                        selected_id = int(selected_action_display.split(' - ')[0].replace('ID ', ''))
                    except Exception:
                        pass
                
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
                            get_dashboard_data.clear()
                            st.success(f"Status for Request ID {selected_id} updated to **{new_status}**.")
                            st.rerun()
                        else:
                            st.warning("Please select a request.")
                            
                st.markdown("---")
            
            # --- FILTERING SECTION ---
            st.subheader("Filter Requests")
            
            # Smart Filters
            col_filter_1, col_filter_2, col_filter_3 = st.columns(3)
            
            with col_filter_1:
                selected_status = st.multiselect("Filter by Status", requests_df['status'].unique(), default=[])
            with col_filter_2:
                selected_area = st.multiselect("Filter by Cost Center", requests_df['cost_area'].unique(), default=[])
            with col_filter_3:
                selected_supplier_type = st.multiselect("Filter by Supplier Type", requests_df['supplier_type'].unique(), default=[])

            # Apply Filters
            filtered_df = requests_df.copy()
            if selected_status:
                filtered_df = filtered_df[filtered_df['status'].isin(selected_status)]
            if selected_area:
                filtered_df = filtered_df[filtered_df['cost_area'].isin(selected_area)]
            if selected_supplier_type:
                filtered_df = filtered_df[filtered_df['supplier_type'].isin(selected_supplier_type)]
            
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
        st.session_state['admin_edit_mode'] = None
        st.session_state['edit_id'] = None

        st.title("📝 Create New Maintenance Notification")

        # Load data needed for configuration and calculation
        budgets = load_data("SELECT cost_area, department FROM budget_heads")
        fx_rates, customs_duty_pct = get_config_rates()
        
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
                    supplier_type, currency, foreign_spare_cost, freight_fca_charges, customs_duty_rate, 
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
        st.session_state['admin_edit_mode'] = None
        st.session_state['edit_id'] = None

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
        st.session_state['admin_edit_mode'] = None
        st.session_state['edit_id'] = None

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
                            return datetime.strptime(tracker_data[key], "%Y-%m-%d").date()
                        except ValueError:
                            pass
                    
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
                    get_dashboard_data.clear() # Clear dashboard cache
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


    # --- TAB 5: BUDGET SETUP & IMPORT (CLEANED UP) ---
    elif page_name == "Budget Setup & Import":
        # Clear any old submission message when changing tabs
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False
        st.session_state['admin_edit_mode'] = None
        st.session_state['edit_id'] = None

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
                        get_dashboard_data.clear()
                        st.success(f"✅ Successfully imported/updated {rows_imported} budget heads.")
                        st.rerun()
            except Exception as e:
                st.error(f"An unexpected error occurred during file processing: {e}")

        # --- MANUAL ENTRY OPTION (USED FOR ADDING NEW BUDGETS) ---
        st.header("2. Manual Budget Entry (Add New)")
        st.markdown("Use this form to **add a new** budget head.")
        
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
                        # Use INSERT OR REPLACE to allow quick updates for existing cost areas
                        execute_query("INSERT OR REPLACE INTO budget_heads (cost_area, department, total_budget) VALUES (?, ?, ?)", (area, dept, amount))
                        # LOGGING MANUAL BUDGET UPDATE
                        log_event("BUDGET_UPDATE", f"Manually added/updated budget for {area} to {amount:,.2f} BDT.")
                        calculate_status.clear()
                        get_dashboard_data.clear()
                        load_data.clear()
                        st.success(f"Added/Updated {area} with budget {amount:,.2f}")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Database error: The Cost Area name may already exist with different capitalization, or another database constraint was violated. Please check the name.")
                        
	    # --- START FIX: Correcting the validation flow ---
            # REMOVE the 'else:' that was previously here.
            # Add the 'else:' block for the main validation check:
            else: 
            	st.warning("Please fill all manual entry fields and ensure the budget amount is greater than 0.")
            # --- END FIX ---
            
        # Display current budget allocations
        st.subheader("3. Current Master Budget Data")
        current_budget_df = load_data("SELECT id, department, cost_area, total_budget FROM budget_heads")
        st.dataframe(current_budget_df, use_container_width=True, hide_index=True)
        
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
        st.header("4. Danger Zone (Clear Data)")
        st.markdown("Use this to clear all existing budget allocations to start fresh for a new fiscal year. **This does NOT delete request history.**")
        
        if st.button("🔴 CLEAR ALL BUDGET DATA", help="This action cannot be undone!", type="secondary"):
            execute_query("DELETE FROM budget_heads")
            # LOGGING BUDGET CLEAR
            
            load_data.clear()
            calculate_status.clear()
            get_dashboard_data.clear()
            
            log_event("ADMIN_ACTION", "Cleared all budget data.")
            st.success("All budget data cleared! The table below is now empty.")
            st.rerun()


    # --- TAB 6: USERS & ACCESS CONTROL (CENTRALIZED ADMIN EDIT HUB) ---
    elif page_name == "Users & Access Control":
        # Clear any old submission message when changing tabs
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False
        
        if st.session_state['role'] != 'administrator':
            st.error("🚫 Access Denied: Only Administrators can access User and Configuration settings.")
            st.stop()
            
        st.title("👥 User, Config & Admin Edit Hub")
        
        # --- 1. FINANCIAL CONFIGURATION ---
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
                get_config_rates.clear() # Clear cache for rates
                st.success("Financial configuration updated successfully!")
                st.rerun()
        
        st.markdown("---")
        
        # --- 2. ADMIN EDIT SECTION ---
        st.header("2. Centralized Admin Edit Tools")
        st.markdown("Select a data type to edit an entry by its unique identifier.")
        
        edit_type = st.radio("Select Data Type to Edit", 
                             ['Maintenance Notification (MN)', 'Budget Head (Cost Area)', 'Indent / Purchase Record (Bill No.)'],
                             index=['MN', 'BUDGET', 'INDENT'].index(st.session_state['admin_edit_mode']) if st.session_state['admin_edit_mode'] else 0,
                             key='edit_type_radio', 
                             horizontal=True)
        
        # Map radio selection to internal mode
        if edit_type == 'Maintenance Notification (MN)':
            st.session_state['admin_edit_mode'] = 'MN'
        elif edit_type == 'Budget Head (Cost Area)':
            st.session_state['admin_edit_mode'] = 'BUDGET'
        elif edit_type == 'Indent / Purchase Record (Bill No.)':
            st.session_state['admin_edit_mode'] = 'INDENT'

        # Fetch necessary data for dropdowns
        if st.session_state['admin_edit_mode'] == 'MN':
            mn_df = load_data("SELECT id, mn_number, status FROM requests ORDER BY id DESC")
            mn_options = ['--- Select MN ID ---'] + [f"ID {row['id']} - MN: {row['mn_number']} ({row['status']})" for idx, row in mn_df.iterrows()]
            selected_mn_display = st.selectbox("Select MN Request to Edit", options=mn_options, key="admin_edit_mn_select")
            
            selected_id = None
            if selected_mn_display != '--- Select MN ID ---':
                try:
                    selected_id = int(selected_mn_display.split(' - ')[0].replace('ID ', ''))
                except:
                    pass
            
            if selected_id:
                if st.button(f"✏️ Load Details for MN ID {selected_id}", type="primary"):
                    st.session_state['edit_id'] = selected_id
                    st.rerun()

        elif st.session_state['admin_edit_mode'] == 'BUDGET':
            budget_df = load_data("SELECT id, cost_area, total_budget FROM budget_heads ORDER BY cost_area")
            budget_df['total_budget'] = pd.to_numeric(budget_df['total_budget'], errors='coerce').fillna(0.0)
            budget_options = ['--- Select Budget Head ID ---'] + [f"ID {row['id']} - Area: {row['cost_area']} ({row['total_budget']:,.2f})" for idx, row in budget_df.iterrows()]
            selected_budget_display = st.selectbox("Select Budget Head to Edit", options=budget_options, key="admin_edit_budget_select")
            
            selected_id = None
            if selected_budget_display != '--- Select Budget Head ID ---':
                try:
                    selected_id = int(selected_budget_display.split(' - ')[0].replace('ID ', ''))
                except:
                    pass
            
            if selected_id:
                if st.button(f"✏️ Load Details for Budget ID {selected_id}", type="primary"):
                    st.session_state['edit_id'] = selected_id
                    st.rerun()

        elif st.session_state['admin_edit_mode'] == 'INDENT':
            indent_df = load_data("SELECT bill_no, supplier, total_bill_amount FROM indent_purchase_record ORDER BY bill_date DESC")
            indent_options = ['--- Select Bill No. ---'] + [f"Bill: {row['bill_no']} - Supp: {row['supplier']} ({row['total_bill_amount']:,.2f})" for idx, row in indent_df.iterrows()]
            selected_indent_display = st.selectbox("Select Bill No. to Edit", options=indent_options, key="admin_edit_indent_select")
            
            selected_bill_no = None
            if selected_indent_display != '--- Select Bill No. ---':
                try:
                    # Bill number is a string, not an ID
                    selected_bill_no = selected_indent_display.split(' - ')[0].replace('Bill: ', '')
                except:
                    pass
            
            if selected_bill_no:
                if st.button(f"✏️ Load Details for Bill No. {selected_bill_no}", type="primary"):
                    st.session_state['edit_id'] = selected_bill_no
                    st.rerun()

        st.markdown("---")
        
        # --- START ADMIN EDIT FORMS ---
        if st.session_state['edit_id']:
            
            # --- FORM 2A: EDIT MAINTENANCE NOTIFICATION (MN) ---
            if st.session_state['admin_edit_mode'] == 'MN':
                edit_mn_id = st.session_state['edit_id']
                
                # Fetch the record to be edited
                record_to_edit_df = load_data("SELECT * FROM requests WHERE id = ?", (edit_mn_id,))
                if record_to_edit_df.empty:
                    st.error(f"Could not find MN request with ID {edit_mn_id}.")
                    st.session_state['admin_edit_mode'] = None
                    st.session_state['edit_id'] = None
                    st.stop()
                
                original_data = record_to_edit_df.iloc[0].to_dict()
                original_landed_cost = original_data['landed_total_cost']
                original_cost_area = original_data['cost_area']
                
                st.header(f"✏️ Editing MN Request ID: {edit_mn_id} (MN: {original_data['mn_number']})")
                
                # Load dependencies for dropdowns
                budgets = load_data("SELECT cost_area, department FROM budget_heads")
                departments = sorted(budgets['department'].unique().tolist())
                fx_rates, customs_duty_pct = get_config_rates()
                
                with st.form("admin_edit_mn_form"):
                    
                    # 1. GENERAL & CATEGORIZATION 
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

                    # 2. FINANCIAL & PROCUREMENT DETAILS 
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
                        
                    # 3. TIMELINE & REMARKS
                    st.subheader("3. Timeline & Remarks")
                    col_date, col_remarks = st.columns([1, 2])
                    with col_date:
                        date_sent_ho = st.date_input("Date of Sending To HO *", value=date_ho_val)
                    with col_remarks:
                        plant_remarks = st.text_area("Plant Remarks/Notes", value=original_data['plant_remarks'])

                    st.markdown("---")
                    
                    col_save, col_cancel = st.columns(2)
                    save_button = col_save.form_submit_button("💾 Save Edited MN Request", type="primary")
                    cancel_button = col_cancel.form_submit_button("❌ Cancel Edit", type="secondary")
                    
                    if cancel_button:
                        st.session_state['admin_edit_mode'] = None
                        st.session_state['edit_id'] = None
                        st.rerun()

                    if save_button:
                        # --- VALIDATION ---
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

                        # --- DUPLICATE MN CHECK (Excluding the current MN) ---
                        if mn_no_new != original_data['mn_number']:
                            conn = sqlite3.connect(DB_FILE)
                            c = conn.cursor()
                            c.execute("SELECT mn_number FROM requests WHERE mn_number = ? AND id != ?", (mn_no_new, edit_mn_id))
                            if c.fetchone():
                                conn.close()
                                st.error(f"❌ Duplicate MN Error: An MN request with number **{mn_no_new}** already exists.")
                                st.stop()
                            conn.close()
                            
                        # --- BUDGET RE-CHECK LOGIC ---
                        df_status, _, _, _ = calculate_status()
                        
                        if area != original_cost_area:
                            new_area_status = df_status[df_status['cost_area'] == area]
                            if new_area_status.empty: st.error(f"Budget data for new Cost Area '{area}' not found."); st.stop()
                                
                            new_area_remaining = new_area_status['Remaining Balance'].iloc[0]
                            if landed_total_cost_new > new_area_remaining:
                                st.error(f"⚠️ Budget Exceeded in new Cost Area! '{area}' only has **{new_area_remaining:,.2f} BDT** remaining. Save aborted.")
                                st.stop()
                        else:
                            old_area_status = df_status[df_status['cost_area'] == original_cost_area]
                            if old_area_status.empty: st.error(f"Budget data for original Cost Area '{original_cost_area}' not found."); st.stop()
                            
                            current_remaining = old_area_status['Remaining Balance'].iloc[0]
                            available_after_removal = current_remaining + original_landed_cost
                            
                            if landed_total_cost_new > available_after_removal:
                                st.error(f"⚠️ Budget Exceeded! '{area}' can only support an updated cost of up to **{available_after_removal:,.2f} BDT**.")
                                st.stop()

                        # --- DB UPDATE ---
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
                            edit_mn_id
                        )
                        
                        execute_query(update_query, params)
                        calculate_status.clear()
                        get_dashboard_data.clear() # Clear dashboard cache
                        log_event("MN_ADMIN_EDIT", f"Request ID {edit_mn_id} (MN: {mn_no_new}) edited. Old cost: {original_landed_cost:,.2f}, New cost: {landed_total_cost_new:,.2f}.")

                        st.success(f"✅ Request ID **{edit_mn_id}** (MN: {mn_no_new}) updated successfully!")
                        st.session_state['admin_edit_mode'] = None
                        st.session_state['edit_id'] = None
                        st.rerun()
                
            # --- FORM 2B: EDIT BUDGET HEAD ---
            elif st.session_state['admin_edit_mode'] == 'BUDGET':
                edit_budget_id = st.session_state['edit_id']
                
                record_to_edit_df = load_data("SELECT * FROM budget_heads WHERE id = ?", (edit_budget_id,))
                if record_to_edit_df.empty:
                    st.error(f"Could not find Budget Head with ID {edit_budget_id}.")
                    st.session_state['admin_edit_mode'] = None
                    st.session_state['edit_id'] = None
                    st.stop()
                
                original_data = record_to_edit_df.iloc[0].to_dict()
                original_area = original_data['cost_area']
                
                st.header(f"✏️ Editing Budget Head ID: {edit_budget_id} (Area: {original_area})")
                
                with st.form("admin_edit_budget_form"):
                    
                    st.subheader("Budget Head Details")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    dept_new = col1.text_input("Department *", value=original_data['department'], key="edit_budget_dept")
                    area_new = col2.text_input("Cost Area Name *", value=original_area, key="edit_budget_area")
                    amount_new = col3.number_input("Approved Budget 2026 (BDT) *", min_value=0.0, format="%.2f", value=original_data['total_budget'], key="edit_budget_amount")

                    st.markdown("---")
                    
                    col_save, col_cancel = st.columns(2)
                    save_button = col_save.form_submit_button("💾 Save Edited Budget Head", type="primary")
                    cancel_button = col_cancel.form_submit_button("❌ Cancel Edit", type="secondary")
                    
                    if cancel_button:
                        st.session_state['admin_edit_mode'] = None
                        st.session_state['edit_id'] = None
                        st.rerun()

                    if save_button:
                        # --- VALIDATION ---
                        if not all([dept_new, area_new]) or amount_new <= 0:
                            st.error("⚠️ Please fill in all mandatory fields and ensure Budget is positive.")
                            st.stop()

                        # --- UTILIZATION CHECK ---
                        # Check current utilization for this cost area
                        df_status, _, _, _ = calculate_status()
                        
                        if area_new == original_area:
                            # Area name unchanged, check if new budget covers current utilized cost
                            current_utilization = df_status[df_status['cost_area'] == original_area]['Total Utilized Cost'].iloc[0] if not df_status[df_status['cost_area'] == original_area].empty else 0
                            
                            if amount_new < current_utilization:
                                st.error(f"⚠️ New Budget **{amount_new:,.2f} BDT** is lower than the currently utilized cost of **{current_utilization:,.2f} BDT** for this area. Update aborted.")
                                st.stop()

                            # If utilization check passes, proceed with update
                            update_query = "UPDATE budget_heads SET department = ?, cost_area = ?, total_budget = ? WHERE id = ?"
                            execute_query(update_query, (dept_new, area_new, amount_new, edit_budget_id))
                            
                            # Update requests table foreign key if the cost area name changed (unlikely with this query, but good practice)
                            if area_new != original_area:
                                execute_query("UPDATE requests SET cost_area = ?, department = ? WHERE cost_area = ?", (area_new, dept_new, original_area))
                                log_event("BUDGET_AREA_RENAME", f"Renamed Budget Cost Area '{original_area}' to '{area_new}'.")
                            
                            log_event("BUDGET_ADMIN_EDIT", f"Budget ID {edit_budget_id} ({area_new}) edited. New budget: {amount_new:,.2f} BDT.")
                            
                        else:
                            # Area name changed - Check for duplicate first
                            conn = sqlite3.connect(DB_FILE)
                            c = conn.cursor()
                            c.execute("SELECT cost_area FROM budget_heads WHERE cost_area = ? AND id != ?", (area_new, edit_budget_id))
                            if c.fetchone():
                                conn.close()
                                st.error(f"❌ Duplicate Cost Area Error: Cost Area **{area_new}** already exists by another budget head. Rename aborted.")
                                st.stop()
                            conn.close()

                            # Get current utilization of the OLD area
                            current_utilization = df_status[df_status['cost_area'] == original_area]['Total Utilized Cost'].iloc[0] if not df_status[df_status['cost_area'] == original_area].empty else 0
                            
                            if current_utilization > 0:
                                st.error(f"⚠️ Cannot rename Cost Area **'{original_area}'** as it has an active utilized cost of **{current_utilization:,.2f} BDT**. Clear requests or zero out utilization first.")
                                st.stop()
                                
                            # If no utilization, allow full rename and update
                            update_query = "UPDATE budget_heads SET department = ?, cost_area = ?, total_budget = ? WHERE id = ?"
                            execute_query(update_query, (dept_new, area_new, amount_new, edit_budget_id))
                            log_event("BUDGET_ADMIN_EDIT", f"Budget ID {edit_budget_id} ({original_area} -> {area_new}) edited. New budget: {amount_new:,.2f} BDT.")
                            
                        calculate_status.clear()
                        get_dashboard_data.clear() # Clear dashboard cache
                        st.success(f"✅ Budget Head ID **{edit_budget_id}** ({area_new}) updated successfully!")
                        st.session_state['admin_edit_mode'] = None
                        st.session_state['edit_id'] = None
                        st.rerun()

            # --- FORM 2C: EDIT INDENT/PURCHASE RECORD ---
            elif st.session_state['admin_edit_mode'] == 'INDENT':
                edit_bill_no = st.session_state['edit_id']
                
                # Fetch the record header
                header_df = load_data("SELECT * FROM indent_purchase_record WHERE bill_no = ?", (edit_bill_no,))
                # Fetch line items
                goods_df = load_data("SELECT * FROM indent_goods_details WHERE indent_no = ? ORDER BY id", (edit_bill_no,))
                
                if header_df.empty:
                    st.error(f"Could not find Indent/Purchase Record with Bill No. **{edit_bill_no}**.")
                    st.session_state['admin_edit_mode'] = None
                    st.session_state['edit_id'] = None
                    st.stop()
                
                original_header_data = header_df.iloc[0].to_dict()
                
                st.header(f"✏️ Editing Purchase Record: Bill No. **{edit_bill_no}**")
                st.warning("Editing this record requires changing the header data, and deleting/re-adding the line items below.")
                
                # --- HEADER EDIT ---
                with st.form("admin_edit_indent_header_form"):
                    st.subheader("Header Details")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    bill_no_new = col1.text_input("Bill No. * (Pivotal Identifier)", value=original_header_data['bill_no'], key="edit_indent_bill_no")
                    bill_date = col2.date_input("Bill Date *", value=datetime.strptime(original_header_data['bill_date'], "%Y-%m-%d").date(), key="edit_indent_bill_date")
                    supplier = col3.text_input("Supplier", value=original_header_data['supplier'], key="edit_indent_supplier")

                    col4, col5, col6 = st.columns(3)
                    indent_no = col4.text_input("Indent No.", value=original_header_data['indent_no'], key="edit_indent_indent_no")
                    grn_no = col5.text_input("GRN (Gate Receiving) No.", value=original_header_data['grn_no'], key="edit_indent_grn_no")
                    payment_mode = col6.selectbox("Payment Mode *", ["Cash", "Cheque", "Online Transfer", "Credit"], 
                                                  index=["Cash", "Cheque", "Online Transfer", "Credit"].index(original_header_data['payment_mode']), key="edit_indent_payment_mode")
                    
                    remarks = st.text_area("Remarks/Purpose", value=original_header_data['remarks'], key="edit_indent_remarks")
                    
                    st.markdown(f"**Current Total Bill Amount (Read-Only):** **{original_header_data['total_bill_amount']:,.2f}** Tk")
                    
                    col_save, col_cancel = st.columns(2)
                    save_button = col_save.form_submit_button("💾 Save Edited Header Details", type="primary")
                    cancel_button = col_cancel.form_submit_button("❌ Cancel Edit", type="secondary")
                    
                    if cancel_button:
                        st.session_state['admin_edit_mode'] = None
                        st.session_state['edit_id'] = None
                        st.rerun()

                    if save_button:
                        if not all([bill_no_new, bill_date, payment_mode]):
                            st.error("⚠️ Please fill in all mandatory Header fields.")
                            st.stop()

                        # Check for Duplicate Bill No
                        if bill_no_new != original_header_data['bill_no']:
                            conn = sqlite3.connect(DB_FILE)
                            c = conn.cursor()
                            c.execute("SELECT bill_no FROM indent_purchase_record WHERE bill_no = ?", (bill_no_new,))
                            if c.fetchone():
                                conn.close()
                                st.error(f"❌ Duplicate Bill No. Error: A Bill with number **{bill_no_new}** already exists.")
                                st.stop()
                            conn.close()
                            
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        try:
                            # 1. Update the Header Record (if Bill No changes, we delete the old and insert the new)
                            if bill_no_new != original_header_data['bill_no']:
                                # Delete old header and goods details
                                c.execute("DELETE FROM indent_goods_details WHERE indent_no = ?", (original_header_data['bill_no'],))
                                c.execute("DELETE FROM indent_purchase_record WHERE bill_no = ?", (original_header_data['bill_no'],))
                                # Insert new header with all data (including old total amount for now)
                                c.execute("""
                                    INSERT INTO indent_purchase_record (
                                        bill_no, indent_no, grn_no, supplier, bill_date, payment_mode, 
                                        total_bill_amount, remarks
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    bill_no_new, indent_no, grn_no, supplier, bill_date.strftime("%Y-%m-%d"), 
                                    payment_mode, original_header_data['total_bill_amount'], remarks
                                ))
                                # Re-insert goods details with the new bill_no (PK update)
                                for idx, row in goods_df.iterrows():
                                    c.execute("""
                                        INSERT INTO indent_goods_details (
                                            indent_no, description, quantity, unit, rate, amount
                                        ) VALUES (?, ?, ?, ?, ?, ?)
                                    """, (
                                        bill_no_new, row['description'], row['quantity'], row['unit'], 
                                        row['rate'], row['amount']
                                    ))
                                log_event("INDENT_ADMIN_RENAME", f"Purchase Bill '{original_header_data['bill_no']}' renamed to '{bill_no_new}' and header details updated.")
                                get_dashboard_data.clear()
                                st.session_state['edit_id'] = bill_no_new # Update session state to new Bill No
                            else:
                                # Update Header Record (Bill No UNCHANGED)
                                c.execute("""
                                    UPDATE indent_purchase_record SET
                                        indent_no = ?, grn_no = ?, supplier = ?, bill_date = ?, payment_mode = ?, 
                                        remarks = ?
                                    WHERE bill_no = ?
                                """, (
                                    indent_no, grn_no, supplier, bill_date.strftime("%Y-%m-%d"), payment_mode, 
                                    remarks, bill_no_new
                                ))
                                log_event("INDENT_ADMIN_EDIT", f"Purchase Bill '{bill_no_new}' header details updated.")
                                get_dashboard_data.clear()
                            
                            conn.commit()
                            st.success(f"✅ Purchase Record Header **{bill_no_new}** updated successfully!")
                            st.rerun() # Rerun to refresh goods data if Bill No changed
                            
                        except Exception as e:
                            conn.rollback()
                            st.error(f"An unexpected error occurred during database update: {e}")
                        finally:
                            conn.close()

                st.subheader("Line Item Details (Goods)")
                st.info("To edit line items, you must **delete** and **re-add** them. The new total amount will update the header record upon saving.")
                
                if goods_df.empty:
                    st.markdown("No line items currently attached to this Bill No.")
                else:
                    st.dataframe(goods_df[['description', 'quantity', 'unit', 'rate', 'amount']], use_container_width=True, hide_index=True)

                # --- LINE ITEM MANAGEMENT (DELETE/ADD) ---
                col_d_in, col_d_btn = st.columns([3, 1])
                line_item_id_to_delete = col_d_in.selectbox("Select Line Item ID to Delete", 
                                                            options=['---'] + goods_df['id'].unique().tolist(), 
                                                            key="delete_line_item_select")
                
                if col_d_btn.button("🗑️ Delete Selected Line Item", type="secondary"):
                    if line_item_id_to_delete != '---':
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        try:
                            # 1. Get the amount of the item being deleted
                            item_amount_deleted = goods_df[goods_df['id'] == line_item_id_to_delete]['amount'].iloc[0]
                            
                            # 2. Delete the item
                            c.execute("DELETE FROM indent_goods_details WHERE id = ?", (line_item_id_to_delete,))
                            
                            # 3. Update the Header total
                            latest_header_df = load_data("SELECT total_bill_amount FROM indent_purchase_record WHERE bill_no = ?", (edit_bill_no,))
                            current_total = latest_header_df['total_bill_amount'].iloc[0]
                            new_total_amount = current_total - item_amount_deleted
                            c.execute("UPDATE indent_purchase_record SET total_bill_amount = ? WHERE bill_no = ?", (new_total_amount, edit_bill_no))
                            
                            conn.commit()
                            log_event("INDENT_LINE_DELETE", f"Deleted line item ID {line_item_id_to_delete} from Bill {edit_bill_no}. New Total: {new_total_amount:,.2f} Tk.")
                            get_dashboard_data.clear()
                            st.success(f"✅ Line item deleted. New Bill Total: **{new_total_amount:,.2f}** Tk.")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error deleting line item: {e}")
                        finally:
                            conn.close()
                    else:
                        st.warning("Please select a line item ID to delete.")

                st.markdown("---")
                
                # --- ADD NEW LINE ITEM ---
                st.subheader(f"Add New Line Item to Bill No. **{edit_bill_no}**")
                
                with st.form("add_goods_to_existing_bill_form"):
                    col_a1, col_a2, col_a3, col_a4 = st.columns([3, 1, 1, 1])
                    
                    desc = col_a1.text_input("Description of Goods *", key="add_goods_desc")
                    qty = col_a2.number_input("Quantity *", min_value=0.0, format="%.2f", value=0.0, key="add_goods_qty")
                    unit = col_a3.text_input("Unit *", key="add_goods_unit")
                    rate = col_a4.number_input("Rate (Tk) *", min_value=0.0, format="%.2f", value=0.0, key="add_goods_rate")
                    
                    new_item_amount = qty * rate
                    st.markdown(f"**New Item Amount (Tk):** **{new_item_amount:,.2f}**")
                    
                    if st.form_submit_button("➕ Add New Line Item"):
                        if not all([desc, unit]) or qty <= 0 or rate < 0:
                            st.error("Please fill in all mandatory goods details and ensure quantity is positive.")
                            st.stop()
                            
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        try:
                            # 1. Insert the new line item
                            c.execute("""
                                INSERT INTO indent_goods_details (
                                    indent_no, description, quantity, unit, rate, amount
                                ) VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                edit_bill_no, desc, qty, unit, rate, new_item_amount
                            ))
                            
                            # 2. Update the Header total
                            # Must re-fetch the *latest* total_bill_amount in case another operation updated it during this session
                            latest_header_df = load_data("SELECT total_bill_amount FROM indent_purchase_record WHERE bill_no = ?", (edit_bill_no,))
                            current_total = latest_header_df['total_bill_amount'].iloc[0]
                            
                            new_total_amount = current_total + new_item_amount
                            c.execute("UPDATE indent_purchase_record SET total_bill_amount = ? WHERE bill_no = ?", (new_total_amount, edit_bill_no))
                            
                            conn.commit()
                            log_event("INDENT_LINE_ADD", f"Added line item to Bill {edit_bill_no}. Item Amount: {new_item_amount:,.2f} Tk. New Total: {new_total_amount:,.2f} Tk.")
                            get_dashboard_data.clear()
                            st.success(f"✅ Line item added. New Bill Total: **{new_total_amount:,.2f}** Tk.")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error adding line item: {e}")
                        finally:
                            conn.close()

            # --- END OF ADMIN EDIT FORMS ---
            
        st.markdown("---")
        
        # --- 3. CREATE NEW USER (Standard) ---
        st.header("3. Create New User")
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
        
        st.subheader("4. Existing Users")
        users_df = load_data("SELECT id, username, role FROM users")
        st.dataframe(users_df, use_container_width=True, hide_index=True)
        
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
        st.session_state['admin_edit_mode'] = None
        st.session_state['edit_id'] = None
        
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

    # --- TAB 8: INDENT & PURCHASE RECORD (UPDATED WITH FILTERS & BILL ENTRY) ---
    elif page_name == "Indent & Purchase Record":
        # Clear any old submission message when changing tabs
        st.session_state['mn_submission_result'] = None
        st.session_state['mn_submission_status'] = None
        st.session_state['show_mn_details'] = False
        st.session_state['admin_edit_mode'] = None
        st.session_state['edit_id'] = None
        
        if st.session_state['role'] != 'administrator':
            st.error("🚫 Access Denied: Only Administrators can access the Indent & Purchase Record.")
            st.stop()
            
        st.title("🛒 Indent & Purchase Record (Bill Entry)")
        st.markdown("Record details related to received Indents and subsequent Bill Payments. **Bill No.** is the pivotal unique reference.")
        
        # --- Session State Initialization for Dynamic Goods and Final Data ---
        if 'current_goods_data' not in st.session_state:
            st.session_state['current_goods_data'] = []
        if 'goods_form_key' not in st.session_state:
            st.session_state['goods_form_key'] = 0 # Key to force form reset

        # --- Helper Functions ---
        def clear_goods_data():
            """Clears the session state goods data after a successful final submission."""
            st.session_state['current_goods_data'] = []
            st.session_state['goods_form_key'] += 1
            
        def add_goods_item(desc, qty, unit, rate, amount):
            """Appends a single item to the temporary goods list in session state."""
            if not all([desc, unit]) or qty is None or rate is None:
                st.warning("Please fill in all goods details (Description, Quantity, Unit, Rate).")
                return
            if qty <= 0 or rate < 0:
                st.warning("Quantity must be greater than 0 and Rate must be non-negative.")
                return
            
            new_item = {
                'description': desc.strip(), 
                'quantity': qty, 
                'unit': unit.strip(), 
                'rate': rate, 
                'amount': amount
            }
            st.session_state['current_goods_data'].append(new_item)
            st.success(f"Added item: **{desc}** (Amount: {amount:,.2f} Tk)")
            st.session_state['goods_form_key'] += 1 # Rerender the goods form for new input
            st.rerun() # Use rerun to clear the goods form immediately

        # --- Dynamic Goods Input Form ---
        st.subheader("1. Add Goods Line Item")
        
        with st.form(key=f"goods_input_form_{st.session_state['goods_form_key']}"):
            col_d1, col_d2, col_d3, col_d4 = st.columns([3, 1, 1, 1])
            
            desc = col_d1.text_input("Description of Goods *")
            qty = col_d2.number_input("Quantity *", min_value=0.0, format="%.2f", value=0.0)
            unit = col_d3.text_input("Unit *")
            rate = col_d4.number_input("Rate (Tk) *", min_value=0.0, format="%.2f", value=0.0)
            
            item_amount = qty * rate
            
            st.markdown(f"**Item Amount (Tk):** **{item_amount:,.2f}**")
            
            if st.form_submit_button("➕ Add Goods"):
                add_goods_item(desc, qty, unit, rate, item_amount)
                
        # --- Display Added Goods and Total Sum ---
        st.subheader("2. Review Added Items")
        
        if st.session_state['current_goods_data']:
            df_goods = pd.DataFrame(st.session_state['current_goods_data'])
            
            st.dataframe(df_goods[['description', 'quantity', 'unit', 'rate', 'amount']], use_container_width=True, hide_index=True)
            
            total_amount = df_goods['amount'].sum()
            st.markdown(f"### Total Bill Amount (Sum of Items): **{total_amount:,.2f}**")
        else:
            total_amount = 0.0
            st.info("No goods items have been added yet.")


        st.markdown("---")
        
        # --- Final Indent & Bill Details Form ---
        st.subheader("3. Final Bill & Indent Details")
        
        with st.form("final_indent_form"):
            st.warning("Ensure all goods items are added above before saving the Bill. The calculated total amount is automatically used.")
            
            col1, col2, col3 = st.columns(3)
            # Bill No. is the pivotal input parameter
            bill_no = col1.text_input("Bill No. * (Pivotal Identifier)")
            bill_date = col2.date_input("Bill Date *", value=date.today())
            supplier = col3.text_input("Supplier")

            col4, col5, col6 = st.columns(3)
            indent_no = col4.text_input("Indent No.")
            grn_no = col5.text_input("GRN (Gate Receiving) No.")
            payment_mode = col6.selectbox("Payment Mode *", ["Cash", "Cheque", "Online Transfer", "Credit"], index=None)

            remarks = st.text_area("Remarks/Purpose")
            
            st.markdown(f"### Final Total Bill Amount to Save: **{total_amount:,.2f}** Tk")

            submitted = st.form_submit_button("Save Final Purchase Record")

            if submitted:
                # Basic Validation
                if not st.session_state['current_goods_data']:
                    st.error("Cannot save: No goods items have been added to the record.")
                    st.stop()
                if not all([bill_no, bill_date, payment_mode]):
                    st.error("Please fill in all mandatory Bill fields.")
                    st.stop()
                if total_amount <= 0:
                    st.error("Total Bill Amount must be greater than 0.")
                    st.stop()

                # Check for Duplicate Bill No
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT bill_no FROM indent_purchase_record WHERE bill_no = ?", (bill_no,))
                if c.fetchone():
                    conn.close()
                    st.error(f"❌ Duplicate Submission Error: A Bill with number **{bill_no}** already exists.")
                    st.stop()
                
                # Use Bill No as the primary key reference in the header and line items
                pk_identifier = bill_no.strip()
                
                # 1. Insert into Main Record Header
                try:
                    c.execute("""
                        INSERT INTO indent_purchase_record (
                            bill_no, indent_no, grn_no, supplier, bill_date, payment_mode, 
                            total_bill_amount, remarks
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pk_identifier, indent_no.strip(), grn_no.strip(), supplier.strip(), bill_date.strftime("%Y-%m-%d"), 
                        payment_mode, total_amount, remarks.strip()
                    ))
                    
                    # 2. Insert into Goods Details (Line Items)
                    for item in st.session_state['current_goods_data']:
                        c.execute("""
                            -- indent_goods_details.indent_no stores the bill_no from the header table (the unique ID)
                            INSERT INTO indent_goods_details (
                                indent_no, description, quantity, unit, rate, amount
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            pk_identifier, item['description'], item['quantity'], item['unit'], 
                            item['rate'], item['amount']
                        ))
                            
                    conn.commit()
                    log_event("INDENT_RECORD_CREATE", f"Recorded new Purchase Bill: {pk_identifier} (Indent: {indent_no.strip()}).")
                    st.success(f"✅ Purchase Record Bill No. **{pk_identifier}** saved successfully!")
                    
                    # Reset dynamic fields and rerun to clear the form and goods data
                    clear_goods_data()
                    get_dashboard_data.clear() # Clear dashboard cache
                    st.rerun() 
                    
                except Exception as e:
                    conn.rollback()
                    st.error(f"An unexpected error occurred during database insertion: {e}")
                finally:
                    conn.close()


        st.markdown("---")

        # --- Display Table with Smart Filtering (Updated to pivot on Bill No.) ---
        st.header("4. Existing Indent Records")
        st.caption("Admin editing for these records is available in the **Users & Access Control** tab.")
        
        # SQL JOIN uses Bill No (stored in indent_goods_details.indent_no) to join back to the header
        indent_record_df = load_data("""
            SELECT
                r.bill_no,
                r.bill_date,
                r.supplier,
                r.total_bill_amount,
                d.description AS goods_description,
                d.quantity,
                d.unit,
                d.rate,
                d.amount AS item_amount,
                r.indent_no,
                r.grn_no,
                r.payment_mode,
                r.remarks
            FROM indent_purchase_record r
            INNER JOIN indent_goods_details d ON r.bill_no = d.indent_no 
            ORDER BY r.bill_date DESC, r.bill_no
        """)
        
        if indent_record_df.empty:
            st.info("No indent records found.")
        else:
            
            st.subheader("Filter Records")
            col_f1, col_f2 = st.columns(2)
            
            # Filters
            filter_text = col_f1.text_input("Filter by Bill No., Indent No., or Supplier (Text Search)")
            
            # --- NEW FILTER BY GOODS DESCRIPTION ---
            filter_supplier = col_f2.multiselect("Filter by Supplier (Exact Match)", sorted(indent_record_df['supplier'].unique().tolist()))
            filter_goods_description = st.multiselect("Filter by Goods Description (Exact Match)", 
                                                      sorted(indent_record_df['goods_description'].unique().tolist()))
            
            filtered_indent_df = indent_record_df.copy()
            
            # Apply Filters
            if filter_text:
                filtered_indent_df = filtered_indent_df[
                    filtered_indent_df['bill_no'].str.contains(filter_text, case=False, na=False) |
                    filtered_indent_df['indent_no'].str.contains(filter_text, case=False, na=False) |
                    filtered_indent_df['supplier'].str.contains(filter_text, case=False, na=False)
                ]
            if filter_supplier:
                filtered_indent_df = filtered_indent_df[filtered_indent_df['supplier'].isin(filter_supplier)]
                
            if filter_goods_description:
                filtered_indent_df = filtered_indent_df[filtered_indent_df['goods_description'].isin(filter_goods_description)]
            
            # Reorder columns for display clarity
            display_cols = ['bill_no', 'bill_date', 'supplier', 'total_bill_amount', 
                            'goods_description', 'quantity', 'unit', 'rate', 'item_amount', 
                            'indent_no', 'grn_no', 'payment_mode', 'remarks']
            
            st.dataframe(filtered_indent_df[display_cols], use_container_width=True)
            
            # Download CSV option
            st.download_button(
                label="Download Indent Record CSV",
                data=filtered_indent_df.to_csv(index=False).encode('utf-8'),
                file_name='indent_purchase_records_by_bill.csv',
                mime='text/csv',
                key='download_indent_records'
            )

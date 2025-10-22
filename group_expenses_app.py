import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import json

# Try to import Google Sheets libraries (optional if testing locally)
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================
SHEET_ID = "1blpS3ZCtNNdUOVUSszotbJYoz9BpJAuWnq19VIZa4mI"
UNIVERSITY_LOGO_URL = "https://ik.imagekit.io/senti/EJUST%20LOGO.jpg?updatedAt=1761143903947"
DATE_MASCOT_GIF_URL = "blob:chrome-untrusted://image-magnify/81285f7b-139b-4f5d-899b-9c33400f88bf"
BACKGROUND_IMAGE_URL = "https://via.placeholder.com/1920x1080.png?text=Background"

MEMBERS = [
    "Fares Samer",
    "Mohamed Tarek",
    "Yassin Sherif",
    "Youssef Ossama",
    "Yousef Ibrahim",
    "Mahmoud Sayed",
    "Abdalrahman Ahmad",
    "Mostafa Khaled",
    "Mohamed Walid",
    "Beshoy Fayez",
    "Mohamed Hamada"
]

CURRENCY = "EGP"

# ============================================================================
# CUSTOM CSS
# ============================================================================
def apply_custom_css():
    st.markdown("""
    <style>
        /* Color Scheme: Red/Black/White with Date Fruit Accents */
        :root {
            --primary-red: #C41E3A;
            --dark-bg: #1a1a1a;
            --light-bg: #ffffff;
            --accent-brown: #8B4513;
            --text-light: #f5f5f5;
        }
        
        .stApp {
            background-color: #f8f8f8;
        }
        
        /* Header Styling */
        .main-header {
            background: linear-gradient(135deg, #C41E3A 0%, #8B0000 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            color: white;
            text-align: center;
        }
        
        .main-header h1 {
            color: white;
            margin: 0;
            font-size: 2.5rem;
        }
        
        .main-header p {
            color: #f5f5f5;
            margin: 0.5rem 0 0 0;
        }
        
        /* Card Styling */
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
            border-left: 4px solid #C41E3A;
            margin-bottom: 1rem;
        }
        
        .metric-card h3 {
            color: #C41E3A;
            margin: 0 0 0.5rem 0;
            font-size: 1rem;
        }
        
        .metric-card .value {
            color: #1a1a1a;
            font-size: 2rem;
            font-weight: bold;
            margin: 0;
        }
        
        /* Balance Styling */
        .balance-positive {
            color: #28a745;
            font-weight: bold;
        }
        
        .balance-negative {
            color: #dc3545;
            font-weight: bold;
        }
        
        .balance-zero {
            color: #6c757d;
            font-weight: bold;
        }
        
        /* Button Styling */
        .stButton > button {
            background-color: #C41E3A;
            color: white;
            border-radius: 8px;
            padding: 0.5rem 2rem;
            border: none;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .stButton > button:hover {
            background-color: #8B0000;
            box-shadow: 0 4px 8px rgba(196,30,58,0.3);
        }
        
        /* Tab Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: white;
            border-radius: 10px;
            padding: 0.5rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            background-color: transparent;
            color: #1a1a1a;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #C41E3A;
            color: white;
        }
        
        /* Input Styling */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {
            border-radius: 8px;
            border: 1px solid #ddd;
        }
        
        /* Success/Error Messages */
        .success-message {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        .settlement-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            padding: 1.5rem;
            border-radius: 12px;
            border: 2px solid #C41E3A;
            margin: 0.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .settlement-card .transfer {
            font-size: 1.1rem;
            color: #1a1a1a;
            font-weight: 600;
        }
        
        .all-settled {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            font-size: 1.5rem;
            font-weight: bold;
            margin: 2rem 0;
            box-shadow: 0 4px 8px rgba(40,167,69,0.3);
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# GOOGLE SHEETS FUNCTIONS
# ============================================================================
def connect_to_sheet():
    """Connect to Google Sheet using service account credentials."""
    if not GSPREAD_AVAILABLE:
        return None
    
    try:
        # Check if credentials are stored in Streamlit secrets
        if "gcp_service_account" in st.secrets:
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
            )
            client = gspread.authorize(credentials)
            sheet = client.open_by_key(SHEET_ID)
            return sheet
        else:
            return None
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

def read_expenses_from_sheet(sheet):
    """Read expenses from Google Sheet."""
    try:
        worksheet = sheet.worksheet("Expenses")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["Date", "Item", "Buyer", "Amount", "Notes"])

def read_payments_from_sheet(sheet):
    """Read payments from Google Sheet."""
    try:
        worksheet = sheet.worksheet("Payments")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["Date", "From", "To", "Amount", "Notes"])

def write_expense_to_sheet(sheet, date, item, buyer, amount, notes):
    """Write a new expense to Google Sheet."""
    try:
        worksheet = sheet.worksheet("Expenses")
        worksheet.append_row([date, item, buyer, float(amount), notes])
        return True
    except Exception as e:
        st.error(f"Error writing to sheet: {e}")
        return False

def write_payment_to_sheet(sheet, date, from_person, to_person, amount, notes):
    """Write a new payment to Google Sheet."""
    try:
        worksheet = sheet.worksheet("Payments")
        worksheet.append_row([date, from_person, to_person, float(amount), notes])
        return True
    except Exception as e:
        st.error(f"Error writing to sheet: {e}")
        return False

# ============================================================================
# DEMO DATA FUNCTIONS
# ============================================================================
def generate_demo_data():
    """Generate demo data for testing without Google Sheets."""
    expenses = pd.DataFrame([
        {"Date": "2024-01-15", "Item": "Transportation", "Buyer": "Fares Samer", "Amount": 550.0, "Notes": "Bus rental"},
        {"Date": "2024-01-16", "Item": "Food", "Buyer": "Mohamed Tarek", "Amount": 880.0, "Notes": "Lunch for team"},
        {"Date": "2024-01-17", "Item": "Equipment", "Buyer": "Yassin Sherif", "Amount": 1200.0, "Notes": "Sorting tools"},
        {"Date": "2024-01-18", "Item": "Supplies", "Buyer": "Youssef Ossama", "Amount": 330.0, "Notes": "Packaging materials"},
        {"Date": "2024-01-19", "Item": "Refreshments", "Buyer": "Yousef Ibrahim", "Amount": 440.0, "Notes": "Water and snacks"},
        {"Date": "2024-01-20", "Item": "Documentation", "Buyer": "Mahmoud Sayed", "Amount": 220.0, "Notes": "Printing costs"},
    ])
    
    payments = pd.DataFrame([
        {"Date": "2024-01-21", "From": "Mohamed Tarek", "To": "Fares Samer", "Amount": 100.0, "Notes": "Partial payment"},
        {"Date": "2024-01-22", "From": "Yassin Sherif", "To": "Fares Samer", "Amount": 150.0, "Notes": "Settling up"},
    ])
    
    return expenses, payments

# ============================================================================
# CALCULATION FUNCTIONS
# ============================================================================
def calculate_balances(expenses_df, payments_df):
    """Calculate per-person balances."""
    balances = {member: {"spent": 0.0, "share": 0.0, "balance": 0.0} for member in MEMBERS}
    
    # Calculate total spent by each person
    if not expenses_df.empty:
        for _, row in expenses_df.iterrows():
            buyer = row["Buyer"]
            amount = float(row["Amount"])
            if buyer in balances:
                balances[buyer]["spent"] += amount
    
    # Calculate total expenses and per-person share
    total_expenses = sum(b["spent"] for b in balances.values())
    per_person_share = total_expenses / len(MEMBERS)
    
    for member in MEMBERS:
        balances[member]["share"] = per_person_share
        balances[member]["balance"] = balances[member]["spent"] - per_person_share
    
    # Apply payments
    if not payments_df.empty:
        for _, row in payments_df.iterrows():
            from_person = row["From"]
            to_person = row["To"]
            amount = float(row["Amount"])
            
            if from_person in balances and to_person in balances:
                balances[from_person]["balance"] -= amount
                balances[to_person]["balance"] += amount
    
    return balances, total_expenses, per_person_share

def calculate_settlement(balances):
    """Calculate minimal settlement transfers."""
    # Create lists of creditors (owed money) and debtors (owe money)
    creditors = []
    debtors = []
    
    for member, data in balances.items():
        balance = round(data["balance"], 2)
        if balance > 0.01:  # Creditor (is owed)
            creditors.append({"name": member, "amount": balance})
        elif balance < -0.01:  # Debtor (owes)
            debtors.append({"name": member, "amount": -balance})
    
    # Sort by amount (descending)
    creditors.sort(key=lambda x: x["amount"], reverse=True)
    debtors.sort(key=lambda x: x["amount"], reverse=True)
    
    # Generate settlement plan
    settlement_plan = []
    
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]
        
        # Transfer the minimum of what debtor owes and what creditor is owed
        transfer_amount = min(debtor["amount"], creditor["amount"])
        
        if transfer_amount > 0.01:  # Only record meaningful transfers
            settlement_plan.append({
                "from": debtor["name"],
                "to": creditor["name"],
                "amount": round(transfer_amount, 2)
            })
        
        # Update amounts
        debtor["amount"] -= transfer_amount
        creditor["amount"] -= transfer_amount
        
        # Move to next if settled
        if debtor["amount"] < 0.01:
            i += 1
        if creditor["amount"] < 0.01:
            j += 1
    
    return settlement_plan

# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================
def create_spending_chart(balances):
    """Create a bar chart showing spending per person."""
    members = list(balances.keys())
    spent = [balances[m]["spent"] for m in members]
    
    if PLOTLY_AVAILABLE:
        fig = go.Figure(data=[
            go.Bar(
                x=members,
                y=spent,
                marker_color='#C41E3A',
                text=[f"{s:.2f}" for s in spent],
                textposition='outside'
            )
        ])
        fig.update_layout(
            title="Spending per Member",
            xaxis_title="Member",
            yaxis_title=f"Amount ({CURRENCY})",
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12),
            xaxis=dict(tickangle=-45),
            height=400
        )
        return fig
    else:
        return None

def create_balance_chart(balances):
    """Create a bar chart showing balance per person."""
    members = list(balances.keys())
    balance_vals = [balances[m]["balance"] for m in members]
    colors = ['#28a745' if b > 0 else '#dc3545' if b < 0 else '#6c757d' for b in balance_vals]
    
    if PLOTLY_AVAILABLE:
        fig = go.Figure(data=[
            go.Bar(
                x=members,
                y=balance_vals,
                marker_color=colors,
                text=[f"{b:.2f}" for b in balance_vals],
                textposition='outside'
            )
        ])
        fig.update_layout(
            title="Balance per Member (Positive = Owed, Negative = Owes)",
            xaxis_title="Member",
            yaxis_title=f"Balance ({CURRENCY})",
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12),
            xaxis=dict(tickangle=-45),
            height=400
        )
        return fig
    else:
        return None

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================
def validate_amount(amount):
    """Validate that amount is positive."""
    try:
        amt = float(amount)
        return amt > 0
    except:
        return False

def validate_member(name):
    """Validate that name is in the member list."""
    return name in MEMBERS

# ============================================================================
# STREAMLIT APP
# ============================================================================
def main():
    st.set_page_config(
        page_title="Date Fruit Sorting - Expense Manager",
        page_icon="🍂",
        layout="wide"
    )
    
    apply_custom_css()
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>🍂 Date Fruit Sorting Project</h1>
        <p>Expense Manager - {len(MEMBERS)} Members</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if "use_demo_data" not in st.session_state:
        st.session_state.use_demo_data = False
    if "demo_expenses" not in st.session_state:
        st.session_state.demo_expenses, st.session_state.demo_payments = generate_demo_data()
    
    # Connect to Google Sheets or use demo data
    sheet = None
    if GSPREAD_AVAILABLE and SHEET_ID != "YOUR_GOOGLE_SHEET_ID_HERE":
        sheet = connect_to_sheet()
    
    # Data source toggle
    with st.sidebar:
        st.image(DATE_MASCOT_GIF_URL, width=150)
        st.markdown("### ⚙️ Settings")
        
        if sheet is None:
            st.warning("⚠️ Google Sheets not configured")
            use_demo = st.checkbox("Use Demo Data", value=True)
            st.session_state.use_demo_data = use_demo
        else:
            st.success("✅ Connected to Google Sheets")
            st.session_state.use_demo_data = False
        
        st.markdown("---")
        st.markdown("### 👥 Team Members")
        for i, member in enumerate(MEMBERS, 1):
            st.markdown(f"{i}. {member}")
    
    # Load data
    if st.session_state.use_demo_data:
        expenses_df = st.session_state.demo_expenses.copy()
        payments_df = st.session_state.demo_payments.copy()
    elif sheet:
        expenses_df = read_expenses_from_sheet(sheet)
        payments_df = read_payments_from_sheet(sheet)
    else:
        expenses_df = pd.DataFrame(columns=["Date", "Item", "Buyer", "Amount", "Notes"])
        payments_df = pd.DataFrame(columns=["Date", "From", "To", "Amount", "Notes"])
    
    # Calculate balances
    balances, total_expenses, per_person_share = calculate_balances(expenses_df, payments_df)
    settlement_plan = calculate_settlement(balances)
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💰 Add Expense", "💸 Add Payment"])
    
    # ========================================================================
    # TAB 1: DASHBOARD
    # ========================================================================
    with tab1:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Expenses</h3>
                <p class="value">{total_expenses:.2f} {CURRENCY}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Per Person Share</h3>
                <p class="value">{per_person_share:.2f} {CURRENCY}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Expenses</h3>
                <p class="value">{len(expenses_df)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Payments</h3>
                <p class="value">{len(payments_df)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Balances table
        st.subheader("💳 Member Balances")
        
        balance_data = []
        for member in MEMBERS:
            bal = balances[member]
            balance_data.append({
                "Member": member,
                "Spent": f"{bal['spent']:.2f}",
                "Share": f"{bal['share']:.2f}",
                "Balance": bal['balance']
            })
        
        balance_df = pd.DataFrame(balance_data)
        
        # Style the balance column
        def style_balance(val):
            try:
                v = float(val)
                if v > 0.01:
                    return f'<span class="balance-positive">+{v:.2f} {CURRENCY}</span>'
                elif v < -0.01:
                    return f'<span class="balance-negative">{v:.2f} {CURRENCY}</span>'
                else:
                    return f'<span class="balance-zero">0.00 {CURRENCY}</span>'
            except:
                return val
        
        # Display table with HTML styling
        st.markdown("""
        <style>
        .balance-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .balance-table th {
            background-color: #C41E3A;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        .balance-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #f0f0f0;
        }
        .balance-table tr:hover {
            background-color: #f8f9fa;
        }
        </style>
        """, unsafe_allow_html=True)
        
        html_table = '<table class="balance-table"><thead><tr><th>Member</th><th>Spent</th><th>Share</th><th>Balance</th></tr></thead><tbody>'
        for _, row in balance_df.iterrows():
            html_table += f'<tr><td>{row["Member"]}</td><td>{row["Spent"]} {CURRENCY}</td><td>{row["Share"]} {CURRENCY}</td><td>{style_balance(row["Balance"])}</td></tr>'
        html_table += '</tbody></table>'
        
        st.markdown(html_table, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            spending_chart = create_spending_chart(balances)
            if spending_chart:
                st.plotly_chart(spending_chart, use_container_width=True)
            else:
                st.info("Install plotly for interactive charts")
        
        with col2:
            balance_chart = create_balance_chart(balances)
            if balance_chart:
                st.plotly_chart(balance_chart, use_container_width=True)
            else:
                st.info("Install plotly for interactive charts")
        
        st.markdown("---")
        
        # Settlement Plan
        st.subheader("🔄 Settlement Plan")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("Minimal transfers to settle all balances:")
        with col2:
            if st.button("🔄 Recompute Settlement"):
                st.rerun()
        
        if not settlement_plan:
            st.markdown("""
            <div class="all-settled">
                🎉 All Settled! No transfers needed.
            </div>
            """, unsafe_allow_html=True)
        else:
            for transfer in settlement_plan:
                st.markdown(f"""
                <div class="settlement-card">
                    <div class="transfer">
                        {transfer['from']} ➜ {transfer['to']} : <strong>{transfer['amount']:.2f} {CURRENCY}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Export settlement plan
            if st.button("📥 Export Settlement Plan as CSV"):
                settlement_df = pd.DataFrame(settlement_plan)
                settlement_df.columns = ["From", "To", "Amount (EGP)"]
                csv = settlement_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"settlement_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        st.markdown("---")
        
        # Recent transactions
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📝 Recent Expenses")
            if not expenses_df.empty:
                recent_expenses = expenses_df.tail(5).sort_values("Date", ascending=False)
                for _, row in recent_expenses.iterrows():
                    st.markdown(f"""
                    <div style="background: white; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 3px solid #C41E3A;">
                        <strong>{row['Item']}</strong> - {row['Amount']:.2f} {CURRENCY}<br>
                        <small>Paid by {row['Buyer']} on {row['Date']}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No expenses recorded yet")
        
        with col2:
            st.subheader("💸 Recent Payments")
            if not payments_df.empty:
                recent_payments = payments_df.tail(5).sort_values("Date", ascending=False)
                for _, row in recent_payments.iterrows():
                    st.markdown(f"""
                    <div style="background: white; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 3px solid #28a745;">
                        <strong>{row['From']} ➜ {row['To']}</strong><br>
                        {row['Amount']:.2f} {CURRENCY} on {row['Date']}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No payments recorded yet")
    
    # ========================================================================
    # TAB 2: ADD EXPENSE
    # ========================================================================
    with tab2:
        st.subheader("➕ Add New Expense")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.form("expense_form"):
                expense_date = st.date_input(
                    "Date",
                    value=datetime.now(),
                    help="Date of the expense"
                )
                
                expense_item = st.text_input(
                    "Item/Description",
                    placeholder="e.g., Transportation, Food, Equipment",
                    help="Brief description of the expense"
                )
                
                expense_buyer = st.selectbox(
                    "Paid By",
                    options=MEMBERS,
                    help="Who paid for this expense"
                )
                
                expense_amount = st.number_input(
                    f"Amount ({CURRENCY})",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    help="Total amount in EGP"
                )
                
                expense_notes = st.text_area(
                    "Notes (Optional)",
                    placeholder="Additional details...",
                    help="Any additional information"
                )
                
                submit_expense = st.form_submit_button("💾 Add Expense")
                
                if submit_expense:
                    # Validation
                    if not expense_item.strip():
                        st.error("❌ Please enter an item description")
                    elif not validate_amount(expense_amount):
                        st.error("❌ Amount must be positive")
                    elif not validate_member(expense_buyer):
                        st.error("❌ Invalid member selected")
                    else:
                        # Add expense
                        date_str = expense_date.strftime("%Y-%m-%d")
                        
                        if st.session_state.use_demo_data:
                            # Add to demo data
                            new_expense = pd.DataFrame([{
                                "Date": date_str,
                                "Item": expense_item,
                                "Buyer": expense_buyer,
                                "Amount": float(expense_amount),
                                "Notes": expense_notes
                            }])
                            st.session_state.demo_expenses = pd.concat([
                                st.session_state.demo_expenses,
                                new_expense
                            ], ignore_index=True)
                            st.success(f"✅ Expense added successfully! {expense_buyer} paid {expense_amount:.2f} {CURRENCY} for {expense_item}")
                            st.balloons()
                            st.rerun()
                        elif sheet:
                            if write_expense_to_sheet(sheet, date_str, expense_item, expense_buyer, expense_amount, expense_notes):
                                st.success(f"✅ Expense added successfully! {expense_buyer} paid {expense_amount:.2f} {CURRENCY} for {expense_item}")
                                st.balloons()
                                st.rerun()
                        else:
                            st.error("❌ No data source configured")
        
        with col2:
            st.info("""
            ### 📌 Guidelines
            - Enter accurate amounts
            - Select the correct payer
            - Add notes for clarity
            - All amounts in EGP
            """)
            
            st.image(DATE_MASCOT_GIF_URL, width=150)
    
    # ========================================================================
    # TAB 3: ADD PAYMENT
    # ========================================================================
    with tab3:
        st.subheader("💸 Record Payment")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.form("payment_form"):
                payment_date = st.date_input(
                    "Date",
                    value=datetime.now(),
                    help="Date of the payment"
                )
                
                col_a, col_b = st.columns(2)
                with col_a:
                    payment_from = st.selectbox(
                        "From (Payer)",
                        options=MEMBERS,
                        help="Who is making the payment"
                    )
                
                with col_b:
                    payment_to = st.selectbox(
                        "To (Recipient)",
                        options=MEMBERS,
                        help="Who is receiving the payment"
                    )
                
                payment_amount = st.number_input(
                    f"Amount ({CURRENCY})",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    help="Payment amount in EGP"
                )
                
                payment_notes = st.text_area(
                    "Notes (Optional)",
                    placeholder="Payment details...",
                    help="Any additional information"
                )
                
                submit_payment = st.form_submit_button("💾 Record Payment")
                
                if submit_payment:
                    # Validation
                    if payment_from == payment_to:
                        st.error("❌ Payer and recipient cannot be the same person")
                    elif not validate_amount(payment_amount):
                        st.error("❌ Amount must be positive")
                    elif not validate_member(payment_from) or not validate_member(payment_to):
                        st.error("❌ Invalid member selected")
                    else:
                        # Add payment
                        date_str = payment_date.strftime("%Y-%m-%d")
                        
                        if st.session_state.use_demo_data:
                            # Add to demo data
                            new_payment = pd.DataFrame([{
                                "Date": date_str,
                                "From": payment_from,
                                "To": payment_to,
                                "Amount": float(payment_amount),
                                "Notes": payment_notes
                            }])
                            st.session_state.demo_payments = pd.concat([
                                st.session_state.demo_payments,
                                new_payment
                            ], ignore_index=True)
                            st.success(f"✅ Payment recorded! {payment_from} paid {payment_amount:.2f} {CURRENCY} to {payment_to}")
                            st.balloons()
                            st.rerun()
                        elif sheet:
                            if write_payment_to_sheet(sheet, date_str, payment_from, payment_to, payment_amount, payment_notes):
                                st.success(f"✅ Payment recorded! {payment_from} paid {payment_amount:.2f} {CURRENCY} to {payment_to}")
                                st.balloons()
                                st.rerun()
                        else:
                            st.error("❌ No data source configured")
        
        with col2:
            st.info("""
            ### 💡 Quick Settle
            Use the settlement plan in the Dashboard tab to see recommended transfers.
            
            Record payments here as they happen to keep balances updated.
            """)
            
            # Show current settlement suggestions
            if settlement_plan:
                st.markdown("### 🎯 Suggested Transfers:")
                for i, transfer in enumerate(settlement_plan[:3], 1):
                    st.markdown(f"""
                    <div style="background: #fff3cd; padding: 8px; border-radius: 6px; margin: 5px 0; font-size: 0.9rem;">
                        {i}. {transfer['from']} ➜ {transfer['to']}<br>
                        <strong>{transfer['amount']:.2f} {CURRENCY}</strong>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d; padding: 1rem;">
        <p>Graduation Project - Expense Manager</p>
        <p style="font-size: 0.9rem;">Made with ❤️ by Youssef Ossama</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

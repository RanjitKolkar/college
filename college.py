import streamlit as st
import pandas as pd
import os

# -------------------------
# Streamlit page setup
# -------------------------
st.set_page_config(page_title="PU College Financial Model", layout="wide")
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------
# Utility: Indian number format (₹12,34,567)
# -------------------------
def fmt_inr(num):
    """Format number with Indian commas (₹1,23,45,678)."""
    if pd.isna(num): return ""
    try:
        num = float(num)
        if abs(num) < 1000:
            return f"₹{num:,.0f}"
        s, *d = str(int(abs(num))), []
        while s:
            d.append(s[-2:] if len(d) else s[-3:])
            s = s[:-2] if len(d) > 1 else s[:-3]
        sign = '-' if num < 0 else ''
        return f"{sign}₹{','.join(d[::-1])}"
    except Exception:
        return str(num)

# -------------------------
# Default dataframes
# -------------------------
def default_income_df():
    return pd.DataFrame({
        "Source": ["1st Year PU", "2nd Year PU", "Admission Fees", "Misc Income"],
        "No. of Students": [200, 180, None, None],
        "Fee per Student (₹)": [45000, 45000, None, None],
        "Notes": ["Science/Commerce", "", "", "Fine, Events, etc."]
    })

def default_expenses_df():
    return pd.DataFrame({
        "Expense Category": [
            "Infrastructure", "Staff Salaries (Teaching)", "Staff Salaries (Non-Teaching)",
            "Library", "Events", "Marketing", "Miscellaneous"
        ],
        "Per Month (₹)": [80000, 35000, 12000, 5000, 4000, 3000, 2000],
        "QTY": [1, 5, 2, 1, 1, 1, 1],
        "Description": ["", "", "", "", "", "", ""]
    })

def default_distribution_df():
    return pd.DataFrame({
        "Head": ["Management Royalty", "Faculty Bonus", "Development Fund", "Reserve"],
        "Percentage": [20, 10, 30, 10],
        "Description": ["Share to trust", "Incentives", "Infrastructure", "Contingency"]
    })

def default_projection_df():
    return pd.DataFrame({
        "Year": [f"Year {i}" for i in range(1, 6)],
        "Projected Income (₹)": [17350000, 18000000, 18700000, 19450000, 20250000],
        "Projected Expenses (₹)": [4003000, 4200000, 4410000, 4620000, 4840000]
    })

# -------------------------
# JSON helpers
# -------------------------
def save_df_json(df, name):
    df.to_json(os.path.join(DATA_DIR, f"{name}.json"), orient="records", indent=2, force_ascii=False)

def load_df_json(name, default_func):
    path = os.path.join(DATA_DIR, f"{name}.json")
    if os.path.exists(path):
        try:
            return pd.read_json(path)
        except Exception:
            df = default_func()
            save_df_json(df, name)
            return df
    else:
        df = default_func()
        save_df_json(df, name)
        return df

# -------------------------
# Compute helpers
# -------------------------
def compute_income(df):
    df = df.copy()
    df["No. of Students"] = pd.to_numeric(df.get("No. of Students", 0), errors="coerce").fillna(0)
    df["Fee per Student (₹)"] = pd.to_numeric(df.get("Fee per Student (₹)", 0), errors="coerce").fillna(0)
    df["Total (₹)"] = df["No. of Students"] * df["Fee per Student (₹)"]
    return df

def compute_expenses(df):
    df = df.copy()
    df["Per Month (₹)"] = pd.to_numeric(df.get("Per Month (₹)", 0), errors="coerce").fillna(0)
    df["QTY"] = pd.to_numeric(df.get("QTY", 1), errors="coerce").fillna(0)
    df["Yearly (₹)"] = df["Per Month (₹)"] * 12 * df["QTY"]
    return df

def compute_distribution(df, net_balance):
    df = df.copy()
    df["Percentage"] = pd.to_numeric(df.get("Percentage", 0), errors="coerce").fillna(0)
    df["Amount (₹)"] = df["Percentage"] / 100 * net_balance
    return df

def compute_projection(df):
    df = df.copy()
    df["Projected Income (₹)"] = pd.to_numeric(df.get("Projected Income (₹)", 0), errors="coerce").fillna(0)
    df["Projected Expenses (₹)"] = pd.to_numeric(df.get("Projected Expenses (₹)", 0), errors="coerce").fillna(0)
    df["Net Projected Balance (₹)"] = df["Projected Income (₹)"] - df["Projected Expenses (₹)"]
    return df

# -------------------------
# Load data
# -------------------------
income_df = load_df_json("income", default_income_df)
expenses_df = load_df_json("expenses", default_expenses_df)
distribution_df = load_df_json("distribution", default_distribution_df)
projection_df = load_df_json("projection", default_projection_df)

# -------------------------
# Sidebar Mode
# -------------------------
st.sidebar.header("🔧 Mode Selection")
mode = st.sidebar.radio("Choose Mode", ["Admin Panel", "User Dashboard"])

# -------------------------
# Admin Panel
# -------------------------
if mode == "Admin Panel":
    st.markdown("<h2 style='color:#1f77b4;'>🧮 Admin Panel</h2>", unsafe_allow_html=True)
    st.info("Edit inputs below and click **Save & Recalculate** to update totals.")

    with st.expander("📘 Income", expanded=True):
        income_inputs = st.data_editor(income_df, num_rows="dynamic", use_container_width=True)

    with st.expander("📗 Expenses", expanded=True):
        expenses_inputs = st.data_editor(expenses_df, num_rows="dynamic", use_container_width=True)

    with st.expander("📙 Distribution", expanded=True):
        distribution_inputs = st.data_editor(distribution_df, num_rows="dynamic", use_container_width=True)

    with st.expander("📈 Projection (5-Year)", expanded=True):
        projection_inputs = st.data_editor(projection_df, num_rows="dynamic", use_container_width=True)

    if st.button("💾 Save & Recalculate", use_container_width=True, type="primary"):
        computed_income = compute_income(income_inputs)
        computed_expenses = compute_expenses(expenses_inputs)
        total_income = computed_income["Total (₹)"].sum()
        total_expenses = computed_expenses["Yearly (₹)"].sum()
        net_balance = total_income - total_expenses
        computed_distribution = compute_distribution(distribution_inputs, net_balance)
        computed_projection = compute_projection(projection_inputs)

        save_df_json(computed_income, "income")
        save_df_json(computed_expenses, "expenses")
        save_df_json(computed_distribution, "distribution")
        save_df_json(computed_projection, "projection")

        st.success(f"✅ Data saved successfully! | Net Balance = {fmt_inr(net_balance)}")

        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Total Income", fmt_inr(total_income))
        c2.metric("💸 Total Expenses", fmt_inr(total_expenses))
        c3.metric("🏦 Net Balance", fmt_inr(net_balance))

# -------------------------
# User Dashboard
# -------------------------
else:
    st.markdown("<h2 style='color:#4CAF50;'>📊 PU College Financial Dashboard</h2>", unsafe_allow_html=True)

    income_df = compute_income(income_df)
    expenses_df = compute_expenses(expenses_df)
    total_income = income_df["Total (₹)"].sum()
    total_expenses = expenses_df["Yearly (₹)"].sum()
    net_balance = total_income - total_expenses
    distribution_df = compute_distribution(distribution_df, net_balance)
    projection_df = compute_projection(projection_df)

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total Income", fmt_inr(total_income))
    c2.metric("💸 Total Expenses", fmt_inr(total_expenses))
    c3.metric("🏦 Net Balance", fmt_inr(net_balance))

    st.markdown("<hr>", unsafe_allow_html=True)

    # Income section
    st.markdown("<h3 style='color:#1f77b4;'>📘 Income Summary</h3>", unsafe_allow_html=True)
    income_fmt = income_df.copy()
    income_fmt["Total (₹)"] = income_fmt["Total (₹)"].map(fmt_inr)
    st.dataframe(income_fmt, use_container_width=True)
    st.bar_chart(income_df.set_index("Source")["Total (₹)"])

    # Expenses section
    st.markdown("<h3 style='color:#e74c3c;'>📗 Expense Summary</h3>", unsafe_allow_html=True)
    exp_fmt = expenses_df.copy()
    exp_fmt["Yearly (₹)"] = exp_fmt["Yearly (₹)"].map(fmt_inr)
    st.dataframe(exp_fmt, use_container_width=True)
    st.bar_chart(expenses_df.set_index("Expense Category")["Yearly (₹)"])

    # Distribution section
    st.markdown("<h3 style='color:#f39c12;'>📙 Fund Distribution</h3>", unsafe_allow_html=True)
    dist_fmt = distribution_df.copy()
    dist_fmt["Amount (₹)"] = dist_fmt["Amount (₹)"].map(fmt_inr)
    st.dataframe(dist_fmt, use_container_width=True)
    st.bar_chart(distribution_df.set_index("Head")["Amount (₹)"])

    # Projection section
    st.markdown("<h3 style='color:#16a085;'>📈 5-Year Projection</h3>", unsafe_allow_html=True)
    proj_fmt = projection_df.copy()
    for col in ["Projected Income (₹)", "Projected Expenses (₹)", "Net Projected Balance (₹)"]:
        proj_fmt[col] = proj_fmt[col].map(fmt_inr)

    # Highlight "Year" column
    proj_fmt = proj_fmt.style.set_properties(subset=["Year"], **{'background-color': '#e8f5e9', 'font-weight': 'bold'})
    st.dataframe(proj_fmt, use_container_width=True)

    st.line_chart(
        projection_df.set_index("Year")[["Projected Income (₹)", "Projected Expenses (₹)", "Net Projected Balance (₹)"]]
    )

    st.caption("All amounts shown in Indian numbering format (₹10,00,000).")

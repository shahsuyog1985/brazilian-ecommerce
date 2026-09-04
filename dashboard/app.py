"""Interactive Streamlit dashboard for the Olist dataset."""

from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

st.set_page_config(page_title="Olist commerce dashboard", page_icon="📦", layout="wide")
st.title("Olist commerce dashboard")
st.caption("Brazilian marketplace orders, January 2017–August 2018 complete-month view")


@st.cache_data
def load_reports():
    monthly = pd.read_csv(REPORTS / "monthly_performance.csv", parse_dates=["month"])
    category = pd.read_csv(REPORTS / "category_performance.csv")
    states = pd.read_csv(REPORTS / "state_performance.csv")
    payments = pd.read_csv(REPORTS / "payment_mix.csv")
    delivery = pd.read_csv(REPORTS / "delivery_review_relationship.csv")
    return monthly, category, states, payments, delivery


monthly, category, states, payments, delivery = load_reports()
complete = monthly[(monthly.month >= "2017-01-01") & (monthly.month < "2018-09-01")].copy()

start, end = st.sidebar.select_slider(
    "Month range",
    options=complete.month.dt.strftime("%Y-%m").tolist(),
    value=("2017-01", "2018-08"),
)
top_n = st.sidebar.slider("Categories and states shown", 5, 20, 10)
period = complete[complete.month.between(pd.Timestamp(start), pd.Timestamp(end))]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Orders", f"{period.orders.sum():,.0f}")
col2.metric("Payment value", f"R$ {period.payment_value.sum()/1_000_000:.2f}M")
col3.metric("Average order value", f"R$ {period.payment_value.sum()/period.orders.sum():,.2f}")
col4.metric("Customers", f"{period.customers.sum():,.0f}", help="Monthly unique customers; a person can appear in multiple months")

st.subheader("Monthly performance")
metric = st.radio("Metric", ["payment_value", "orders", "average_order_value"], horizontal=True)
st.line_chart(period.set_index("month")[[metric]], color="#d95f02")

left, right = st.columns(2)
with left:
    st.subheader("Top product categories")
    selected_metric = st.selectbox("Category measure", ["item_revenue", "orders", "units"])
    chart = category.nlargest(top_n, selected_metric).set_index("category")[[selected_metric]]
    st.bar_chart(chart, horizontal=True, color="#1f6f8b")
with right:
    st.subheader("Top customer states")
    state_metric = st.selectbox("State measure", ["payment_value", "orders", "average_order_value"])
    chart = states.nlargest(top_n, state_metric).set_index("customer_state")[[state_metric]]
    st.bar_chart(chart, horizontal=True, color="#4c78a8")

left, right = st.columns(2)
with left:
    st.subheader("Payment mix")
    st.bar_chart(payments.set_index("payment_type")[["payment_value"]], color="#9c755f")
with right:
    st.subheader("Delivery timing and reviews")
    st.bar_chart(delivery.set_index("delivery_bucket")[["average_review_score"]], color="#59a14f")

with st.expander("Methodology and limitations"):
    st.markdown(
        """
        Payment data is aggregated to one row per order before analysis. Item revenue excludes
        freight. Edge months are excluded from the default trend because they are incomplete.
        Review and delivery relationships are descriptive, not causal. Raw customer records are
        not included in this repository.
        """
    )


import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="Bridge LA 2026 Impact",
    page_icon="📊",
    layout="wide"
)

st.title("Bridge LA | 2026 Impact Report")
st.caption("Digital Literacy & Community Impact")

# Load data
DATA_PATH = Path(__file__).parent / "impact_2026.csv"

if not DATA_PATH.exists():
    st.error("impact_2026.csv was not found.")
    st.stop()

df = pd.read_csv(DATA_PATH)

df["check_in_date"] = pd.to_datetime(
    df["check_in_date"],
    errors="coerce"
)

df = df[
    (df["check_in_date"].dt.year == 2026)
    & (df["status"] == "present")
].copy()

df = df.drop_duplicates(subset=["id"])

# Sidebar filters
st.sidebar.header("Filters")

months = sorted(
    df["check_in_date"].dt.strftime("%Y-%m")
    .dropna().unique()
)

selected_months = st.sidebar.multiselect(
    "Select months",
    months,
    default=months
)

df = df[
    df["check_in_date"].dt.strftime("%Y-%m")
    .isin(selected_months)
]

# Calculate metrics
students = df["student_id"].nunique()
attendance = len(df)

sessions = df.dropna(
    subset=["class_id", "check_in_date"]
).drop_duplicates(
    subset=["class_id", "check_in_date"]
)

session_count = len(sessions)
delivery_hours = session_count * 2
participant_hours = attendance * 2

# KPI cards
st.subheader("Impact Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Unique Students", f"{students:,}")
col2.metric("Attendance Records", f"{attendance:,}")
col3.metric("Class Sessions", f"{session_count:,}")
col4.metric(
    "Est. Delivery Hours",
    f"{delivery_hours:,}"
)

st.metric(
    "Estimated Participant-Hours",
    f"{participant_hours:,}"
)

st.divider()

# Monthly attendance
st.subheader("Monthly Attendance Trends")

monthly = (
    df.groupby(
        df["check_in_date"].dt.to_period("M")
    )
    .size()
    .reset_index(name="Attendance")
)

monthly["Month"] = (
    monthly["check_in_date"].astype(str)
)

st.bar_chart(
    monthly.set_index("Month")["Attendance"]
)

# Top classes
st.subheader("Most Attended Classes")

top_classes = (
    df["class_name"]
    .value_counts()
    .head(10)
)

st.bar_chart(top_classes)

# Attendance by location
st.subheader("Attendance by Location")

locations = (
    df["location_name"]
    .fillna("Unknown")
    .value_counts()
)

st.bar_chart(locations)

# Estimated reach
st.subheader("Estimated Community Reach")

col1, col2, col3 = st.columns(3)

col1.metric("Recorded Students", f"{students:,}")
col2.metric("2x Estimate", f"{students * 2:,}")
col3.metric("3x Estimate", f"{students * 3:,}")

st.caption(
    "Estimates use the supervisor's suggested "
    "2x–3x multiplier and are not verified totals."
)

st.info(
    "Class hours assume two hours per unique "
    "class/date session. Validate against schedules."
)

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

st.set_page_config(
    page_title="Bridge Program Analytics",
    layout="wide"
)

st.title("Bridge Student Engagement & Retention")
st.caption("Preliminary program analysis")

# Current validated output from your 5,000-row extract
total_attendance = 5000
unique_students = 465
eligible_students = 422
returned_students = 328

return_rate = returned_students / eligible_students * 100

# Dashboard metrics
col1, col2, col3, col4 = st.columns(4)

col1.metric("Attendance Records", f"{total_attendance:,}")
col2.metric("Unique Students", unique_students)
col3.metric("Eligible Students", eligible_students)
col4.metric("30-Day Return Rate", f"{return_rate:.1f}%")

st.divider()

# Return rate chart
st.subheader("30-Day Return Outcomes")

return_data = pd.DataFrame({
    "Outcome": ["Returned", "Did Not Return"],
    "Students": [
        returned_students,
        eligible_students - returned_students
    ]
})

fig = px.pie(
    return_data,
    names="Outcome",
    values="Students",
    hole=0.5
)

st.plotly_chart(fig, use_container_width=True)

# Student engagement
st.subheader("Student Engagement")

engagement = pd.read_csv(DATA_DIR / "engagement.csv")

fig2 = px.bar(
    engagement,
    x="engagement_group",
    y="proportion",
    labels={
        "engagement_group": "Engagement Group",
        "proportion": "Percentage of Students"
    }
)

st.plotly_chart(fig2, use_container_width=True)

# Location performance
st.subheader("30-Day Return Rate by Location")

locations = pd.read_csv(DATA_DIR / "location_retention.csv")

locations = locations.sort_values(
    "return_rate_30",
    ascending=True
)

fig3 = px.bar(
    locations,
    x="return_rate_30",
    y="location_name",
    orientation="h",
    hover_data=["eligible_students", "returned_students"],
    labels={
        "return_rate_30": "30-Day Return Rate (%)",
        "location_name": "Location"
    }
)

st.plotly_chart(fig3, use_container_width=True)

st.info(
    "Preliminary findings based on the latest 5,000 "
    "attendance records. Complete historical coverage "
    "has not yet been verified."
)
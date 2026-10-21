import os
import requests
import pandas as pd 
from pathlib import Path
from dotenv import load_dotenv 


BASE_URL = os.getenv("BRIDGE_API_BASE_URL")
APP_ID = os.getenv("BRIDGE_APP_ID")

if not BASE_URL or not APP_ID:
    raise ValueError("Missing Bridge API configuration")

#Attendence API
url = f"{BASE_URL.rstrip('/')}/Attendance"

params = {

    "sort": "-check_in_date",
    "limit": 10000
}

headers = {
    "x-app-id": APP_ID
}
response = requests.get(
    url,
    params=params,
    headers=headers,
    timeout=30
)


response = requests.get(
    url, 
    params=params, 
    headers=headers,
    timeout=30
    )

# Convert API response from JSON
response.raise_for_status()
data = response.json()


# Convert JSON into a pandas DataFrame
df = pd.DataFrame(data)
df["check_in_date"] = pd.to_datetime(df["check_in_date"])

print("Rows and columns:")
print(df.shape)

print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst 5 records:")
print(df.head())

print("\nMissing values:")
print(df.isnull().sum().sort_values(ascending=False))

# Get class data
class_url = f"{BASE_URL.rstrip('/')}/Class"

class_params = {
    "limit": 200
}

class_response = requests.get(
    class_url,
    params=class_params,
    headers=headers
)

class_data = class_response.json()

class_df = pd.DataFrame(class_data)

print("\nClass dataset:")
print(class_df.shape)

print("\nClass columns:")
print(class_df.columns.tolist())

merged_df = df.merge(
    class_df[["id", "name", "instructor", "location_name"]],
    left_on="class_id",
    right_on="id",
    how="left",
    suffixes=("_attendance", "_class")
)

print("\nMerged dataset shape:")
print(merged_df.shape)

print("\nMissing instructor values after merge:")
print(merged_df["instructor"].isnull().sum())

print("\nSample class + instructor:")
print(
    merged_df[
        ["class_name", "name", "instructor", "check_in_date"]
    ].head(10)
)

# How many claszses has each student attended?
attendance_per_student = (
    df.groupby("student_id")
      .size()
      .reset_index(name="classes_attended")
)

print(attendance_per_student["classes_attended"].describe())

def engagement_group(visits):
    if visits == 1:
        return "1 visit"
    elif visits <= 4:
        return "2-4 visits"
    elif visits <= 9:
        return "5-9 visits"
    else:
        return "10+ visits"

attendance_per_student["engagement_group"] = (
    attendance_per_student["classes_attended"]
    .apply(engagement_group)
)
print("Total attendance records:", len(df))
print("Unique students:", df["student_id"].nunique())
print("Earliest date:", df["check_in_date"].min())
print("Latest date:", df["check_in_date"].max())

def engagement_group(visits):
    if visits == 1:
        return "One-time (1)"
    elif visits <= 4:
        return "Returning (2-4)"
    elif visits <= 9:
        return "Engaged (5-9)"
    else:
        return "Highly engaged (10+)"

attendance_per_student["engagement_group"] = (
    attendance_per_student["classes_attended"]
    .apply(engagement_group)
)

engagement_summary = (
    attendance_per_student["engagement_group"]
    .value_counts()
)

print("\nStudent engagement:")
print(engagement_summary)

engagement_percent = (
    attendance_per_student["engagement_group"]
    .value_counts(normalize=True)
    .mul(100)
    .round(1)
)

print("\nStudent engagement percentages:")
print(engagement_percent)

location_summary = (
    df.groupby("location_name")
      .agg(
          total_checkins=("id", "count"),
          unique_students=("student_id", "nunique")
      )
      .reset_index()
)

location_summary["checkins_per_student"] = (
    location_summary["total_checkins"] /
    location_summary["unique_students"]
).round(2)

location_summary = location_summary.sort_values(
    "total_checkins",
    ascending=False
)

print(location_summary.to_string(index=False))

# Count each student's visits at each location
student_location_visits = (
    df.groupby(["location_name", "student_id"])
      .size()
      .reset_index(name="visits")
)

# Mark whether the student returned to that location
student_location_visits["returned"] = (
    student_location_visits["visits"] >= 2
)

# Calculate retention/return metrics by location
location_retention = (
    student_location_visits
    .groupby("location_name")
    .agg(
        unique_students=("student_id", "nunique"),
        returning_students=("returned", "sum"),
        avg_visits=("visits", "mean")
    )
    .reset_index()
)

location_retention["return_rate"] = (
    location_retention["returning_students"]
    / location_retention["unique_students"]
    * 100
).round(1)

location_retention = location_retention.sort_values(
    "return_rate",
    ascending=False
)

print(location_retention.to_string(index=False))

#30 day
first_visits = (
    df.groupby("student_id")["check_in_date"]
      .min()
      .reset_index(name="first_visit")
)

print(first_visits.head())

latest_date = df["check_in_date"].max()
cutoff_date = latest_date - pd.Timedelta(days=30)

eligible_students = first_visits[
    first_visits["first_visit"] <= cutoff_date
].copy()

print("Latest data:", latest_date)
print("30-day cutoff:", cutoff_date)
print("Students eligible for 30-day analysis:", len(eligible_students))

# Keep attendance records for eligible students
eligible_attendance = df.merge(
    eligible_students,
    on="student_id",
    how="inner"
)

# Calculate days since each student's first visit
eligible_attendance["days_since_first"] = (
    eligible_attendance["check_in_date"]
    - eligible_attendance["first_visit"]
).dt.days

# A return visit must be AFTER the first visit
# and within 30 days
returns_30 = eligible_attendance[
    (eligible_attendance["days_since_first"] > 0) &
    (eligible_attendance["days_since_first"] <= 30)
]

# Find students who returned
returned_students = returns_30["student_id"].nunique()

total_eligible = len(eligible_students)

return_rate_30 = (
    returned_students / total_eligible * 100
)

print("\n30-Day Repeat Attendance Analysis")
print("Eligible students:", total_eligible)
print("Returned within 30 days:", returned_students)
print("Did not return within 30 days:",
      total_eligible - returned_students)

print(f"30-day return rate: {return_rate_30:.1f}%")

#30 day location performance 

first_location_visit = (
    df.groupby(["student_id", "location_name"])["check_in_date"]
      .min()
      .reset_index(name="first_location_visit")
)
latest_date = df["check_in_date"].max()
cutoff_date = latest_date - pd.Timedelta(days=30)

eligible_location_students = first_location_visit[
    first_location_visit["first_location_visit"] <= cutoff_date
].copy()
location_attendance = df.merge(
    eligible_location_students,
    on=["student_id", "location_name"],
    how="inner"
)
location_attendance["days_since_first"] = (
    location_attendance["check_in_date"]
    - location_attendance["first_location_visit"]
).dt.days
location_attendance["returned_30"] = (
    (location_attendance["days_since_first"] > 0) &
    (location_attendance["days_since_first"] <= 30)
)
student_location_return = (
    location_attendance
    .groupby(["location_name", "student_id"])
    .agg(
        returned_30=("returned_30", "max")
    )
    .reset_index()
)
location_30day = (
    student_location_return
    .groupby("location_name")
    .agg(
        eligible_students=("student_id", "nunique"),
        returned_students=("returned_30", "sum")
    )
    .reset_index()
)

location_30day["return_rate_30"] = (
    location_30day["returned_students"]
    / location_30day["eligible_students"]
    * 100
).round(1)

location_30day = location_30day.sort_values(
    "return_rate_30",
    ascending=False
)

print(location_30day.to_string(index=False))
location_30day_reliable = location_30day[
    location_30day["eligible_students"] >= 10
].copy()

print("\n30-Day Return Rate by Location (10+ eligible students)")
print(location_30day_reliable.to_string(index=False))

print("Total attendance records:", len(df))
print("Unique students:", df["student_id"].nunique())
print("Earliest date:", df["check_in_date"].min())
print("Latest date:", df["check_in_date"].max())
print("Eligible students:", total_eligible)
print("Returned students:", returned_students)

from pathlib import Path

output_dir = Path("data")
output_dir.mkdir(exist_ok=True)

# Save aggregated results, not individual student records
location_30day_reliable.to_csv(
    output_dir / "location_retention.csv",
    index=False
)

engagement_percent.to_csv(
    output_dir / "engagement.csv"
)

print("Dashboard data saved!")
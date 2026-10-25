
import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Load API credentials
load_dotenv()

BASE_URL = os.getenv("BRIDGE_API_BASE_URL")
APP_ID = os.getenv("BRIDGE_APP_ID")

if not BASE_URL or not APP_ID:
    raise ValueError("Missing Bridge API configuration")

# Attendance API
url = f"{BASE_URL.rstrip('/')}/Attendance"

params = {
    "sort": "-check_in_date",
    "limit": 10000
}

headers = {
    "x-app-id": APP_ID
}

# Fetch attendance records
response = requests.get(
    url,
    params=params,
    headers=headers,
    timeout=30
)

response.raise_for_status()
data = response.json()

# Inspect the API response
print("Response type:", type(data))

if isinstance(data, dict):
    print("Available keys:", list(data.keys()))
elif isinstance(data, list):
    print("Total records returned:", len(data))

    if data:
        print("Sample record:", data[0])


# Convert API data to DataFrame
df = pd.DataFrame(data)

# Convert check-in dates
df["check_in_date"] = pd.to_datetime(
    df["check_in_date"],
    errors="coerce"
)

print("\n--- ATTENDANCE DATA SUMMARY ---")

print("Total records:", len(df))

print(
    "Earliest attendance:",
    df["check_in_date"].min()
)

print(
    "Latest attendance:",
    df["check_in_date"].max()
)

print(
    "\nAttendance records by year:"
)

print(
    df["check_in_date"].dt.year.value_counts()
    .sort_index()
)

print(
    "\nAttendance status:"
)

print(df["status"].value_counts(dropna=False))



from datetime import date, timedelta
import time

# Collect attendance from January 1 through today
start_date = date(2026, 1, 1)
end_date = date.today()

all_records = []
current_date = start_date

while current_date <= end_date:
    date_string = current_date.isoformat()

    params = {
        "check_in_date": date_string,
        "limit": 5000
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()
        records = response.json()

        if not isinstance(records, list):
            raise ValueError(
                f"Unexpected response on {date_string}"
            )

        # Verify the API returned the requested date
        if any(
            r.get("check_in_date") != date_string
            for r in records
        ):
            raise ValueError(
                f"Date mismatch on {date_string}"
            )

        if len(records) == 5000:
            raise ValueError(
                f"Possible truncated data on {date_string}"
            )

        all_records.extend(records)

        if records:
            print(f"{date_string}: {len(records)} records")

    except (requests.RequestException, ValueError) as error:
        print(f"ERROR on {date_string}: {error}")
        raise

    current_date += timedelta(days=1)
    time.sleep(0.1)

# Create DataFrame
df = pd.DataFrame(all_records)

if df.empty:
    raise ValueError("No attendance records retrieved")

# Remove duplicate attendance IDs
df = df.drop_duplicates(subset=["id"])

# Convert dates
df["check_in_date"] = pd.to_datetime(
    df["check_in_date"],
    errors="coerce"
)

# Save locally
df.to_csv("impact_2026.csv", index=False)

print("\n--- 2026 IMPACT SUMMARY ---")
print("Attendance records:", len(df))
print("Unique students:", df["student_id"].nunique())
print("Earliest date:", df["check_in_date"].min())
print("Latest date:", df["check_in_date"].max())

print("\nAttendance by month:")
print(
    df.groupby(
        df["check_in_date"].dt.to_period("M")
    ).size()
)

print("\n--- DIGITAL LITERACY TRAINING ---")

# One class can meet on multiple dates.
# Count each class/date combination as a session.
sessions = df.dropna(
    subset=["class_id", "check_in_date"]
).drop_duplicates(
    subset=["class_id", "check_in_date"]
)

total_sessions = len(sessions)
estimated_delivery_hours = total_sessions * 2

print("Unique class sessions:", total_sessions)
print(
    "Estimated class delivery hours:",
    estimated_delivery_hours
)

print(
    "Estimated participant-hours:",
    len(df) * 2
)

print("\nTop 10 classes by attendance:")
print(
    df["class_name"]
    .value_counts()
    .head(10)
)

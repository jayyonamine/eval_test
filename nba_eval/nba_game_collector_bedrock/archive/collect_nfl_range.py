"""
Collect real NFL game data for a date range
"""

import os
from datetime import datetime, timedelta
from nfl_agent import run_daily_collection

# Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")

# Date range: NFL 2024 season start through yesterday (REAL games only)
start_date = datetime(2024, 9, 5)  # NFL 2024 season opener
end_date = datetime(2024, 12, 2)  # Yesterday (today is Dec 3, 2024)

current_date = start_date

print(f"Collecting NFL games from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
print("=" * 70)

while current_date <= end_date:
    date_str = current_date.strftime("%Y-%m-%d")
    print(f"\nCollecting NFL games for {date_str}...")
    print("-" * 70)

    try:
        run_daily_collection(
            aws_region=AWS_REGION,
            gcp_project_id=GCP_PROJECT_ID,
            dataset_id="nfl_data",
            table_id="game_results",
            target_date=date_str,
            aws_access_key=AWS_ACCESS_KEY,
            aws_secret_key=AWS_SECRET_KEY,
            model_id=BEDROCK_MODEL_ID
        )
    except Exception as e:
        print(f"Error collecting games for {date_str}: {e}")

    current_date += timedelta(days=1)

print("\n" + "=" * 70)
print("NFL data collection complete!")

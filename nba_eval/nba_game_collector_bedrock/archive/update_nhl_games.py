"""
Update NHL games from last game date to specified end date
"""

import os
from datetime import datetime, timedelta
from google.cloud import bigquery
from nhl_agent import run_daily_collection


def get_last_game_date(project_id: str, dataset_id: str = "nhl_data",
                       table_id: str = "game_results") -> str:
    """Query BigQuery to get the most recent game date in the table"""
    client = bigquery.Client(project=project_id)

    query = f"""
        SELECT MAX(game_date) as last_game_date
        FROM `{project_id}.{dataset_id}.{table_id}`
    """

    try:
        query_job = client.query(query)
        results = query_job.result()

        for row in results:
            if row.last_game_date:
                return row.last_game_date.strftime("%Y-%m-%d")
            else:
                return None
    except Exception as e:
        print(f"Error querying BigQuery: {e}")
        return None


def update_nhl_games(end_date: str = "2025-12-05"):
    """Update NHL games from last game date to end_date"""

    # Configuration from environment
    AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID")
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")

    print("=" * 70)
    print("NHL Game Data Incremental Update")
    print("=" * 70)

    # Get the last game date from BigQuery
    print(f"\nQuerying {GCP_PROJECT_ID}.nhl_data.game_results for most recent game...")
    last_game_date = get_last_game_date(GCP_PROJECT_ID)

    if not last_game_date:
        print("No games found in table.")
        return

    print(f"Most recent game date in table: {last_game_date}")

    # Calculate start date (day after last game)
    last_date = datetime.strptime(last_game_date, "%Y-%m-%d")
    start_date = last_date + timedelta(days=1)
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

    print(f"Update range: {start_date.strftime('%Y-%m-%d')} to {end_date}")

    # Check if we need to update
    if start_date > end_date_obj:
        print("\nTable is already up to date! No new games to add.")
        return

    # Collect games for each day
    current_date = start_date
    total_games = 0

    print(f"\nCollecting NHL games...")
    print("-" * 70)

    while current_date <= end_date_obj:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"\nCollecting games for {date_str}...")

        try:
            result = run_daily_collection(
                aws_region=AWS_REGION,
                gcp_project_id=GCP_PROJECT_ID,
                dataset_id="nhl_data",
                table_id="game_results",
                target_date=date_str,
                aws_access_key=AWS_ACCESS_KEY,
                aws_secret_key=AWS_SECRET_KEY,
                model_id=BEDROCK_MODEL_ID
            )
            if result:
                print(f"✓ Successfully added games for {date_str}")
                total_games += result.get('inserted', 0)
        except Exception as e:
            print(f"✗ Error collecting games for {date_str}: {e}")

        current_date += timedelta(days=1)

    print("\n" + "=" * 70)
    print("NHL UPDATE COMPLETE")
    print("=" * 70)
    print(f"Total games inserted: {total_games}")
    print(f"Table now contains games through: {end_date}")


if __name__ == "__main__":
    update_nhl_games()

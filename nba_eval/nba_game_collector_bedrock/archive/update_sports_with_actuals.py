"""
Update all sports AND populate actual results in forecasts table

This is the comprehensive update script that:
1. Collects new games for NBA, NHL, NFL
2. Automatically populates game_ids
3. Populates actual results in forecasts table
"""

import os
from datetime import datetime, timedelta
from google.cloud import bigquery
from nba_agent import run_daily_collection as nba_collect
from nhl_agent import run_daily_collection as nhl_collect
from nfl_agent import run_daily_collection as nfl_collect
from populate_actual_results_auto import populate_actual_results, validate_results

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID")


def get_last_date(dataset_id, table_id):
    """Get last game date from table"""
    client = bigquery.Client(project=GCP_PROJECT_ID)
    query = f"""
    SELECT MAX(game_date) as last_date
    FROM `{GCP_PROJECT_ID}.{dataset_id}.{table_id}`
    """
    result = client.query(query).result()
    for row in result:
        if row.last_date:
            return row.last_date if isinstance(row.last_date, str) else row.last_date.strftime("%Y-%m-%d")
    return None


def update_sport(sport_name, dataset_id, collect_fn, start_date, end_date):
    """Update a sport from start_date to end_date"""
    print(f"\n{'=' * 70}")
    print(f"Updating {sport_name} from {start_date} to {end_date}")
    print('=' * 70)

    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        print(f"\n{sport_name} - {date_str}:")
        print("-" * 70)

        try:
            collect_fn(
                aws_region=AWS_REGION,
                gcp_project_id=GCP_PROJECT_ID,
                dataset_id=dataset_id,
                table_id="game_results",
                target_date=date_str,
                aws_access_key=AWS_ACCESS_KEY,
                aws_secret_key=AWS_SECRET_KEY,
                model_id=BEDROCK_MODEL_ID
            )
        except Exception as e:
            print(f"Error: {e}")

        current = current + timedelta(days=1)


def main():
    print("=" * 70)
    print("COMPREHENSIVE SPORTS UPDATE WITH ACTUAL RESULTS")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Update NBA/NHL/NFL games through today")
    print("  2. Automatically populate game_ids from forecasts")
    print("  3. Populate actual results back into forecasts table")

    target_date = datetime.now().strftime("%Y-%m-%d")

    # Check last dates
    print(f"\n{'=' * 70}")
    print(f"TARGET DATE: {target_date}")
    print('=' * 70)

    nba_last = get_last_date("nba_data", "game_results")
    nhl_last = get_last_date("nhl_data", "game_results")
    nfl_last = get_last_date("nfl_data", "game_results")

    print(f"\nCurrent last game dates:")
    print(f"  NBA: {nba_last}")
    print(f"  NHL: {nhl_last}")
    print(f"  NFL: {nfl_last}")

    # Update NBA
    if nba_last and nba_last < target_date:
        next_date = (datetime.strptime(nba_last, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        update_sport("NBA", "nba_data", nba_collect, next_date, target_date)
    else:
        print(f"\nNBA already up to date through {target_date}")

    # Update NHL
    if nhl_last and nhl_last < target_date:
        next_date = (datetime.strptime(nhl_last, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        update_sport("NHL", "nhl_data", nhl_collect, next_date, target_date)
    else:
        print(f"\nNHL already up to date through {target_date}")

    # Update NFL
    if nfl_last and nfl_last < target_date:
        next_date = (datetime.strptime(nfl_last, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        update_sport("NFL", "nfl_data", nfl_collect, next_date, target_date)
    else:
        print(f"\nNFL already up to date through {target_date}")

    # Populate actual results in forecasts table
    print("\n" + "=" * 70)
    print("POPULATING ACTUAL RESULTS IN FORECASTS TABLE")
    print("=" * 70)

    client = bigquery.Client(project=GCP_PROJECT_ID)
    populate_actual_results(client)
    validate_results(client)

    # Final verification
    print("\n" + "=" * 70)
    print("FINAL VERIFICATION")
    print("=" * 70)

    for sport, dataset in [("NBA", "nba_data"), ("NHL", "nhl_data"), ("NFL", "nfl_data")]:
        query = f"""
        SELECT MAX(game_date) as last_date, COUNT(*) as total_games,
               COUNT(DISTINCT game_date) as days_with_games
        FROM `{GCP_PROJECT_ID}.{dataset}.game_results`
        """
        result = client.query(query).result()
        for row in result:
            last_date = row.last_date if isinstance(row.last_date, str) else row.last_date.strftime("%Y-%m-%d")
            print(f"{sport}: Last={last_date}, Total={row.total_games} games, {row.days_with_games} days")

    print("\n" + "=" * 70)
    print("✓ ALL UPDATES COMPLETE!")
    print("=" * 70)
    print("\nSummary:")
    print("  ✅ Game results updated through today")
    print("  ✅ Game IDs automatically populated from forecasts")
    print("  ✅ Actual results populated back into forecasts table")


if __name__ == "__main__":
    main()

"""
Test script to verify automatic game_id population when adding new games
"""

import os
from nba_agent import run_daily_collection

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID")

def test_auto_game_id():
    """Test that game_ids are automatically populated for Dec 7 games"""
    print("=" * 70)
    print("TESTING AUTOMATIC GAME_ID POPULATION")
    print("=" * 70)

    print("\nThis test will:")
    print("1. Collect NBA games for December 7, 2025")
    print("2. Automatically look up game_ids from forecasts table")
    print("3. Insert games WITH game_ids into BigQuery")

    # Create a temporary test table to avoid modifying production data
    test_table = "game_results_test"

    print(f"\nUsing test table: nba_data.{test_table}")
    print("-" * 70)

    try:
        run_daily_collection(
            aws_region=AWS_REGION,
            gcp_project_id=GCP_PROJECT_ID,
            dataset_id="nba_data",
            table_id=test_table,  # Use test table
            target_date="2025-12-07",
            aws_access_key=AWS_ACCESS_KEY,
            aws_secret_key=AWS_SECRET_KEY,
            model_id=BEDROCK_MODEL_ID
        )
    except Exception as e:
        print(f"Collection completed with note: {e}")

    # Verify results
    from google.cloud import bigquery
    client = bigquery.Client(project=GCP_PROJECT_ID)

    print("\n" + "=" * 70)
    print("VERIFICATION - Checking game_ids in test table")
    print("=" * 70)

    query = f"""
    SELECT
        game_date,
        away_team,
        home_team,
        away_score,
        home_score,
        game_id
    FROM `{GCP_PROJECT_ID}.nba_data.{test_table}`
    WHERE game_date = '2025-12-07'
    ORDER BY home_team
    """

    result = client.query(query).result()
    games_with_id = 0
    games_without_id = 0

    print("\nGames in test table:")
    print("-" * 70)
    for row in result:
        status = "✓" if row.game_id else "✗"
        game_id_str = row.game_id[:12] + "..." if row.game_id else "NO GAME_ID"
        print(f"{status} {row.game_date} | {row.away_team:28} @ {row.home_team:28} | {game_id_str}")

        if row.game_id:
            games_with_id += 1
        else:
            games_without_id += 1

    print("-" * 70)
    print(f"\nResults:")
    print(f"  Games with game_id: {games_with_id}")
    print(f"  Games without game_id: {games_without_id}")

    # Clean up test table
    print(f"\nCleaning up test table...")
    client.delete_table(f"{GCP_PROJECT_ID}.nba_data.{test_table}")
    print(f"✓ Test table deleted")

    print("\n" + "=" * 70)
    if games_with_id > 0 and games_without_id == 0:
        print("✅ TEST PASSED - All games have game_ids!")
    elif games_with_id > 0:
        print("⚠️  TEST PARTIAL - Some games have game_ids")
    else:
        print("❌ TEST FAILED - No games have game_ids")
    print("=" * 70)

    return games_with_id, games_without_id


if __name__ == "__main__":
    test_auto_game_id()

"""
Upload sports game data to BigQuery
Supports NBA, NHL, and NFL data with flexible dataset configuration
"""

import json
import sys
from bigquery_writer import NBAGameBigQueryWriter
import os


def upload_sports_data(json_file: str, dataset_id: str, sport_name: str):
    """
    Upload sports game data to BigQuery

    Args:
        json_file: Path to JSON file with game data
        dataset_id: BigQuery dataset (e.g., 'nba_data', 'nhl_data', 'nfl_data')
        sport_name: Sport name for display (e.g., 'NBA', 'NHL', 'NFL')
    """
    # Get project ID from environment
    project_id = os.getenv("GCP_PROJECT_ID", "tenki-476718")

    # Load game data
    with open(json_file, 'r') as f:
        games = json.load(f)

    print(f"Loaded {len(games)} {sport_name} games from {json_file}")

    # Initialize writer (using the same class since schema is identical)
    writer = NBAGameBigQueryWriter(
        project_id=project_id,
        dataset_id=dataset_id,
        table_id="game_results"
    )

    # Ensure table exists
    writer.create_table_if_not_exists()

    # Insert games
    print(f"Uploading to {dataset_id}.game_results...")
    results = writer.insert_games(games, skip_duplicates=True)

    print(f"\n{sport_name} Upload Results:")
    print(f"  Inserted: {results['inserted']}")
    print(f"  Skipped (duplicates): {results['skipped']}")
    print(f"  Errors: {results['errors']}")

    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python upload_sports_data.py <json_file> <dataset_id> [sport_name]")
        print("Example: python upload_sports_data.py nhl_test_week.json nhl_data NHL")
        sys.exit(1)

    json_file = sys.argv[1]
    dataset_id = sys.argv[2]
    sport_name = sys.argv[3] if len(sys.argv) > 3 else dataset_id.upper().replace("_DATA", "")

    upload_sports_data(json_file, dataset_id, sport_name)

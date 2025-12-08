"""
Upload generated NBA game data to BigQuery
"""

import json
import os
import sys
from bigquery_writer import NBAGameBigQueryWriter


def upload_json_to_bigquery(json_file: str, project_id: str, dataset_id: str = "nba_data",
                             table_id: str = "game_results", credentials_path: str = None):
    """Upload games from JSON file to BigQuery"""

    # Load games from JSON
    with open(json_file, 'r') as f:
        games = json.load(f)

    print(f"Loaded {len(games)} games from {json_file}")

    # Create writer
    writer = NBAGameBigQueryWriter(
        project_id=project_id,
        dataset_id=dataset_id,
        table_id=table_id,
        credentials_path=credentials_path
    )

    # Ensure table exists
    writer.create_table_if_not_exists()

    # Insert data
    print(f"Uploading to BigQuery table {project_id}.{dataset_id}.{table_id}...")
    results = writer.insert_games(games, skip_duplicates=True)

    print(f"\nUpload complete:")
    print(f"  Inserted: {results['inserted']}")
    print(f"  Skipped (duplicates): {results['skipped']}")
    print(f"  Errors: {results['errors']}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Upload NBA game JSON to BigQuery")
    parser.add_argument("json_file", help="Path to JSON file containing games")
    parser.add_argument("--project-id", help="GCP project ID (or set GCP_PROJECT_ID env var)")
    parser.add_argument("--dataset-id", default="nba_data", help="BigQuery dataset ID")
    parser.add_argument("--table-id", default="game_results", help="BigQuery table ID")
    parser.add_argument("--credentials-path", help="Path to GCP credentials JSON")

    args = parser.parse_args()

    project_id = args.project_id or os.getenv("GCP_PROJECT_ID")
    credentials_path = args.credentials_path or os.getenv("GCP_CREDENTIALS_PATH")

    if not project_id:
        print("Error: GCP_PROJECT_ID must be provided via --project-id or environment variable")
        sys.exit(1)

    upload_json_to_bigquery(
        json_file=args.json_file,
        project_id=project_id,
        dataset_id=args.dataset_id,
        table_id=args.table_id,
        credentials_path=credentials_path
    )

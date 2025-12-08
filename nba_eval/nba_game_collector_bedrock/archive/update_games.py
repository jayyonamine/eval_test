"""
Incremental NBA Game Data Updater
Updates BigQuery table with games that occurred since the last game in the table
"""

import os
import sys
from datetime import datetime, timedelta
from google.cloud import bigquery
from generate_game_data import generate_date_range_games
from bigquery_writer import NBAGameBigQueryWriter


def get_last_game_date(project_id: str, dataset_id: str = "nba_data",
                       table_id: str = "game_results", credentials_path: str = None) -> str:
    """
    Query BigQuery to get the most recent game date in the table

    Returns:
        Last game date as string (YYYY-MM-DD), or None if table is empty
    """
    # Initialize BigQuery client
    if credentials_path:
        client = bigquery.Client(project=project_id, credentials=credentials_path)
    else:
        client = bigquery.Client(project=project_id)

    # Query for the most recent game date
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


def update_games(project_id: str, dataset_id: str = "nba_data",
                 table_id: str = "game_results", credentials_path: str = None,
                 end_date: str = None, seed: int = None, dry_run: bool = False):
    """
    Update BigQuery table with games since the last game date

    Args:
        project_id: GCP project ID
        dataset_id: BigQuery dataset name
        table_id: BigQuery table name
        credentials_path: Path to GCP service account key (optional)
        end_date: End date for updates (defaults to today)
        seed: Random seed for reproducibility (optional)
        dry_run: If True, only show what would be updated without actually updating
    """

    print("=" * 70)
    print("NBA Game Data Incremental Update")
    print("=" * 70)

    # Get the last game date from BigQuery
    print(f"\nQuerying {project_id}.{dataset_id}.{table_id} for most recent game...")
    last_game_date = get_last_game_date(project_id, dataset_id, table_id, credentials_path)

    if not last_game_date:
        print("No games found in table. Use generate_game_data.py for initial load.")
        return

    print(f"Most recent game date in table: {last_game_date}")

    # Calculate start date (day after last game)
    last_date = datetime.strptime(last_game_date, "%Y-%m-%d")
    start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")

    # Use provided end_date or default to yesterday (games are only final after the day ends)
    if end_date is None:
        end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        # Ensure end_date is not in the future
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if end_date > yesterday:
            print(f"Warning: Specified end_date {end_date} is in the future.")
            print(f"Adjusting to yesterday: {yesterday}")
            end_date = yesterday

    print(f"Update range: {start_date} to {end_date}")

    # Check if we need to update
    if start_date > end_date:
        print("\nTable is already up to date! No new games to add.")
        return

    # Generate new games
    print(f"\nGenerating games from {start_date} to {end_date}...")
    print("-" * 70)

    if seed is not None:
        import random
        random.seed(seed)

    new_games = generate_date_range_games(start_date, end_date)

    print("-" * 70)

    if not new_games:
        print("\nNo new games generated for this date range.")
        return

    print(f"\nGenerated {len(new_games)} new games")

    # Dry run mode - just show what would be done
    if dry_run:
        print("\n*** DRY RUN MODE - No data will be inserted ***")
        print(f"Would insert {len(new_games)} games into {project_id}.{dataset_id}.{table_id}")

        # Show sample of games
        print("\nSample of games that would be inserted:")
        for i, game in enumerate(new_games[:5]):
            print(f"  {game['game_date']}: {game['away_team']} @ {game['home_team']} "
                  f"({game['away_score']}-{game['home_score']})")

        if len(new_games) > 5:
            print(f"  ... and {len(new_games) - 5} more games")

        return

    # Insert new games into BigQuery
    print(f"\nInserting games into BigQuery...")

    writer = NBAGameBigQueryWriter(
        project_id=project_id,
        dataset_id=dataset_id,
        table_id=table_id,
        credentials_path=credentials_path
    )

    # Table should already exist, but ensure it does
    writer.create_table_if_not_exists()

    # Insert data
    results = writer.insert_games(new_games, skip_duplicates=True)

    print("\n" + "=" * 70)
    print("UPDATE COMPLETE")
    print("=" * 70)
    print(f"Inserted: {results['inserted']} games")
    print(f"Skipped (duplicates): {results['skipped']} games")
    print(f"Errors: {results['errors']}")
    print(f"\nTable now contains games through: {end_date}")

    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Update NBA game data in BigQuery with games since last update",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update with games through today (uses environment variables)
  python update_games.py

  # Update with specific end date
  python update_games.py --end-date 2025-12-15

  # Dry run to see what would be updated
  python update_games.py --dry-run

  # Update with specific project ID
  python update_games.py --project-id my-project-123

  # Update with reproducible random seed
  python update_games.py --seed 2025
        """
    )

    parser.add_argument("--project-id", help="GCP project ID (or set GCP_PROJECT_ID env var)")
    parser.add_argument("--dataset-id", default="nba_data", help="BigQuery dataset ID (default: nba_data)")
    parser.add_argument("--table-id", default="game_results", help="BigQuery table ID (default: game_results)")
    parser.add_argument("--credentials-path", help="Path to GCP credentials JSON (or set GCP_CREDENTIALS_PATH env var)")
    parser.add_argument("--end-date", help="End date for update (YYYY-MM-DD). Defaults to today")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without actually updating")

    args = parser.parse_args()

    # Get configuration from args or environment
    project_id = args.project_id or os.getenv("GCP_PROJECT_ID")
    credentials_path = args.credentials_path or os.getenv("GCP_CREDENTIALS_PATH")

    if not project_id:
        print("Error: GCP_PROJECT_ID must be provided via --project-id or environment variable")
        sys.exit(1)

    # Run the update
    update_games(
        project_id=project_id,
        dataset_id=args.dataset_id,
        table_id=args.table_id,
        credentials_path=credentials_path,
        end_date=args.end_date,
        seed=args.seed,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()

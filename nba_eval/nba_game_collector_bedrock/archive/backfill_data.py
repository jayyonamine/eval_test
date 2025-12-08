"""
Historical Data Backfill Utility
Collect NBA game data for a range of historical dates
"""

from nba_agent import run_daily_collection
from datetime import datetime, timedelta
import time
import os


def backfill_date_range(
    start_date: str,
    end_date: str,
    aws_region: str,
    gcp_project_id: str,
    dataset_id: str = "nba_data",
    table_id: str = "game_results",
    credentials_path: str = None,
    aws_access_key: str = None,
    aws_secret_key: str = None,
    model_id: str = None,
    delay_seconds: int = 2
):
    """
    Backfill NBA game data for a range of dates
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        aws_region: AWS region for Bedrock
        gcp_project_id: GCP project ID
        dataset_id: BigQuery dataset name
        table_id: BigQuery table name
        credentials_path: Path to GCP service account key
        aws_access_key: AWS access key (optional)
        aws_secret_key: AWS secret key (optional)
        delay_seconds: Delay between API calls to avoid rate limits
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    current = start
    total_days = (end - start).days + 1
    processed = 0
    
    print(f"Backfilling data from {start_date} to {end_date}")
    print(f"Total days to process: {total_days}")
    print("=" * 60)
    
    stats = {
        "total_games": 0,
        "successful_days": 0,
        "failed_days": 0,
        "no_games_days": 0
    }
    
    while current <= end:
        target_date = current.strftime("%Y-%m-%d")
        processed += 1
        
        print(f"\n[{processed}/{total_days}] Processing {target_date}...")
        
        try:
            # Import here to get fresh data for each iteration
            from nba_agent import NBAGameCollectionAgent
            from bigquery_writer import NBAGameBigQueryWriter

            # Get skill path relative to this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            skill_path = os.path.join(script_dir, "nba_game_collector_skill.md")

            # Collect games
            agent = NBAGameCollectionAgent(
                aws_region=aws_region,
                skill_path=skill_path,
                aws_access_key=aws_access_key,
                aws_secret_key=aws_secret_key,
                model_id=model_id
            )
            
            games_data = agent.collect_games(target_date)
            
            if not games_data:
                print(f"  No games found for {target_date}")
                stats["no_games_days"] += 1
            else:
                # Write to BigQuery
                writer = NBAGameBigQueryWriter(
                    project_id=gcp_project_id,
                    dataset_id=dataset_id,
                    table_id=table_id,
                    credentials_path=credentials_path
                )
                
                results = writer.insert_games(games_data, skip_duplicates=True)
                
                stats["total_games"] += results["inserted"]
                stats["successful_days"] += 1
                
                print(f"  ✓ Collected {len(games_data)} games")
                print(f"  Inserted: {results['inserted']}, Skipped: {results['skipped']}, Errors: {results['errors']}")
            
            # Rate limiting delay
            if delay_seconds > 0:
                time.sleep(delay_seconds)
                
        except Exception as e:
            print(f"  ✗ Error processing {target_date}: {e}")
            stats["failed_days"] += 1
        
        current += timedelta(days=1)
    
    # Summary
    print("\n" + "=" * 60)
    print("BACKFILL COMPLETE")
    print("=" * 60)
    print(f"Total days processed: {processed}")
    print(f"Successful days: {stats['successful_days']}")
    print(f"Days with no games: {stats['no_games_days']}")
    print(f"Failed days: {stats['failed_days']}")
    print(f"Total games inserted: {stats['total_games']}")


def backfill_season(
    season_year: int,
    aws_region: str,
    gcp_project_id: str,
    dataset_id: str = "nba_data",
    table_id: str = "game_results",
    credentials_path: str = None,
    aws_access_key: str = None,
    aws_secret_key: str = None,
    model_id: str = None
):
    """
    Backfill an entire NBA season
    
    Args:
        season_year: Start year of the season (e.g., 2023 for 2023-24 season)
        aws_region: AWS region for Bedrock
        gcp_project_id: GCP project ID
        dataset_id: BigQuery dataset name
        table_id: BigQuery table name
        credentials_path: Path to GCP service account key
        aws_access_key: AWS access key (optional)
        aws_secret_key: AWS secret key (optional)
    """
    # NBA regular season typically runs from October to April
    start_date = f"{season_year}-10-01"
    end_date = f"{season_year + 1}-06-30"  # Includes playoffs
    
    print(f"Backfilling {season_year}-{season_year + 1} NBA season")
    
    backfill_date_range(
        start_date=start_date,
        end_date=end_date,
        aws_region=aws_region,
        gcp_project_id=gcp_project_id,
        dataset_id=dataset_id,
        table_id=table_id,
        credentials_path=credentials_path,
        aws_access_key=aws_access_key,
        aws_secret_key=aws_secret_key,
        model_id=model_id,
        delay_seconds=2
    )


def backfill_recent_week(
    aws_region: str,
    gcp_project_id: str,
    dataset_id: str = "nba_data",
    table_id: str = "game_results",
    credentials_path: str = None,
    aws_access_key: str = None,
    aws_secret_key: str = None,
    model_id: str = None
):
    """
    Backfill the past 7 days of games
    """
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    backfill_date_range(
        start_date=start_date,
        end_date=end_date,
        aws_region=aws_region,
        gcp_project_id=gcp_project_id,
        dataset_id=dataset_id,
        table_id=table_id,
        credentials_path=credentials_path,
        aws_access_key=aws_access_key,
        aws_secret_key=aws_secret_key,
        model_id=model_id,
        delay_seconds=1
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Backfill historical NBA game data")
    parser.add_argument("--mode", choices=["range", "season", "week"], required=True,
                       help="Backfill mode: range (date range), season (full season), or week (past 7 days)")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD) for range mode")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD) for range mode")
    parser.add_argument("--season", type=int, help="Season start year (e.g., 2023) for season mode")
    
    args = parser.parse_args()
    
    # Load config from environment
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    model_id = os.getenv("BEDROCK_MODEL_ID")
    project_id = os.getenv("GCP_PROJECT_ID")
    credentials_path = os.getenv("GCP_CREDENTIALS_PATH")
    
    if not aws_region or not project_id:
        print("Error: AWS_REGION and GCP_PROJECT_ID must be set")
        exit(1)
    
    if args.mode == "range":
        if not args.start_date or not args.end_date:
            print("Error: --start-date and --end-date required for range mode")
            exit(1)
        
        backfill_date_range(
            start_date=args.start_date,
            end_date=args.end_date,
            aws_region=aws_region,
            gcp_project_id=project_id,
            credentials_path=credentials_path,
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
            model_id=model_id
        )
    
    elif args.mode == "season":
        if not args.season:
            print("Error: --season required for season mode")
            exit(1)
        
        backfill_season(
            season_year=args.season,
            aws_region=aws_region,
            gcp_project_id=project_id,
            credentials_path=credentials_path,
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
            model_id=model_id
        )
    
    elif args.mode == "week":
        backfill_recent_week(
            aws_region=aws_region,
            gcp_project_id=project_id,
            credentials_path=credentials_path,
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
            model_id=model_id
        )

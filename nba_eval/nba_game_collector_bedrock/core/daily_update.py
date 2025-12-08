#!/usr/bin/env python3
"""
Daily Sports Data Update & Evaluation Pipeline

Single command to:
1. Collect game results from official APIs (NBA, NHL, NFL)
2. Auto-populate game_ids from forecasts table
3. Insert games into BigQuery
4. Auto-calculate eval features (actual results + bet correctness)

Usage:
    python3 core/daily_update.py               # Update all sports
    python3 core/daily_update.py --sport nba   # Update NBA only
    python3 core/daily_update.py --date 2025-12-08  # Specific date
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

# Import from same directory (core/)
from nba_agent import run_daily_collection as run_nba_collection
from nhl_agent import run_daily_collection as run_nhl_collection
from nfl_agent import run_daily_collection as run_nfl_collection


def get_config():
    """Get configuration from environment variables"""
    return {
        'aws_region': os.getenv("AWS_REGION", "us-east-1"),
        'gcp_project_id': os.getenv("GCP_PROJECT_ID"),
        'credentials_path': os.getenv("GCP_CREDENTIALS_PATH"),
        'aws_access_key': os.getenv("AWS_ACCESS_KEY_ID"),
        'aws_secret_key': os.getenv("AWS_SECRET_ACCESS_KEY"),
        'model_id': os.getenv("BEDROCK_MODEL_ID")
    }


def update_nba(target_date=None):
    """Update NBA games"""
    print("=" * 70)
    print("NBA UPDATE")
    print("=" * 70)

    try:
        config = get_config()
        run_nba_collection(
            aws_region=config['aws_region'],
            gcp_project_id=config['gcp_project_id'],
            dataset_id="nba_data",
            table_id="game_results",
            credentials_path=config['credentials_path'],
            target_date=target_date,
            aws_access_key=config['aws_access_key'],
            aws_secret_key=config['aws_secret_key'],
            model_id=config['model_id']
        )
        return True
    except Exception as e:
        print(f"❌ NBA update failed: {e}")
        return False


def update_nhl(target_date=None):
    """Update NHL games"""
    print("\n" + "=" * 70)
    print("NHL UPDATE")
    print("=" * 70)

    try:
        config = get_config()
        run_nhl_collection(
            aws_region=config['aws_region'],
            gcp_project_id=config['gcp_project_id'],
            dataset_id="nhl_data",
            table_id="game_results",
            credentials_path=config['credentials_path'],
            target_date=target_date,
            aws_access_key=config['aws_access_key'],
            aws_secret_key=config['aws_secret_key'],
            model_id=config['model_id']
        )
        return True
    except Exception as e:
        print(f"❌ NHL update failed: {e}")
        return False


def update_nfl(target_date=None):
    """Update NFL games"""
    print("\n" + "=" * 70)
    print("NFL UPDATE")
    print("=" * 70)

    try:
        config = get_config()
        run_nfl_collection(
            aws_region=config['aws_region'],
            gcp_project_id=config['gcp_project_id'],
            dataset_id="nfl_data",
            table_id="game_results",
            credentials_path=config['credentials_path'],
            target_date=target_date,
            aws_access_key=config['aws_access_key'],
            aws_secret_key=config['aws_secret_key'],
            model_id=config['model_id']
        )
        return True
    except Exception as e:
        print(f"❌ NFL update failed: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Update sports data and calculate eval features"
    )
    parser.add_argument(
        "--sport",
        choices=["nba", "nhl", "nfl", "all"],
        default="all",
        help="Which sport to update (default: all)"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Target date (YYYY-MM-DD). Default: yesterday"
    )

    args = parser.parse_args()

    # Parse target date
    if args.date:
        target_date = args.date  # Already in YYYY-MM-DD format
    else:
        target_date = (datetime.now() - timedelta(days=1)).date().strftime("%Y-%m-%d")

    print("=" * 70)
    print("DAILY SPORTS DATA UPDATE & EVALUATION")
    print("=" * 70)
    print(f"Target Date: {target_date}")
    print(f"Sports: {args.sport.upper()}")
    print("=" * 70)

    results = {}

    # Update requested sport(s)
    if args.sport in ["nba", "all"]:
        results["nba"] = update_nba(target_date)

    if args.sport in ["nhl", "all"]:
        results["nhl"] = update_nhl(target_date)

    if args.sport in ["nfl", "all"]:
        results["nfl"] = update_nfl(target_date)

    # Summary
    print("\n" + "=" * 70)
    print("UPDATE SUMMARY")
    print("=" * 70)

    for sport, success in results.items():
        status = "✓ Success" if success else "❌ Failed"
        print(f"{sport.upper():10} {status}")

    all_success = all(results.values())

    if all_success:
        print("\n✅ All updates completed successfully!")
        print("\nWhat happened automatically:")
        print("  1. ✓ Collected games from official APIs")
        print("  2. ✓ Auto-populated game_ids from forecasts")
        print("  3. ✓ Inserted games into BigQuery")
        print("  4. ✓ Calculated eval features (actuals + bet correctness)")
    else:
        print("\n⚠️  Some updates failed. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

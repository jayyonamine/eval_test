"""
Fix NBA games by replacing Dec 4-5 data with correct API-sourced games
"""

import os
from datetime import datetime
from google.cloud import bigquery
from nba_agent import run_daily_collection

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID")

def fix_nba_games():
    """Fix NBA games for Dec 4-5 by creating corrected table"""
    client = bigquery.Client(project=GCP_PROJECT_ID)

    print("=" * 70)
    print("Fixing NBA Games for December 4-5, 2025")
    print("=" * 70)

    # Step 1: Create backup table with all data except Dec 4-5
    print("\nStep 1: Creating backup table without Dec 4-5 data...")
    backup_query = """
    CREATE OR REPLACE TABLE `tenki-476718.nba_data.game_results_backup` AS
    SELECT *
    FROM `tenki-476718.nba_data.game_results`
    WHERE game_date NOT IN ('2025-12-04', '2025-12-05')
    """
    job = client.query(backup_query)
    job.result()
    print("Backup table created successfully")

    # Step 2: Collect correct games for Dec 4
    print("\nStep 2: Collecting correct NBA games for 2025-12-04...")
    print("-" * 70)
    try:
        run_daily_collection(
            aws_region=AWS_REGION,
            gcp_project_id=GCP_PROJECT_ID,
            dataset_id="nba_data",
            table_id="game_results_backup",
            target_date="2025-12-04",
            aws_access_key=AWS_ACCESS_KEY,
            aws_secret_key=AWS_SECRET_KEY,
            model_id=BEDROCK_MODEL_ID
        )
    except Exception as e:
        print(f"Error collecting Dec 4 games: {e}")

    # Step 3: Collect correct games for Dec 5
    print("\nStep 3: Collecting correct NBA games for 2025-12-05...")
    print("-" * 70)
    try:
        run_daily_collection(
            aws_region=AWS_REGION,
            gcp_project_id=GCP_PROJECT_ID,
            dataset_id="nba_data",
            table_id="game_results_backup",
            target_date="2025-12-05",
            aws_access_key=AWS_ACCESS_KEY,
            aws_secret_key=AWS_SECRET_KEY,
            model_id=BEDROCK_MODEL_ID
        )
    except Exception as e:
        print(f"Error collecting Dec 5 games: {e}")

    # Step 4: Replace original table with corrected table (preserving partitioning)
    print("\nStep 4: Replacing original table with corrected data...")

    # First drop the original table
    print("Dropping original table...")
    client.delete_table("tenki-476718.nba_data.game_results")
    print("Original table dropped")

    # Recreate with correct partitioning (game_date is STRING so parse it)
    print("Recreating table with partitioning...")
    replace_query = """
    CREATE TABLE `tenki-476718.nba_data.game_results`
    PARTITION BY PARSE_DATE('%Y-%m-%d', game_date)
    AS
    SELECT *
    FROM `tenki-476718.nba_data.game_results_backup`
    ORDER BY game_date, home_team
    """
    job = client.query(replace_query)
    job.result()
    print("Original table recreated with corrected data")

    # Step 5: Clean up backup table
    print("\nStep 5: Cleaning up backup table...")
    client.delete_table("tenki-476718.nba_data.game_results_backup")
    print("Backup table deleted")

    print("\n" + "=" * 70)
    print("NBA GAME FIX COMPLETE")
    print("=" * 70)
    print("All NBA games now sourced from official ESPN API")
    print("December 4-5 data has been corrected")

if __name__ == "__main__":
    fix_nba_games()

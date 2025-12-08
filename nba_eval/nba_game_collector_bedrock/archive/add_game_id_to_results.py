"""
Add game_id field to nba_data.game_results table to enable joining with forecasts_mike.relational_forecasts

This script:
1. Analyzes both tables to understand matching criteria
2. Creates a mapping between game_results and forecasts using:
   - game_date (parsed from kalshi_event_ticker in forecasts)
   - away_team = team_away
   - home_team = team_home
3. Handles team name variations (LA Clippers vs Los Angeles Clippers)
4. Adds game_id column to game_results table
5. Updates all matching games with their corresponding game_id
6. Validates the results

Perfect matching logic:
- Extract game_date from kalshi_event_ticker using PARSE_DATE
- Standardize team names to handle "LA Clippers" <-> "Los Angeles Clippers"
- Match on (game_date, standardized_away_team, standardized_home_team)
"""

import os
from google.cloud import bigquery
from datetime import datetime

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")


def standardize_team_name(team_name):
    """Standardize team names to ensure perfect matching"""
    # Handle the LA Clippers / Los Angeles Clippers variation
    if team_name == "LA Clippers":
        return "Los Angeles Clippers"
    return team_name


def analyze_tables(client):
    """Analyze both tables before making changes"""
    print("=" * 70)
    print("ANALYZING TABLES")
    print("=" * 70)

    # Check game_results structure
    query = """
    SELECT
        COUNT(*) as total_games,
        MIN(game_date) as first_date,
        MAX(game_date) as last_date,
        COUNT(DISTINCT CONCAT(game_date, away_team, home_team)) as unique_matchups
    FROM `tenki-476718.nba_data.game_results`
    """
    result = client.query(query).result()
    for row in result:
        print(f"\ngame_results:")
        print(f"  Total games: {row.total_games}")
        print(f"  Date range: {row.first_date} to {row.last_date}")
        print(f"  Unique matchups: {row.unique_matchups}")

    # Check forecasts structure
    query = """
    WITH forecast_games AS (
        SELECT DISTINCT
            game_id,
            PARSE_DATE('%y%b%d',
                REGEXP_EXTRACT(kalshi_event_ticker, r'-(\d{2}[A-Z]{3}\d{2})')) as game_date,
            team_away,
            team_home
        FROM `tenki-476718.forecasts_mike.relational_forecasts`
    )
    SELECT
        COUNT(*) as total_unique_games,
        MIN(game_date) as first_date,
        MAX(game_date) as last_date
    FROM forecast_games
    """
    result = client.query(query).result()
    for row in result:
        print(f"\nrelational_forecasts:")
        print(f"  Unique games: {row.total_unique_games}")
        print(f"  Date range: {row.first_date} to {row.last_date}")


def test_matching_logic(client):
    """Test the matching logic before applying"""
    print("\n" + "=" * 70)
    print("TESTING MATCHING LOGIC")
    print("=" * 70)

    query = """
    WITH forecast_games AS (
        SELECT DISTINCT
            game_id,
            PARSE_DATE('%y%b%d',
                REGEXP_EXTRACT(kalshi_event_ticker, r'-(\d{2}[A-Z]{3}\d{2})')) as game_date,
            -- Standardize team names
            CASE
                WHEN team_away = 'LA Clippers' THEN 'Los Angeles Clippers'
                WHEN team_away = 'Los Angeles Clippers' THEN 'Los Angeles Clippers'
                ELSE team_away
            END as away_team_std,
            CASE
                WHEN team_home = 'LA Clippers' THEN 'Los Angeles Clippers'
                WHEN team_home = 'Los Angeles Clippers' THEN 'Los Angeles Clippers'
                ELSE team_home
            END as home_team_std
        FROM `tenki-476718.forecasts_mike.relational_forecasts`
    ),
    game_results_std AS (
        SELECT
            game_date,
            away_team,
            home_team,
            away_score,
            home_score,
            points_total,
            -- Standardize team names
            CASE
                WHEN away_team = 'LA Clippers' THEN 'Los Angeles Clippers'
                WHEN away_team = 'Los Angeles Clippers' THEN 'Los Angeles Clippers'
                ELSE away_team
            END as away_team_std,
            CASE
                WHEN home_team = 'LA Clippers' THEN 'Los Angeles Clippers'
                WHEN home_team = 'Los Angeles Clippers' THEN 'Los Angeles Clippers'
                ELSE home_team
            END as home_team_std
        FROM `tenki-476718.nba_data.game_results`
    )
    SELECT
        gr.game_date,
        gr.away_team as away_team_orig,
        gr.home_team as home_team_orig,
        gr.away_score,
        gr.home_score,
        gr.points_total,
        fg.game_id,
        CASE
            WHEN fg.game_id IS NOT NULL THEN 'MATCHED'
            ELSE 'NO MATCH'
        END as match_status
    FROM game_results_std gr
    LEFT JOIN forecast_games fg
        ON gr.game_date = fg.game_date
        AND gr.away_team_std = fg.away_team_std
        AND gr.home_team_std = fg.home_team_std
    WHERE gr.game_date >= '2025-12-05'
    ORDER BY gr.game_date DESC, match_status, gr.home_team
    """

    result = client.query(query).result()

    matched = 0
    unmatched = 0

    print("\nMatch results:")
    print("-" * 70)
    for row in result:
        status = "✓" if row.game_id else "✗"
        game_id_str = row.game_id[:8] if row.game_id else "N/A"
        print(f"{status} {row.game_date} | {row.away_team_orig:25} @ {row.home_team_orig:25} | ID: {game_id_str:8}")

        if row.game_id:
            matched += 1
        else:
            unmatched += 1

    print("-" * 70)
    print(f"Matched: {matched}")
    print(f"Unmatched: {unmatched}")

    return matched, unmatched


def add_game_id_column(client):
    """Add game_id column to game_results table if it doesn't exist"""
    print("\n" + "=" * 70)
    print("ADDING GAME_ID COLUMN")
    print("=" * 70)

    # Check if column already exists
    table = client.get_table('tenki-476718.nba_data.game_results')
    existing_fields = [field.name for field in table.schema]

    if 'game_id' in existing_fields:
        print("✓ game_id column already exists")
        return False

    print("Adding game_id column to game_results table...")

    # Add the column
    query = """
    ALTER TABLE `tenki-476718.nba_data.game_results`
    ADD COLUMN IF NOT EXISTS game_id STRING
    """

    job = client.query(query)
    job.result()

    print("✓ game_id column added successfully")
    return True


def update_game_ids(client):
    """Update game_id values in game_results by matching with forecasts"""
    print("\n" + "=" * 70)
    print("UPDATING GAME_IDs")
    print("=" * 70)

    # Use MERGE statement instead of UPDATE with correlated subquery
    query = """
    MERGE `tenki-476718.nba_data.game_results` AS target
    USING (
        SELECT DISTINCT
            game_id,
            PARSE_DATE('%y%b%d',
                REGEXP_EXTRACT(kalshi_event_ticker, r'-(\d{2}[A-Z]{3}\d{2})')) as game_date,
            -- Standardize team names for matching
            CASE
                WHEN team_away = 'LA Clippers' THEN 'Los Angeles Clippers'
                WHEN team_away = 'Los Angeles Clippers' THEN 'Los Angeles Clippers'
                ELSE team_away
            END as away_team_std,
            CASE
                WHEN team_home = 'LA Clippers' THEN 'Los Angeles Clippers'
                WHEN team_home = 'Los Angeles Clippers' THEN 'Los Angeles Clippers'
                ELSE team_home
            END as home_team_std
        FROM `tenki-476718.forecasts_mike.relational_forecasts`
    ) AS source
    ON target.game_date = source.game_date
        AND CASE
                WHEN target.away_team = 'LA Clippers' THEN 'Los Angeles Clippers'
                WHEN target.away_team = 'Los Angeles Clippers' THEN 'Los Angeles Clippers'
                ELSE target.away_team
            END = source.away_team_std
        AND CASE
                WHEN target.home_team = 'LA Clippers' THEN 'Los Angeles Clippers'
                WHEN target.home_team = 'Los Angeles Clippers' THEN 'Los Angeles Clippers'
                ELSE target.home_team
            END = source.home_team_std
    WHEN MATCHED THEN
        UPDATE SET game_id = source.game_id
    """

    print("Executing MERGE query...")
    job = client.query(query)
    result = job.result()

    print(f"✓ Updated {job.num_dml_affected_rows} rows")
    return job.num_dml_affected_rows


def validate_results(client):
    """Validate the game_id assignments"""
    print("\n" + "=" * 70)
    print("VALIDATING RESULTS")
    print("=" * 70)

    # Check how many games have game_ids
    query = """
    SELECT
        COUNT(*) as total_games,
        COUNT(game_id) as games_with_id,
        COUNT(*) - COUNT(game_id) as games_without_id,
        ROUND(100.0 * COUNT(game_id) / COUNT(*), 2) as percent_with_id
    FROM `tenki-476718.nba_data.game_results`
    """
    result = client.query(query).result()
    for row in result:
        print(f"\nOverall statistics:")
        print(f"  Total games: {row.total_games}")
        print(f"  Games with game_id: {row.games_with_id}")
        print(f"  Games without game_id: {row.games_without_id}")
        print(f"  Percentage with game_id: {row.percent_with_id}%")

    # Show sample joined data
    print("\nSample joined data (game_results + forecasts):")
    print("-" * 70)

    query = """
    SELECT
        gr.game_date,
        gr.away_team,
        gr.home_team,
        gr.away_score,
        gr.home_score,
        gr.points_total,
        gr.game_id,
        COUNT(DISTINCT rf.kalshi_market_ticker) as num_forecast_markets
    FROM `tenki-476718.nba_data.game_results` gr
    LEFT JOIN `tenki-476718.forecasts_mike.relational_forecasts` rf
        ON gr.game_id = rf.game_id
    WHERE gr.game_id IS NOT NULL
    GROUP BY gr.game_date, gr.away_team, gr.home_team, gr.away_score, gr.home_score, gr.points_total, gr.game_id
    ORDER BY gr.game_date DESC
    LIMIT 5
    """

    result = client.query(query).result()
    for row in result:
        print(f"{row.game_date} | {row.away_team:25} @ {row.home_team:25} | "
              f"Score: {row.away_score}-{row.home_score} | "
              f"game_id: {row.game_id[:8]}... | "
              f"Forecast markets: {row.num_forecast_markets}")


def main():
    """Main execution function"""
    print("=" * 70)
    print("NBA GAME RESULTS - ADD GAME_ID FIELD")
    print("Matching with forecasts_mike.relational_forecasts")
    print("=" * 70)

    client = bigquery.Client(project=GCP_PROJECT_ID)

    # Step 1: Analyze tables
    analyze_tables(client)

    # Step 2: Test matching logic
    matched, unmatched = test_matching_logic(client)

    if unmatched > 0:
        print(f"\n⚠️  Warning: {unmatched} games will not have game_ids (forecasts not available yet)")

    # Step 3: Confirm before proceeding
    print("\n" + "=" * 70)
    response = input("Proceed with adding game_id column and updating values? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return

    # Step 4: Add column
    add_game_id_column(client)

    # Step 5: Update game_ids
    updated_rows = update_game_ids(client)

    # Step 6: Validate
    validate_results(client)

    print("\n" + "=" * 70)
    print("✓ COMPLETE - game_id field successfully added and populated!")
    print("=" * 70)
    print(f"\nYou can now join tables using:")
    print(f"  FROM `tenki-476718.nba_data.game_results` gr")
    print(f"  JOIN `tenki-476718.forecasts_mike.relational_forecasts` rf")
    print(f"    ON gr.game_id = rf.game_id")


if __name__ == "__main__":
    main()

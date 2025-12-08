"""
Add game_id to game_results by recreating the table with the field populated

This approach avoids streaming buffer issues by:
1. Creating a new table with game_id populated via JOIN
2. Dropping the original table
3. Renaming the new table to replace the original
"""

import os
from google.cloud import bigquery

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")


def create_table_with_game_ids(client):
    """Create new table with game_ids populated"""
    print("=" * 70)
    print("CREATING NEW TABLE WITH GAME_IDs")
    print("=" * 70)

    # Create new table with game_ids populated
    # Use EXCEPT(game_id) in case the column already exists
    query = """
    CREATE OR REPLACE TABLE `tenki-476718.nba_data.game_results_with_ids`
    PARTITION BY game_date
    AS
    SELECT
        gr.* EXCEPT(game_id),
        fg.game_id
    FROM `tenki-476718.nba_data.game_results` gr
    LEFT JOIN (
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
    ) fg
    ON gr.game_date = fg.game_date
        AND CASE
                WHEN gr.away_team = 'LA Clippers' THEN 'Los Angeles Clippers'
                WHEN gr.away_team = 'Los Angeles Clippers' THEN 'Los Angeles Clippers'
                ELSE gr.away_team
            END = fg.away_team_std
        AND CASE
                WHEN gr.home_team = 'LA Clippers' THEN 'Los Angeles Clippers'
                WHEN gr.home_team = 'Los Angeles Clippers' THEN 'Los Angeles Clippers'
                ELSE gr.home_team
            END = fg.home_team_std
    """

    print("Creating game_results_with_ids table...")
    job = client.query(query)
    job.result()
    print("✓ New table created with game_ids")


def validate_new_table(client):
    """Validate the new table"""
    print("\n" + "=" * 70)
    print("VALIDATING NEW TABLE")
    print("=" * 70)

    query = """
    SELECT
        COUNT(*) as total_rows,
        COUNT(game_id) as rows_with_game_id,
        COUNT(*) - COUNT(game_id) as rows_without_game_id
    FROM `tenki-476718.nba_data.game_results_with_ids`
    """

    result = client.query(query).result()
    for row in result:
        print(f"\nNew table statistics:")
        print(f"  Total rows: {row.total_rows}")
        print(f"  Rows with game_id: {row.rows_with_game_id}")
        print(f"  Rows without game_id: {row.rows_without_game_id}")

    # Show sample matches
    print("\nSample matched games:")
    query = """
    SELECT
        game_date,
        away_team,
        home_team,
        away_score,
        home_score,
        points_total,
        game_id
    FROM `tenki-476718.nba_data.game_results_with_ids`
    WHERE game_id IS NOT NULL
    ORDER BY game_date DESC
    LIMIT 5
    """

    result = client.query(query).result()
    for row in result:
        print(f"  {row.game_date} | {row.away_team:25} @ {row.home_team:25} | game_id: {row.game_id[:8]}...")


def replace_original_table(client):
    """Replace original table with new one"""
    print("\n" + "=" * 70)
    print("REPLACING ORIGINAL TABLE")
    print("=" * 70)

    # Drop original table
    print("Dropping original game_results table...")
    client.delete_table("tenki-476718.nba_data.game_results", not_found_ok=True)
    print("✓ Original table dropped")

    # Rename new table to original name
    print("Creating new game_results table from game_results_with_ids...")
    query = """
    CREATE OR REPLACE TABLE `tenki-476718.nba_data.game_results`
    PARTITION BY game_date
    AS
    SELECT *
    FROM `tenki-476718.nba_data.game_results_with_ids`
    """

    job = client.query(query)
    job.result()
    print("✓ New table created as game_results")

    # Clean up temporary table
    print("Cleaning up temporary table...")
    client.delete_table("tenki-476718.nba_data.game_results_with_ids")
    print("✓ Temporary table removed")


def final_validation(client):
    """Final validation of the result"""
    print("\n" + "=" * 70)
    print("FINAL VALIDATION")
    print("=" * 70)

    # Check schema
    table = client.get_table('tenki-476718.nba_data.game_results')
    print("\nTable schema:")
    for field in table.schema:
        print(f"  {field.name}: {field.field_type}")

    # Check data
    query = """
    SELECT
        COUNT(*) as total_games,
        COUNT(game_id) as games_with_id,
        ROUND(100.0 * COUNT(game_id) / COUNT(*), 2) as percent_with_id,
        COUNT(DISTINCT game_id) as unique_game_ids
    FROM `tenki-476718.nba_data.game_results`
    """

    result = client.query(query).result()
    print("\nData statistics:")
    for row in result:
        print(f"  Total games: {row.total_games}")
        print(f"  Games with game_id: {row.games_with_id}")
        print(f"  Percentage with game_id: {row.percent_with_id}%")
        print(f"  Unique game_ids: {row.unique_game_ids}")

    # Test join
    print("\nTest JOIN query:")
    query = """
    SELECT
        gr.game_date,
        gr.away_team,
        gr.home_team,
        gr.away_score,
        gr.home_score,
        gr.points_total,
        COUNT(DISTINCT rf.kalshi_market_ticker) as forecast_markets
    FROM `tenki-476718.nba_data.game_results` gr
    JOIN `tenki-476718.forecasts_mike.relational_forecasts` rf
        ON gr.game_id = rf.game_id
    GROUP BY gr.game_date, gr.away_team, gr.home_team, gr.away_score, gr.home_score, gr.points_total
    ORDER BY gr.game_date DESC
    LIMIT 3
    """

    result = client.query(query).result()
    print("\nSample joined data (first 3 games):")
    for row in result:
        print(f"  {row.game_date} | {row.away_team:25} @ {row.home_team:25} | "
              f"{row.away_score}-{row.home_score} (Total: {row.points_total}) | "
              f"Forecasts: {row.forecast_markets} markets")


def main():
    """Main execution"""
    print("=" * 70)
    print("ADD GAME_ID TO NBA GAME_RESULTS")
    print("Using table recreation to avoid streaming buffer issues")
    print("=" * 70)

    client = bigquery.Client(project=GCP_PROJECT_ID)

    # Confirm
    response = input("\nThis will recreate the game_results table. Proceed? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return

    # Step 1: Create new table with game_ids
    create_table_with_game_ids(client)

    # Step 2: Validate new table
    validate_new_table(client)

    # Step 3: Confirm replacement
    response = input("\nReplace original table? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted. Temporary table game_results_with_ids remains.")
        return

    # Step 4: Replace original
    replace_original_table(client)

    # Step 5: Final validation
    final_validation(client)

    print("\n" + "=" * 70)
    print("✓ COMPLETE!")
    print("=" * 70)
    print("\nThe game_results table now has a game_id field.")
    print("You can join with forecasts using:")
    print("  FROM `tenki-476718.nba_data.game_results` gr")
    print("  JOIN `tenki-476718.forecasts_mike.relational_forecasts` rf")
    print("    ON gr.game_id = rf.game_id")


if __name__ == "__main__":
    main()

"""
Update game_ids for December 6, 2025 NBA games
Uses table recreation approach to avoid streaming buffer issues
"""

import os
from google.cloud import bigquery

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")


def test_matching_logic(client):
    """Test matching logic for Dec 6 games"""
    print("=" * 70)
    print("TESTING MATCHING LOGIC FOR DEC 6 GAMES")
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
        WHERE PARSE_DATE('%y%b%d',
                REGEXP_EXTRACT(kalshi_event_ticker, r'-(\d{2}[A-Z]{3}\d{2})')) = '2025-12-06'
    ),
    game_results_std AS (
        SELECT
            game_date,
            away_team,
            home_team,
            away_score,
            home_score,
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
        WHERE game_date = '2025-12-06'
    )
    SELECT
        gr.game_date,
        gr.away_team,
        gr.home_team,
        gr.away_score,
        gr.home_score,
        fg.game_id,
        CASE WHEN fg.game_id IS NOT NULL THEN 'MATCHED' ELSE 'NO MATCH' END as status
    FROM game_results_std gr
    LEFT JOIN forecast_games fg
        ON gr.game_date = fg.game_date
        AND gr.away_team_std = fg.away_team_std
        AND gr.home_team_std = fg.home_team_std
    ORDER BY gr.home_team
    """

    result = client.query(query).result()
    matched = 0
    unmatched = 0

    print("\nMatch results:")
    print("-" * 70)
    for row in result:
        status = "✓" if row.game_id else "✗"
        game_id_str = row.game_id[:12] + "..." if row.game_id else "N/A"
        print(f"{status} {row.game_date} | {row.away_team:28} @ {row.home_team:28} | ID: {game_id_str}")

        if row.game_id:
            matched += 1
        else:
            unmatched += 1

    print("-" * 70)
    print(f"Matched: {matched}")
    print(f"Unmatched: {unmatched}")

    return matched, unmatched


def update_game_ids_via_recreation(client):
    """Update game_ids by recreating table (avoids streaming buffer issues)"""
    print("\n" + "=" * 70)
    print("UPDATING GAME_IDs VIA TABLE RECREATION")
    print("=" * 70)

    # Step 1: Create new table with updated game_ids
    print("\nStep 1: Creating table with updated game_ids...")
    query = """
    CREATE OR REPLACE TABLE `tenki-476718.nba_data.game_results_temp`
    PARTITION BY game_date
    AS
    SELECT
        gr.* EXCEPT(game_id),
        COALESCE(gr.game_id, fg.game_id) as game_id
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
        WHERE PARSE_DATE('%y%b%d',
                REGEXP_EXTRACT(kalshi_event_ticker, r'-(\d{2}[A-Z]{3}\d{2})')) = '2025-12-06'
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

    job = client.query(query)
    job.result()
    print("✓ Temporary table created with updated game_ids")

    # Step 2: Drop original table
    print("\nStep 2: Dropping original table...")
    client.delete_table("tenki-476718.nba_data.game_results")
    print("✓ Original table dropped")

    # Step 3: Recreate original table from temp
    print("\nStep 3: Recreating original table...")
    query = """
    CREATE TABLE `tenki-476718.nba_data.game_results`
    PARTITION BY game_date
    AS
    SELECT *
    FROM `tenki-476718.nba_data.game_results_temp`
    """

    job = client.query(query)
    job.result()
    print("✓ Original table recreated")

    # Step 4: Drop temp table
    print("\nStep 4: Cleaning up temporary table...")
    client.delete_table("tenki-476718.nba_data.game_results_temp")
    print("✓ Temporary table removed")


def validate_results(client):
    """Validate the game_id updates"""
    print("\n" + "=" * 70)
    print("VALIDATION - DEC 5-6 GAMES")
    print("=" * 70)

    query = """
    SELECT
        game_date,
        away_team,
        home_team,
        away_score,
        home_score,
        game_id,
        CASE WHEN game_id IS NOT NULL THEN 'HAS ID' ELSE 'MISSING' END as status
    FROM `tenki-476718.nba_data.game_results`
    WHERE game_date IN ('2025-12-05', '2025-12-06')
    ORDER BY game_date, home_team
    """

    result = client.query(query).result()
    games_with_id = 0
    games_without_id = 0

    for row in result:
        status_symbol = "✓" if row.game_id else "✗"
        game_id_str = row.game_id[:12] + "..." if row.game_id else "MISSING"
        print(f"{status_symbol} {row.game_date} | {row.away_team:28} @ {row.home_team:28} | {game_id_str}")
        if row.game_id:
            games_with_id += 1
        else:
            games_without_id += 1

    print(f"\nGames with game_id: {games_with_id}")
    print(f"Games without game_id: {games_without_id}")

    # Test JOIN
    print("\n" + "=" * 70)
    print("TESTING JOIN WITH FORECASTS")
    print("=" * 70)

    query = """
    SELECT
        gr.game_date,
        gr.away_team,
        gr.home_team,
        COUNT(DISTINCT rf.kalshi_market_ticker) as forecast_markets
    FROM `tenki-476718.nba_data.game_results` gr
    JOIN `tenki-476718.forecasts_mike.relational_forecasts` rf
        ON gr.game_id = rf.game_id
    WHERE gr.game_date IN ('2025-12-05', '2025-12-06')
    GROUP BY gr.game_date, gr.away_team, gr.home_team
    ORDER BY gr.game_date, gr.home_team
    """

    result = client.query(query).result()
    count = 0
    for row in result:
        count += 1
        print(f"  {row.game_date} | {row.away_team:28} @ {row.home_team:28} | Markets: {row.forecast_markets}")

    print(f"\nTotal games with forecasts: {count}")


def main():
    """Main execution"""
    print("=" * 70)
    print("UPDATE GAME_IDs FOR DECEMBER 6, 2025")
    print("=" * 70)

    client = bigquery.Client(project=GCP_PROJECT_ID)

    # Test matching logic
    matched, unmatched = test_matching_logic(client)

    if matched == 0:
        print("\n⚠️  No matches found! Check team name standardization.")
        return

    # Update game_ids
    update_game_ids_via_recreation(client)

    # Validate
    validate_results(client)

    print("\n" + "=" * 70)
    print("✓ COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    main()

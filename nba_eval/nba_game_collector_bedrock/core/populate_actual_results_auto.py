"""
Automatically populate actual results in forecasts table (non-interactive)

This script runs automatically without user prompts.
Use this for automated pipelines.
"""

import os
from google.cloud import bigquery

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")


def populate_actual_results(client):
    """Populate actual results using table recreation"""
    print("=" * 70)
    print("POPULATING ACTUAL RESULTS")
    print("=" * 70)

    # Check what will be updated (either missing actuals OR missing bet correctness)
    query = """
    SELECT
        COUNT(*) as total_forecast_rows,
        COUNT(DISTINCT rf.game_id) as total_games
    FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
    JOIN `tenki-476718.nba_data.game_results` gr
        ON rf.game_id = gr.game_id
    WHERE rf.actual_team_away_points IS NULL
        OR rf.tenki_bet_correct IS NULL
        OR rf.kalshi_bet_correct IS NULL
    """

    result = client.query(query).result()
    for row in result:
        rows_to_update = row.total_forecast_rows
        games_to_update = row.total_games

        if rows_to_update == 0:
            print("\n✓ All forecasts already have actual results populated")
            return

        print(f"\nWill update: {rows_to_update} forecast rows across {games_to_update} games")

    print("\nStep 1: Creating updated table with actual results...")

    query = """
    CREATE OR REPLACE TABLE `tenki-476718.forecasts_mike.relational_forecasts_temp`
    AS
    SELECT
        rf.* EXCEPT(actual_team_away_points, actual_team_home_points,
                    actual_team_home_win, actual_points_total, actual_points_total_over,
                    tenki_bet_correct, kalshi_bet_correct),
        -- Populate actual fields from game results
        COALESCE(rf.actual_team_away_points, gr.away_score) as actual_team_away_points,
        COALESCE(rf.actual_team_home_points, gr.home_score) as actual_team_home_points,
        COALESCE(rf.actual_points_total, gr.points_total) as actual_points_total,
        COALESCE(rf.actual_team_home_win,
            CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
        ) as actual_team_home_win,
        COALESCE(rf.actual_points_total_over,
            CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
        ) as actual_points_total_over,
        -- Calculate bet correctness for Tenki
        COALESCE(rf.tenki_bet_correct,
            CASE
                WHEN rf.tenki_team_home_winner_bet = 1 THEN
                    CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
                WHEN rf.tenki_points_total_over_bet = 1 THEN
                    CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
                WHEN rf.tenki_points_total_over_bet = 0 THEN
                    CASE WHEN gr.points_total <= rf.points_total_over THEN 1 ELSE 0 END
                ELSE NULL
            END
        ) as tenki_bet_correct,
        -- Calculate bet correctness for Kalshi
        COALESCE(rf.kalshi_bet_correct,
            CASE
                WHEN rf.kalshi_team_home_winner_bet = 1 THEN
                    CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
                WHEN rf.kalshi_points_total_over_bet = 1 THEN
                    CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
                WHEN rf.kalshi_points_total_over_bet = 0 THEN
                    CASE WHEN gr.points_total <= rf.points_total_over THEN 1 ELSE 0 END
                ELSE NULL
            END
        ) as kalshi_bet_correct
    FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
    LEFT JOIN `tenki-476718.nba_data.game_results` gr
        ON rf.game_id = gr.game_id
    """

    job = client.query(query)
    job.result()
    print("✓ Temporary table created with actual results")

    print("\nStep 2: Replacing original table...")
    client.delete_table("tenki-476718.forecasts_mike.relational_forecasts")
    print("✓ Original table dropped")

    query = """
    CREATE TABLE `tenki-476718.forecasts_mike.relational_forecasts`
    AS
    SELECT * FROM `tenki-476718.forecasts_mike.relational_forecasts_temp`
    """

    job = client.query(query)
    job.result()
    print("✓ Original table recreated")

    client.delete_table("tenki-476718.forecasts_mike.relational_forecasts_temp")
    print("✓ Temporary table removed")


def validate_results(client):
    """Validate results"""
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    query = """
    SELECT
        COUNT(DISTINCT rf.game_id) as total_games_with_forecasts,
        COUNT(DISTINCT CASE
            WHEN rf.actual_team_away_points IS NOT NULL
            THEN rf.game_id
        END) as games_with_actuals
    FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
    """

    result = client.query(query).result()
    for row in result:
        print(f"\nResults:")
        print(f"  Games with forecasts: {row.total_games_with_forecasts}")
        print(f"  Games with actual results: {row.games_with_actuals}")


def main():
    """Main execution"""
    print("=" * 70)
    print("AUTO-POPULATE ACTUAL RESULTS")
    print("=" * 70)

    client = bigquery.Client(project=GCP_PROJECT_ID)

    populate_actual_results(client)
    validate_results(client)

    print("\n" + "=" * 70)
    print("✓ COMPLETE!")
    print("=" * 70)


def populate_actual_results_silent(client):
    """
    Silently populate actual results (for automatic execution)

    Returns:
        Number of forecast rows updated
    """
    # Check what needs to be updated (either missing actuals OR missing bet correctness)
    query = """
    SELECT
        COUNT(*) as total_forecast_rows
    FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
    JOIN `tenki-476718.nba_data.game_results` gr
        ON rf.game_id = gr.game_id
    WHERE rf.actual_team_away_points IS NULL
        OR rf.tenki_bet_correct IS NULL
        OR rf.kalshi_bet_correct IS NULL
    """

    result = client.query(query).result()
    for row in result:
        rows_to_update = row.total_forecast_rows

        if rows_to_update == 0:
            return 0

    # Create updated table
    query = """
    CREATE OR REPLACE TABLE `tenki-476718.forecasts_mike.relational_forecasts_temp`
    AS
    SELECT
        rf.* EXCEPT(actual_team_away_points, actual_team_home_points,
                    actual_team_home_win, actual_points_total, actual_points_total_over,
                    tenki_bet_correct, kalshi_bet_correct),
        COALESCE(rf.actual_team_away_points, gr.away_score) as actual_team_away_points,
        COALESCE(rf.actual_team_home_points, gr.home_score) as actual_team_home_points,
        COALESCE(rf.actual_points_total, gr.points_total) as actual_points_total,
        COALESCE(rf.actual_team_home_win,
            CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
        ) as actual_team_home_win,
        COALESCE(rf.actual_points_total_over,
            CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
        ) as actual_points_total_over,
        -- Calculate bet correctness for Tenki
        COALESCE(rf.tenki_bet_correct,
            CASE
                WHEN rf.tenki_team_home_winner_bet = 1 THEN
                    CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
                WHEN rf.tenki_points_total_over_bet = 1 THEN
                    CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
                WHEN rf.tenki_points_total_over_bet = 0 THEN
                    CASE WHEN gr.points_total <= rf.points_total_over THEN 1 ELSE 0 END
                ELSE NULL
            END
        ) as tenki_bet_correct,
        -- Calculate bet correctness for Kalshi
        COALESCE(rf.kalshi_bet_correct,
            CASE
                WHEN rf.kalshi_team_home_winner_bet = 1 THEN
                    CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
                WHEN rf.kalshi_points_total_over_bet = 1 THEN
                    CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
                WHEN rf.kalshi_points_total_over_bet = 0 THEN
                    CASE WHEN gr.points_total <= rf.points_total_over THEN 1 ELSE 0 END
                ELSE NULL
            END
        ) as kalshi_bet_correct
    FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
    LEFT JOIN `tenki-476718.nba_data.game_results` gr
        ON rf.game_id = gr.game_id
    """

    job = client.query(query)
    job.result()

    # Replace original table
    client.delete_table("tenki-476718.forecasts_mike.relational_forecasts")

    query = """
    CREATE TABLE `tenki-476718.forecasts_mike.relational_forecasts`
    AS
    SELECT * FROM `tenki-476718.forecasts_mike.relational_forecasts_temp`
    """

    job = client.query(query)
    job.result()

    client.delete_table("tenki-476718.forecasts_mike.relational_forecasts_temp")

    return rows_to_update


if __name__ == "__main__":
    main()

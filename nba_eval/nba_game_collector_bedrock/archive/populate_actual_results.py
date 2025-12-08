"""
Populate Actual Results in Forecasts Table

Updates forecasts_mike.relational_forecasts with actual game results
from nba_data.game_results for all games with matching game_ids.

Fields populated:
- actual_team_away_points = game_results.away_score
- actual_team_home_points = game_results.home_score
- actual_points_total = game_results.points_total
- actual_team_home_win = 1 if home won, 0 otherwise
- actual_points_total_over = 1 if total > over line, 0 otherwise
"""

import os
from google.cloud import bigquery
from datetime import datetime

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")


def analyze_games_to_update(client):
    """Analyze which games need actual results populated"""
    print("=" * 70)
    print("ANALYZING GAMES TO UPDATE")
    print("=" * 70)

    query = """
    SELECT
        COUNT(DISTINCT rf.game_id) as games_with_forecasts,
        COUNT(DISTINCT CASE
            WHEN rf.actual_team_away_points IS NULL
            THEN rf.game_id
        END) as games_missing_actuals,
        COUNT(DISTINCT CASE
            WHEN rf.actual_team_away_points IS NOT NULL
            THEN rf.game_id
        END) as games_with_actuals
    FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
    JOIN `tenki-476718.nba_data.game_results` gr
        ON rf.game_id = gr.game_id
    """

    result = client.query(query).result()
    for row in result:
        print(f"\nForecast Games Summary:")
        print(f"  Games with forecasts: {row.games_with_forecasts}")
        print(f"  Games missing actual results: {row.games_missing_actuals}")
        print(f"  Games with actual results: {row.games_with_actuals}")

    # Show which games need updates
    query = """
    SELECT
        gr.game_id,
        gr.game_date,
        gr.away_team,
        gr.home_team,
        gr.away_score,
        gr.home_score,
        gr.points_total,
        COUNT(rf.forecast_id) as num_forecast_rows,
        MAX(rf.actual_team_away_points) as current_actual_away
    FROM `tenki-476718.nba_data.game_results` gr
    JOIN `tenki-476718.forecasts_mike.relational_forecasts` rf
        ON gr.game_id = rf.game_id
    GROUP BY gr.game_id, gr.game_date, gr.away_team, gr.home_team,
             gr.away_score, gr.home_score, gr.points_total
    ORDER BY gr.game_date DESC
    """

    result = client.query(query).result()
    games = []

    print("\n" + "=" * 70)
    print("GAMES WITH FORECAST DATA")
    print("=" * 70)

    for row in result:
        games.append(row)
        status = "✓ Has actuals" if row.current_actual_away else "✗ Missing actuals"
        game_id_short = row.game_id[:12] + "..."
        print(f"{status} | {row.game_date} | {row.away_team:25} @ {row.home_team:25}")
        print(f"         Score: {row.away_score}-{row.home_score} (Total: {row.points_total}) | "
              f"{row.num_forecast_rows} forecast rows | game_id: {game_id_short}")

    return games


def populate_actual_results(client):
    """
    Populate actual results using table recreation to avoid streaming buffer issues
    """
    print("\n" + "=" * 70)
    print("POPULATING ACTUAL RESULTS")
    print("=" * 70)

    print("\nStep 1: Creating updated table with actual results...")

    # Use CREATE OR REPLACE to recreate table with actual results populated
    query = """
    CREATE OR REPLACE TABLE `tenki-476718.forecasts_mike.relational_forecasts`
    AS
    SELECT
        rf.*,
        -- Only update if game_id matches and actuals not already set
        COALESCE(rf.actual_team_away_points, gr.away_score) as actual_team_away_points_new,
        COALESCE(rf.actual_team_home_points, gr.home_score) as actual_team_home_points_new,
        COALESCE(rf.actual_points_total, gr.points_total) as actual_points_total_new,
        COALESCE(rf.actual_team_home_win,
            CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
        ) as actual_team_home_win_new,
        COALESCE(rf.actual_points_total_over,
            CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
        ) as actual_points_total_over_new
    FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
    LEFT JOIN `tenki-476718.nba_data.game_results` gr
        ON rf.game_id = gr.game_id
    """

    # This won't work because we can't replace a table with a different schema
    # Let me use a different approach with EXCEPT and explicit field selection

    query = """
    CREATE OR REPLACE TABLE `tenki-476718.forecasts_mike.relational_forecasts_temp`
    AS
    SELECT
        rf.* EXCEPT(actual_team_away_points, actual_team_home_points,
                    actual_team_home_win, actual_points_total, actual_points_total_over),
        -- Populate actual fields from game results
        COALESCE(rf.actual_team_away_points, gr.away_score) as actual_team_away_points,
        COALESCE(rf.actual_team_home_points, gr.home_score) as actual_team_home_points,
        COALESCE(rf.actual_points_total, gr.points_total) as actual_points_total,
        COALESCE(rf.actual_team_home_win,
            CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
        ) as actual_team_home_win,
        COALESCE(rf.actual_points_total_over,
            CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
        ) as actual_points_total_over
    FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
    LEFT JOIN `tenki-476718.nba_data.game_results` gr
        ON rf.game_id = gr.game_id
    """

    job = client.query(query)
    job.result()
    print("✓ Temporary table created with actual results populated")

    print("\nStep 2: Replacing original table...")

    # Drop original
    client.delete_table("tenki-476718.forecasts_mike.relational_forecasts")
    print("✓ Original table dropped")

    # Rename temp to original
    query = """
    CREATE TABLE `tenki-476718.forecasts_mike.relational_forecasts`
    AS
    SELECT * FROM `tenki-476718.forecasts_mike.relational_forecasts_temp`
    """

    job = client.query(query)
    job.result()
    print("✓ Original table recreated with actual results")

    # Drop temp
    client.delete_table("tenki-476718.forecasts_mike.relational_forecasts_temp")
    print("✓ Temporary table removed")


def validate_results(client):
    """Validate that actual results were populated correctly"""
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    query = """
    SELECT
        COUNT(DISTINCT rf.game_id) as total_games_with_forecasts,
        COUNT(DISTINCT CASE
            WHEN rf.actual_team_away_points IS NOT NULL
            THEN rf.game_id
        END) as games_with_actuals,
        COUNT(DISTINCT CASE
            WHEN rf.actual_team_away_points IS NULL
            THEN rf.game_id
        END) as games_without_actuals
    FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
    """

    result = client.query(query).result()
    for row in result:
        print(f"\nOverall Statistics:")
        print(f"  Total games with forecasts: {row.total_games_with_forecasts}")
        print(f"  Games with actual results: {row.games_with_actuals}")
        print(f"  Games without actual results: {row.games_without_actuals}")

    # Sample populated data
    print("\n" + "=" * 70)
    print("SAMPLE POPULATED DATA")
    print("=" * 70)

    query = """
    SELECT
        rf.game_id,
        rf.team_away,
        rf.team_home,
        rf.kalshi_market_ticker,
        rf.points_total_over,
        rf.actual_team_away_points,
        rf.actual_team_home_points,
        rf.actual_points_total,
        rf.actual_team_home_win,
        rf.actual_points_total_over
    FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
    WHERE rf.actual_team_away_points IS NOT NULL
    ORDER BY rf.game_id
    LIMIT 5
    """

    result = client.query(query).result()
    print("\nSample rows with actual results:")
    print("-" * 70)

    for row in result:
        game_id_short = row.game_id[:12] + "..."
        print(f"game_id: {game_id_short} | Market: {row.kalshi_market_ticker}")
        print(f"  {row.team_away} @ {row.team_home}")
        print(f"  Actual Score: {row.actual_team_away_points}-{row.actual_team_home_points} "
              f"(Total: {row.actual_points_total})")
        print(f"  Home Win: {row.actual_team_home_win} | "
              f"Over {row.points_total_over}: {row.actual_points_total_over}")
        print()


def main():
    """Main execution"""
    print("=" * 70)
    print("POPULATE ACTUAL RESULTS IN FORECASTS TABLE")
    print("=" * 70)

    client = bigquery.Client(project=GCP_PROJECT_ID)

    # Step 1: Analyze what needs to be updated
    games = analyze_games_to_update(client)

    if not games:
        print("\n⚠️  No games with forecasts found")
        return

    # Step 2: Populate actual results
    print("\nReady to populate actual results for forecast data")
    response = input("\nProceed with updating forecasts table? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return

    populate_actual_results(client)

    # Step 3: Validate
    validate_results(client)

    print("\n" + "=" * 70)
    print("✓ COMPLETE!")
    print("=" * 70)
    print("\nActual results have been populated in the forecasts table.")
    print("Fields updated:")
    print("  • actual_team_away_points")
    print("  • actual_team_home_points")
    print("  • actual_points_total")
    print("  • actual_team_home_win")
    print("  • actual_points_total_over")


if __name__ == "__main__":
    main()

"""
Preview what actual results will be populated (dry run)
"""

import os
from google.cloud import bigquery

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")


def preview_updates(client):
    """Preview what will be updated"""
    print("=" * 70)
    print("PREVIEW - ACTUAL RESULTS TO BE POPULATED")
    print("=" * 70)

    query = """
    WITH updates AS (
        SELECT
            rf.game_id,
            rf.team_away,
            rf.team_home,
            rf.kalshi_market_ticker,
            rf.points_total_over,
            rf.actual_team_away_points as current_away_pts,
            rf.actual_team_home_points as current_home_pts,
            rf.actual_points_total as current_total_pts,
            gr.away_score as new_away_pts,
            gr.home_score as new_home_pts,
            gr.points_total as new_total_pts,
            CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END as new_home_win,
            CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END as new_total_over
        FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
        JOIN `tenki-476718.nba_data.game_results` gr
            ON rf.game_id = gr.game_id
        WHERE rf.actual_team_away_points IS NULL
    )
    SELECT * FROM updates
    LIMIT 10
    """

    result = client.query(query).result()

    print("\nSample forecast rows that will be updated:")
    print("-" * 70)

    for row in result:
        game_id_short = row.game_id[:12] + "..."
        print(f"game_id: {game_id_short} | Market: {row.kalshi_market_ticker}")
        print(f"  {row.team_away} @ {row.team_home}")
        print(f"  NEW VALUES:")
        print(f"    actual_team_away_points: {row.current_away_pts} → {row.new_away_pts}")
        print(f"    actual_team_home_points: {row.current_home_pts} → {row.new_home_pts}")
        print(f"    actual_points_total: {row.current_total_pts} → {row.new_total_pts}")
        print(f"    actual_team_home_win: → {row.new_home_win}")
        print(f"    actual_points_total_over (line={row.points_total_over}): → {row.new_total_over}")
        print()

    # Count total rows to be updated
    query = """
    SELECT
        COUNT(*) as total_forecast_rows,
        COUNT(DISTINCT rf.game_id) as total_games
    FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
    JOIN `tenki-476718.nba_data.game_results` gr
        ON rf.game_id = gr.game_id
    WHERE rf.actual_team_away_points IS NULL
    """

    result = client.query(query).result()
    for row in result:
        print("=" * 70)
        print(f"TOTAL TO UPDATE:")
        print(f"  {row.total_forecast_rows} forecast rows across {row.total_games} games")
        print("=" * 70)


def main():
    """Preview updates"""
    client = bigquery.Client(project=GCP_PROJECT_ID)
    preview_updates(client)

    print("\nTo apply these updates, run:")
    print("  python3 populate_actual_results.py")


if __name__ == "__main__":
    main()

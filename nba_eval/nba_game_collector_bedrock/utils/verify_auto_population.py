"""
Verify that actual results are being automatically populated
Run this after collecting new games to verify the integration works
"""

import os
from google.cloud import bigquery

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")


def verify_auto_population():
    """Verify that recent games have actuals populated"""
    client = bigquery.Client(project=GCP_PROJECT_ID)

    print("=" * 70)
    print("VERIFYING AUTOMATIC ACTUAL RESULTS POPULATION")
    print("=" * 70)

    # Get most recent games with game_ids
    query = """
    SELECT
        gr.game_date,
        gr.away_team,
        gr.home_team,
        gr.away_score,
        gr.home_score,
        gr.game_id,
        COUNT(rf.forecast_id) as num_forecast_rows,
        COUNT(CASE WHEN rf.actual_team_away_points IS NOT NULL THEN 1 END) as forecasts_with_actuals
    FROM `tenki-476718.nba_data.game_results` gr
    LEFT JOIN `tenki-476718.forecasts_mike.relational_forecasts` rf
        ON gr.game_id = rf.game_id
    WHERE gr.game_id IS NOT NULL
    GROUP BY gr.game_date, gr.away_team, gr.home_team, gr.away_score, gr.home_score, gr.game_id
    ORDER BY gr.game_date DESC
    LIMIT 10
    """

    result = client.query(query).result()

    print("\nMost recent games with game_ids:")
    print("-" * 70)

    all_synced = True
    for row in result:
        has_forecasts = row.num_forecast_rows > 0
        fully_synced = has_forecasts and row.forecasts_with_actuals == row.num_forecast_rows

        if has_forecasts:
            status = "✓ Synced" if fully_synced else f"✗ Missing ({row.forecasts_with_actuals}/{row.num_forecast_rows})"
            if not fully_synced:
                all_synced = False
        else:
            status = "○ No forecasts"

        print(f"{row.game_date} | {row.away_team:25} @ {row.home_team:25}")
        print(f"  Score: {row.away_score}-{row.home_score} | {status}")
        print()

    print("=" * 70)

    if all_synced:
        print("✅ SUCCESS - All games with forecasts have actual results populated!")
        print("\nAutomatic population is working correctly:")
        print("  1. New games collected ✓")
        print("  2. game_ids auto-populated ✓")
        print("  3. Actual results auto-populated in forecasts ✓")
    else:
        print("⚠️  Some games with forecasts are missing actual results")
        print("\nTo manually sync, run:")
        print("  python3 populate_actual_results_auto.py")

    return all_synced


if __name__ == "__main__":
    verify_auto_population()

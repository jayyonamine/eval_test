"""
Preview bet correctness calculations
"""

import os
from google.cloud import bigquery

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")


def preview_bet_correctness(client):
    """Preview bet correctness calculations"""
    print("=" * 70)
    print("PREVIEW - BET CORRECTNESS CALCULATIONS")
    print("=" * 70)

    query = """
    WITH calculations AS (
        SELECT
            rf.kalshi_market_ticker,
            rf.tenki_team_home_winner_bet,
            rf.tenki_points_total_over_bet,
            rf.kalshi_team_home_winner_bet,
            rf.kalshi_points_total_over_bet,
            rf.points_total_over as line,
            gr.away_score,
            gr.home_score,
            gr.points_total as actual_total,
            CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END as actual_home_win,
            CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END as actual_over,
            -- Tenki bet correctness
            CASE
                WHEN rf.tenki_team_home_winner_bet = 1 THEN
                    CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
                WHEN rf.tenki_points_total_over_bet = 1 THEN
                    CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
                WHEN rf.tenki_points_total_over_bet = 0 THEN
                    CASE WHEN gr.points_total <= rf.points_total_over THEN 1 ELSE 0 END
                ELSE NULL
            END as tenki_bet_correct_calc,
            -- Kalshi bet correctness
            CASE
                WHEN rf.kalshi_team_home_winner_bet = 1 THEN
                    CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
                WHEN rf.kalshi_points_total_over_bet = 1 THEN
                    CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
                WHEN rf.kalshi_points_total_over_bet = 0 THEN
                    CASE WHEN gr.points_total <= rf.points_total_over THEN 1 ELSE 0 END
                ELSE NULL
            END as kalshi_bet_correct_calc,
            rf.tenki_bet_correct as current_tenki_bet_correct,
            rf.kalshi_bet_correct as current_kalshi_bet_correct
        FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
        JOIN `tenki-476718.nba_data.game_results` gr
            ON rf.game_id = gr.game_id
        WHERE rf.actual_team_away_points IS NOT NULL
    )
    SELECT * FROM calculations
    LIMIT 15
    """

    result = client.query(query).result()

    print("\nSample bet correctness calculations:")
    print("-" * 70)

    for row in result:
        print(f"Market: {row.kalshi_market_ticker}")
        print(f"  Score: {row.away_score}-{row.home_score} (Total: {row.actual_total})")
        print(f"  Line: {row.line}")

        # Determine bet type
        if row.tenki_points_total_over_bet is not None:
            bet_type = "OVER" if row.tenki_points_total_over_bet == 1 else "UNDER"
            actual_result = "OVER" if row.actual_over == 1 else "UNDER"
            print(f"  Bet Type: Over/Under")
            print(f"    Tenki bet: {bet_type} | Actual: {actual_result}")
            print(f"    Tenki correct: {row.current_tenki_bet_correct} → {row.tenki_bet_correct_calc}")
            print(f"    Kalshi bet: {bet_type} | Actual: {actual_result}")
            print(f"    Kalshi correct: {row.current_kalshi_bet_correct} → {row.kalshi_bet_correct_calc}")
        elif row.tenki_team_home_winner_bet == 1:
            actual_winner = "HOME" if row.actual_home_win == 1 else "AWAY"
            print(f"  Bet Type: Team Winner")
            print(f"    Bet: HOME | Actual: {actual_winner}")
            print(f"    Tenki correct: {row.current_tenki_bet_correct} → {row.tenki_bet_correct_calc}")
            print(f"    Kalshi correct: {row.current_kalshi_bet_correct} → {row.kalshi_bet_correct_calc}")
        print()

    # Summary stats
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    query = """
    SELECT
        COUNT(*) as total_rows,
        COUNT(CASE WHEN tenki_bet_correct IS NULL THEN 1 END) as missing_tenki,
        COUNT(CASE WHEN kalshi_bet_correct IS NULL THEN 1 END) as missing_kalshi
    FROM `tenki-476718.forecasts_mike.relational_forecasts`
    WHERE actual_team_away_points IS NOT NULL
    """

    result = client.query(query).result()
    for row in result:
        print(f"\nForecast rows with actual results: {row.total_rows}")
        print(f"  Missing tenki_bet_correct: {row.missing_tenki}")
        print(f"  Missing kalshi_bet_correct: {row.missing_kalshi}")

    print("\nTo apply these calculations, run:")
    print("  python3 populate_actual_results_auto.py")


def main():
    """Preview bet correctness"""
    client = bigquery.Client(project=GCP_PROJECT_ID)
    preview_bet_correctness(client)


if __name__ == "__main__":
    main()

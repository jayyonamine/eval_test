"""
Fix bet correctness calculations for December 7, 2025 games

The issue: COALESCE preserved incorrect pre-existing values
The fix: Force recalculation for Dec 7 games
"""

import os
from google.cloud import bigquery

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")


def fix_dec7_bet_correctness(client):
    """Fix bet correctness for December 7 games"""
    print("=" * 70)
    print("FIXING DECEMBER 7, 2025 BET CORRECTNESS")
    print("=" * 70)

    print("\nStep 1: Creating corrected table...")

    query = """
    CREATE OR REPLACE TABLE `tenki-476718.forecasts_mike.relational_forecasts_temp`
    AS
    SELECT
        rf.* EXCEPT(actual_team_away_points, actual_team_home_points,
                    actual_team_home_win, actual_points_total, actual_points_total_over,
                    tenki_bet_correct, kalshi_bet_correct),
        -- For Dec 7 games: force recalculation
        -- For other games: preserve existing values
        CASE
            WHEN gr.game_date = '2025-12-07' THEN gr.away_score
            ELSE COALESCE(rf.actual_team_away_points, gr.away_score)
        END as actual_team_away_points,
        CASE
            WHEN gr.game_date = '2025-12-07' THEN gr.home_score
            ELSE COALESCE(rf.actual_team_home_points, gr.home_score)
        END as actual_team_home_points,
        CASE
            WHEN gr.game_date = '2025-12-07' THEN gr.points_total
            ELSE COALESCE(rf.actual_points_total, gr.points_total)
        END as actual_points_total,
        CASE
            WHEN gr.game_date = '2025-12-07' THEN
                CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
            ELSE COALESCE(rf.actual_team_home_win,
                CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END)
        END as actual_team_home_win,
        -- THIS IS THE KEY FIX: Force recalculation for Dec 7
        CASE
            WHEN gr.game_date = '2025-12-07' THEN
                CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
            ELSE COALESCE(rf.actual_points_total_over,
                CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END)
        END as actual_points_total_over,
        -- Calculate bet correctness for Tenki (force for Dec 7)
        CASE
            WHEN gr.game_date = '2025-12-07' THEN
                CASE
                    WHEN rf.tenki_team_home_winner_bet = 1 THEN
                        CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
                    WHEN rf.tenki_points_total_over_bet = 1 THEN
                        CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
                    WHEN rf.tenki_points_total_over_bet = 0 THEN
                        CASE WHEN gr.points_total <= rf.points_total_over THEN 1 ELSE 0 END
                    ELSE NULL
                END
            ELSE COALESCE(rf.tenki_bet_correct,
                CASE
                    WHEN rf.tenki_team_home_winner_bet = 1 THEN
                        CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
                    WHEN rf.tenki_points_total_over_bet = 1 THEN
                        CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
                    WHEN rf.tenki_points_total_over_bet = 0 THEN
                        CASE WHEN gr.points_total <= rf.points_total_over THEN 1 ELSE 0 END
                    ELSE NULL
                END)
        END as tenki_bet_correct,
        -- Calculate bet correctness for Kalshi (force for Dec 7)
        CASE
            WHEN gr.game_date = '2025-12-07' THEN
                CASE
                    WHEN rf.kalshi_team_home_winner_bet = 1 THEN
                        CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
                    WHEN rf.kalshi_points_total_over_bet = 1 THEN
                        CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
                    WHEN rf.kalshi_points_total_over_bet = 0 THEN
                        CASE WHEN gr.points_total <= rf.points_total_over THEN 1 ELSE 0 END
                    ELSE NULL
                END
            ELSE COALESCE(rf.kalshi_bet_correct,
                CASE
                    WHEN rf.kalshi_team_home_winner_bet = 1 THEN
                        CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
                    WHEN rf.kalshi_points_total_over_bet = 1 THEN
                        CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
                    WHEN rf.kalshi_points_total_over_bet = 0 THEN
                        CASE WHEN gr.points_total <= rf.points_total_over THEN 1 ELSE 0 END
                    ELSE NULL
                END)
        END as kalshi_bet_correct
    FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
    LEFT JOIN `tenki-476718.nba_data.game_results` gr
        ON rf.game_id = gr.game_id
    """

    job = client.query(query)
    job.result()
    print("✓ Temporary table created with corrected calculations")

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


def verify_fix(client):
    """Verify the fix worked"""
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    query = """
    SELECT
        COUNT(*) as total_bets,
        SUM(CASE WHEN tenki_bet_correct = 1 THEN 1 ELSE 0 END) as tenki_correct,
        SUM(CASE WHEN kalshi_bet_correct = 1 THEN 1 ELSE 0 END) as kalshi_correct,
        ROUND(100.0 * SUM(CASE WHEN tenki_bet_correct = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as tenki_accuracy,
        ROUND(100.0 * SUM(CASE WHEN kalshi_bet_correct = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as kalshi_accuracy
    FROM `tenki-476718.forecasts_mike.relational_forecasts` rf
    JOIN `tenki-476718.nba_data.game_results` gr ON rf.game_id = gr.game_id
    WHERE rf.actual_team_away_points IS NOT NULL
        AND gr.game_date = '2025-12-07'
    """

    result = client.query(query).result()

    print("\nDecember 7, 2025 Performance (After Fix):")
    for row in result:
        print(f"  Total Bets: {row.total_bets}")
        print(f"  Tenki: {row.tenki_correct}/{row.total_bets} correct ({row.tenki_accuracy}%)")
        print(f"  Kalshi: {row.kalshi_correct}/{row.total_bets} correct ({row.kalshi_accuracy}%)")


def main():
    """Main execution"""
    print("=" * 70)
    print("FIX DECEMBER 7 BET CORRECTNESS")
    print("=" * 70)

    client = bigquery.Client(project=GCP_PROJECT_ID)

    fix_dec7_bet_correctness(client)
    verify_fix(client)

    print("\n" + "=" * 70)
    print("✓ COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    main()

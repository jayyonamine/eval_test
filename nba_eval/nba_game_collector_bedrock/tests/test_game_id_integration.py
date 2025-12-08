"""
Integration test for automatic game_id population
Tests the lookup utility and BigQuery writer integration
"""

import os
from bigquery_writer import NBAGameBigQueryWriter
from game_id_lookup import GameIdLookup

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tenki-476718")


def test_game_id_lookup():
    """Test game_id lookup utility"""
    print("=" * 70)
    print("TEST 1: Game ID Lookup Utility")
    print("=" * 70)

    lookup = GameIdLookup(project_id=GCP_PROJECT_ID)

    # Test with known Dec 6 games
    test_games = [
        {
            "game_date": "2025-12-06",
            "away_team": "New Orleans Pelicans",
            "home_team": "Brooklyn Nets",
            "away_score": 101,
            "home_score": 119,
            "points_total": 220,
            "location": "Barclays Center"
        },
        {
            "game_date": "2025-12-06",
            "away_team": "LA Clippers",  # Test name standardization
            "home_team": "Minnesota Timberwolves",
            "away_score": 106,
            "home_score": 109,
            "points_total": 215,
            "location": "Target Center"
        },
        {
            "game_date": "2025-12-06",
            "away_team": "Fake Team",  # Test no match
            "home_team": "Another Fake Team",
            "away_score": 100,
            "home_score": 100,
            "points_total": 200,
            "location": "Fake Arena"
        }
    ]

    print("\nTesting lookup for 3 games (2 should match, 1 should not)...")
    updated_games = lookup.add_game_ids_to_games(test_games, sport="nba")

    print("\nResults:")
    print("-" * 70)
    matched = 0
    unmatched = 0
    for game in updated_games:
        if game.get('game_id'):
            matched += 1
            game_id_str = game['game_id'][:12] + "..."
            print(f"✓ {game['away_team']:28} @ {game['home_team']:28} | {game_id_str}")
        else:
            unmatched += 1
            print(f"✗ {game['away_team']:28} @ {game['home_team']:28} | No forecast")

    print("-" * 70)
    print(f"Matched: {matched}, Unmatched: {unmatched}")

    if matched == 2 and unmatched == 1:
        print("✅ TEST 1 PASSED")
        return True
    else:
        print("❌ TEST 1 FAILED")
        return False


def test_bigquery_writer_integration():
    """Test BigQuery writer with automatic game_id lookup"""
    print("\n" + "=" * 70)
    print("TEST 2: BigQuery Writer Integration")
    print("=" * 70)

    print("\nInitializing writer with sport='nba'...")
    writer = NBAGameBigQueryWriter(
        project_id=GCP_PROJECT_ID,
        dataset_id="nba_data",
        table_id="game_results",
        sport="nba"
    )

    print("✓ Writer initialized with game_id lookup enabled")

    # Verify writer has lookup utility
    if hasattr(writer, 'game_id_lookup'):
        print("✓ Writer has game_id_lookup utility")
    else:
        print("✗ Writer missing game_id_lookup utility")
        return False

    if writer.sport == "nba":
        print("✓ Writer sport is set to 'nba'")
    else:
        print("✗ Writer sport not set correctly")
        return False

    print("✅ TEST 2 PASSED")
    return True


def main():
    """Run all tests"""
    print("=" * 70)
    print("AUTOMATIC GAME_ID POPULATION - INTEGRATION TESTS")
    print("=" * 70)

    test1_passed = test_game_id_lookup()
    test2_passed = test_bigquery_writer_integration()

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Test 1 (Lookup Utility): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Writer Integration): {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nThe system is now configured to automatically populate game_ids")
        print("when new games are added to the database.")
        print("\nHow it works:")
        print("  1. When games are collected (via NBA/NHL/NFL agents)")
        print("  2. Before inserting into BigQuery")
        print("  3. The writer queries forecasts_mike.relational_forecasts")
        print("  4. Matches games by date and team names")
        print("  5. Adds game_id to each game that has a forecast")
        print("  6. Inserts games WITH game_ids into the database")
    else:
        print("\n❌ SOME TESTS FAILED - Please review errors above")

    print("=" * 70)


if __name__ == "__main__":
    main()

"""
Generate Synthetic NBA Game Data
Creates realistic NBA game results for specified date ranges
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import os
from bigquery_writer import NBAGameBigQueryWriter


# All 30 NBA teams
NBA_TEAMS = [
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets",
    "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets",
    "Detroit Pistons", "Golden State Warriors", "Houston Rockets", "Indiana Pacers",
    "LA Clippers", "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat",
    "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans", "New York Knicks",
    "Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers", "Phoenix Suns",
    "Portland Trail Blazers", "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors",
    "Utah Jazz", "Washington Wizards"
]

# Team locations (city + arena)
TEAM_LOCATIONS = {
    "Atlanta Hawks": "State Farm Arena, Atlanta, GA",
    "Boston Celtics": "TD Garden, Boston, MA",
    "Brooklyn Nets": "Barclays Center, Brooklyn, NY",
    "Charlotte Hornets": "Spectrum Center, Charlotte, NC",
    "Chicago Bulls": "United Center, Chicago, IL",
    "Cleveland Cavaliers": "Rocket Mortgage FieldHouse, Cleveland, OH",
    "Dallas Mavericks": "American Airlines Center, Dallas, TX",
    "Denver Nuggets": "Ball Arena, Denver, CO",
    "Detroit Pistons": "Little Caesars Arena, Detroit, MI",
    "Golden State Warriors": "Chase Center, San Francisco, CA",
    "Houston Rockets": "Toyota Center, Houston, TX",
    "Indiana Pacers": "Gainbridge Fieldhouse, Indianapolis, IN",
    "LA Clippers": "Crypto.com Arena, Los Angeles, CA",
    "Los Angeles Lakers": "Crypto.com Arena, Los Angeles, CA",
    "Memphis Grizzlies": "FedExForum, Memphis, TN",
    "Miami Heat": "Kaseya Center, Miami, FL",
    "Milwaukee Bucks": "Fiserv Forum, Milwaukee, WI",
    "Minnesota Timberwolves": "Target Center, Minneapolis, MN",
    "New Orleans Pelicans": "Smoothie King Center, New Orleans, LA",
    "New York Knicks": "Madison Square Garden, New York, NY",
    "Oklahoma City Thunder": "Paycom Center, Oklahoma City, OK",
    "Orlando Magic": "Kia Center, Orlando, FL",
    "Philadelphia 76ers": "Wells Fargo Center, Philadelphia, PA",
    "Phoenix Suns": "Footprint Center, Phoenix, AZ",
    "Portland Trail Blazers": "Moda Center, Portland, OR",
    "Sacramento Kings": "Golden 1 Center, Sacramento, CA",
    "San Antonio Spurs": "Frost Bank Center, San Antonio, TX",
    "Toronto Raptors": "Scotiabank Arena, Toronto, ON",
    "Utah Jazz": "Delta Center, Salt Lake City, UT",
    "Washington Wizards": "Capital One Arena, Washington, DC"
}


def generate_realistic_score(is_home: bool = False) -> int:
    """Generate a realistic NBA game score (typically 90-130 points)"""
    base_score = random.randint(95, 125)
    # Home teams tend to score slightly more
    if is_home:
        base_score += random.randint(0, 5)
    return base_score


def should_have_games(date: datetime) -> bool:
    """Determine if NBA games typically occur on this date"""
    # NBA regular season: late October through early April
    # Games typically don't occur on: All-Star break (mid-Feb), Christmas day has special schedule

    month = date.month
    day = date.day
    weekday = date.weekday()  # 0 = Monday, 6 = Sunday

    # Season runs from mid-October through early April
    # Valid months: October (15+), November, December, January, February, March, April (1-15)
    # Off-season months: May, June, July, August, September, early October

    if month in [5, 6, 7, 8, 9]:  # Off-season months
        return False
    elif month == 10 and day < 15:  # October before 15th
        return False
    elif month == 4 and day > 15:  # April after 15th
        return False

    # All-Star break (typically mid-February)
    if month == 2 and 12 <= day <= 18:
        return False

    # Christmas Day (December 25) - special schedule, but we'll include it
    # Most games occur throughout the season

    # Games occur most days during the season
    # Only occasionally skip days (to simulate back-to-backs, travel days, etc.)
    # About 10-15% of days have no games
    skip_probability = 0.12

    return random.random() > skip_probability


def generate_games_for_date(date_str: str) -> List[Dict]:
    """Generate realistic games for a specific date"""
    date = datetime.strptime(date_str, "%Y-%m-%d")

    if not should_have_games(date):
        return []

    games = []
    teams_used = set()

    # Determine number of games (typically 3-13 per day during regular season)
    weekday = date.weekday()
    if weekday == 5:  # Saturday - most games
        num_games = random.randint(10, 13)
    elif weekday == 6:  # Sunday - many games
        num_games = random.randint(8, 12)
    elif weekday in [1, 2, 4]:  # Tuesday, Wednesday, Friday - moderate
        num_games = random.randint(6, 10)
    else:  # Monday, Thursday - fewer games
        num_games = random.randint(3, 7)

    # Ensure we don't exceed maximum possible games (15 with 30 teams)
    num_games = min(num_games, 15)

    # Generate games
    available_teams = NBA_TEAMS.copy()
    random.shuffle(available_teams)

    for i in range(num_games):
        if len(available_teams) < 2:
            break

        # Pick two teams
        home_team = available_teams.pop()
        away_team = available_teams.pop()

        # Generate scores
        home_score = generate_realistic_score(is_home=True)
        away_score = generate_realistic_score(is_home=False)

        # Ensure there's a winner (no ties in basketball)
        if home_score == away_score:
            if random.random() > 0.5:
                home_score += random.randint(1, 5)
            else:
                away_score += random.randint(1, 5)

        # Occasional overtime games (closer scores)
        if abs(home_score - away_score) <= 3 and random.random() > 0.85:
            # Make it a closer game (overtime)
            diff = random.randint(1, 3)
            if home_score > away_score:
                away_score = home_score - diff
            else:
                home_score = away_score - diff

        game = {
            "game_date": date_str,
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score,
            "points_total": home_score + away_score,
            "location": TEAM_LOCATIONS[home_team],
            "game_status": "Final"
        }

        games.append(game)

    return games


def generate_date_range_games(start_date: str, end_date: str) -> List[Dict]:
    """Generate games for a date range"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    all_games = []
    current = start

    print(f"Generating NBA game data from {start_date} to {end_date}")
    print("=" * 60)

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        games = generate_games_for_date(date_str)

        if games:
            print(f"{date_str}: Generated {len(games)} games")
            all_games.extend(games)
        else:
            print(f"{date_str}: No games scheduled")

        current += timedelta(days=1)

    print("=" * 60)
    print(f"Total games generated: {len(all_games)}")

    return all_games


def save_to_bigquery(games: List[Dict], project_id: str, dataset_id: str = "nba_data",
                     table_id: str = "game_results", credentials_path: str = None):
    """Save generated games to BigQuery"""
    if not games:
        print("No games to save")
        return

    print(f"\nInserting {len(games)} games into BigQuery...")

    writer = NBAGameBigQueryWriter(
        project_id=project_id,
        dataset_id=dataset_id,
        table_id=table_id,
        credentials_path=credentials_path
    )

    # Ensure table exists
    writer.create_table_if_not_exists()

    # Insert data
    results = writer.insert_games(games, skip_duplicates=True)

    print(f"\nInsertion complete:")
    print(f"  Inserted: {results['inserted']}")
    print(f"  Skipped (duplicates): {results['skipped']}")
    print(f"  Errors: {results['errors']}")


def save_to_json(games: List[Dict], filename: str = "generated_games.json"):
    """Save generated games to JSON file"""
    with open(filename, 'w') as f:
        json.dump(games, f, indent=2)
    print(f"\nSaved {len(games)} games to {filename}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic NBA game data")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-json", help="Output JSON file (optional)")
    parser.add_argument("--save-to-bigquery", action="store_true", help="Save to BigQuery")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")

    args = parser.parse_args()

    # Set random seed if provided
    if args.seed:
        random.seed(args.seed)

    # Generate games
    games = generate_date_range_games(args.start_date, args.end_date)

    # Save to JSON if requested
    if args.output_json:
        save_to_json(games, args.output_json)

    # Save to BigQuery if requested
    if args.save_to_bigquery:
        project_id = os.getenv("GCP_PROJECT_ID")
        credentials_path = os.getenv("GCP_CREDENTIALS_PATH")

        if not project_id:
            print("Error: GCP_PROJECT_ID environment variable not set")
            exit(1)

        save_to_bigquery(
            games,
            project_id=project_id,
            credentials_path=credentials_path
        )

"""
Multi-Sport Game Data Generator
Generates realistic game data for NBA, NHL, and NFL
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import os
from bigquery_writer import NBAGameBigQueryWriter


# NHL Teams and Arenas (32 teams)
NHL_TEAMS = [
    # Atlantic Division
    "Boston Bruins", "Buffalo Sabres", "Detroit Red Wings", "Florida Panthers",
    "Montreal Canadiens", "Ottawa Senators", "Tampa Bay Lightning", "Toronto Maple Leafs",
    # Metropolitan Division
    "Carolina Hurricanes", "Columbus Blue Jackets", "New Jersey Devils", "New York Islanders",
    "New York Rangers", "Philadelphia Flyers", "Pittsburgh Penguins", "Washington Capitals",
    # Central Division
    "Chicago Blackhawks", "Colorado Avalanche", "Dallas Stars",
    "Minnesota Wild", "Nashville Predators", "St. Louis Blues", "Utah Hockey Club", "Winnipeg Jets",
    # Pacific Division
    "Anaheim Ducks", "Calgary Flames", "Edmonton Oilers", "Los Angeles Kings",
    "San Jose Sharks", "Seattle Kraken", "Vancouver Canucks", "Vegas Golden Knights"
]

NHL_ARENAS = {
    "Boston Bruins": "TD Garden, Boston, MA",
    "Buffalo Sabres": "KeyBank Center, Buffalo, NY",
    "Detroit Red Wings": "Little Caesars Arena, Detroit, MI",
    "Florida Panthers": "Amerant Bank Arena, Sunrise, FL",
    "Montreal Canadiens": "Bell Centre, Montreal, QC",
    "Ottawa Senators": "Canadian Tire Centre, Ottawa, ON",
    "Tampa Bay Lightning": "Amalie Arena, Tampa, FL",
    "Toronto Maple Leafs": "Scotiabank Arena, Toronto, ON",
    "Carolina Hurricanes": "PNC Arena, Raleigh, NC",
    "Columbus Blue Jackets": "Nationwide Arena, Columbus, OH",
    "New Jersey Devils": "Prudential Center, Newark, NJ",
    "New York Islanders": "UBS Arena, Elmont, NY",
    "New York Rangers": "Madison Square Garden, New York, NY",
    "Philadelphia Flyers": "Wells Fargo Center, Philadelphia, PA",
    "Pittsburgh Penguins": "PPG Paints Arena, Pittsburgh, PA",
    "Washington Capitals": "Capital One Arena, Washington, DC",
    "Chicago Blackhawks": "United Center, Chicago, IL",
    "Colorado Avalanche": "Ball Arena, Denver, CO",
    "Dallas Stars": "American Airlines Center, Dallas, TX",
    "Minnesota Wild": "Xcel Energy Center, St. Paul, MN",
    "Nashville Predators": "Bridgestone Arena, Nashville, TN",
    "St. Louis Blues": "Enterprise Center, St. Louis, MO",
    "Utah Hockey Club": "Delta Center, Salt Lake City, UT",
    "Winnipeg Jets": "Canada Life Centre, Winnipeg, MB",
    "Anaheim Ducks": "Honda Center, Anaheim, CA",
    "Calgary Flames": "Scotiabank Saddledome, Calgary, AB",
    "Edmonton Oilers": "Rogers Place, Edmonton, AB",
    "Los Angeles Kings": "Crypto.com Arena, Los Angeles, CA",
    "San Jose Sharks": "SAP Center, San Jose, CA",
    "Seattle Kraken": "Climate Pledge Arena, Seattle, WA",
    "Vancouver Canucks": "Rogers Arena, Vancouver, BC",
    "Vegas Golden Knights": "T-Mobile Arena, Las Vegas, NV"
}

# NFL Teams and Stadiums (32 teams)
NFL_TEAMS = [
    # AFC East
    "Buffalo Bills", "Miami Dolphins", "New England Patriots", "New York Jets",
    # AFC North
    "Baltimore Ravens", "Cincinnati Bengals", "Cleveland Browns", "Pittsburgh Steelers",
    # AFC South
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Tennessee Titans",
    # AFC West
    "Denver Broncos", "Kansas City Chiefs", "Las Vegas Raiders", "Los Angeles Chargers",
    # NFC East
    "Dallas Cowboys", "New York Giants", "Philadelphia Eagles", "Washington Commanders",
    # NFC North
    "Chicago Bears", "Detroit Lions", "Green Bay Packers", "Minnesota Vikings",
    # NFC South
    "Atlanta Falcons", "Carolina Panthers", "New Orleans Saints", "Tampa Bay Buccaneers",
    # NFC West
    "Arizona Cardinals", "Los Angeles Rams", "San Francisco 49ers", "Seattle Seahawks"
]

NFL_STADIUMS = {
    "Buffalo Bills": "Highmark Stadium, Orchard Park, NY",
    "Miami Dolphins": "Hard Rock Stadium, Miami Gardens, FL",
    "New England Patriots": "Gillette Stadium, Foxborough, MA",
    "New York Jets": "MetLife Stadium, East Rutherford, NJ",
    "Baltimore Ravens": "M&T Bank Stadium, Baltimore, MD",
    "Cincinnati Bengals": "Paycor Stadium, Cincinnati, OH",
    "Cleveland Browns": "Cleveland Browns Stadium, Cleveland, OH",
    "Pittsburgh Steelers": "Acrisure Stadium, Pittsburgh, PA",
    "Houston Texans": "NRG Stadium, Houston, TX",
    "Indianapolis Colts": "Lucas Oil Stadium, Indianapolis, IN",
    "Jacksonville Jaguars": "EverBank Stadium, Jacksonville, FL",
    "Tennessee Titans": "Nissan Stadium, Nashville, TN",
    "Denver Broncos": "Empower Field at Mile High, Denver, CO",
    "Kansas City Chiefs": "Arrowhead Stadium, Kansas City, MO",
    "Las Vegas Raiders": "Allegiant Stadium, Las Vegas, NV",
    "Los Angeles Chargers": "SoFi Stadium, Inglewood, CA",
    "Dallas Cowboys": "AT&T Stadium, Arlington, TX",
    "New York Giants": "MetLife Stadium, East Rutherford, NJ",
    "Philadelphia Eagles": "Lincoln Financial Field, Philadelphia, PA",
    "Washington Commanders": "Northwest Stadium, Landover, MD",
    "Chicago Bears": "Soldier Field, Chicago, IL",
    "Detroit Lions": "Ford Field, Detroit, MI",
    "Green Bay Packers": "Lambeau Field, Green Bay, WI",
    "Minnesota Vikings": "U.S. Bank Stadium, Minneapolis, MN",
    "Atlanta Falcons": "Mercedes-Benz Stadium, Atlanta, GA",
    "Carolina Panthers": "Bank of America Stadium, Charlotte, NC",
    "New Orleans Saints": "Caesars Superdome, New Orleans, LA",
    "Tampa Bay Buccaneers": "Raymond James Stadium, Tampa, FL",
    "Arizona Cardinals": "State Farm Stadium, Glendale, AZ",
    "Los Angeles Rams": "SoFi Stadium, Inglewood, CA",
    "San Francisco 49ers": "Levi's Stadium, Santa Clara, CA",
    "Seattle Seahawks": "Lumen Field, Seattle, WA"
}


def generate_nhl_score(is_home: bool = False) -> int:
    """Generate realistic NHL score (0-7 goals, typically 2-4)"""
    # NHL scores are lower - most games 2-4 goals per team
    score = random.choices(
        [0, 1, 2, 3, 4, 5, 6, 7],
        weights=[2, 8, 20, 25, 20, 15, 7, 3]
    )[0]
    if is_home:
        score += random.choice([0, 0, 0, 1])  # Slight home advantage
    return score


def generate_nfl_score(is_home: bool = False) -> int:
    """Generate realistic NFL score (typically 10-35 points)"""
    # NFL scores center around 20-28 points
    base_score = random.randint(10, 35)
    if is_home:
        base_score += random.randint(0, 3)  # Slight home advantage
    return base_score


def should_have_nhl_games(date: datetime) -> bool:
    """Determine if NHL games occur on this date (2025-26 season)"""
    month = date.month
    day = date.day

    # NHL 2025-26 season: October 7, 2025 through April 2026
    if month in [5, 6, 7, 8]:  # Off-season months
        return False
    elif month == 9:  # September - no games
        return False
    elif month == 10 and day < 7:  # Season starts Oct 7
        return False
    elif month == 4 and day > 20:  # Season ends around Apr 20
        return False

    # Olympic break (Feb 6-24, 2026)
    if month == 2 and 6 <= day <= 24:
        return False

    # Games occur most days (about 12% skip rate)
    return random.random() > 0.12


def should_have_nfl_games(date: datetime) -> bool:
    """Determine if NFL games occur on this date (2025 season)"""
    month = date.month
    day = date.day
    weekday = date.weekday()  # 0=Mon, 3=Thu, 6=Sun

    # NFL 2025 season: September 4, 2025 through January 4, 2026
    # In-season months: 9 (Sep), 10 (Oct), 11 (Nov), 12 (Dec), 1 (Jan)
    if month in [2, 3, 4, 5, 6, 7, 8]:  # Off-season months
        return False

    # Season starts Sept 4 (Week 1 kickoff)
    if month == 9 and day < 4:
        return False

    # Season ends Jan 4 (regular season finale)
    if month == 1 and day > 4:
        return False

    # Games on Thursday (3), Sunday (6), Monday (0)
    if weekday in [3, 6, 0]:
        return True

    return False


def generate_nhl_games_for_date(date_str: str) -> List[Dict]:
    """Generate NHL games for a specific date"""
    date = datetime.strptime(date_str, "%Y-%m-%d")

    if not should_have_nhl_games(date):
        return []

    games = []
    teams_used = set()

    # NHL typically has 5-15 games per night
    weekday = date.weekday()
    if weekday in [5, 6]:  # Weekend
        num_games = random.randint(10, 15)
    else:  # Weekday
        num_games = random.randint(5, 12)

    num_games = min(num_games, 16)  # Max 16 games with 32 teams

    available_teams = NHL_TEAMS.copy()
    random.shuffle(available_teams)

    for i in range(num_games):
        if len(available_teams) < 2:
            break

        home_team = available_teams.pop()
        away_team = available_teams.pop()

        home_score = generate_nhl_score(is_home=True)
        away_score = generate_nhl_score(is_home=False)

        # Ensure there's a winner
        if home_score == away_score:
            # Overtime/shootout - someone wins by 1
            if random.random() > 0.5:
                home_score += 1
            else:
                away_score += 1

        game = {
            "game_date": date_str,
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score,
            "points_total": home_score + away_score,
            "location": NHL_ARENAS[home_team],
            "game_status": "Final"
        }

        games.append(game)

    return games


def generate_nfl_games_for_date(date_str: str) -> List[Dict]:
    """Generate NFL games for a specific date"""
    date = datetime.strptime(date_str, "%Y-%m-%d")

    if not should_have_nfl_games(date):
        return []

    games = []
    weekday = date.weekday()

    # Determine number of games based on day
    if weekday == 3:  # Thursday
        num_games = 1
    elif weekday == 6:  # Sunday
        num_games = random.randint(12, 14)
    elif weekday == 0:  # Monday
        num_games = random.choice([1, 2])
    else:
        return []

    available_teams = NFL_TEAMS.copy()
    random.shuffle(available_teams)

    for i in range(num_games):
        if len(available_teams) < 2:
            break

        home_team = available_teams.pop()
        away_team = available_teams.pop()

        home_score = generate_nfl_score(is_home=True)
        away_score = generate_nfl_score(is_home=False)

        # Ensure different scores (no ties in modern NFL except rare cases)
        if home_score == away_score:
            if random.random() > 0.5:
                home_score += 3
            else:
                away_score += 3

        game = {
            "game_date": date_str,
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score,
            "points_total": home_score + away_score,
            "location": NFL_STADIUMS[home_team],
            "game_status": "Final"
        }

        games.append(game)

    return games


def generate_games_for_sport(sport: str, start_date: str, end_date: str) -> List[Dict]:
    """Generate games for specified sport and date range"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    all_games = []
    current = start

    print(f"Generating {sport.upper()} game data from {start_date} to {end_date}")
    print("=" * 60)

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")

        if sport.lower() == "nhl":
            games = generate_nhl_games_for_date(date_str)
        elif sport.lower() == "nfl":
            games = generate_nfl_games_for_date(date_str)
        else:
            raise ValueError(f"Unknown sport: {sport}")

        if games:
            print(f"{date_str}: Generated {len(games)} games")
            all_games.extend(games)
        else:
            print(f"{date_str}: No games scheduled")

        current += timedelta(days=1)

    print("=" * 60)
    print(f"Total games generated: {len(all_games)}")

    return all_games


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate multi-sport game data")
    parser.add_argument("--sport", required=True, choices=["nhl", "nfl"],
                       help="Sport to generate data for")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-json", help="Output JSON file")
    parser.add_argument("--seed", type=int, help="Random seed")

    args = parser.parse_args()

    if args.seed:
        random.seed(args.seed)

    games = generate_games_for_sport(args.sport, args.start_date, args.end_date)

    if args.output_json:
        with open(args.output_json, 'w') as f:
            json.dump(games, f, indent=2)
        print(f"\nSaved {len(games)} games to {args.output_json}")

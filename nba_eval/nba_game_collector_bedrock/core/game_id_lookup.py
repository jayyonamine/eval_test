"""
Game ID Lookup Utility

Fetches game_ids from forecasts_mike.relational_forecasts table
to automatically populate game_id field when inserting new games.
"""

from google.cloud import bigquery
from typing import List, Dict, Optional
import os


class GameIdLookup:
    """Utility class to fetch game_ids from forecasts table"""

    def __init__(self, project_id: str = None):
        """
        Initialize the lookup utility

        Args:
            project_id: GCP project ID (defaults to env var GCP_PROJECT_ID)
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "tenki-476718")
        self.client = bigquery.Client(project=self.project_id)

    def standardize_team_name(self, team_name: str) -> str:
        """
        Standardize team names to handle variations

        Args:
            team_name: Original team name

        Returns:
            Standardized team name
        """
        # Handle LA Clippers / Los Angeles Clippers variation
        if team_name in ("LA Clippers", "Los Angeles Clippers"):
            return "Los Angeles Clippers"
        return team_name

    def fetch_game_ids_for_date(self, game_date: str, sport: str = "nba") -> Dict[str, str]:
        """
        Fetch all available game_ids for a specific date from forecasts table

        Args:
            game_date: Game date in YYYY-MM-DD format
            sport: Sport type (currently only NBA forecasts available)

        Returns:
            Dictionary mapping (away_team, home_team) tuple to game_id
        """
        # Currently only NBA has forecasts
        if sport.lower() != "nba":
            return {}

        query = f"""
        SELECT DISTINCT
            game_id,
            PARSE_DATE('%y%b%d',
                REGEXP_EXTRACT(kalshi_event_ticker, r'-(\\d{{2}}[A-Z]{{3}}\\d{{2}})')) as game_date,
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
        FROM `{self.project_id}.forecasts_mike.relational_forecasts`
        WHERE PARSE_DATE('%y%b%d',
                REGEXP_EXTRACT(kalshi_event_ticker, r'-(\\d{{2}}[A-Z]{{3}}\\d{{2}})')
            ) = '{game_date}'
        """

        try:
            result = self.client.query(query).result()
            game_id_map = {}

            for row in result:
                # Create key from standardized team names
                key = (row.away_team_std, row.home_team_std)
                game_id_map[key] = row.game_id

            return game_id_map
        except Exception as e:
            print(f"Warning: Could not fetch game_ids from forecasts table: {e}")
            return {}

    def add_game_ids_to_games(self, games_data: List[Dict], sport: str = "nba") -> List[Dict]:
        """
        Add game_ids to a list of games by matching with forecasts table

        Args:
            games_data: List of game dictionaries (must have game_date, away_team, home_team)
            sport: Sport type (nba, nhl, nfl)

        Returns:
            Updated list of game dictionaries with game_id field added where available
        """
        if not games_data:
            return games_data

        # Group games by date for efficient querying
        games_by_date = {}
        for game in games_data:
            game_date = game.get('game_date')
            if game_date:
                if game_date not in games_by_date:
                    games_by_date[game_date] = []
                games_by_date[game_date].append(game)

        # Fetch game_ids for each date
        total_matched = 0
        total_unmatched = 0

        for game_date, games in games_by_date.items():
            # Get game_id mapping for this date
            game_id_map = self.fetch_game_ids_for_date(game_date, sport)

            if not game_id_map:
                # No forecasts available for this date
                for game in games:
                    game['game_id'] = None
                total_unmatched += len(games)
                continue

            # Match games with forecasts
            for game in games:
                away_team = self.standardize_team_name(game.get('away_team', ''))
                home_team = self.standardize_team_name(game.get('home_team', ''))
                key = (away_team, home_team)

                if key in game_id_map:
                    game['game_id'] = game_id_map[key]
                    total_matched += 1
                else:
                    game['game_id'] = None
                    total_unmatched += 1

        if total_matched > 0 or total_unmatched > 0:
            print(f"\nGame ID Lookup Results:")
            print(f"  Matched with forecasts: {total_matched}")
            print(f"  No forecast available: {total_unmatched}")

        return games_data

    def lookup_single_game(self, game_date: str, away_team: str, home_team: str,
                          sport: str = "nba") -> Optional[str]:
        """
        Look up game_id for a single game

        Args:
            game_date: Game date in YYYY-MM-DD format
            away_team: Away team name
            home_team: Home team name
            sport: Sport type (nba, nhl, nfl)

        Returns:
            game_id if found, None otherwise
        """
        game_id_map = self.fetch_game_ids_for_date(game_date, sport)

        away_team_std = self.standardize_team_name(away_team)
        home_team_std = self.standardize_team_name(home_team)
        key = (away_team_std, home_team_std)

        return game_id_map.get(key)


# Convenience function for easy import
def add_game_ids(games_data: List[Dict], sport: str = "nba",
                 project_id: str = None) -> List[Dict]:
    """
    Convenience function to add game_ids to games data

    Args:
        games_data: List of game dictionaries
        sport: Sport type (nba, nhl, nfl)
        project_id: GCP project ID (optional)

    Returns:
        Updated games data with game_ids
    """
    lookup = GameIdLookup(project_id=project_id)
    return lookup.add_game_ids_to_games(games_data, sport=sport)


if __name__ == "__main__":
    # Test the lookup
    lookup = GameIdLookup()

    # Test with Dec 5, 2025 games
    test_games = [
        {
            "game_date": "2025-12-05",
            "away_team": "Denver Nuggets",
            "home_team": "Atlanta Hawks",
            "away_score": 134,
            "home_score": 133
        },
        {
            "game_date": "2025-12-05",
            "away_team": "LA Clippers",  # Test name standardization
            "home_team": "Memphis Grizzlies",
            "away_score": 98,
            "home_score": 107
        }
    ]

    print("Testing game_id lookup...")
    updated_games = lookup.add_game_ids_to_games(test_games, sport="nba")

    print("\nResults:")
    for game in updated_games:
        game_id_str = game['game_id'][:12] + "..." if game['game_id'] else "No forecast"
        print(f"  {game['away_team']:25} @ {game['home_team']:25} | {game_id_str}")

"""
NBA Game Data to BigQuery Pipeline
Handles writing structured NBA game data to Google BigQuery
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import json
from datetime import datetime, timedelta
from typing import List, Dict
import os
from game_id_lookup import GameIdLookup


class NBAGameBigQueryWriter:
    """Writes NBA game data to BigQuery with proper schema validation"""
    
    def __init__(self, project_id: str, dataset_id: str, table_id: str,
                 credentials_path: str = None, sport: str = "nba"):
        """
        Initialize BigQuery client and table reference

        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset name
            table_id: BigQuery table name
            credentials_path: Path to service account JSON (optional if using default credentials)
            sport: Sport type for game_id lookup (nba, nhl, nfl)
        """
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/bigquery"]
            )
            self.client = bigquery.Client(credentials=credentials, project=project_id)
        else:
            self.client = bigquery.Client(project=project_id)

        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.sport = sport

        # Initialize game_id lookup utility
        self.game_id_lookup = GameIdLookup(project_id=project_id)
    
    def create_table_if_not_exists(self):
        """Create the NBA games table with proper schema if it doesn't exist"""
        schema = [
            bigquery.SchemaField("game_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("home_team", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("away_team", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("home_score", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("away_score", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("points_total", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("location", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("inserted_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("game_id", "STRING", mode="NULLABLE"),  # Populated from forecasts table
        ]
        
        table = bigquery.Table(self.table_ref, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="game_date"
        )
        
        try:
            self.client.get_table(self.table_ref)
            print(f"Table {self.table_ref} already exists")
        except Exception:
            table = self.client.create_table(table)
            print(f"Created table {self.table_ref}")
    
    def validate_game_data(self, game: Dict) -> bool:
        """Validate that game data has all required fields and correct types"""
        required_fields = ["game_date", "home_team", "away_team",
                          "home_score", "away_score", "points_total", "location"]
        
        for field in required_fields:
            if field not in game:
                print(f"Missing required field: {field}")
                return False
        
        # Validate date format
        try:
            datetime.strptime(game["game_date"], "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date format: {game['game_date']}")
            return False
        
        # Validate scores are integers
        if not isinstance(game["home_score"], int) or not isinstance(game["away_score"], int):
            print(f"Scores must be integers")
            return False

        # Validate points_total is an integer
        if not isinstance(game["points_total"], int):
            print(f"points_total must be an integer")
            return False
        
        return True
    
    def check_duplicate(self, game_date: str, home_team: str, away_team: str) -> bool:
        """Check if a game already exists in the table"""
        query = f"""
        SELECT COUNT(*) as count
        FROM `{self.table_ref}`
        WHERE game_date = @game_date
          AND home_team = @home_team
          AND away_team = @away_team
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("game_date", "DATE", game_date),
                bigquery.ScalarQueryParameter("home_team", "STRING", home_team),
                bigquery.ScalarQueryParameter("away_team", "STRING", away_team),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        return results[0].count > 0
    
    def insert_games(self, games_data: List[Dict], skip_duplicates: bool = True) -> Dict:
        """
        Insert NBA game data into BigQuery

        Args:
            games_data: List of game dictionaries
            skip_duplicates: If True, skip games that already exist

        Returns:
            Dictionary with insertion statistics
        """
        if not games_data:
            return {"inserted": 0, "skipped": 0, "errors": 0}

        # Add game_ids from forecasts table before insertion
        print(f"\nLooking up game_ids from forecasts table...")
        games_data = self.game_id_lookup.add_game_ids_to_games(games_data, sport=self.sport)

        inserted = 0
        skipped = 0
        errors = 0

        rows_to_insert = []
        
        for game in games_data:
            # Validate data
            if not self.validate_game_data(game):
                print(f"Invalid game data: {game}")
                errors += 1
                continue
            
            # Check for duplicates
            if skip_duplicates:
                if self.check_duplicate(game["game_date"], game["home_team"], game["away_team"]):
                    print(f"Skipping duplicate: {game['home_team']} vs {game['away_team']} on {game['game_date']}")
                    skipped += 1
                    continue
            
            # Prepare row for insertion
            row = {
                "game_date": game["game_date"],
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "home_score": game["home_score"],
                "away_score": game["away_score"],
                "points_total": game["points_total"],
                "location": game["location"],
                "inserted_at": datetime.utcnow().isoformat(),
                "game_id": game.get("game_id")  # May be None if no forecast available
            }
            rows_to_insert.append(row)
        
        # Insert rows
        if rows_to_insert:
            errors_result = self.client.insert_rows_json(self.table_ref, rows_to_insert)
            
            if errors_result:
                print(f"Errors inserting rows: {errors_result}")
                errors += len(errors_result)
            else:
                inserted = len(rows_to_insert)
                print(f"Successfully inserted {inserted} rows")
        
        return {
            "inserted": inserted,
            "skipped": skipped,
            "errors": errors
        }
    
    def get_games_by_date(self, game_date: str) -> List[Dict]:
        """Retrieve all games for a specific date"""
        query = f"""
        SELECT game_date, home_team, away_team, home_score, away_score, location
        FROM `{self.table_ref}`
        WHERE game_date = @game_date
        ORDER BY home_team
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("game_date", "DATE", game_date),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        
        results = []
        for row in query_job.result():
            results.append({
                "game_date": row.game_date.isoformat(),
                "home_team": row.home_team,
                "away_team": row.away_team,
                "home_score": row.home_score,
                "away_score": row.away_score,
                "location": row.location
            })
        
        return results


def main():
    """Example usage"""
    # Configuration
    PROJECT_ID = "your-gcp-project-id"
    DATASET_ID = "nba_data"
    TABLE_ID = "game_results"
    CREDENTIALS_PATH = "path/to/service-account-key.json"  # Optional
    
    # Initialize writer
    writer = NBAGameBigQueryWriter(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        table_id=TABLE_ID,
        credentials_path=CREDENTIALS_PATH
    )
    
    # Create table if needed
    writer.create_table_if_not_exists()
    
    # Example game data (this would come from your AI agent)
    games_data = [
        {
            "game_date": "2024-12-02",
            "home_team": "Los Angeles Lakers",
            "away_team": "Boston Celtics",
            "home_score": 115,
            "away_score": 110,
            "location": "Crypto.com Arena, Los Angeles, CA"
        }
    ]
    
    # Insert data
    results = writer.insert_games(games_data)
    print(f"Insertion results: {results}")
    
    # Query data
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    games = writer.get_games_by_date(yesterday)
    print(f"Games from {yesterday}: {json.dumps(games, indent=2)}")


if __name__ == "__main__":
    main()

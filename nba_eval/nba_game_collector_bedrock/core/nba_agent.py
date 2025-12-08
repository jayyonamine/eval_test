"""
NBA Game Data Collection Agent
Uses Claude AI via Amazon Bedrock with custom skill to collect and structure game data
"""

import boto3
import json
import requests
from datetime import datetime, timedelta
from bigquery_writer import NBAGameBigQueryWriter
import os


class NBAGameCollectionAgent:
    """AI agent that collects NBA game data using Claude via Amazon Bedrock"""
    
    def __init__(self, aws_region: str, skill_path: str, aws_access_key: str = None, 
                 aws_secret_key: str = None, model_id: str = None):
        """
        Initialize the agent with Amazon Bedrock
        
        Args:
            aws_region: AWS region (e.g., 'us-east-1', 'us-west-2')
            skill_path: Path to the NBA game collection skill file
            aws_access_key: AWS access key (optional, uses default credentials if not provided)
            aws_secret_key: AWS secret key (optional, uses default credentials if not provided)
            model_id: Bedrock model ID (defaults to Claude Sonnet 4)
        """
        # Initialize Bedrock client
        if aws_access_key and aws_secret_key:
            self.client = boto3.client(
                service_name='bedrock-runtime',
                region_name=aws_region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
        else:
            # Use default AWS credentials (from environment, ~/.aws/credentials, or IAM role)
            self.client = boto3.client(
                service_name='bedrock-runtime',
                region_name=aws_region
            )
        
        # Default to Claude Sonnet 4 if not specified
        self.model_id = model_id or "anthropic.claude-sonnet-4-20250514-v1:0"
        self.skill_content = self._load_skill(skill_path)
    
    def _load_skill(self, skill_path: str) -> str:
        """Load the skill file content"""
        with open(skill_path, 'r') as f:
            return f.read()

    def _fetch_nba_games_api(self, target_date: str) -> dict:
        """Fetch NBA games from ESPN API for a specific date"""
        # ESPN API format: YYYYMMDD
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        date_param = date_obj.strftime("%Y%m%d")

        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_param}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching ESPN NBA API: {e}")
            return None

    def collect_games(self, target_date: str = None) -> list:
        """
        Collect game data for a specific date using Claude via Bedrock

        Args:
            target_date: Date to collect games for (YYYY-MM-DD format)
                        If None, uses yesterday's date

        Returns:
            List of game dictionaries
        """
        if target_date is None:
            yesterday = datetime.now() - timedelta(days=1)
            target_date = yesterday.strftime("%Y-%m-%d")

        # Fetch NBA game data from ESPN API
        print(f"Fetching NBA scores from ESPN API for {target_date}")
        api_data = self._fetch_nba_games_api(target_date)

        if not api_data:
            print("Failed to fetch ESPN NBA API data")
            return []

        # Extract compact game data to avoid API response truncation
        events = api_data.get('events', [])
        compact_games = []
        for event in events:
            try:
                status = event['status']['type']['state']
                comps = event['competitions'][0]
                home_team = [t for t in comps['competitors'] if t['homeAway'] == 'home'][0]
                away_team = [t for t in comps['competitors'] if t['homeAway'] == 'away'][0]

                compact_game = {
                    'status': status,
                    'home_team_name': home_team['team']['displayName'],
                    'away_team_name': away_team['team']['displayName'],
                    'home_score': int(home_team['score']),
                    'away_score': int(away_team['score']),
                    'venue': comps.get('venue', {}).get('fullName', 'Unknown Venue')
                }
                compact_games.append(compact_game)
            except Exception as e:
                print(f"Error parsing game: {e}")
                continue

        # Construct the prompt with skill instructions and compact game data
        prompt = f"""I have fetched NBA game data from ESPN API for {target_date}. Please extract ALL NBA games from the JSON data below.

Compact NBA Game Data:
{json.dumps(compact_games, indent=2)}

Using the NBA Game Data Collection Skill guidelines below, convert the API data into the required format.

{self.skill_content}

Convert the API data above into the exact JSON format specified in the skill.

CRITICAL REQUIREMENTS:
- Return ONLY valid JSON array, no other text
- Extract ALL games from the array, not just the first one
- Use the exact field names specified in the skill: game_date, home_team, away_team, home_score, away_score, points_total, location
- Calculate points_total as home_score + away_score (this field is MANDATORY)
- Use home_team_name for home_team and away_team_name for away_team from the data
- Use venue for location
- Only include games with status == "post" (completed/final games)
- game_date should always be "{target_date}"
- If no completed games are found, return an empty array: []

Example output format:
[
  {{
    "game_date": "2025-12-05",
    "home_team": "Boston Celtics",
    "away_team": "Los Angeles Lakers",
    "home_score": 126,
    "away_score": 105,
    "points_total": 231,
    "location": "TD Garden, Boston, MA"
  }}
]

Respond with only the JSON array."""

        # Prepare request body for Bedrock
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 8000,  # Increased to handle multiple games
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        # Call Claude via Bedrock
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            response_text = response_body['content'][0]['text'].strip()
            
        except Exception as e:
            print(f"Error calling Bedrock: {e}")
            return []
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()
        
        try:
            games_data = json.loads(response_text)
            print(f"Successfully collected {len(games_data)} games for {target_date}")
            return games_data
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response was: {response_text}")
            return []
    
    def verify_game_data(self, games_data: list) -> bool:
        """
        Verify collected game data meets quality standards
        
        Args:
            games_data: List of game dictionaries
            
        Returns:
            True if data is valid, False otherwise
        """
        required_fields = ["game_date", "home_team", "away_team", 
                          "home_score", "away_score", "location"]
        
        for game in games_data:
            for field in required_fields:
                if field not in game:
                    print(f"Missing field {field} in game: {game}")
                    return False
            
            # Check score types
            if not isinstance(game["home_score"], int) or not isinstance(game["away_score"], int):
                print(f"Invalid score types in game: {game}")
                return False
        
        return True


def run_daily_collection(
    aws_region: str,
    gcp_project_id: str,
    dataset_id: str,
    table_id: str,
    credentials_path: str = None,
    target_date: str = None,
    aws_access_key: str = None,
    aws_secret_key: str = None,
    model_id: str = None
):
    """
    Run the complete daily collection and insertion pipeline
    
    Args:
        aws_region: AWS region for Bedrock (e.g., 'us-east-1', 'us-west-2')
        gcp_project_id: GCP project ID
        dataset_id: BigQuery dataset name
        table_id: BigQuery table name
        credentials_path: Path to GCP service account key (optional)
        target_date: Date to collect (YYYY-MM-DD), defaults to yesterday
        aws_access_key: AWS access key (optional, uses default credentials if not provided)
        aws_secret_key: AWS secret key (optional, uses default credentials if not provided)
        model_id: Bedrock model ID (optional, defaults to Claude Sonnet 4)
    """
    print(f"Starting NBA game collection for {target_date or 'yesterday'}...")

    # Initialize agent
    # Use path relative to this script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_path = os.path.join(script_dir, "nba_game_collector_skill.md")
    agent = NBAGameCollectionAgent(
        aws_region=aws_region,
        skill_path=skill_path,
        aws_access_key=aws_access_key,
        aws_secret_key=aws_secret_key,
        model_id=model_id
    )
    
    # Collect game data
    games_data = agent.collect_games(target_date)
    
    if not games_data:
        print("No games found for the specified date")
        return
    
    # Verify data quality
    if not agent.verify_game_data(games_data):
        print("Data validation failed!")
        return
    
    print(f"Collected data for {len(games_data)} games:")
    for game in games_data:
        print(f"  {game['away_team']} @ {game['home_team']}: {game['away_score']}-{game['home_score']}")
    
    # Initialize BigQuery writer
    writer = NBAGameBigQueryWriter(
        project_id=gcp_project_id,
        dataset_id=dataset_id,
        table_id=table_id,
        credentials_path=credentials_path,
        sport="nba"  # Enable automatic game_id lookup from forecasts
    )
    
    # Ensure table exists
    writer.create_table_if_not_exists()
    
    # Insert data
    results = writer.insert_games(games_data, skip_duplicates=True)
    
    print(f"\nInsertion complete:")
    print(f"  Inserted: {results['inserted']}")
    print(f"  Skipped (duplicates): {results['skipped']}")
    print(f"  Errors: {results['errors']}")

    # Automatically populate actual results in forecasts table
    if results['inserted'] > 0:
        print(f"\nPopulating actual results in forecasts table...")
        try:
            from populate_actual_results_auto import populate_actual_results_silent
            from google.cloud import bigquery

            forecast_client = bigquery.Client(project=gcp_project_id)
            updated_count = populate_actual_results_silent(forecast_client)

            if updated_count > 0:
                print(f"✓ Populated actual results for {updated_count} forecast rows")
            else:
                print(f"  No forecast rows needed updating")
        except Exception as e:
            print(f"  Note: Could not populate actual results in forecasts: {e}")
            print(f"  (This is normal if forecasts don't exist for this game)")


if __name__ == "__main__":
    # Load configuration from environment variables
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")  # Optional
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")  # Optional
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID")  # Optional
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCP_CREDENTIALS_PATH = os.getenv("GCP_CREDENTIALS_PATH")

    # BigQuery configuration
    DATASET_ID = "nba_data"
    TABLE_ID = "game_results"

    # Run the collection
    run_daily_collection(
        aws_region=AWS_REGION,
        gcp_project_id=GCP_PROJECT_ID,
        dataset_id=DATASET_ID,
        table_id=TABLE_ID,
        credentials_path=GCP_CREDENTIALS_PATH,
        aws_access_key=AWS_ACCESS_KEY,
        aws_secret_key=AWS_SECRET_KEY,
        model_id=BEDROCK_MODEL_ID
    )

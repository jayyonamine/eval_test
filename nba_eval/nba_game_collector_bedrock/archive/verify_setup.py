"""
System Verification Script
Tests all components of the NBA data collection system
"""

import os
import sys
from datetime import datetime, timedelta
import json


def check_environment_variables():
    """Verify all required environment variables are set"""
    print("=" * 60)
    print("Checking Environment Variables...")
    print("=" * 60)
    
    required_vars = {
        "AWS_REGION": "AWS Region for Bedrock",
        "GCP_PROJECT_ID": "GCP Project ID",
    }
    
    optional_vars = {
        "AWS_ACCESS_KEY_ID": "AWS Access Key (uses default credentials if not set)",
        "AWS_SECRET_ACCESS_KEY": "AWS Secret Key (uses default credentials if not set)",
        "GCP_CREDENTIALS_PATH": "GCP Service Account Key Path",
        "DATASET_ID": "BigQuery Dataset ID",
        "TABLE_ID": "BigQuery Table ID",
    }
    
    all_good = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✓ {var}: {masked_value}")
        else:
            print(f"✗ {var}: NOT SET ({description})")
            all_good = False
    
    print("\nOptional variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {value}")
        else:
            print(f"- {var}: Not set (will use defaults)")
    
    return all_good


def test_bedrock_connection():
    """Test Amazon Bedrock connection"""
    print("\n" + "=" * 60)
    print("Testing Amazon Bedrock Connection...")
    print("=" * 60)
    
    try:
        import boto3
        
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if not aws_region:
            print("✗ No AWS region found")
            return False
        
        # Initialize Bedrock client
        if aws_access_key and aws_secret_key:
            client = boto3.client(
                service_name='bedrock-runtime',
                region_name=aws_region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
            print(f"✓ Using provided AWS credentials in region: {aws_region}")
        else:
            client = boto3.client(
                service_name='bedrock-runtime',
                region_name=aws_region
            )
            print(f"✓ Using default AWS credentials in region: {aws_region}")
        
        # Simple test message
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": "Respond with just the word 'SUCCESS' if you can read this."
                }
            ]
        }
        
        response = client.invoke_model(
            modelId="anthropic.claude-sonnet-4-20250514-v1:0",
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        result = response_body['content'][0]['text'].strip()
        
        if "SUCCESS" in result:
            print("✓ Bedrock connection successful")
            return True
        else:
            print(f"✗ Unexpected response: {result}")
            return False
            
    except Exception as e:
        print(f"✗ Error connecting to Bedrock: {e}")
        return False


def test_bigquery_connection():
    """Test BigQuery connection"""
    print("\n" + "=" * 60)
    print("Testing BigQuery Connection...")
    print("=" * 60)
    
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
        
        project_id = os.getenv("GCP_PROJECT_ID")
        credentials_path = os.getenv("GCP_CREDENTIALS_PATH")
        
        if not project_id:
            print("✗ No GCP project ID found")
            return False
        
        # Initialize client
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/bigquery"]
            )
            client = bigquery.Client(credentials=credentials, project=project_id)
            print(f"✓ Using service account from: {credentials_path}")
        else:
            client = bigquery.Client(project=project_id)
            print(f"✓ Using default credentials")
        
        # Test query
        query = "SELECT 1 as test"
        query_job = client.query(query)
        results = list(query_job.result())
        
        if results and results[0].test == 1:
            print("✓ BigQuery connection successful")
            return True
        else:
            print("✗ Unexpected query result")
            return False
            
    except Exception as e:
        print(f"✗ Error connecting to BigQuery: {e}")
        return False


def test_skill_file():
    """Verify skill file exists and is readable"""
    print("\n" + "=" * 60)
    print("Checking Skill File...")
    print("=" * 60)

    # Use path relative to this script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_path = os.path.join(script_dir, "nba_game_collector_skill.md")
    
    if os.path.exists(skill_path):
        with open(skill_path, 'r') as f:
            content = f.read()
            if len(content) > 100 and "NBA" in content:
                print(f"✓ Skill file found and valid ({len(content)} bytes)")
                return True
            else:
                print("✗ Skill file exists but appears invalid")
                return False
    else:
        print(f"✗ Skill file not found at: {skill_path}")
        return False


def test_agent_collection():
    """Test the full agent collection process with a known date"""
    print("\n" + "=" * 60)
    print("Testing Agent Collection (Dry Run)...")
    print("=" * 60)
    
    try:
        from nba_agent import NBAGameCollectionAgent
        
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        # Use path relative to this script's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        skill_path = os.path.join(script_dir, "nba_game_collector_skill.md")
        
        agent = NBAGameCollectionAgent(
            aws_region=aws_region,
            skill_path=skill_path,
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key
        )
        
        # Test with a known date that had games (Christmas 2023)
        test_date = "2023-12-25"
        print(f"Testing collection for {test_date} (known game date)...")
        
        games = agent.collect_games(test_date)
        
        if games and len(games) > 0:
            print(f"✓ Successfully collected {len(games)} games")
            print("\nSample game data:")
            print(json.dumps(games[0], indent=2))
            
            # Verify data structure
            if agent.verify_game_data(games):
                print("✓ Data validation passed")
                return True
            else:
                print("✗ Data validation failed")
                return False
        else:
            print("✗ No games collected (may be off-season or API issue)")
            return False
            
    except Exception as e:
        print(f"✗ Error during agent collection test: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all verification tests"""
    print("\n" + "=" * 60)
    print("NBA DATA COLLECTION SYSTEM - VERIFICATION")
    print("=" * 60)
    
    tests = [
        ("Environment Variables", check_environment_variables),
        ("Amazon Bedrock", test_bedrock_connection),
        ("BigQuery Connection", test_bigquery_connection),
        ("Skill File", test_skill_file),
        ("Agent Collection", test_agent_collection),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED - System is ready!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run: python nba_agent.py")
        print("2. Check BigQuery for data")
        print("3. Set up daily scheduling")
    else:
        print("✗ SOME TESTS FAILED - Please fix issues above")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("- Check your .env file configuration")
        print("- Verify API keys and permissions")
        print("- Review SETUP_GUIDE.md for detailed instructions")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

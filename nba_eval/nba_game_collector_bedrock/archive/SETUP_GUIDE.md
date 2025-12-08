# NBA Game Data Collection System - Setup Guide

## Overview
This system uses AI agents (Claude) with custom skills to collect NBA game data daily with 100% accuracy and consistent formatting, then writes it to Google BigQuery.

## Architecture

```
┌─────────────────┐
│   Scheduler     │  (Cloud Scheduler/Cron)
│   Daily Trigger │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   AI Agent      │
│   (Claude API)  │  Uses NBA Game Collection Skill
│   + Web Search  │  to find and structure data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Validation    │  Verify data quality and format
│   Layer         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   BigQuery      │  Store game results
│   Table         │
└─────────────────┘
```

## Prerequisites

1. **Anthropic API Access**
   - Sign up at https://console.anthropic.com
   - Generate an API key
   - Note: The API will use web search capabilities

2. **Google Cloud Platform Setup**
   - GCP project with billing enabled
   - BigQuery API enabled
   - Service account with BigQuery permissions

3. **Python Environment**
   - Python 3.8 or higher
   - pip for package management

## Step 1: GCP Setup

### Create BigQuery Dataset and Table

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Create dataset
bq mk --dataset --location=US nba_data

# The table will be created automatically by the script
# But you can create it manually if preferred:
bq mk --table \
  nba_data.game_results \
  game_date:DATE,home_team:STRING,away_team:STRING,home_score:INTEGER,away_score:INTEGER,location:STRING,inserted_at:TIMESTAMP
```

### Create Service Account

```bash
# Create service account
gcloud iam service-accounts create nba-data-collector \
    --description="NBA game data collection service account" \
    --display-name="NBA Data Collector"

# Grant BigQuery permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:nba-data-collector@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:nba-data-collector@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"

# Create and download key
gcloud iam service-accounts keys create ~/nba-collector-key.json \
    --iam-account=nba-data-collector@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## Step 2: Local Setup

### Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file:

```bash
# Anthropic API
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google Cloud
GCP_PROJECT_ID=your-gcp-project-id
GCP_CREDENTIALS_PATH=/path/to/nba-collector-key.json

# BigQuery (optional, uses defaults if not set)
DATASET_ID=nba_data
TABLE_ID=game_results
```

Or export them directly:

```bash
export ANTHROPIC_API_KEY="your_key_here"
export GCP_PROJECT_ID="your-project-id"
export GCP_CREDENTIALS_PATH="/path/to/key.json"
```

## Step 3: Test the System

### Manual Test Run

```bash
# Test collection for yesterday's games
python nba_agent.py

# Test collection for a specific date
python -c "
from nba_agent import run_daily_collection
import os

run_daily_collection(
    anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
    gcp_project_id=os.getenv('GCP_PROJECT_ID'),
    dataset_id='nba_data',
    table_id='game_results',
    credentials_path=os.getenv('GCP_CREDENTIALS_PATH'),
    target_date='2024-12-02'  # Specify date
)
"
```

### Verify Data in BigQuery

```bash
# Query the data
bq query --use_legacy_sql=false \
'SELECT * FROM `YOUR_PROJECT_ID.nba_data.game_results` 
 ORDER BY game_date DESC 
 LIMIT 10'
```

## Step 4: Production Deployment

### Option A: Google Cloud Run + Cloud Scheduler

1. **Create Cloud Run Service**

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY nba_agent.py .
COPY bigquery_writer.py .
COPY nba_game_collector_skill.md .

CMD ["python", "nba_agent.py"]
```

Deploy:

```bash
# Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/nba-collector

# Deploy to Cloud Run
gcloud run deploy nba-game-collector \
    --image gcr.io/YOUR_PROJECT_ID/nba-collector \
    --region us-central1 \
    --no-allow-unauthenticated \
    --service-account nba-data-collector@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars ANTHROPIC_API_KEY=your_key,GCP_PROJECT_ID=YOUR_PROJECT_ID
```

2. **Create Cloud Scheduler Job**

```bash
# Create a job that runs daily at 8 AM (after games finish)
gcloud scheduler jobs create http nba-daily-collection \
    --schedule="0 8 * * *" \
    --uri="https://YOUR_CLOUD_RUN_URL" \
    --http-method=POST \
    --oidc-service-account-email=nba-data-collector@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --location=us-central1 \
    --time-zone="America/New_York"
```

### Option B: Cloud Functions

Create `main.py`:

```python
import functions_framework
from nba_agent import run_daily_collection
import os

@functions_framework.http
def collect_nba_games(request):
    try:
        run_daily_collection(
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            gcp_project_id=os.getenv('GCP_PROJECT_ID'),
            dataset_id='nba_data',
            table_id='game_results'
        )
        return 'Collection completed successfully', 200
    except Exception as e:
        return f'Error: {str(e)}', 500
```

Deploy:

```bash
gcloud functions deploy nba-game-collector \
    --runtime python311 \
    --trigger-http \
    --entry-point collect_nba_games \
    --service-account nba-data-collector@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars ANTHROPIC_API_KEY=your_key,GCP_PROJECT_ID=YOUR_PROJECT_ID
```

### Option C: Traditional Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add daily job at 8 AM
0 8 * * * cd /path/to/project && /path/to/venv/bin/python nba_agent.py >> /path/to/logs/nba_collection.log 2>&1
```

## Step 5: Monitoring and Maintenance

### Query Recent Collections

```sql
-- Check recent insertions
SELECT 
    game_date,
    COUNT(*) as games_count,
    MAX(inserted_at) as last_inserted
FROM `YOUR_PROJECT_ID.nba_data.game_results`
GROUP BY game_date
ORDER BY game_date DESC
LIMIT 30;
```

### Check for Missing Dates

```sql
-- Find dates with no games (might indicate collection failure)
WITH date_range AS (
    SELECT DATE_SUB(CURRENT_DATE(), INTERVAL n DAY) as check_date
    FROM UNNEST(GENERATE_ARRAY(1, 30)) as n
)
SELECT 
    d.check_date,
    COUNT(g.game_date) as games_found
FROM date_range d
LEFT JOIN `YOUR_PROJECT_ID.nba_data.game_results` g
    ON d.check_date = g.game_date
GROUP BY d.check_date
HAVING games_found = 0
    AND EXTRACT(DAYOFWEEK FROM d.check_date) NOT IN (1, 7)  -- Exclude weekends
ORDER BY d.check_date DESC;
```

### Set Up Alerts

Create a Cloud Monitoring alert for failed collections:

```bash
gcloud alpha monitoring policies create \
    --notification-channels=YOUR_CHANNEL_ID \
    --display-name="NBA Collection Failure" \
    --condition-display-name="No data collected" \
    --condition-expression="..."
```

## How It Ensures 100% Accuracy

1. **AI Agent with Skill**: Claude uses the custom skill that defines exact output format and validation rules

2. **Web Search Verification**: Agent searches multiple sources and cross-references data

3. **Structured Output**: JSON schema ensures consistent field names and data types

4. **Validation Layer**: Python code validates all data before insertion

5. **Duplicate Detection**: BigQuery writer checks for existing records

6. **Audit Trail**: `inserted_at` timestamp tracks when data was added

## Customization Options

### Modify Collection Time

Edit the Cloud Scheduler cron expression:
- `0 8 * * *` = 8 AM daily
- `0 */6 * * *` = Every 6 hours
- `0 10 * * 2,4,6` = 10 AM on Tue, Thu, Sat

### Add More Fields

Edit `nba_game_collector_skill.md` to include additional fields like:
- `attendance`
- `game_duration`
- `officials`
- `winning_margin`

Update BigQuery schema accordingly.

### Change Data Source

Modify the skill to prefer specific sources:
- ESPN
- NBA.com
- Sports data APIs

## Troubleshooting

### API Key Issues
```bash
# Verify Anthropic API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}'
```

### BigQuery Permission Issues
```bash
# Test BigQuery access
bq query --use_legacy_sql=false 'SELECT 1'
```

### No Games Found
- Check if games actually occurred on that date
- Verify web search is working in Claude API
- Try running for a known game date

## Cost Estimation

- **Anthropic API**: ~$0.10-0.30 per day (depends on number of games)
- **BigQuery**: 
  - Storage: ~$0.02/GB/month (minimal for this data)
  - Queries: Free tier covers most use cases
- **Cloud Scheduler**: $0.10/month per job

**Total estimated cost: ~$5-15/month for full NBA season**

## Support and Resources

- Anthropic Documentation: https://docs.anthropic.com
- BigQuery Documentation: https://cloud.google.com/bigquery/docs
- NBA Schedule: Check for all-star break, playoffs, off-season

## Next Steps

1. Test the system with historical dates
2. Set up monitoring and alerts
3. Create dashboard/visualization layer
4. Add data quality checks
5. Consider adding player statistics, play-by-play data, etc.

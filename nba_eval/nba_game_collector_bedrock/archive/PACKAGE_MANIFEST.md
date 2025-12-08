# NBA Game Data Collection System - Complete Package

## 📦 Package Contents

This package contains everything you need to run the NBA game data collection system using Amazon Bedrock and Google BigQuery.

### Core Application Files

1. **nba_agent.py** (Main Application)
   - Orchestrates the data collection process
   - Uses Claude via Amazon Bedrock for AI-powered data extraction
   - Handles date parsing and collection scheduling
   - Validates and structures game data
   - **Usage**: `python nba_agent.py`

2. **bigquery_writer.py** (Database Integration)
   - Manages Google BigQuery connections
   - Creates tables with proper schema
   - Validates data before insertion
   - Handles duplicate detection
   - Provides query utilities

3. **nba_game_collector_skill.md** (AI Skill Definition)
   - Defines exact output format for Claude
   - Contains validation rules
   - Lists all 30 NBA teams with official names
   - Includes arena locations
   - Ensures 100% accuracy and consistency

4. **backfill_data.py** (Historical Data Utility)
   - Collects games for date ranges
   - Supports full season backfill
   - Includes rate limiting
   - **Usage**: 
     ```bash
     python backfill_data.py --mode range --start-date 2024-12-01 --end-date 2024-12-10
     python backfill_data.py --mode season --season 2024
     python backfill_data.py --mode week
     ```

5. **verify_setup.py** (System Verification)
   - Tests all components
   - Verifies AWS Bedrock connection
   - Tests BigQuery connectivity
   - Validates skill file
   - Runs end-to-end collection test
   - **Usage**: `python verify_setup.py`

### Configuration Files

6. **requirements.txt** (Python Dependencies)
   - boto3>=1.34.0 (AWS SDK)
   - google-cloud-bigquery>=3.25.0
   - google-auth>=2.34.0

7. **.env.template** (Configuration Template)
   - AWS credentials template
   - GCP configuration
   - Copy to `.env` and fill in your values
   - Never commit `.env` to version control!

8. **setup.sh** (Automated Setup Script)
   - Creates virtual environment
   - Installs dependencies
   - Creates configuration file
   - Checks prerequisites
   - **Usage**: `bash setup.sh`

### Documentation Files

9. **README_BEDROCK.md** (Quick Start Guide)
   - 10-minute quick start
   - Feature overview
   - Basic configuration
   - Common use cases

10. **BEDROCK_SETUP.md** (Detailed Bedrock Guide)
    - Complete AWS Bedrock setup
    - IAM configuration
    - Model access approval
    - Credential management
    - Security best practices
    - Troubleshooting guide

11. **SETUP_GUIDE.md** (Comprehensive Setup)
    - 60+ page detailed guide
    - All deployment options
    - Production configuration
    - Monitoring setup
    - Cost optimization
    - Advanced customization

12. **MIGRATION_SUMMARY.md** (Bedrock Migration)
    - Changes from Anthropic API
    - Code comparison
    - Quick migration steps
    - Troubleshooting

13. **IMPLEMENTATION_SUMMARY.md** (Architecture)
    - System design overview
    - How accuracy is ensured
    - Component descriptions
    - Data flow diagrams

## 🚀 Quick Start (5 Commands)

```bash
# 1. Extract package
unzip nba-game-collector-bedrock.zip
cd nba-game-collector-bedrock

# 2. Run setup
bash setup.sh

# 3. Configure credentials (edit with your values)
nano .env

# 4. Verify everything works
python verify_setup.py

# 5. Start collecting data
python nba_agent.py
```

## 📋 Prerequisites Checklist

Before running the system, ensure you have:

### AWS Requirements
- [ ] AWS account created
- [ ] Bedrock access enabled in your region
- [ ] Claude Sonnet 4 model access approved
- [ ] AWS credentials obtained (access key + secret key)
  - OR AWS CLI configured
  - OR IAM role attached (if on EC2/Lambda)

### GCP Requirements
- [ ] Google Cloud project created
- [ ] BigQuery API enabled
- [ ] Service account created with BigQuery permissions
- [ ] Service account key JSON downloaded

### Local Requirements
- [ ] Python 3.8 or higher installed
- [ ] pip package manager available
- [ ] Internet connection for API calls

## 🔧 Configuration Steps

### 1. AWS Bedrock Setup

```bash
# Option A: Use AWS CLI
aws configure
# Enter: Access Key, Secret Key, Region (us-east-1)

# Option B: Set environment variables
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
```

### 2. Enable Claude in Bedrock

1. Go to https://console.aws.amazon.com/bedrock/
2. Click **Model access** in left sidebar
3. Click **Modify model access**
4. Find **Anthropic Claude Sonnet 4** → Check the box
5. Click **Save changes**
6. Wait for approval (usually instant)

### 3. GCP BigQuery Setup

```bash
# Create service account
gcloud iam service-accounts create nba-collector \
    --display-name="NBA Data Collector"

# Grant BigQuery permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:nba-collector@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

# Create and download key
gcloud iam service-accounts keys create ~/nba-key.json \
    --iam-account=nba-collector@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 4. Environment Configuration

Edit `.env` file:
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key_here  # Optional if using AWS CLI
AWS_SECRET_ACCESS_KEY=your_secret_here  # Optional if using AWS CLI

# GCP Configuration
GCP_PROJECT_ID=your-gcp-project-id
GCP_CREDENTIALS_PATH=/path/to/nba-key.json

# BigQuery Configuration (optional)
DATASET_ID=nba_data
TABLE_ID=game_results
```

## 📊 Data Schema

The system creates a BigQuery table with this schema:

```sql
CREATE TABLE nba_data.game_results (
  game_date DATE NOT NULL,
  home_team STRING NOT NULL,
  away_team STRING NOT NULL,
  home_score INTEGER NOT NULL,
  away_score INTEGER NOT NULL,
  location STRING NOT NULL,
  inserted_at TIMESTAMP NOT NULL
)
PARTITION BY game_date;
```

## 🎯 Usage Examples

### Daily Collection (Yesterday's Games)
```bash
python nba_agent.py
```

### Specific Date
```python
from nba_agent import run_daily_collection
import os

run_daily_collection(
    aws_region=os.getenv('AWS_REGION'),
    gcp_project_id=os.getenv('GCP_PROJECT_ID'),
    dataset_id='nba_data',
    table_id='game_results',
    target_date='2024-12-15'
)
```

### Backfill Date Range
```bash
python backfill_data.py --mode range \
    --start-date 2024-12-01 \
    --end-date 2024-12-31
```

### Backfill Entire Season
```bash
python backfill_data.py --mode season --season 2024
```

### Recent Week
```bash
python backfill_data.py --mode week
```

## 🔍 Verification & Testing

### System Check
```bash
python verify_setup.py
```

This tests:
- ✓ Environment variables set correctly
- ✓ AWS Bedrock connection working
- ✓ BigQuery connection working
- ✓ Skill file present and valid
- ✓ End-to-end data collection

### Query Results
```sql
-- Check recent collections
SELECT 
    game_date,
    home_team,
    away_team,
    home_score,
    away_score
FROM `your-project.nba_data.game_results`
ORDER BY game_date DESC, inserted_at DESC
LIMIT 10;
```

## 🚨 Troubleshooting

### "Model access not granted"
**Problem**: Claude model not enabled in Bedrock
**Solution**: Go to Bedrock Console → Model access → Enable Claude

### "Could not connect to endpoint"
**Problem**: Wrong AWS region or Bedrock not available there
**Solution**: Set `AWS_REGION=us-east-1` or `us-west-2`

### "AccessDeniedException"
**Problem**: IAM permissions insufficient
**Solution**: Add `bedrock:InvokeModel` permission to your IAM user/role

### "BigQuery permission denied"
**Problem**: Service account lacks BigQuery permissions
**Solution**: Grant `roles/bigquery.dataEditor` and `roles/bigquery.jobUser`

### No games found
**Problem**: Requesting games from off-season, all-star break, or future date
**Solution**: Check NBA schedule - games only occur during regular season and playoffs

## 💰 Cost Breakdown

### AWS Bedrock
- Input tokens: $3 per million
- Output tokens: $15 per million
- Daily collection: ~5,000 tokens = $0.10
- **Monthly**: $3-9

### Google BigQuery
- Storage: $0.02 per GB per month
- Season data: ~180 MB = $0.004
- Queries: 1 TB free per month (plenty)
- **Monthly**: ~$0.01

### Total Estimated Cost
**$5-15 per month** for complete NBA season coverage

## 🎨 Customization

### Add More Data Fields
Edit `nba_game_collector_skill.md` to include:
- Player statistics
- Game duration
- Attendance
- TV ratings
- Officials

Then update BigQuery schema in `bigquery_writer.py`

### Change Claude Model
In `nba_agent.py`, change:
```python
model_id = "anthropic.claude-opus-4-20250514-v1:0"  # More capable
# or
model_id = "anthropic.claude-haiku-4-20250514-v1:0"  # Faster, cheaper
```

### Modify Collection Schedule
```bash
# Daily at 8 AM
0 8 * * * cd /path/to/project && python nba_agent.py

# Every 6 hours
0 */6 * * * cd /path/to/project && python nba_agent.py

# Specific days (Tue, Thu, Sat)
0 8 * * 2,4,6 cd /path/to/project && python nba_agent.py
```

## 📚 Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [Claude API on Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html)
- [NBA Official Schedule](https://www.nba.com/schedule)

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review `BEDROCK_SETUP.md` for detailed setup help
3. Run `python verify_setup.py` to identify problems
4. Check AWS CloudWatch logs for error details

## 📝 File Checklist

Verify you have all these files:

Core Files:
- [x] nba_agent.py
- [x] bigquery_writer.py
- [x] nba_game_collector_skill.md
- [x] backfill_data.py
- [x] verify_setup.py

Configuration:
- [x] requirements.txt
- [x] .env.template
- [x] setup.sh

Documentation:
- [x] README_BEDROCK.md
- [x] BEDROCK_SETUP.md
- [x] SETUP_GUIDE.md
- [x] MIGRATION_SUMMARY.md
- [x] IMPLEMENTATION_SUMMARY.md
- [x] PACKAGE_MANIFEST.md (this file)

## 🎉 You're Ready!

All files are included. Follow the Quick Start steps above to begin collecting NBA game data!

**Recommended First Steps:**
1. Run `bash setup.sh`
2. Edit `.env` with your credentials
3. Run `python verify_setup.py`
4. Run `python nba_agent.py`

Good luck! 🏀

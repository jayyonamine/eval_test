# NBA Game Data Collection System (Amazon Bedrock Edition)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Automated NBA game data collection system using **Claude AI via Amazon Bedrock** with custom skills to ensure 100% accurate, consistently formatted data written to Google BigQuery.

## 🎯 Features

- **AI-Powered Collection**: Uses Claude via AWS Bedrock with web search to find and verify game data
- **100% Accuracy**: Custom skill file defines exact validation rules and output format
- **Consistent Structure**: Every data point follows the same schema
- **Duplicate Prevention**: Automatically detects and skips existing records
- **Scalable**: Handles full NBA season (1,230+ games)
- **Production Ready**: Includes deployment options for AWS Lambda, Cloud Run, or cron jobs

## 📊 Data Schema

Each game record contains:
- `game_date`: Date the game was played (YYYY-MM-DD)
- `home_team`: Full official home team name
- `away_team`: Full official away team name  
- `home_score`: Final score for home team
- `away_score`: Final score for away team
- `location`: Full arena name with city and state
- `inserted_at`: Timestamp of data insertion

## 🚀 Quick Start (10 Minutes)

### 1. Enable Amazon Bedrock (2 minutes)

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Navigate to **Model access**
3. Enable **Anthropic Claude Sonnet 4**
4. Wait for approval (usually instant)

### 2. Set Up AWS Credentials (3 minutes)

**Option A: AWS CLI (Recommended)**
```bash
pip install awscli
aws configure
# Enter your access key, secret key, and region (us-east-1)
```

**Option B: Environment Variables**
```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
```

### 3. Configure GCP for BigQuery (3 minutes)

```bash
# Set GCP project and credentials
export GCP_PROJECT_ID=your-gcp-project-id
export GCP_CREDENTIALS_PATH=/path/to/service-account-key.json
```

### 4. Install Dependencies (1 minute)

```bash
pip install -r requirements.txt
```

### 5. Verify Setup (1 minute)

```bash
python verify_setup.py
```

### 6. Run First Collection

```bash
# Collect yesterday's games
python nba_agent.py

# Or specify a date
python -c "
from nba_agent import run_daily_collection
import os

run_daily_collection(
    aws_region='us-east-1',
    gcp_project_id=os.getenv('GCP_PROJECT_ID'),
    dataset_id='nba_data',
    table_id='game_results',
    target_date='2024-12-02'
)
"
```

## 📁 Project Structure

```
nba-game-collector/
├── nba_game_collector_skill.md  # AI agent skill definition
├── nba_agent.py                  # Main orchestration script
├── bigquery_writer.py            # BigQuery integration
├── backfill_data.py              # Historical data utility
├── verify_setup.py               # System verification
├── requirements.txt              # Python dependencies
├── .env.template                 # Configuration template
├── README.md                     # This file
├── BEDROCK_SETUP.md             # Detailed Bedrock setup
└── SETUP_GUIDE.md               # Comprehensive guide
```

## 🔧 Configuration

Create a `.env` file (or set environment variables):

```bash
# AWS Bedrock
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...          # Optional if using AWS CLI
AWS_SECRET_ACCESS_KEY=...          # Optional if using AWS CLI

# Google Cloud
GCP_PROJECT_ID=your-project-id
GCP_CREDENTIALS_PATH=/path/to/key.json

# BigQuery (optional - uses defaults)
DATASET_ID=nba_data
TABLE_ID=game_results
```

## 🎓 Why Amazon Bedrock?

### Advantages:
- ✅ **Unified AWS Billing** - Single bill for all AWS services
- ✅ **IAM Integration** - Use roles instead of API keys
- ✅ **CloudWatch Monitoring** - Built-in logging and metrics
- ✅ **VPC Support** - Keep traffic within AWS network
- ✅ **Compliance** - Leverage AWS certifications
- ✅ **Lambda-Native** - Deploy directly on AWS Lambda

### Comparison:
| Feature | Anthropic API | Amazon Bedrock |
|---------|---------------|----------------|
| Pricing | $3/$15 per M tokens | Same |
| Setup | Simple API key | AWS account + IAM |
| Deployment | Any platform | Best on AWS |
| Monitoring | External tools | CloudWatch native |
| Billing | Separate | Unified AWS bill |

## 📈 Production Deployment

### Option 1: AWS Lambda (Recommended for AWS)

```bash
# Package
pip install -r requirements.txt -t package/
cp *.py *.md package/
cd package && zip -r ../nba_collector.zip .

# Deploy
aws lambda create-function \
    --function-name nba-game-collector \
    --runtime python3.11 \
    --role arn:aws:iam::ACCOUNT:role/lambda-bedrock-bigquery \
    --handler nba_agent.lambda_handler \
    --zip-file fileb://../nba_collector.zip \
    --timeout 300

# Schedule daily
aws events put-rule \
    --name nba-daily-collection \
    --schedule-expression "cron(0 8 * * ? *)"

aws events put-targets \
    --rule nba-daily-collection \
    --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT:function:nba-game-collector"
```

### Option 2: Google Cloud Run

```bash
# Create Dockerfile (see SETUP_GUIDE.md)
gcloud builds submit --tag gcr.io/PROJECT/nba-collector
gcloud run deploy nba-game-collector \
    --image gcr.io/PROJECT/nba-collector \
    --region us-central1
```

### Option 3: Traditional Cron

```bash
# Add to crontab
crontab -e
# Add: 0 8 * * * cd /path/to/project && python nba_agent.py
```

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed deployment instructions.

## 🔍 Monitoring

### Query Recent Collections

```sql
SELECT 
    game_date,
    COUNT(*) as games_count,
    MAX(inserted_at) as last_inserted
FROM `your-project.nba_data.game_results`
GROUP BY game_date
ORDER BY game_date DESC
LIMIT 30;
```

### CloudWatch Logs (if on AWS)

```bash
# View Bedrock invocations
aws logs tail /aws/bedrock/modelinvocations --follow

# View Lambda logs (if using Lambda)
aws logs tail /aws/lambda/nba-game-collector --follow
```

## 🎨 Customization

### Add More Fields

Edit `nba_game_collector_skill.md` to include:
- Player statistics
- Game duration
- Attendance
- Officials

Update BigQuery schema in `bigquery_writer.py` accordingly.

### Change Collection Schedule

Modify cron expression:
- `0 8 * * *` = Daily at 8 AM
- `0 */6 * * *` = Every 6 hours
- `0 10 * * 2,4,6` = Tue/Thu/Sat at 10 AM

### Use Different Claude Model

```python
# In nba_agent.py, use different model:
model_id = "anthropic.claude-opus-4-20250514-v1:0"  # More capable
# or
model_id = "anthropic.claude-haiku-4-20250514-v1:0"  # Faster, cheaper
```

## 💰 Cost Estimate

- **Bedrock**: ~$3-9/month (same as Anthropic API)
- **BigQuery Storage**: ~$0.01/month
- **BigQuery Queries**: Free tier sufficient
- **Lambda/Cloud Run**: Free tier covers daily runs

**Total: ~$5-15/month for full NBA season**

## 🐛 Troubleshooting

### "Model access not granted"
→ Go to Bedrock Console → Model access → Enable Claude

### "Could not connect to endpoint"
→ Verify AWS_REGION is correct (try us-east-1 or us-west-2)

### "AccessDeniedException"
→ Add `bedrock:InvokeModel` permission to IAM user/role

### No games found
→ Check if games actually occurred on that date (all-star break, off-season)

See [BEDROCK_SETUP.md](BEDROCK_SETUP.md) for detailed troubleshooting.

## 📚 Documentation

- **[BEDROCK_SETUP.md](BEDROCK_SETUP.md)** - Complete Bedrock setup guide
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Comprehensive setup instructions
- **[MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md)** - Migration from Anthropic API

## 🤝 Support

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [NBA Schedule](https://www.nba.com/schedule)

## 🎯 Roadmap

- [ ] Add player statistics collection
- [ ] Real-time game updates during live games
- [ ] Historical data backfill utility (✅ Available)
- [ ] Dashboard visualization layer
- [ ] Playoff/championship tracking
- [ ] Machine learning prediction models

## 📝 License

MIT License - see LICENSE file for details

## 🙋 FAQ

**Q: Why use Bedrock instead of Anthropic API?**
A: Better if you're already in AWS ecosystem. Unified billing, IAM integration, CloudWatch monitoring.

**Q: Can I still use Anthropic API?**
A: Yes, but you'll need the older version of the code (before Bedrock migration).

**Q: Does this work with Claude 3.5 Sonnet?**
A: Yes! Just change the model_id in the code.

**Q: What about data privacy?**
A: Bedrock processes data in your specified region and doesn't use it for training.

**Q: Cost vs. direct Anthropic API?**
A: Identical pricing for model usage. Bedrock may have small service fees but they're negligible.

---

**Built with Claude AI via Amazon Bedrock | Powered by Anthropic & AWS**

Ready to start? Run `python verify_setup.py` to begin! 🏀

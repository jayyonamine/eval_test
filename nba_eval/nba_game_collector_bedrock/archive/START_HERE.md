# 🏀 NBA Game Data Collection System - START HERE

## Welcome! 👋

This package contains a complete, production-ready system for collecting NBA game data using **Claude AI via Amazon Bedrock** and storing it in **Google BigQuery**.

## ⚡ Quick Start (Choose Your Path)

### Path 1: Automated Setup (Recommended) ⚙️
```bash
bash setup.sh
# Follow the prompts
```

### Path 2: Manual Setup 📝
1. Install dependencies: `pip install -r requirements.txt`
2. Copy config: `cp .env.template .env`
3. Edit `.env` with your AWS and GCP credentials
4. Verify: `python verify_setup.py`
5. Run: `python nba_agent.py`

## 📋 What You Need (Before Starting)

### AWS (Amazon Bedrock)
- [ ] AWS account
- [ ] Bedrock access enabled
- [ ] Claude Sonnet 4 model access approved
- [ ] AWS credentials (access key + secret key) OR AWS CLI configured

**→ Get Access**: https://console.aws.amazon.com/bedrock/

### GCP (Google BigQuery)
- [ ] Google Cloud project
- [ ] BigQuery API enabled
- [ ] Service account with BigQuery permissions
- [ ] Service account key JSON file

**→ Setup Guide**: See `BEDROCK_SETUP.md` Section "GCP Setup"

## 📚 Documentation Guide

**Start here based on your situation:**

### New to Everything? 🌱
1. **README_BEDROCK.md** - 10-minute overview (read this first!)
2. **BEDROCK_SETUP.md** - Step-by-step AWS Bedrock setup
3. **SETUP_GUIDE.md** - Comprehensive guide for production

### Already Have AWS Setup? 🚀
1. **PACKAGE_MANIFEST.md** - Quick reference guide
2. **SETUP_GUIDE.md** - Jump to "GCP Setup" section

### Migrating from Anthropic API? 🔄
1. **MIGRATION_SUMMARY.md** - What changed
2. **BEDROCK_SETUP.md** - How to set up Bedrock

### Want Architecture Details? 🏗️
1. **IMPLEMENTATION_SUMMARY.md** - System design & how it works

## 🎯 First Time Setup (10 Minutes)

### Step 1: Enable Bedrock (2 min)
```
1. Go to: https://console.aws.amazon.com/bedrock/
2. Click: Model access → Modify model access
3. Enable: Anthropic Claude Sonnet 4
4. Click: Save changes
```

### Step 2: Get AWS Credentials (3 min)
```bash
# Option A: Use AWS CLI (easiest)
pip install awscli
aws configure

# Option B: Manual credentials
# Go to AWS IAM → Users → Your user → Create access key
# Copy the access key ID and secret key
```

### Step 3: Install & Configure (3 min)
```bash
# Run automated setup
bash setup.sh

# Edit configuration
nano .env  # or use your preferred editor
```

### Step 4: Test Everything (2 min)
```bash
python verify_setup.py
```

### Step 5: Collect Data! 🎉
```bash
python nba_agent.py
```

## 📦 Package Contents

```
nba-game-collector-bedrock/
├── 🎯 START_HERE.md ................. This file
├── 📖 README_BEDROCK.md ............. Quick start guide
├── 🔧 BEDROCK_SETUP.md .............. Detailed Bedrock setup
├── 📚 SETUP_GUIDE.md ................ Comprehensive guide
├── 📋 PACKAGE_MANIFEST.md ........... Complete file reference
├── 🔄 MIGRATION_SUMMARY.md .......... Anthropic → Bedrock migration
├── 🏗️ IMPLEMENTATION_SUMMARY.md ..... System architecture
│
├── 🐍 Core Python Files
│   ├── nba_agent.py ................. Main collection script
│   ├── bigquery_writer.py ........... BigQuery integration
│   ├── backfill_data.py ............. Historical data utility
│   └── verify_setup.py .............. System verification
│
├── ⚙️ Configuration
│   ├── requirements.txt ............. Python dependencies
│   ├── .env.template ................ Config template
│   ├── setup.sh ..................... Auto-setup script
│   └── nba_game_collector_skill.md .. AI agent skill
│
└── 📊 Sample Output
    └── nba_dec2_2025_games.json .... Example data
```

## 🚨 Common First-Time Issues

### "Model access not granted"
**Fix**: Go to Bedrock Console → Model access → Enable Claude
**Link**: https://console.aws.amazon.com/bedrock/

### "UnrecognizedClientException"
**Fix**: Check your AWS credentials are correct
```bash
aws sts get-caller-identity  # Test credentials
```

### "Could not connect to endpoint"
**Fix**: Set AWS_REGION to us-east-1 or us-west-2
```bash
export AWS_REGION=us-east-1
```

### "Permission denied" (BigQuery)
**Fix**: Grant service account these roles:
- roles/bigquery.dataEditor
- roles/bigquery.jobUser

## 💰 Cost Expectations

**Monthly Cost for Full NBA Season:**
- AWS Bedrock: $3-9/month (same as Anthropic API)
- BigQuery: ~$0.01/month
- **Total: $5-15/month**

**Per Collection:**
- ~$0.10-0.30 per day
- 5,000 tokens average
- 82 games per day during peak season

## 🎓 Learning Path

### If you have 5 minutes:
→ Read `README_BEDROCK.md`

### If you have 15 minutes:
→ Read `README_BEDROCK.md`
→ Skim `PACKAGE_MANIFEST.md`
→ Run `bash setup.sh`

### If you have 1 hour:
→ Read `README_BEDROCK.md`
→ Read `BEDROCK_SETUP.md`
→ Complete full setup
→ Run first collection

## 🆘 Need Help?

1. **Check the docs** (start with README_BEDROCK.md)
2. **Run verification** (`python verify_setup.py`)
3. **Read error messages** (they're usually helpful!)
4. **Check troubleshooting** (in BEDROCK_SETUP.md)

## ✅ Success Checklist

Before you start collecting data, verify:

- [ ] AWS Bedrock access enabled
- [ ] Claude Sonnet 4 model access approved
- [ ] AWS credentials configured
- [ ] GCP project created
- [ ] BigQuery API enabled
- [ ] Service account created with permissions
- [ ] `.env` file configured
- [ ] Dependencies installed
- [ ] `verify_setup.py` passes all tests

## 🎉 You're Ready!

Once everything is set up:

```bash
# Collect yesterday's games
python nba_agent.py

# Collect specific date
python nba_agent.py --date 2024-12-15

# Backfill a week
python backfill_data.py --mode week

# Backfill entire season
python backfill_data.py --mode season --season 2024
```

## 📞 Resources

- **AWS Bedrock Console**: https://console.aws.amazon.com/bedrock/
- **AWS Bedrock Docs**: https://docs.aws.amazon.com/bedrock/
- **BigQuery Console**: https://console.cloud.google.com/bigquery
- **BigQuery Docs**: https://cloud.google.com/bigquery/docs
- **NBA Schedule**: https://www.nba.com/schedule

---

**Let's get started!** 🏀

Run `bash setup.sh` to begin, or read `README_BEDROCK.md` for an overview.

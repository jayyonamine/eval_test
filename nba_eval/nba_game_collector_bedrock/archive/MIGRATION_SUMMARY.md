# Migration to Amazon Bedrock - Quick Summary

## What Changed

The system now uses **Amazon Bedrock** instead of direct Anthropic API calls to access Claude.

## Key Changes

### 1. Dependencies
**Before:**
```
anthropic>=0.39.0
```

**After:**
```
boto3>=1.34.0
```

### 2. Environment Variables
**Before:**
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

**After:**
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...  # Optional
AWS_SECRET_ACCESS_KEY=...  # Optional
```

### 3. Code Changes
**Before:**
```python
import anthropic
client = anthropic.Anthropic(api_key=api_key)
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": prompt}]
)
```

**After:**
```python
import boto3
import json
client = boto3.client('bedrock-runtime', region_name='us-east-1')
request_body = {
    "anthropic_version": "bedrock-2023-05-31",
    "messages": [{"role": "user", "content": prompt}]
}
response = client.invoke_model(
    modelId="anthropic.claude-sonnet-4-20250514-v1:0",
    body=json.dumps(request_body)
)
```

## Files Updated

✅ `requirements.txt` - Changed from anthropic to boto3
✅ `nba_agent.py` - Updated to use Bedrock API
✅ `backfill_data.py` - Updated to use Bedrock API
✅ `verify_setup.py` - Updated to test Bedrock connection
✅ `.env.template` - Changed to AWS credentials
✅ `BEDROCK_SETUP.md` - Complete setup guide (NEW)

## Files Unchanged

✓ `bigquery_writer.py` - No changes needed
✓ `nba_game_collector_skill.md` - No changes needed
✓ `test_collection.py` - Would need updating if used

## Quick Start (5 Minutes)

### 1. Enable Bedrock
1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Navigate to **Model access**
3. Enable **Claude Sonnet 4**

### 2. Set Credentials
```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export GCP_PROJECT_ID=your-project
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Test
```bash
python verify_setup.py
```

### 5. Run
```bash
python nba_agent.py
```

## Why Bedrock?

**Advantages:**
- ✅ Unified AWS billing
- ✅ IAM roles and policies
- ✅ VPC and compliance support
- ✅ CloudWatch monitoring
- ✅ Multi-region options
- ✅ Can deploy on Lambda

**Trade-offs:**
- ⚠️ Requires AWS account setup
- ⚠️ Slightly more complex initial config
- ⚠️ Regional model availability

## Cost Impact

**Same pricing** - No change to per-token costs
- Claude Sonnet 4: $3 input / $15 output per million tokens
- Estimated: $5-15/month for full NBA season

## Deployment Options

### Still Supported:
- ✅ Google Cloud Run
- ✅ Cloud Functions  
- ✅ Cron jobs
- ✅ EC2/ECS

### Now Also Available:
- ✨ **AWS Lambda** (native integration!)
- ✨ **ECS with IAM roles** (no credentials needed)

## Troubleshooting

### "Model access not granted"
→ Enable Claude in Bedrock Console → Model access

### "Could not connect to endpoint"
→ Verify AWS_REGION is correct (us-east-1 or us-west-2)

### "UnrecognizedClientException"
→ Check AWS credentials are valid

### "AccessDeniedException"  
→ Add `bedrock:InvokeModel` permission to IAM user/role

## Testing Without Bedrock

If you prefer to keep using Anthropic API:
1. Keep the old version of files
2. Use `anthropic>=0.39.0` in requirements.txt
3. Set `ANTHROPIC_API_KEY` instead of AWS credentials

## Need Help?

1. Read [BEDROCK_SETUP.md](BEDROCK_SETUP.md) for detailed instructions
2. Check [AWS Bedrock Docs](https://docs.aws.amazon.com/bedrock/)
3. Review [Setup Guide](SETUP_GUIDE.md) for general setup

## Verification Checklist

Before deploying to production:

- [ ] Bedrock model access approved
- [ ] AWS credentials configured
- [ ] `verify_setup.py` passes all tests
- [ ] Test collection returns valid data
- [ ] BigQuery writes successful
- [ ] Daily schedule configured
- [ ] CloudWatch monitoring enabled (optional)
- [ ] Cost alerts set up (optional)

---

**Migration Complete!** 🎉

Your NBA game collection system now runs on Amazon Bedrock.

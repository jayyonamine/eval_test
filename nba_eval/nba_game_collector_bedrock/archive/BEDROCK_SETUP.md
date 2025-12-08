# NBA Game Data Collection - AWS Bedrock Setup Guide

This system now uses **Amazon Bedrock** instead of the direct Anthropic API to access Claude. This provides several advantages:
- Integrated AWS billing and management
- Support for AWS IAM roles and policies
- Better integration with other AWS services
- Regional availability and compliance options

## Prerequisites

1. **AWS Account** with Bedrock access
2. **Google Cloud Platform** account for BigQuery
3. **Python 3.8+** installed

## Step 1: Enable Amazon Bedrock

### 1.1 Request Model Access

1. Go to the [Amazon Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Select your preferred region (e.g., `us-east-1` or `us-west-2`)
3. Navigate to **Model access** in the left sidebar
4. Click **Modify model access**
5. Find **Anthropic - Claude Sonnet 4** and enable it
6. Click **Save changes**

⚠️ **Important**: Model access approval may take a few minutes. You'll receive a notification once approved.

### 1.2 Verify Available Regions

Bedrock with Claude is available in these regions (as of 2025):
- `us-east-1` (N. Virginia)
- `us-west-2` (Oregon)
- `ap-southeast-1` (Singapore)
- `ap-northeast-1` (Tokyo)
- `eu-central-1` (Frankfurt)
- `eu-west-3` (Paris)

Choose the region closest to your infrastructure for best performance.

## Step 2: Set Up AWS Credentials

You have three options for AWS authentication:

### Option A: AWS Credentials (Simplest for Testing)

1. Create an IAM user in AWS Console
2. Attach the `AmazonBedrockFullAccess` policy
3. Generate access keys
4. Set environment variables:

```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_access_key_here
export AWS_SECRET_ACCESS_KEY=your_secret_key_here
```

### Option B: AWS CLI Configuration (Recommended for Development)

1. Install AWS CLI:
```bash
pip install awscli
```

2. Configure credentials:
```bash
aws configure
# Enter your access key, secret key, and default region
```

3. Set only the region in your environment:
```bash
export AWS_REGION=us-east-1
```

The system will automatically use your AWS CLI credentials.

### Option C: IAM Roles (Best for Production)

For EC2, Lambda, or ECS deployments:

1. Create an IAM role with `AmazonBedrockFullAccess` policy
2. Attach the role to your compute resource
3. Set only the region:
```bash
export AWS_REGION=us-east-1
```

No additional credentials needed - the role provides automatic authentication.

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `boto3` - AWS SDK for Python (replaces `anthropic`)
- `google-cloud-bigquery` - BigQuery client
- `google-auth` - GCP authentication

## Step 4: Configure Environment Variables

Create a `.env` file from the template:

```bash
cp .env.template .env
```

Edit `.env` with your settings:

```bash
# AWS Bedrock Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here  # Optional if using AWS CLI or IAM role
AWS_SECRET_ACCESS_KEY=your_secret_key_here  # Optional if using AWS CLI or IAM role

# Google Cloud Configuration
GCP_PROJECT_ID=your-gcp-project-id
GCP_CREDENTIALS_PATH=/path/to/service-account-key.json

# BigQuery Configuration (optional)
DATASET_ID=nba_data
TABLE_ID=game_results
```

## Step 5: Verify Setup

Run the verification script:

```bash
python verify_setup.py
```

This will test:
- ✓ Environment variables
- ✓ Amazon Bedrock connection
- ✓ BigQuery connection
- ✓ Skill file
- ✓ End-to-end collection

## Step 6: Run Your First Collection

```bash
python nba_agent.py
```

This will collect games from yesterday and write them to BigQuery.

## Architecture Changes

### Previous (Anthropic API):
```
Python App → Anthropic API → Claude Model
```

### Current (Amazon Bedrock):
```
Python App → AWS Bedrock → Claude Model (via Bedrock)
```

## API Comparison

### Old (Anthropic API):
```python
import anthropic

client = anthropic.Anthropic(api_key="sk-ant-...")
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4000,
    messages=[{"role": "user", "content": "Hello"}]
)
```

### New (Bedrock):
```python
import boto3
import json

client = boto3.client('bedrock-runtime', region_name='us-east-1')
request_body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 4000,
    "messages": [{"role": "user", "content": "Hello"}]
}
response = client.invoke_model(
    modelId="anthropic.claude-sonnet-4-20250514-v1:0",
    body=json.dumps(request_body)
)
```

## Cost Comparison

### Anthropic API Pricing:
- Claude Sonnet 4: $3 per million input tokens, $15 per million output tokens

### AWS Bedrock Pricing (as of 2025):
- Claude Sonnet 4: Same pricing as Anthropic API
- Plus AWS Bedrock service fees (minimal)

**For this application**: Cost difference is negligible (~$5-15/month either way)

## Advantages of Bedrock

1. **Unified Billing**: Everything on one AWS bill
2. **IAM Integration**: Use AWS roles and policies for access control
3. **VPC Support**: Keep traffic within AWS network
4. **Compliance**: Leverage AWS compliance certifications
5. **Monitoring**: Native CloudWatch integration
6. **Multi-Model**: Easy to switch between Claude, other models

## Model IDs in Bedrock

Available Claude models:
- `anthropic.claude-sonnet-4-20250514-v1:0` (default, used by this system)
- `anthropic.claude-opus-4-20250514-v1:0` (more capable, higher cost)
- `anthropic.claude-haiku-4-20250514-v1:0` (faster, lower cost)

## Troubleshooting

### Error: "Model access not granted"
**Solution**: Go to Bedrock Console → Model access → Enable Claude models

### Error: "Could not connect to the endpoint URL"
**Solution**: Verify your AWS_REGION is correct and Bedrock is available there

### Error: "UnrecognizedClientException"
**Solution**: Check your AWS credentials are valid

### Error: "ThrottlingException"
**Solution**: You've hit rate limits. Add delays between requests or request a quota increase

### Error: "AccessDeniedException"
**Solution**: Your IAM user/role needs `bedrock:InvokeModel` permission

## Deployment Options

All deployment methods from the original guide still work:

### Cloud Run / Cloud Functions
Add AWS credentials as environment variables in GCP

### EC2 / ECS
Use IAM roles - no credentials needed in environment

### Lambda (New Option!)
Since you're now using AWS, you can deploy the entire system on Lambda:

```bash
# Package deployment
pip install -r requirements.txt -t package/
cp *.py package/
cd package && zip -r ../nba_collector.zip .

# Deploy
aws lambda create-function \
    --function-name nba-game-collector \
    --runtime python3.11 \
    --role arn:aws:iam::ACCOUNT:role/lambda-bedrock-role \
    --handler nba_agent.lambda_handler \
    --zip-file fileb://../nba_collector.zip
```

## Security Best Practices

1. **Never commit AWS credentials** to version control
2. **Use IAM roles** when possible instead of access keys
3. **Follow least privilege**: Only grant necessary Bedrock permissions
4. **Rotate access keys** regularly
5. **Enable CloudTrail** to log all Bedrock API calls
6. **Use AWS Secrets Manager** for production credentials

## Monitoring with CloudWatch

Bedrock automatically logs to CloudWatch:

```bash
# View invocation logs
aws logs tail /aws/bedrock/modelinvocations --follow

# View metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/Bedrock \
    --metric-name InvocationCount \
    --dimensions Name=ModelId,Value=anthropic.claude-sonnet-4-20250514-v1:0 \
    --start-time 2025-12-01T00:00:00Z \
    --end-time 2025-12-03T00:00:00Z \
    --period 3600 \
    --statistics Sum
```

## Migration from Anthropic API

If you were using the old version:

1. **No data migration needed** - BigQuery schema is unchanged
2. **Update credentials** - Replace `ANTHROPIC_API_KEY` with AWS credentials
3. **Test thoroughly** - Run `verify_setup.py` to confirm
4. **Monitor costs** - Check AWS billing dashboard

## Next Steps

1. ✅ Complete Bedrock setup
2. ✅ Run test collection
3. ✅ Verify data in BigQuery
4. ✅ Set up daily scheduling
5. ✅ Configure CloudWatch alerts
6. ⏭️ Optimize costs with haiku model for testing
7. ⏭️ Set up AWS Cost Anomaly Detection

## Support Resources

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Bedrock User Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/)
- [Claude on Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html)
- [AWS Support](https://console.aws.amazon.com/support/)

## FAQ

**Q: Can I use both Anthropic API and Bedrock?**
A: Yes, but you'll need to maintain two versions of the code.

**Q: Which is better - Anthropic API or Bedrock?**
A: Bedrock is better if you're already in AWS. Anthropic API is simpler if you're not.

**Q: Does this work with Claude 3.5 Sonnet?**
A: Yes! Just change the model_id to the appropriate Claude 3.5 model.

**Q: Can I use this with other AWS regions?**
A: Yes, but verify Bedrock with Claude is available in your target region first.

**Q: What about data residency?**
A: Bedrock processes data in the region you specify, helping with compliance.

---

**You're now set up with Amazon Bedrock!** 🎉

Run `python nba_agent.py` to start collecting NBA game data.

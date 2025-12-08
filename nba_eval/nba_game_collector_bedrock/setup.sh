#!/bin/bash
# NBA Game Data Collection - Quick Setup Script
# This script helps you get started quickly

set -e

echo "========================================================================"
echo "NBA Game Data Collection System - Quick Setup"
echo "Using Amazon Bedrock + Google BigQuery"
echo "========================================================================"
echo ""

# Check Python version
echo "📋 Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "✓ Found Python $PYTHON_VERSION"
else
    echo "✗ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "ℹ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✓ Dependencies installed"

# Create .env file if it doesn't exist
echo ""
echo "⚙️  Setting up configuration..."
if [ ! -f ".env" ]; then
    cp .env.template .env
    echo "✓ Created .env file from template"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your credentials:"
    echo "   - AWS_REGION"
    echo "   - AWS_ACCESS_KEY_ID (optional if using AWS CLI)"
    echo "   - AWS_SECRET_ACCESS_KEY (optional if using AWS CLI)"
    echo "   - GCP_PROJECT_ID"
    echo "   - GCP_CREDENTIALS_PATH"
else
    echo "ℹ .env file already exists"
fi

# Check AWS CLI
echo ""
echo "🔍 Checking AWS CLI..."
if command -v aws &> /dev/null; then
    echo "✓ AWS CLI found"
    if aws sts get-caller-identity &> /dev/null; then
        echo "✓ AWS credentials configured"
    else
        echo "⚠️  AWS CLI installed but not configured"
        echo "   Run: aws configure"
    fi
else
    echo "ℹ AWS CLI not found (optional)"
    echo "   You can install it with: pip install awscli"
    echo "   Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env"
fi

# Summary
echo ""
echo "========================================================================"
echo "Setup Complete!"
echo "========================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Enable Bedrock in AWS Console:"
echo "   → https://console.aws.amazon.com/bedrock/"
echo "   → Model access → Enable Claude Sonnet 4"
echo ""
echo "2. Set up AWS credentials:"
echo "   → Run: aws configure"
echo "   → Or edit .env file with your AWS keys"
echo ""
echo "3. Set up GCP credentials:"
echo "   → Edit .env file with GCP_PROJECT_ID and GCP_CREDENTIALS_PATH"
echo ""
echo "4. Verify setup:"
echo "   → Run: python verify_setup.py"
echo ""
echo "5. Start collecting data:"
echo "   → Run: python nba_agent.py"
echo ""
echo "For detailed instructions, see:"
echo "   - README_BEDROCK.md (quick overview)"
echo "   - BEDROCK_SETUP.md (detailed Bedrock setup)"
echo "   - SETUP_GUIDE.md (comprehensive guide)"
echo ""
echo "========================================================================"

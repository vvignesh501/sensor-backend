#!/bin/bash

# AWS S3 Setup Script for Sensor Backend

echo "🚀 Setting up AWS S3 for Sensor Backend..."

# Check if AWS credentials are set
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "❌ AWS credentials not set!"
    echo "Please set environment variables:"
    echo "  export AWS_ACCESS_KEY_ID='your-key'"
    echo "  export AWS_SECRET_ACCESS_KEY='your-secret'"
    echo ""
    echo "Or configure AWS CLI:"
    echo "  aws configure"
    exit 1
fi

# Set default region if not set
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-2}"

# Use existing S3 bucket
BUCKET_NAME="sensor-prod-data-vvignesh501-2025"
echo "Using existing S3 bucket: $BUCKET_NAME"

# Verify bucket exists
if aws s3 ls s3://$BUCKET_NAME > /dev/null 2>&1; then
    echo "✅ Bucket $BUCKET_NAME exists and accessible"
else
    echo "❌ Cannot access bucket $BUCKET_NAME"
    exit 1
fi

# Update bucket name in app
sed -i '' "s/sensor-raw-data-demo/$BUCKET_NAME/g" simple_app.py

echo "✅ S3 bucket created: $BUCKET_NAME"
echo "✅ Environment variables set"
echo "✅ Ready to run: python3 simple_app.py"

# Start the app
python3 simple_app.py
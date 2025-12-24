#!/bin/bash

echo "=========================================="
echo "🚀 PARQUET + PYSPARK DEMO"
echo "=========================================="
echo ""

# Configuration
export AWS_REGION=${AWS_REGION:-us-east-1}
export S3_BUCKET=${S3_BUCKET:-sensor-data-demo}

echo "📋 Configuration:"
echo "  AWS Region: $AWS_REGION"
echo "  S3 Bucket: $S3_BUCKET"
echo ""

# Check AWS credentials
if [ ! -d ~/.aws ]; then
    echo "❌ AWS credentials not found at ~/.aws"
    echo "Please configure AWS credentials first:"
    echo "  aws configure"
    exit 1
fi

echo "✓ AWS credentials found"
echo ""

# Create S3 bucket if it doesn't exist
echo "📦 Checking S3 bucket..."
if aws s3 ls "s3://$S3_BUCKET" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Creating bucket: $S3_BUCKET"
    aws s3 mb "s3://$S3_BUCKET" --region "$AWS_REGION"
else
    echo "✓ Bucket exists: $S3_BUCKET"
fi
echo ""

# Build Docker image
echo "🐳 Building Docker image..."
docker-compose build
echo ""

# Step 1: Run Parquet conversion
echo "=========================================="
echo "STEP 1: Convert JSON to Parquet"
echo "=========================================="
docker-compose run --rm pyspark-processor python parquet_converter.py
echo ""

# Step 2: Start dashboard
echo "=========================================="
echo "STEP 2: Starting Real-Time Dashboard"
echo "=========================================="
echo ""
echo "🌐 Dashboard will be available at:"
echo "   http://localhost:8501"
echo ""
echo "🔥 Spark UI available at:"
echo "   http://localhost:4040"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

docker-compose up

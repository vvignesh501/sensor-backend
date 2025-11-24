#!/bin/bash

# AWS Lambda Deployment Script for N-Dimensional Data Processor

set -e

FUNCTION_NAME="sensor-data-processor"
REGION="us-east-1"
ROLE_ARN="arn:aws:iam::123456789012:role/lambda-execution-role"

echo "🚀 Deploying N-Dimensional Sensor Data Processor to AWS Lambda"

# Create deployment package
echo "📦 Creating deployment package..."
mkdir -p lambda_package
cp lambda_data_processor.py lambda_package/
cd lambda_package

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r ../lambda_requirements.txt -t .

# Create ZIP package
echo "🗜️  Creating ZIP package..."
zip -r ../sensor_data_processor.zip .
cd ..

# Deploy to AWS Lambda
echo "☁️  Deploying to AWS Lambda..."
aws lambda create-function \
    --function-name $FUNCTION_NAME \
    --runtime python3.9 \
    --role $ROLE_ARN \
    --handler lambda_data_processor.lambda_handler \
    --zip-file fileb://sensor_data_processor.zip \
    --timeout 300 \
    --memory-size 1024 \
    --environment Variables='{
        "SOURCE_BUCKET":"sensor-prod-data-vvignesh501-2025",
        "PROCESSED_BUCKET":"sensor-analytics-processed-data",
        "METADATA_TABLE":"sensor-analytics-metadata",
        "ANOMALY_TOPIC_ARN":"arn:aws:sns:us-east-1:123456789012:sensor-anomalies"
    }' \
    --description "N-dimensional sensor data preprocessing for analytics" \
    || aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://sensor_data_processor.zip

# Configure S3 trigger
echo "🔗 Configuring S3 trigger..."
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --principal s3.amazonaws.com \
    --action lambda:InvokeFunction \
    --statement-id s3-trigger \
    --source-arn arn:aws:s3:::sensor-prod-data-vvignesh501-2025 \
    || echo "Permission already exists"

# Create S3 event notification
aws s3api put-bucket-notification-configuration \
    --bucket sensor-prod-data-vvignesh501-2025 \
    --notification-configuration '{
        "LambdaConfigurations": [
            {
                "Id": "sensor-data-processing",
                "LambdaFunctionArn": "arn:aws:lambda:'$REGION':123456789012:function:'$FUNCTION_NAME'",
                "Events": ["s3:ObjectCreated:*"],
                "Filter": {
                    "Key": {
                        "FilterRules": [
                            {
                                "Name": "prefix",
                                "Value": "raw_data/"
                            },
                            {
                                "Name": "suffix",
                                "Value": ".npy"
                            }
                        ]
                    }
                }
            }
        ]
    }'

echo "✅ Lambda function deployed successfully!"
echo "📊 Function Name: $FUNCTION_NAME"
echo "🌍 Region: $REGION"
echo "⚡ Trigger: S3 bucket sensor-prod-data-vvignesh501-2025"

# Cleanup
rm -rf lambda_package sensor_data_processor.zip

echo "🧹 Cleanup completed"
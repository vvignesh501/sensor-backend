#!/bin/bash

echo "🚀 Creating Lambda Function"
echo "==========================="
echo ""

# Navigate to terraform directory
cd terraform

# Create Lambda package first
echo "1. Creating Lambda deployment package..."
cd ..
mkdir -p lambda_package

# Install numpy
pip install numpy==1.24.3 -t lambda_package/ --platform manylinux2014_x86_64 --only-binary=:all: -q

# Copy Lambda function
cp lambda/lambda_data_processor.py lambda_package/

# Create ZIP
cd lambda_package
zip -r9 ../terraform/sensor_data_processor.zip . > /dev/null 2>&1
cd ..

SIZE=$(du -h terraform/sensor_data_processor.zip | cut -f1)
echo "   ✅ Lambda package created: $SIZE"

# Cleanup
rm -rf lambda_package

# Initialize Terraform
cd terraform
echo ""
echo "2. Initializing Terraform..."
terraform init

# Create only the Lambda function
echo ""
echo "3. Creating Lambda function..."
terraform apply -target=aws_lambda_function.data_processor -auto-approve

echo ""
echo "✅ Lambda function created!"
echo ""
echo "You can now run the GitHub Actions workflow to deploy code updates."

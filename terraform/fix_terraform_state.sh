#!/bin/bash

echo "🔧 Fixing Terraform State Issues"
echo "================================="
echo ""

# Remove stuck subnet resources from state
echo "1. Removing stuck subnet resources from Terraform state..."
terraform state rm 'aws_subnet.redshift_subnet_1' 2>/dev/null && echo "   ✅ Removed redshift_subnet_1" || echo "   ⚠️  redshift_subnet_1 not in state"
terraform state rm 'aws_subnet.redshift_subnet_2' 2>/dev/null && echo "   ✅ Removed redshift_subnet_2" || echo "   ⚠️  redshift_subnet_2 not in state"
terraform state rm 'aws_redshift_subnet_group.redshift' 2>/dev/null && echo "   ✅ Removed redshift_subnet_group" || echo "   ⚠️  redshift_subnet_group not in state"
terraform state rm 'aws_redshift_cluster.analytics' 2>/dev/null && echo "   ✅ Removed redshift_cluster" || echo "   ⚠️  redshift_cluster not in state"

echo ""
echo "2. Creating Lambda deployment package..."
cd ..

# Create lambda package directory
mkdir -p lambda_package

# Check if requirements.txt exists for lambda
if [ -f lambda/requirements.txt ]; then
    echo "   Installing Lambda dependencies..."
    pip install -r lambda/requirements.txt -t lambda_package/ -q
else
    echo "   No Lambda requirements.txt found, skipping dependencies"
fi

# Copy Lambda function
cp lambda/lambda_data_processor.py lambda_package/

# Create ZIP file
cd lambda_package
zip -r ../terraform/sensor_data_processor.zip . > /dev/null 2>&1
cd ..

if [ -f terraform/sensor_data_processor.zip ]; then
    echo "   ✅ Lambda package created: $(ls -lh terraform/sensor_data_processor.zip | awk '{print $5}')"
else
    echo "   ❌ Failed to create Lambda package"
    exit 1
fi

# Cleanup
rm -rf lambda_package

cd terraform

echo ""
echo "3. Verifying Terraform state..."
terraform state list | grep -i subnet && echo "   ⚠️  Subnets still in state" || echo "   ✅ No problematic subnets in state"

echo ""
echo "✅ Fix complete! You can now run:"
echo "   terraform plan"
echo "   terraform apply"

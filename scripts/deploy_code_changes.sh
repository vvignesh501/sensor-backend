#!/bin/bash

# Code Deployment Script (After Initial Setup)
# Only deploys code changes - no infrastructure changes

set -e

echo "🚀 Deploying Code Changes"
echo "========================="

AWS_REGION="us-east-1"

# Check what changed
echo "📋 Checking what needs deployment..."

DEPLOY_LAMBDA=false
DEPLOY_FASTAPI=false
UPDATE_REDSHIFT=false

# Check if Lambda code changed
if [[ -f "optimized_redshift_processor.py" && "optimized_redshift_processor.py" -nt ".last_lambda_deploy" ]]; then
    DEPLOY_LAMBDA=true
    echo "   🔄 Lambda code changed - will deploy"
fi

# Check if FastAPI code changed
if [[ -f "simple_app.py" && "simple_app.py" -nt ".last_fastapi_deploy" ]]; then
    DEPLOY_FASTAPI=true
    echo "   🔄 FastAPI code changed - will restart"
fi

# Check if SQL schemas changed
if [[ -f "create_redshift_tables.sql" && "create_redshift_tables.sql" -nt ".last_redshift_deploy" ]]; then
    UPDATE_REDSHIFT=true
    echo "   🔄 Redshift schemas changed - will update"
fi

if [[ "$DEPLOY_LAMBDA" == false && "$DEPLOY_FASTAPI" == false && "$UPDATE_REDSHIFT" == false ]]; then
    echo "   ✅ No changes detected - nothing to deploy"
    exit 0
fi

# Deploy Lambda if changed
if [[ "$DEPLOY_LAMBDA" == true ]]; then
    echo "📦 Deploying Lambda Function..."
    
    # Package Lambda
    rm -rf lambda_package
    mkdir lambda_package
    cp optimized_redshift_processor.py lambda_package/lambda_function.py
    
    cd lambda_package
    pip3 install numpy pandas boto3 psycopg2-binary -t . --quiet
    zip -r ../sensor_processor.zip . > /dev/null
    cd ..
    
    # Deploy to AWS
    aws lambda update-function-code \
        --function-name sensor-data-processor \
        --zip-file fileb://sensor_processor.zip \
        --region $AWS_REGION
    
    # Update timestamp
    touch .last_lambda_deploy
    
    echo "   ✅ Lambda deployed successfully"
    
    # Cleanup
    rm -rf lambda_package sensor_processor.zip
fi

# Update Redshift if changed
if [[ "$UPDATE_REDSHIFT" == true ]]; then
    echo "📊 Updating Redshift Schemas..."
    
    # Execute SQL changes
    aws redshift-data execute-statement \
        --cluster-identifier sensor-analytics-cluster \
        --database sensor_analytics \
        --db-user admin \
        --sql "$(cat create_redshift_tables.sql)" \
        --region $AWS_REGION
    
    # Update timestamp
    touch .last_redshift_deploy
    
    echo "   ✅ Redshift schemas updated"
fi

# Restart FastAPI if changed
if [[ "$DEPLOY_FASTAPI" == true ]]; then
    echo "🔄 Restarting FastAPI Application..."
    
    # Kill existing FastAPI process
    pkill -f "simple_app.py" 2>/dev/null || true
    
    # Start new process in background
    python3 simple_app.py &
    FASTAPI_PID=$!
    
    # Wait for startup
    sleep 3
    
    # Test if it's running
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "   ✅ FastAPI restarted successfully (PID: $FASTAPI_PID)"
        touch .last_fastapi_deploy
    else
        echo "   ❌ FastAPI failed to start"
        exit 1
    fi
fi

# Quick integration test
echo "🧪 Running quick integration test..."
python3 << 'EOF'
import requests
import sys

try:
    # Test health endpoint
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        print("   ✅ FastAPI health check passed")
    else:
        print(f"   ❌ Health check failed: {response.status_code}")
        sys.exit(1)
        
    # Test auth endpoint
    auth_data = {"username": "admin", "password": "admin123"}
    response = requests.post("http://localhost:8000/auth/token", data=auth_data, timeout=5)
    if response.status_code == 200:
        print("   ✅ Authentication working")
    else:
        print(f"   ❌ Authentication failed: {response.status_code}")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Integration test failed: {str(e)}")
    sys.exit(1)
EOF

echo ""
echo "🎉 CODE DEPLOYMENT SUCCESSFUL!"
echo "=============================="
echo ""
echo "📊 Deployed components:"
if [[ "$DEPLOY_LAMBDA" == true ]]; then
    echo "   ✅ Lambda function updated"
fi
if [[ "$UPDATE_REDSHIFT" == true ]]; then
    echo "   ✅ Redshift schemas updated"
fi
if [[ "$DEPLOY_FASTAPI" == true ]]; then
    echo "   ✅ FastAPI application restarted"
fi
echo ""
echo "🔍 Next steps:"
echo "   1. Test your changes: python3 test_integration.py"
echo "   2. Run load test: python3 load_test_1000_kafka.py"
echo "   3. Monitor logs: aws logs tail /aws/lambda/sensor-data-processor"
echo ""
echo "🚀 Your code changes are now live!"
#!/bin/bash

# Quick Deploy Script - For Daily Development
# Deploys only what changed, skips infrastructure

set -e

echo "⚡ Quick Deploy - Code Changes Only"
echo "=================================="

# Quick Lambda deployment (most common)
deploy_lambda() {
    echo "📦 Deploying Lambda..."
    
    # Quick package (no dependencies reinstall if they exist)
    if [[ ! -d "lambda_deps" ]]; then
        mkdir lambda_deps
        pip3 install numpy pandas boto3 psycopg2-binary -t lambda_deps --quiet
    fi
    
    # Create package
    cp optimized_redshift_processor.py lambda_function.py
    zip -r sensor_processor.zip lambda_function.py lambda_deps/ > /dev/null
    
    # Deploy
    aws lambda update-function-code \
        --function-name sensor-data-processor \
        --zip-file fileb://sensor_processor.zip \
        --region us-east-1
    
    # Cleanup
    rm lambda_function.py sensor_processor.zip
    
    echo "   ✅ Lambda deployed in 10 seconds"
}

# Quick FastAPI restart
deploy_fastapi() {
    echo "🔄 Restarting FastAPI..."
    
    pkill -f "simple_app.py" 2>/dev/null || true
    python3 simple_app.py &
    sleep 2
    
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "   ✅ FastAPI restarted"
    else
        echo "   ❌ FastAPI failed"
        exit 1
    fi
}

# Parse command line arguments
case "${1:-auto}" in
    "lambda"|"l")
        deploy_lambda
        ;;
    "fastapi"|"f")
        deploy_fastapi
        ;;
    "both"|"b")
        deploy_lambda
        deploy_fastapi
        ;;
    "auto"|"a"|"")
        # Auto-detect what changed
        if [[ "optimized_redshift_processor.py" -nt ".last_deploy" ]]; then
            deploy_lambda
        fi
        if [[ "simple_app.py" -nt ".last_deploy" ]]; then
            deploy_fastapi
        fi
        touch .last_deploy
        ;;
    *)
        echo "Usage: $0 [lambda|fastapi|both|auto]"
        echo "  lambda  - Deploy Lambda function only"
        echo "  fastapi - Restart FastAPI only"  
        echo "  both    - Deploy both"
        echo "  auto    - Auto-detect changes (default)"
        exit 1
        ;;
esac

echo "🎉 Quick deploy complete!"
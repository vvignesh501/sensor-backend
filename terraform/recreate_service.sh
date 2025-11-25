#!/bin/bash
# Recreate ECS service with new configuration

set -e

echo "🔧 Recreating ECS service with high-performance config..."

# Delete existing service
aws ecs delete-service \
  --cluster sensor-app-cluster \
  --service sensor-app-service \
  --force \
  --region us-east-2

echo "⏳ Waiting for service to be deleted (60 seconds)..."
sleep 60

# Now Terraform can create the new service
terraform apply

echo "✅ Service recreated with new configuration"

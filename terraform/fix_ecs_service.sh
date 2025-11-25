#!/bin/bash
# Fix: Import existing ECS service into Terraform state

set -e

echo "🔧 Fixing ECS Service conflict..."

# Import existing service
terraform import aws_ecs_service.app_service sensor-app-cluster/sensor-app-service

echo "✅ Service imported. Now run: terraform apply"

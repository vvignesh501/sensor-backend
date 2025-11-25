#!/bin/bash
# Script to remove stuck resources from Terraform state
# Run this if resources are stuck in destroy and blocking deployment

echo "Removing stuck Redshift subnet resources from Terraform state..."

# Remove the stuck subnet
terraform state rm aws_subnet.redshift_subnet_1 2>/dev/null || echo "Resource not in state"
terraform state rm aws_subnet.redshift_subnet_2 2>/dev/null || echo "Resource not in state"

# Remove any other Redshift resources
terraform state rm aws_redshift_subnet_group.redshift 2>/dev/null || echo "Resource not in state"
terraform state rm aws_redshift_cluster.analytics 2>/dev/null || echo "Resource not in state"

echo "✅ Done! Run 'terraform plan' to verify state is clean"

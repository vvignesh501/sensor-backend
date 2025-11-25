# Terraform Infrastructure Management

Infrastructure is managed **manually** to avoid long destroy cycles in CI/CD.

## Quick Start

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply changes
terraform apply

# Destroy (when needed)
terraform destroy
```

## Stuck Resources?

If resources are stuck during destroy (like subnets with dependencies):

```bash
# Run the cleanup script
./remove_stuck_resources.sh

# Then verify state
terraform plan
```

## Manual Subnet Cleanup

If the script doesn't work, manually remove from AWS Console first, then:

```bash
terraform state rm aws_subnet.redshift_subnet_1
terraform state rm aws_subnet.redshift_subnet_2
```

## Current Infrastructure

- Lambda function for data processing
- S3 buckets for data storage
- DynamoDB for metadata
- SNS for alerts
- CloudWatch for monitoring

**Note:** VPC/ECS removed to simplify deployment. Lambda runs without VPC for faster cold starts.

# Deployment Guide

Complete guide for deploying the Sensor Backend to AWS using GitHub Actions, Docker, and Terraform.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **GitHub Repository** with the code
3. **AWS CLI** installed locally (for initial setup)
4. **Terraform** knowledge (optional, automated via GitHub Actions)

## Architecture Overview

```
GitHub Actions → Docker (ECR) → ECS Fargate
                ↓
              Terraform → S3 + Lambda + Redshift + DynamoDB
```

## Step 1: Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

```
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
```

### Creating AWS IAM User for GitHub Actions

```bash
# Create IAM user
aws iam create-user --user-name github-actions-deployer

# Attach policies
aws iam attach-user-policy \
  --user-name github-actions-deployer \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Create access key
aws iam create-access-key --user-name github-actions-deployer
```

## Step 2: Setup Terraform Backend (One-time)

Run the setup workflow manually from GitHub Actions:

1. Go to **Actions** tab in your repository
2. Select **"Setup Terraform Backend (One-time)"**
3. Click **"Run workflow"**
4. Select region (default: us-east-1)
5. Click **"Run workflow"**

This creates:
- S3 bucket: `sensor-backend-terraform-state`
- DynamoDB table: `terraform-state-lock`

## Step 3: Deploy Infrastructure

### Automatic Deployment (Recommended)

Push to `main` branch:
```bash
git add .
git commit -m "Deploy infrastructure"
git push origin main
```

GitHub Actions will automatically:
1. ✅ Run tests
2. 🐳 Build and push Docker image to ECR
3. 🏗️ Deploy infrastructure with Terraform (S3, Lambda, Redshift, ECS)
4. 🚀 Deploy Lambda functions
5. 📦 Deploy ECS service

### Manual Deployment

Use workflow dispatch from GitHub Actions:

1. Go to **Actions** tab
2. Select **"Deploy Sensor Backend"**
3. Click **"Run workflow"**
4. Choose what to deploy:
   - ✅ Deploy infrastructure (Terraform)
   - ✅ Deploy Lambda functions
   - ✅ Deploy ECS service
5. Click **"Run workflow"**

## Step 4: Verify Deployment

### Check Infrastructure

```bash
# Get Terraform outputs
cd sensor-backend/terraform
terraform output

# Expected outputs:
# - alb_url: http://sensor-backend-alb-xxx.us-east-1.elb.amazonaws.com
# - lambda_function_name: sensor-data-processor
# - source_bucket_name: sensor-prod-data-vvignesh501-2025
# - redshift_cluster_endpoint: sensor-analytics-cluster.xxx.us-east-1.redshift.amazonaws.com:5439
```

### Test API

```bash
# Health check
curl http://<alb-url>/health

# Expected: {"status":"healthy","timestamp":"2025-11-24T..."}
```

### Check ECS Service

```bash
# List running tasks
aws ecs list-tasks --cluster sensor-backend-cluster --service sensor-backend-service

# Check service status
aws ecs describe-services --cluster sensor-backend-cluster --services sensor-backend-service
```

### Check Lambda Function

```bash
# Get Lambda function info
aws lambda get-function --function-name sensor-data-processor

# Test Lambda (upload test file to S3 to trigger)
aws s3 cp test-data.npy s3://sensor-prod-data-vvignesh501-2025/raw_data/test-data.npy
```

## Infrastructure Components

### S3 Buckets
- **Source Data**: `sensor-prod-data-vvignesh501-2025`
  - Stores raw sensor test data
  - Triggers Lambda on new uploads
- **Processed Data**: `sensor-analytics-processed-data`
  - Stores processed analytics results

### Lambda Functions
- **sensor-data-processor**
  - Triggered by S3 uploads
  - Processes sensor data
  - Stores metadata in DynamoDB
  - Sends anomaly alerts via SNS

### DynamoDB
- **sensor-analytics-metadata**
  - Stores test metadata
  - Indexed by test_id and timestamp

### Redshift (Optional)
- **sensor-analytics-cluster**
  - Data warehouse for analytics
  - Single-node dc2.large
  - Connected to processed S3 bucket

### ECS Fargate
- **sensor-backend-cluster**
  - Runs FastAPI application
  - Auto-scaling: 2-10 tasks
  - Behind Application Load Balancer

## Configuration

### Terraform Variables

Edit `sensor-backend/terraform/variables.tf` or pass via command line:

```hcl
variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  default = "prod"
}

variable "enable_redshift" {
  default = true  # Set to false to skip Redshift
}

variable "alert_email" {
  default = "alerts@yourcompany.com"
}
```

### Environment Variables

ECS tasks use these environment variables (configured in Terraform):

```
INSTANCE_ID=ecs-1
AWS_REGION=us-east-1
SOURCE_BUCKET=sensor-prod-data-vvignesh501-2025
PROCESSED_BUCKET=sensor-analytics-processed-data
```

## Monitoring

### CloudWatch Dashboard

Access at: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=SensorAnalyticsDashboard

Monitors:
- Lambda performance (duration, errors, invocations)
- S3 storage usage
- ECS task metrics

### Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/sensor-data-processor --follow

# ECS logs
aws logs tail /ecs/sensor-backend --follow
```

## Scaling

### ECS Auto-scaling

Configured in `terraform/ecs.tf`:
- Min tasks: 2
- Max tasks: 10
- CPU target: 70%
- Memory target: 80%

### Lambda Concurrency

Default: 1000 concurrent executions
Adjust if needed:

```bash
aws lambda put-function-concurrency \
  --function-name sensor-data-processor \
  --reserved-concurrent-executions 500
```

## Cost Optimization

### Disable Redshift (saves ~$180/month)

```bash
cd sensor-backend/terraform
terraform apply -var="enable_redshift=false"
```

### Use Spot Instances for ECS

Edit `terraform/ecs.tf` and change `launch_type` to `FARGATE_SPOT`.

## Troubleshooting

### Deployment Failed

```bash
# Check GitHub Actions logs
# Go to Actions tab → Select failed workflow → View logs

# Check Terraform state
cd sensor-backend/terraform
terraform show
```

### ECS Tasks Not Starting

```bash
# Check task logs
aws ecs describe-tasks --cluster sensor-backend-cluster --tasks <task-id>

# Check service events
aws ecs describe-services --cluster sensor-backend-cluster --services sensor-backend-service
```

### Lambda Errors

```bash
# View recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/sensor-data-processor \
  --filter-pattern "ERROR"
```

## Rollback

### Rollback Infrastructure

```bash
cd sensor-backend/terraform
terraform plan -destroy
terraform destroy
```

### Rollback ECS Deployment

```bash
# Update to previous task definition
aws ecs update-service \
  --cluster sensor-backend-cluster \
  --service sensor-backend-service \
  --task-definition sensor-backend:<previous-revision>
```

## CI/CD Pipeline

### Workflow Triggers

- **Push to main**: Full deployment
- **Push to develop**: Build and test only
- **Pull Request**: Tests only
- **Manual**: Selective deployment

### Pipeline Stages

1. **Test** (all branches)
   - Run pytest
   - Upload coverage

2. **Build** (main/develop)
   - Build Docker image
   - Push to ECR
   - Tag with git SHA

3. **Deploy Infrastructure** (main only)
   - Terraform plan
   - Terraform apply
   - Save outputs

4. **Deploy Lambda** (main only)
   - Package function
   - Update Lambda code

5. **Deploy ECS** (main only)
   - Update task definition
   - Deploy to ECS
   - Wait for stability

## Security

### Secrets Management

- AWS credentials stored in GitHub Secrets
- Redshift password in Terraform variables (use AWS Secrets Manager in production)
- S3 buckets encrypted with AES256
- VPC isolation for Redshift

### Network Security

- ALB accepts traffic on port 80/443
- ECS tasks only accept traffic from ALB
- Redshift in private subnets
- Security groups restrict access

## Production Checklist

- [ ] Configure custom domain for ALB
- [ ] Enable HTTPS with ACM certificate
- [ ] Set up CloudWatch alarms
- [ ] Configure SNS email subscription
- [ ] Enable AWS Backup for RDS/Redshift
- [ ] Set up VPN for Redshift access
- [ ] Configure WAF rules for ALB
- [ ] Enable AWS Config for compliance
- [ ] Set up cost alerts
- [ ] Document runbooks

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review Terraform state
3. Check GitHub Actions logs
4. Review this deployment guide

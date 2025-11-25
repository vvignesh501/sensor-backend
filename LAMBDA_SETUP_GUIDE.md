# Lambda Function Setup Guide

## Quick Setup (Recommended)

### Step 1: Create Lambda Function in AWS Console

1. **Go to AWS Lambda Console**: https://console.aws.amazon.com/lambda
2. **Click "Create function"**
3. **Configure**:
   - Function name: `sensor-data-processor`
   - Runtime: `Python 3.9`
   - Architecture: `x86_64`
4. **Click "Create function"**
5. **Configure settings**:
   - Memory: 1024 MB
   - Timeout: 5 minutes (300 seconds)
6. **Add environment variables**:
   ```
   SOURCE_BUCKET = sensor-prod-data-vvignesh501-2025
   PROCESSED_BUCKET = sensor-analytics-processed-data
   METADATA_TABLE = sensor-analytics-metadata
   ANOMALY_TOPIC_ARN = arn:aws:sns:us-east-2:989239674490:sensor-anomalies
   ```

### Step 2: Create IAM Role (if needed)

The Lambda needs permissions to:
- Read from S3 source bucket
- Write to S3 processed bucket
- Write to DynamoDB
- Publish to SNS
- Write CloudWatch logs

**Attach these policies**:
- `AWSLambdaBasicExecutionRole` (for logs)
- Custom policy for S3/DynamoDB/SNS (or use the one Terraform creates)

### Step 3: Deploy Infrastructure with Terraform

```bash
cd sensor-backend/terraform
terraform init
terraform plan
terraform apply
```

Terraform will:
- ✅ Reference your existing Lambda (not create it)
- ✅ Create S3 buckets
- ✅ Create DynamoDB table
- ✅ Create SNS topic
- ✅ Set up S3 → Lambda trigger

### Step 4: Deploy Lambda Code via GitHub Actions

Push to main branch:
```bash
git push origin main
```

GitHub Actions will automatically:
- Build Lambda package
- Update Lambda function code
- Deploy to AWS

---

## How It Works

```
┌─────────────────────────────────────────────────────┐
│ AWS Console (One-time)                              │
│ - Create Lambda function shell                     │
│ - Set basic configuration                          │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ Terraform (Infrastructure)                          │
│ - Reference existing Lambda                        │
│ - Create S3, DynamoDB, SNS                         │
│ - Set up triggers and permissions                  │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ GitHub Actions (Code Updates)                       │
│ - Build Lambda package                             │
│ - Update Lambda code                               │
│ - Deploy on every push                             │
└─────────────────────────────────────────────────────┘
```

---

## Terraform Configuration

Your Terraform now uses a **data source** instead of creating the Lambda:

```hcl
# References existing Lambda (doesn't create it)
data "aws_lambda_function" "data_processor" {
  function_name = "sensor-data-processor"
}

# Uses the Lambda ARN in other resources
resource "aws_s3_bucket_notification" "bucket_notification" {
  lambda_function {
    lambda_function_arn = data.aws_lambda_function.data_processor.arn
    events              = ["s3:ObjectCreated:*"]
  }
}
```

**Benefits**:
- ✅ No need to create Lambda ZIP before Terraform
- ✅ Terraform manages infrastructure, not code
- ✅ GitHub Actions handles code deployments
- ✅ Faster Terraform runs

---

## Troubleshooting

### Error: "Function not found"

**Problem**: Lambda doesn't exist yet

**Solution**: Create it in AWS Console first (Step 1 above)

### Error: "Access Denied"

**Problem**: Lambda role doesn't have permissions

**Solution**: 
1. Go to Lambda → Configuration → Permissions
2. Click on the role name
3. Attach required policies

### GitHub Actions fails: "Function not found"

**Problem**: Lambda doesn't exist in the region

**Solution**: Make sure Lambda is created in `us-east-2` region

---

## Alternative: Create Lambda via AWS CLI

If you prefer CLI over Console:

```bash
# Create Lambda function
aws lambda create-function \
  --function-name sensor-data-processor \
  --runtime python3.9 \
  --role arn:aws:iam::989239674490:role/sensor-data-processor-role \
  --handler lambda_data_processor.lambda_handler \
  --timeout 300 \
  --memory-size 1024 \
  --zip-file fileb://dummy.zip \
  --region us-east-2

# Set environment variables
aws lambda update-function-configuration \
  --function-name sensor-data-processor \
  --environment Variables="{SOURCE_BUCKET=sensor-prod-data-vvignesh501-2025,PROCESSED_BUCKET=sensor-analytics-processed-data}" \
  --region us-east-2
```

---

## Summary

**What you need to do**:
1. Create Lambda function in AWS Console (5 minutes)
2. Run `terraform apply` (creates infrastructure)
3. Push code to GitHub (deploys Lambda code)

**What happens automatically**:
- GitHub Actions builds and deploys Lambda code
- Terraform manages all other infrastructure
- S3 triggers Lambda on new files

Your setup is now optimized for fast, reliable deployments! 🚀

# How Terraform Accesses Lambda via IAM

## Overview

Terraform uses **your AWS IAM credentials** to access and manage AWS resources, including your manually-created Lambda function.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Your Computer / GitHub Actions                          │
│                                                          │
│  ┌──────────────┐                                       │
│  │  Terraform   │                                       │
│  │  (Client)    │                                       │
│  └──────┬───────┘                                       │
│         │                                                │
│         │ Uses AWS Credentials                          │
│         │ (AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY)  │
└─────────┼──────────────────────────────────────────────┘
          │
          │ IAM Authentication
          ▼
┌─────────────────────────────────────────────────────────┐
│ AWS Cloud                                                │
│                                                          │
│  ┌──────────────┐         ┌──────────────┐             │
│  │ IAM Service  │────────▶│ Lambda API   │             │
│  │ (Verifies)   │         │              │             │
│  └──────────────┘         └──────┬───────┘             │
│                                   │                      │
│                                   ▼                      │
│                          ┌─────────────────┐            │
│                          │ Your Lambda     │            │
│                          │ sensor-data-    │            │
│                          │ processor       │            │
│                          └─────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

## How It Works

### 1. Terraform Uses Your IAM Credentials

When you run `terraform apply`, Terraform uses your AWS credentials to authenticate:

```bash
# Credentials can come from:
# 1. Environment variables
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-2"

# 2. AWS CLI configuration
aws configure

# 3. IAM role (if running on EC2/ECS)
```

### 2. Terraform Calls AWS APIs

Terraform makes API calls to AWS services:

```hcl
# This Terraform code...
data "aws_lambda_function" "data_processor" {
  function_name = "sensor-data-processor"
}

# ...translates to this AWS API call:
# aws lambda get-function --function-name sensor-data-processor
```

### 3. IAM Verifies Permissions

AWS checks if your IAM user/role has permission to access Lambda:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:GetFunction",
        "lambda:UpdateFunctionConfiguration",
        "lambda:UpdateFunctionCode"
      ],
      "Resource": "arn:aws:lambda:us-east-2:*:function:sensor-data-processor"
    }
  ]
}
```

### 4. Terraform Manages Lambda Configuration

Terraform can:
- ✅ **Read** Lambda function details (via `data` source)
- ✅ **Update** Lambda configuration (IAM role, env vars, timeout)
- ✅ **Create** triggers and permissions
- ❌ **Not update** code (GitHub Actions does this)

## What Terraform Does to Your Lambda

### 1. Reads Lambda Information

```hcl
data "aws_lambda_function" "data_processor" {
  function_name = "sensor-data-processor"
}

# Terraform can now access:
# - data.aws_lambda_function.data_processor.arn
# - data.aws_lambda_function.data_processor.function_name
# - data.aws_lambda_function.data_processor.version
```

### 2. Updates Lambda Configuration

```hcl
resource "null_resource" "update_lambda_config" {
  provisioner "local-exec" {
    command = <<-EOT
      aws lambda update-function-configuration \
        --function-name sensor-data-processor \
        --role ${aws_iam_role.lambda_execution_role.arn} \
        --environment Variables="{...}"
    EOT
  }
}
```

This updates:
- IAM execution role
- Environment variables
- Timeout and memory settings

### 3. Creates Lambda Permissions

```hcl
resource "aws_lambda_permission" "s3_invoke" {
  function_name = data.aws_lambda_function.data_processor.function_name
  action        = "lambda:InvokeFunction"
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.source_data.arn
}
```

This allows S3 to trigger your Lambda.

### 4. Sets Up S3 Trigger

```hcl
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = data.aws_s3_bucket.source_data.id

  lambda_function {
    lambda_function_arn = data.aws_lambda_function.data_processor.arn
    events              = ["s3:ObjectCreated:*"]
  }
}
```

This configures S3 to invoke Lambda when files are uploaded.

## IAM Permissions Required

### For Terraform (Your IAM User/Role)

Your AWS credentials need these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:GetFunction",
        "lambda:UpdateFunctionConfiguration",
        "lambda:AddPermission",
        "lambda:RemovePermission",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PutRolePolicy",
        "s3:CreateBucket",
        "s3:PutBucketNotification",
        "dynamodb:CreateTable",
        "sns:CreateTopic"
      ],
      "Resource": "*"
    }
  ]
}
```

### For Lambda Function (Execution Role)

The Lambda function itself needs these permissions (managed by Terraform):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::sensor-prod-data-vvignesh501-2025/*",
        "arn:aws:s3:::sensor-analytics-processed-data/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/sensor-analytics-metadata"
    },
    {
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:*:*:sensor-anomalies"
    }
  ]
}
```

## Security Best Practices

### 1. Use IAM Roles (Not Root Credentials)

❌ **Bad**: Using root account credentials
```bash
export AWS_ACCESS_KEY_ID="AKIA..." # Root account
```

✅ **Good**: Using IAM user with limited permissions
```bash
export AWS_ACCESS_KEY_ID="AKIA..." # IAM user: terraform-deployer
```

### 2. Principle of Least Privilege

Only grant permissions Terraform actually needs:

```json
{
  "Effect": "Allow",
  "Action": [
    "lambda:GetFunction",
    "lambda:UpdateFunctionConfiguration"
  ],
  "Resource": "arn:aws:lambda:us-east-2:*:function:sensor-data-processor"
}
```

### 3. Use GitHub Secrets for CI/CD

Store credentials securely in GitHub Secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

Never commit credentials to git!

### 4. Rotate Credentials Regularly

Change your AWS access keys every 90 days.

## Troubleshooting

### Error: "Access Denied"

**Problem**: Your IAM user doesn't have permission

**Solution**: Add required permissions to your IAM user/role

```bash
# Check current permissions
aws iam get-user-policy --user-name your-username --policy-name your-policy

# Attach policy
aws iam attach-user-policy \
  --user-name your-username \
  --policy-arn arn:aws:iam::aws:policy/AWSLambdaFullAccess
```

### Error: "Function not found"

**Problem**: Lambda doesn't exist or wrong region

**Solution**: 
1. Check Lambda exists: `aws lambda get-function --function-name sensor-data-processor`
2. Check region: `aws configure get region`

### Error: "Invalid credentials"

**Problem**: AWS credentials expired or incorrect

**Solution**:
```bash
# Verify credentials
aws sts get-caller-identity

# Reconfigure
aws configure
```

## Summary

**How Terraform accesses your Lambda**:
1. Uses your AWS IAM credentials (access key + secret key)
2. Calls AWS Lambda API to read function details
3. Updates Lambda configuration (not code)
4. Creates triggers and permissions

**What you need**:
- ✅ AWS IAM user with Lambda permissions
- ✅ AWS credentials configured locally or in GitHub Secrets
- ✅ Lambda function created in AWS Console
- ✅ Terraform configured to reference the Lambda

Your setup is secure and follows AWS best practices! 🔒

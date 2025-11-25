# Terraform configuration for Sensor Backend Infrastructure

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# S3 Buckets - use existing
data "aws_s3_bucket" "source_data" {
  bucket = "sensor-prod-data-vvignesh501-2025"
}

resource "aws_s3_bucket" "processed_data" {
  bucket = "sensor-analytics-processed-data"
  
  tags = {
    Name        = "Processed Analytics Data"
    Environment = var.environment
  }
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "source_versioning" {
  bucket = data.aws_s3_bucket.source_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "processed_versioning" {
  bucket = aws_s3_bucket.processed_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "source_encryption" {
  bucket = data.aws_s3_bucket.source_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "processed_encryption" {
  bucket = aws_s3_bucket.processed_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# DynamoDB Table for Metadata
resource "aws_dynamodb_table" "sensor_metadata" {
  name           = "sensor-analytics-metadata"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "test_id"

  attribute {
    name = "test_id"
    type = "S"
  }

  attribute {
    name = "processing_timestamp"
    type = "S"
  }

  global_secondary_index {
    name            = "TimestampIndex"
    hash_key        = "processing_timestamp"
    projection_type = "ALL"
  }

  tags = {
    Name        = "Sensor Analytics Metadata"
    Environment = var.environment
  }
}

# SNS Topic for Anomaly Alerts
resource "aws_sns_topic" "anomaly_alerts" {
  name = "sensor-anomalies"

  tags = {
    Name        = "Sensor Anomaly Alerts"
    Environment = var.environment
  }
}

# SNS Topic Subscription (Email)
resource "aws_sns_topic_subscription" "anomaly_email" {
  topic_arn = aws_sns_topic.anomaly_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Note: VPC and ECS resources removed to simplify deployment
# Lambda runs without VPC for faster cold starts and simpler networking
# If VPC is needed later, add it back with proper NAT Gateway configuration

# IAM Role for Lambda
resource "aws_iam_role" "lambda_execution_role" {
  name = "sensor-data-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "sensor-data-processor-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${data.aws_s3_bucket.source_data.arn}/*",
          "${aws_s3_bucket.processed_data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          data.aws_s3_bucket.source_data.arn,
          aws_s3_bucket.processed_data.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.sensor_metadata.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.anomaly_alerts.arn
      }
    ]
  })
}

# Reference existing Lambda function (created manually in AWS Console)
data "aws_lambda_function" "data_processor" {
  function_name = "sensor-data-processor"
}

# Update Lambda function configuration (IAM role, environment variables, etc.)
# This doesn't update the code - GitHub Actions handles code updates
resource "null_resource" "update_lambda_config" {
  triggers = {
    role_arn = aws_iam_role.lambda_execution_role.arn
  }

  provisioner "local-exec" {
    command = <<-EOT
      aws lambda update-function-configuration \
        --function-name sensor-data-processor \
        --role ${aws_iam_role.lambda_execution_role.arn} \
        --timeout 300 \
        --memory-size 1024 \
        --environment Variables="{SOURCE_BUCKET=${data.aws_s3_bucket.source_data.bucket},PROCESSED_BUCKET=${aws_s3_bucket.processed_data.bucket},METADATA_TABLE=${aws_dynamodb_table.sensor_metadata.name},ANOMALY_TOPIC_ARN=${aws_sns_topic.anomaly_alerts.arn}}" \
        --region ${var.aws_region}
    EOT
  }

  depends_on = [
    aws_iam_role.lambda_execution_role,
    aws_iam_role_policy.lambda_policy,
    aws_s3_bucket.processed_data,
    aws_dynamodb_table.sensor_metadata,
    aws_sns_topic.anomaly_alerts
  ]
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/sensor-data-processor"
  retention_in_days = 14
}

# S3 Bucket Notification
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = data.aws_s3_bucket.source_data.id

  lambda_function {
    lambda_function_arn = data.aws_lambda_function.data_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw_data/"
    filter_suffix       = ".npy"
  }

  depends_on = [aws_lambda_permission.s3_invoke]
}

# Lambda Permission for S3
resource "aws_lambda_permission" "s3_invoke" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = data.aws_lambda_function.data_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = data.aws_s3_bucket.source_data.arn
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "sensor_analytics" {
  dashboard_name = "SensorAnalyticsDashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", data.aws_lambda_function.data_processor.function_name],
            [".", "Errors", ".", "."],
            [".", "Invocations", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Performance Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/S3", "BucketSizeBytes", "BucketName", data.aws_s3_bucket.source_data.bucket, "StorageType", "StandardStorage"],
            [".", ".", ".", aws_s3_bucket.processed_data.bucket, ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "S3 Storage Usage"
          period  = 86400
        }
      }
    ]
  })
}

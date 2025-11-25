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
  bucket = data.data.aws_s3_bucket.source_data.id
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
  bucket = data.data.aws_s3_bucket.source_data.id

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

# VPC for ECS
resource "aws_vpc" "sensor_analytics" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "Sensor Analytics VPC"
    Environment = var.environment
  }
}

# Subnets for ECS - use different CIDR to avoid conflicts
resource "aws_subnet" "public_subnet_1" {
  vpc_id                  = aws_vpc.sensor_analytics.id
  cidr_block              = "10.0.10.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "ECS Public Subnet 1"
  }
}

resource "aws_subnet" "public_subnet_2" {
  vpc_id                  = aws_vpc.sensor_analytics.id
  cidr_block              = "10.0.20.0/24"
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = true

  tags = {
    Name = "ECS Public Subnet 2"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "sensor_analytics" {
  vpc_id = aws_vpc.sensor_analytics.id

  tags = {
    Name = "Sensor Analytics IGW"
  }
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.sensor_analytics.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.sensor_analytics.id
  }

  tags = {
    Name = "Public Route Table"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_subnet_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_subnet_2.id
  route_table_id = aws_route_table.public.id
}

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

# Lambda Function
resource "aws_lambda_function" "data_processor" {
  filename         = "sensor_data_processor.zip"
  function_name    = "sensor-data-processor"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "lambda_data_processor.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 1024

  environment {
    variables = {
      SOURCE_BUCKET      = data.aws_s3_bucket.source_data.bucket
      PROCESSED_BUCKET   = aws_s3_bucket.processed_data.bucket
      METADATA_TABLE     = aws_dynamodb_table.sensor_metadata.name
      ANOMALY_TOPIC_ARN  = aws_sns_topic.anomaly_alerts.arn
    }
  }

  tags = {
    Name        = "Sensor Data Processor"
    Environment = var.environment
  }
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
    lambda_function_arn = aws_lambda_function.data_processor.arn
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
  function_name = aws_lambda_function.data_processor.function_name
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
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.data_processor.function_name],
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

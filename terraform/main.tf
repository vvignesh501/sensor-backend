# Terraform configuration for N-Dimensional Data Processing Infrastructure

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

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

# S3 Buckets
resource "aws_s3_bucket" "source_data" {
  bucket = "sensor-prod-data-vvignesh501-2025"
  
  tags = {
    Name        = "Sensor Source Data"
    Environment = var.environment
  }
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
  bucket = aws_s3_bucket.source_data.id
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
  bucket = aws_s3_bucket.source_data.id

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
    name     = "TimestampIndex"
    hash_key = "processing_timestamp"
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

# Redshift Subnet Group
resource "aws_redshift_subnet_group" "sensor_analytics" {
  name       = "sensor-analytics-subnet-group"
  subnet_ids = [aws_subnet.redshift_subnet_1.id, aws_subnet.redshift_subnet_2.id]

  tags = {
    Name        = "Sensor Analytics Subnet Group"
    Environment = var.environment
  }
}

# VPC for Redshift
resource "aws_vpc" "sensor_analytics" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "Sensor Analytics VPC"
    Environment = var.environment
  }
}

# Subnets for Redshift
resource "aws_subnet" "redshift_subnet_1" {
  vpc_id            = aws_vpc.sensor_analytics.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "Redshift Subnet 1"
  }
}

resource "aws_subnet" "redshift_subnet_2" {
  vpc_id            = aws_vpc.sensor_analytics.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name = "Redshift Subnet 2"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "sensor_analytics" {
  vpc_id = aws_vpc.sensor_analytics.id

  tags = {
    Name = "Sensor Analytics IGW"
  }
}

# Redshift Cluster
resource "aws_redshift_cluster" "sensor_analytics" {
  count = var.enable_redshift ? 1 : 0
  
  cluster_identifier      = "sensor-analytics-cluster"
  database_name          = "sensor_analytics"
  master_username        = "admin"
  master_password        = var.redshift_master_password
  node_type              = var.redshift_node_type
  cluster_type           = "single-node"
  
  db_subnet_group_name   = aws_redshift_subnet_group.sensor_analytics.name
  vpc_security_group_ids = [aws_security_group.redshift.id]
  
  skip_final_snapshot = true
  publicly_accessible = false

  tags = merge(var.tags, {
    Name        = "Sensor Analytics Cluster"
    Environment = var.environment
  })
}

# Security Group for Redshift
resource "aws_security_group" "redshift" {
  name_prefix = "redshift-sg"
  vpc_id      = aws_vpc.sensor_analytics.id

  ingress {
    from_port   = 5439
    to_port     = 5439
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "Redshift Security Group"
  }
}

# IAM Role for Redshift S3 Access
resource "aws_iam_role" "redshift_s3_access" {
  name = "redshift-s3-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "redshift.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Redshift S3 Access
resource "aws_iam_role_policy" "redshift_s3_policy" {
  name = "redshift-s3-policy"
  role = aws_iam_role.redshift_s3_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.processed_data.arn,
          "${aws_s3_bucket.processed_data.arn}/*"
        ]
      }
    ]
  })
}

# Attach role to Redshift cluster
resource "aws_redshift_cluster_iam_roles" "sensor_analytics" {
  count = var.enable_redshift ? 1 : 0
  
  cluster_identifier = aws_redshift_cluster.sensor_analytics[0].cluster_identifier
  iam_role_arns     = [aws_iam_role.redshift_s3_access.arn]
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
          "${aws_s3_bucket.source_data.arn}/*",
          "${aws_s3_bucket.processed_data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.source_data.arn,
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
      },
      {
        Effect = "Allow"
        Action = [
          "redshift-data:ExecuteStatement",
          "redshift-data:DescribeStatement",
          "redshift-data:GetStatementResult"
        ]
        Resource = "*"
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
      SOURCE_BUCKET      = aws_s3_bucket.source_data.bucket
      PROCESSED_BUCKET   = aws_s3_bucket.processed_data.bucket
      METADATA_TABLE     = aws_dynamodb_table.sensor_metadata.name
      ANOMALY_TOPIC_ARN  = aws_sns_topic.anomaly_alerts.arn
      REDSHIFT_CLUSTER   = var.enable_redshift ? aws_redshift_cluster.sensor_analytics[0].cluster_identifier : ""
      REDSHIFT_DATABASE  = var.enable_redshift ? aws_redshift_cluster.sensor_analytics[0].database_name : ""
      REDSHIFT_USER      = var.enable_redshift ? aws_redshift_cluster.sensor_analytics[0].master_username : ""
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    aws_cloudwatch_log_group.lambda_logs
  ]

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
  bucket = aws_s3_bucket.source_data.id

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
  source_arn    = aws_s3_bucket.source_data.arn
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
            ["AWS/S3", "BucketSizeBytes", "BucketName", aws_s3_bucket.source_data.bucket, "StorageType", "StandardStorage"],
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

# Outputs
output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.data_processor.arn
}

output "source_bucket_name" {
  description = "Name of the source S3 bucket"
  value       = aws_s3_bucket.source_data.bucket
}

output "processed_bucket_name" {
  description = "Name of the processed data S3 bucket"
  value       = aws_s3_bucket.processed_data.bucket
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB metadata table"
  value       = aws_dynamodb_table.sensor_metadata.name
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for anomaly alerts"
  value       = aws_sns_topic.anomaly_alerts.arn
}

output "cloudwatch_dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.sensor_analytics.dashboard_name}"
}

output "redshift_cluster_endpoint" {
  description = "Redshift cluster endpoint"
  value       = var.enable_redshift ? aws_redshift_cluster.sensor_analytics[0].endpoint : null
}

output "redshift_cluster_id" {
  description = "Redshift cluster identifier"
  value       = var.enable_redshift ? aws_redshift_cluster.sensor_analytics[0].cluster_identifier : null
}
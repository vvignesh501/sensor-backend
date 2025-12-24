# ============================================================================
# AWS IAM Roles for Production - Best Practices
# Zero credentials in code, maximum security
# ============================================================================

# ============================================================================
# 1. ECS Task Execution Role (for ECS to pull images, write logs)
# ============================================================================

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "sensor-backend-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "ECS Task Execution Role"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

# Attach AWS managed policy for ECS task execution
resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ============================================================================
# 2. ECS Task Role (for application to access AWS services)
# ============================================================================

resource "aws_iam_role" "ecs_task_role" {
  name = "sensor-backend-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "ECS Task Role"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

# ============================================================================
# 3. S3 Access Policy (Read/Write to specific bucket)
# ============================================================================

resource "aws_iam_policy" "s3_sensor_data_policy" {
  name        = "sensor-backend-s3-access"
  description = "Allow read/write access to sensor data S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::sensor-data-bucket",
          "arn:aws:s3:::sensor-data-bucket/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = "arn:aws:s3:::sensor-data-bucket"
      }
    ]
  })
}

# Attach S3 policy to task role
resource "aws_iam_role_policy_attachment" "ecs_task_s3_policy" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.s3_sensor_data_policy.arn
}

# ============================================================================
# 4. CloudWatch Logs Policy
# ============================================================================

resource "aws_iam_policy" "cloudwatch_logs_policy" {
  name        = "sensor-backend-cloudwatch-logs"
  description = "Allow writing to CloudWatch Logs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/ecs/sensor-backend*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_cloudwatch_policy" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.cloudwatch_logs_policy.arn
}

# ============================================================================
# 5. RDS Access Policy (for database connections)
# ============================================================================

resource "aws_iam_policy" "rds_access_policy" {
  name        = "sensor-backend-rds-access"
  description = "Allow RDS database access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "rds-db:connect"
        ]
        Resource = "arn:aws:rds-db:*:*:dbuser:*/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_rds_policy" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.rds_access_policy.arn
}

# ============================================================================
# 6. Secrets Manager Policy (for database credentials)
# ============================================================================

resource "aws_iam_policy" "secrets_manager_policy" {
  name        = "sensor-backend-secrets-access"
  description = "Allow reading secrets from Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "arn:aws:secretsmanager:*:*:secret:sensor-backend/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_secrets_policy" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.secrets_manager_policy.arn
}

# ============================================================================
# 7. Lambda Execution Role (for Lambda functions)
# ============================================================================

resource "aws_iam_role" "lambda_execution_role" {
  name = "sensor-backend-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "Lambda Execution Role"
    Environment = "production"
  }
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Attach S3 access to Lambda
resource "aws_iam_role_policy_attachment" "lambda_s3_access" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.s3_sensor_data_policy.arn
}

# ============================================================================
# 8. EC2 Instance Profile (for EC2 instances)
# ============================================================================

resource "aws_iam_role" "ec2_instance_role" {
  name = "sensor-backend-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "EC2 Instance Role"
    Environment = "production"
  }
}

# Create instance profile
resource "aws_iam_instance_profile" "ec2_instance_profile" {
  name = "sensor-backend-ec2-profile"
  role = aws_iam_role.ec2_instance_role.name
}

# Attach policies to EC2 role
resource "aws_iam_role_policy_attachment" "ec2_s3_access" {
  role       = aws_iam_role.ec2_instance_role.name
  policy_arn = aws_iam_policy.s3_sensor_data_policy.arn
}

resource "aws_iam_role_policy_attachment" "ec2_cloudwatch_access" {
  role       = aws_iam_role.ec2_instance_role.name
  policy_arn = aws_iam_policy.cloudwatch_logs_policy.arn
}

# ============================================================================
# 9. Outputs (for use in other Terraform modules)
# ============================================================================

output "ecs_task_execution_role_arn" {
  description = "ARN of ECS task execution role"
  value       = aws_iam_role.ecs_task_execution_role.arn
}

output "ecs_task_role_arn" {
  description = "ARN of ECS task role"
  value       = aws_iam_role.ecs_task_role.arn
}

output "lambda_execution_role_arn" {
  description = "ARN of Lambda execution role"
  value       = aws_iam_role.lambda_execution_role.arn
}

output "ec2_instance_profile_name" {
  description = "Name of EC2 instance profile"
  value       = aws_iam_instance_profile.ec2_instance_profile.name
}

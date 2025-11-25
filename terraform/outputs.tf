output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = data.aws_lambda_function.data_processor.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = data.aws_lambda_function.data_processor.function_name
}

output "source_bucket_name" {
  description = "Name of the source S3 bucket"
  value       = data.aws_s3_bucket.source_data.bucket
}

output "source_bucket_arn" {
  description = "ARN of the source S3 bucket"
  value       = data.aws_s3_bucket.source_data.arn
}

output "processed_bucket_name" {
  description = "Name of the processed data S3 bucket"
  value       = aws_s3_bucket.processed_data.bucket
}

output "processed_bucket_arn" {
  description = "ARN of the processed data S3 bucket"
  value       = aws_s3_bucket.processed_data.arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB metadata table"
  value       = aws_dynamodb_table.sensor_metadata.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB metadata table"
  value       = aws_dynamodb_table.sensor_metadata.arn
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for anomaly alerts"
  value       = aws_sns_topic.anomaly_alerts.arn
}

output "cloudwatch_dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.sensor_analytics.dashboard_name}"
}



output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution_role.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for Lambda"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

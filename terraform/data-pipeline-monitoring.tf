# Data Pipeline Monitoring Dashboard
# Tracks sensor data flow through PostgreSQL, Kafka, and S3

# CloudWatch Dashboard for Data Pipeline
resource "aws_cloudwatch_dashboard" "data_pipeline_dashboard" {
  dashboard_name = "sensor-data-pipeline"

  dashboard_body = jsonencode({
    widgets = [
      # Pipeline Success Rate
      {
        type = "metric"
        properties = {
          metrics = [
            ["SensorBackend/DataPipeline", "SuccessCount", { stat = "Sum", label = "Successful Operations" }],
            [".", "FailureCount", { stat = "Sum", label = "Failed Operations" }]
          ]
          period = 60
          stat   = "Sum"
          region = var.aws_region
          title  = "Pipeline Success vs Failures"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 12
        height = 6
        x      = 0
        y      = 0
      },
      # Failure Rate by Stage
      {
        type = "metric"
        properties = {
          metrics = [
            ["SensorBackend/DataPipeline", "FailureCount", { stat = "Sum", label = "Ingestion Failures" }, { dimensions = { Stage = "ingestion" } }],
            ["...", { dimensions = { Stage = "postgres_write" }, label = "PostgreSQL Failures" }],
            ["...", { dimensions = { Stage = "kafka_publish" }, label = "Kafka Failures" }],
            ["...", { dimensions = { Stage = "s3_upload" }, label = "S3 Failures" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Failures by Pipeline Stage"
        }
        width  = 12
        height = 6
        x      = 12
        y      = 0
      },
      # Processing Latency by Stage
      {
        type = "metric"
        properties = {
          metrics = [
            ["SensorBackend/DataPipeline", "ProcessingLatency", { stat = "Average", label = "Avg Latency" }],
            ["...", { stat = "p99", label = "p99 Latency" }]
          ]
          period = 60
          stat   = "Average"
          region = var.aws_region
          title  = "Processing Latency (ms)"
        }
        width  = 12
        height = 6
        x      = 0
        y      = 6
      },
      # Data Throughput
      {
        type = "metric"
        properties = {
          metrics = [
            ["SensorBackend/DataPipeline", "DataSize", { stat = "Sum", label = "Total Data Processed" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Data Throughput (Bytes)"
        }
        width  = 12
        height = 6
        x      = 12
        y      = 6
      },
      # PostgreSQL Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["SensorBackend/DataPipeline", "SuccessCount", { dimensions = { Stage = "postgres_write" }, stat = "Sum", label = "Successful Writes" }],
            [".", "FailureCount", { dimensions = { Stage = "postgres_write" }, stat = "Sum", label = "Failed Writes" }]
          ]
          period = 60
          stat   = "Sum"
          region = var.aws_region
          title  = "PostgreSQL Write Operations"
        }
        width  = 8
        height = 6
        x      = 0
        y      = 12
      },
      # Kafka Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["SensorBackend/DataPipeline", "SuccessCount", { dimensions = { Stage = "kafka_publish" }, stat = "Sum", label = "Successful Publishes" }],
            [".", "FailureCount", { dimensions = { Stage = "kafka_publish" }, stat = "Sum", label = "Failed Publishes" }],
            [".", "QueueDepth", { stat = "Average", label = "Queue Depth" }]
          ]
          period = 60
          stat   = "Sum"
          region = var.aws_region
          title  = "Kafka Operations"
        }
        width  = 8
        height = 6
        x      = 8
        y      = 12
      },
      # S3 Upload Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["SensorBackend/DataPipeline", "SuccessCount", { dimensions = { Stage = "s3_upload" }, stat = "Sum", label = "Successful Uploads" }],
            [".", "FailureCount", { dimensions = { Stage = "s3_upload" }, stat = "Sum", label = "Failed Uploads" }]
          ]
          period = 60
          stat   = "Sum"
          region = var.aws_region
          title  = "S3 Upload Operations"
        }
        width  = 8
        height = 6
        x      = 16
        y      = 12
      },
      # Failure Types Distribution
      {
        type = "metric"
        properties = {
          metrics = [
            ["SensorBackend/DataPipeline", "FailureCount", { dimensions = { FailureType = "connection_error" }, stat = "Sum", label = "Connection Errors" }],
            ["...", { dimensions = { FailureType = "timeout" }, label = "Timeouts" }],
            ["...", { dimensions = { FailureType = "validation_error" }, label = "Validation Errors" }],
            ["...", { dimensions = { FailureType = "network_error" }, label = "Network Errors" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Failure Types"
        }
        width  = 12
        height = 6
        x      = 0
        y      = 18
      },
      # Retry Attempts
      {
        type = "metric"
        properties = {
          metrics = [
            ["SensorBackend/DataPipeline", "RetryAttempts", { stat = "Sum", label = "Total Retries" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Retry Attempts"
        }
        width  = 12
        height = 6
        x      = 12
        y      = 18
      },
      # Recent Pipeline Errors
      {
        type = "log"
        properties = {
          query   = "SOURCE '/ecs/sensor-app'\n| fields @timestamp, @message\n| filter @message like /FAILURE_TRACKED/ or @message like /ERROR/\n| sort @timestamp desc\n| limit 50"
          region  = var.aws_region
          title   = "Recent Pipeline Errors"
        }
        width  = 24
        height = 8
        x      = 0
        y      = 24
      }
    ]
  })
}

# Alarms for Data Pipeline

# High Failure Rate Alarm
resource "aws_cloudwatch_metric_alarm" "pipeline_high_failure_rate" {
  alarm_name          = "sensor-pipeline-high-failure-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = 10
  alarm_description   = "Alert when pipeline failure rate is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "failure_rate"
    expression  = "(failures / (successes + failures)) * 100"
    label       = "Failure Rate %"
    return_data = true
  }

  metric_query {
    id = "failures"
    metric {
      namespace   = "SensorBackend/DataPipeline"
      metric_name = "FailureCount"
      period      = 300
      stat        = "Sum"
    }
  }

  metric_query {
    id = "successes"
    metric {
      namespace   = "SensorBackend/DataPipeline"
      metric_name = "SuccessCount"
      period      = 300
      stat        = "Sum"
    }
  }
}

# PostgreSQL Write Failures
resource "aws_cloudwatch_metric_alarm" "postgres_write_failures" {
  alarm_name          = "sensor-postgres-write-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FailureCount"
  namespace           = "SensorBackend/DataPipeline"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert on PostgreSQL write failures"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Stage = "postgres_write"
  }
}

# Kafka Publish Failures
resource "aws_cloudwatch_metric_alarm" "kafka_publish_failures" {
  alarm_name          = "sensor-kafka-publish-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FailureCount"
  namespace           = "SensorBackend/DataPipeline"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert on Kafka publish failures"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Stage = "kafka_publish"
  }
}

# S3 Upload Failures
resource "aws_cloudwatch_metric_alarm" "s3_upload_failures" {
  alarm_name          = "sensor-s3-upload-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FailureCount"
  namespace           = "SensorBackend/DataPipeline"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert on S3 upload failures"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Stage = "s3_upload"
  }
}

# High Processing Latency
resource "aws_cloudwatch_metric_alarm" "pipeline_high_latency" {
  alarm_name          = "sensor-pipeline-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ProcessingLatency"
  namespace           = "SensorBackend/DataPipeline"
  period              = 300
  statistic           = "Average"
  threshold           = 5000
  alarm_description   = "Alert when processing latency exceeds 5 seconds"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"
}

# CloudWatch Log Insights Queries for Data Pipeline

resource "aws_cloudwatch_query_definition" "pipeline_failures" {
  name = "sensor-pipeline-failures"

  log_group_names = [
    aws_cloudwatch_log_group.ecs_app_logs.name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /FAILURE_TRACKED/
    | parse @message /Stage: (?<stage>\w+)/
    | parse @message /FailureType: (?<failure_type>\w+)/
    | parse @message /Sensor: (?<sensor_id>[\w-]+)/
    | stats count() by stage, failure_type
    | sort count desc
  QUERY
}

resource "aws_cloudwatch_query_definition" "postgres_errors" {
  name = "sensor-postgres-errors"

  log_group_names = [
    aws_cloudwatch_log_group.ecs_app_logs.name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /postgres/ and (@message like /ERROR/ or @message like /Failed/)
    | sort @timestamp desc
    | limit 100
  QUERY
}

resource "aws_cloudwatch_query_definition" "kafka_errors" {
  name = "sensor-kafka-errors"

  log_group_names = [
    aws_cloudwatch_log_group.ecs_app_logs.name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /kafka/ and (@message like /ERROR/ or @message like /Failed/)
    | sort @timestamp desc
    | limit 100
  QUERY
}

resource "aws_cloudwatch_query_definition" "s3_errors" {
  name = "sensor-s3-errors"

  log_group_names = [
    aws_cloudwatch_log_group.ecs_app_logs.name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /s3/ and (@message like /ERROR/ or @message like /Failed/)
    | sort @timestamp desc
    | limit 100
  QUERY
}

resource "aws_cloudwatch_query_definition" "pipeline_latency_analysis" {
  name = "sensor-pipeline-latency"

  log_group_names = [
    aws_cloudwatch_log_group.ecs_app_logs.name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /ProcessingLatency/
    | parse @message /Stage: (?<stage>\w+)/
    | parse @message /duration[:\s]+(?<duration>\d+)/
    | stats avg(duration), max(duration), min(duration) by stage
  QUERY
}

# Outputs
output "data_pipeline_dashboard_url" {
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.data_pipeline_dashboard.dashboard_name}"
  description = "URL to Data Pipeline Dashboard"
}

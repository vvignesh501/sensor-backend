# CloudWatch Monitoring and Alarms for ECS and ALB

# CloudWatch Dashboard for Real-Time Monitoring
resource "aws_cloudwatch_dashboard" "app_dashboard" {
  dashboard_name = "sensor-app-monitoring"

  dashboard_body = jsonencode({
    widgets = [
      # ECS CPU Utilization
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", { stat = "Average", label = "CPU Average" }],
            ["...", { stat = "Maximum", label = "CPU Max" }]
          ]
          period = 60
          stat   = "Average"
          region = var.aws_region
          title  = "ECS CPU Utilization"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
        width  = 12
        height = 6
        x      = 0
        y      = 0
      },
      # ECS Memory Utilization
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "MemoryUtilization", { stat = "Average", label = "Memory Average" }],
            ["...", { stat = "Maximum", label = "Memory Max" }]
          ]
          period = 60
          stat   = "Average"
          region = var.aws_region
          title  = "ECS Memory Utilization"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
        width  = 12
        height = 6
        x      = 12
        y      = 0
      },
      # ALB Request Count
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", { stat = "Sum", label = "Total Requests" }]
          ]
          period = 60
          stat   = "Sum"
          region = var.aws_region
          title  = "ALB Request Count"
        }
        width  = 12
        height = 6
        x      = 0
        y      = 6
      },
      # ALB Response Time
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", { stat = "Average", label = "Avg Response Time" }],
            ["...", { stat = "p99", label = "p99 Response Time" }]
          ]
          period = 60
          stat   = "Average"
          region = var.aws_region
          title  = "ALB Response Time (seconds)"
        }
        width  = 12
        height = 6
        x      = 12
        y      = 6
      },
      # ALB Target Health
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "HealthyHostCount", { stat = "Average", label = "Healthy Targets" }],
            [".", "UnHealthyHostCount", { stat = "Average", label = "Unhealthy Targets" }]
          ]
          period = 60
          stat   = "Average"
          region = var.aws_region
          title  = "Target Health Status"
        }
        width  = 12
        height = 6
        x      = 0
        y      = 12
      },
      # HTTP Status Codes
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_2XX_Count", { stat = "Sum", label = "2XX Success" }],
            [".", "HTTPCode_Target_4XX_Count", { stat = "Sum", label = "4XX Client Error" }],
            [".", "HTTPCode_Target_5XX_Count", { stat = "Sum", label = "5XX Server Error" }]
          ]
          period = 60
          stat   = "Sum"
          region = var.aws_region
          title  = "HTTP Status Codes"
        }
        width  = 12
        height = 6
        x      = 12
        y      = 12
      },
      # ECS Task Count
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "RunningTaskCount", { stat = "Average", label = "Running Tasks" }],
            [".", "DesiredTaskCount", { stat = "Average", label = "Desired Tasks" }]
          ]
          period = 60
          stat   = "Average"
          region = var.aws_region
          title  = "ECS Task Count"
        }
        width  = 12
        height = 6
        x      = 0
        y      = 18
      },
      # RDS CPU
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", { stat = "Average", label = "RDS CPU" }]
          ]
          period = 60
          stat   = "Average"
          region = var.aws_region
          title  = "RDS CPU Utilization"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
        width  = 12
        height = 6
        x      = 12
        y      = 18
      },
      # Recent Logs
      {
        type = "log"
        properties = {
          query   = "SOURCE '/ecs/sensor-app'\n| fields @timestamp, @message\n| sort @timestamp desc\n| limit 100"
          region  = var.aws_region
          title   = "Recent Application Logs"
        }
        width  = 24
        height = 6
        x      = 0
        y      = 24
      }
    ]
  })
}

# CloudWatch Alarms

# High CPU Alarm
resource "aws_cloudwatch_metric_alarm" "ecs_high_cpu" {
  alarm_name          = "sensor-app-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This metric monitors ECS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.app_cluster.name
    ServiceName = aws_ecs_service.app_service.name
  }
}

# High Memory Alarm
resource "aws_cloudwatch_metric_alarm" "ecs_high_memory" {
  alarm_name          = "sensor-app-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This metric monitors ECS memory utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.app_cluster.name
    ServiceName = aws_ecs_service.app_service.name
  }
}

# High Response Time Alarm
resource "aws_cloudwatch_metric_alarm" "alb_high_response_time" {
  alarm_name          = "sensor-app-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 2.0
  alarm_description   = "This metric monitors ALB response time"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = aws_lb.app_alb.arn_suffix
  }
}

# Unhealthy Target Alarm
resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_targets" {
  alarm_name          = "sensor-app-unhealthy-targets"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 0
  alarm_description   = "Alert when targets become unhealthy"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = aws_lb.app_alb.arn_suffix
    TargetGroup  = aws_lb_target_group.app_tg.arn_suffix
  }
}

# High 5XX Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "alb_high_5xx_errors" {
  alarm_name          = "sensor-app-high-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert on high 5XX error rate"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.app_alb.arn_suffix
  }
}

# RDS High CPU Alarm
resource "aws_cloudwatch_metric_alarm" "rds_high_cpu" {
  alarm_name          = "sensor-rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Alert when RDS CPU is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "sensor-app-alerts"
}

resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Log Insights Queries (saved queries)
resource "aws_cloudwatch_query_definition" "error_logs" {
  name = "sensor-app-errors"

  log_group_names = [
    aws_cloudwatch_log_group.ecs_app_logs.name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /ERROR/ or @message like /Exception/ or @message like /Failed/
    | sort @timestamp desc
    | limit 100
  QUERY
}

resource "aws_cloudwatch_query_definition" "slow_requests" {
  name = "sensor-app-slow-requests"

  log_group_names = [
    aws_cloudwatch_log_group.ecs_app_logs.name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /duration/ or @message like /response_time/
    | parse @message /duration[:\s]+(?<duration>\d+)/
    | filter duration > 1000
    | sort @timestamp desc
    | limit 50
  QUERY
}

resource "aws_cloudwatch_query_definition" "request_summary" {
  name = "sensor-app-request-summary"

  log_group_names = [
    aws_cloudwatch_log_group.ecs_app_logs.name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /GET/ or @message like /POST/ or @message like /PUT/ or @message like /DELETE/
    | stats count() by bin(5m)
  QUERY
}

# Enable Container Insights for ECS
resource "aws_ecs_cluster_capacity_providers" "app_cluster_capacity" {
  cluster_name = aws_ecs_cluster.app_cluster.name

  capacity_providers = ["FARGATE"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
    base              = 1
  }
}

# Update ECS Cluster to enable Container Insights
resource "aws_ecs_cluster" "app_cluster_with_insights" {
  name = aws_ecs_cluster.app_cluster.name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# Outputs
output "cloudwatch_dashboard_url" {
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.app_dashboard.dashboard_name}"
  description = "URL to CloudWatch Dashboard"
}

output "cloudwatch_logs_url" {
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#logsV2:log-groups/log-group/${replace(aws_cloudwatch_log_group.ecs_app_logs.name, "/", "$252F")}"
  description = "URL to CloudWatch Logs"
}

output "sns_topic_arn" {
  value       = aws_sns_topic.alerts.arn
  description = "SNS Topic ARN for alerts"
}

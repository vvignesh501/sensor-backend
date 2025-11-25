# Auto-Scaling Configuration for ECS Service

# Auto-Scaling Target
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 10  # Maximum 10 instances
  min_capacity       = 1   # Minimum 1 instance
  resource_id        = "service/${aws_ecs_cluster.app_cluster.name}/${aws_ecs_service.app_service.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Scale UP Policy - CPU Based
resource "aws_appautoscaling_policy" "ecs_scale_up_cpu" {
  name               = "sensor-app-scale-up-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0  # Scale up when CPU > 70%
    scale_in_cooldown  = 300   # Wait 5 min before scaling down
    scale_out_cooldown = 60    # Wait 1 min before scaling up again
  }
}

# Scale UP Policy - Memory Based
resource "aws_appautoscaling_policy" "ecs_scale_up_memory" {
  name               = "sensor-app-scale-up-memory"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = 80.0  # Scale up when Memory > 80%
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Scale UP Policy - Request Count Based (ALB)
resource "aws_appautoscaling_policy" "ecs_scale_up_requests" {
  name               = "sensor-app-scale-up-requests"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = "${aws_lb.app_alb.arn_suffix}/${aws_lb_target_group.app_tg.arn_suffix}"
    }
    target_value       = 1000.0  # Scale up when > 1000 requests/target/minute
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# CloudWatch Alarms for Monitoring
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "sensor-app-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 70
  alarm_description   = "This metric monitors ECS CPU utilization"
  alarm_actions       = []  # Add SNS topic ARN for notifications

  dimensions = {
    ClusterName = aws_ecs_cluster.app_cluster.name
    ServiceName = aws_ecs_service.app_service.name
  }
}

resource "aws_cloudwatch_metric_alarm" "high_memory" {
  alarm_name          = "sensor-app-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This metric monitors ECS memory utilization"
  alarm_actions       = []

  dimensions = {
    ClusterName = aws_ecs_cluster.app_cluster.name
    ServiceName = aws_ecs_service.app_service.name
  }
}

# Outputs
output "autoscaling_min_capacity" {
  value       = aws_appautoscaling_target.ecs_target.min_capacity
  description = "Minimum number of ECS tasks"
}

output "autoscaling_max_capacity" {
  value       = aws_appautoscaling_target.ecs_target.max_capacity
  description = "Maximum number of ECS tasks"
}

# High-Load Scaling Configuration
# Optimized for 1000+ concurrent requests with vertical + horizontal scaling

# ============================================================================
# VERTICAL SCALING - Larger Task Definitions
# ============================================================================

# High-Performance Task Definition (Vertical Scaling)
resource "aws_ecs_task_definition" "app_task_high_performance" {
  family                   = "sensor-app-high-perf"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"    # 1 vCPU (4x increase from 256)
  memory                   = "2048"    # 2 GB (4x increase from 512)
  execution_role_arn       = aws_iam_role.ecs_app_execution_role.arn

  container_definitions = jsonencode([
    {
      name  = "sensor-app"
      image = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/sensor-backend:latest"
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "DATABASE_URL"
          value = "postgresql://postgres:postgresql9891@${aws_db_instance.postgres.endpoint}/sensordb"
        },
        {
          name  = "WORKERS"
          value = "4"  # 4 Uvicorn workers for parallel processing
        },
        {
          name  = "MAX_CONNECTIONS"
          value = "100"  # Database connection pool
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/sensor-app"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# ============================================================================
# HORIZONTAL SCALING - More Instances
# ============================================================================

# Enhanced Auto-Scaling Target
resource "aws_appautoscaling_target" "ecs_target_high_load" {
  max_capacity       = 20  # Up to 20 tasks (from 10)
  min_capacity       = 3   # Start with 3 for HA (from 1)
  resource_id        = "service/${aws_ecs_cluster.app_cluster.name}/${aws_ecs_service.app_service.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Aggressive CPU Scaling (for burst traffic)
resource "aws_appautoscaling_policy" "ecs_scale_aggressive_cpu" {
  name               = "sensor-app-aggressive-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target_high_load.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target_high_load.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target_high_load.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 60.0  # Scale at 60% (more aggressive)
    scale_in_cooldown  = 180   # 3 min cooldown
    scale_out_cooldown = 30    # 30 sec for fast scale-out
  }
}

# Request-Based Scaling (Primary metric for 1000 req/s)
resource "aws_appautoscaling_policy" "ecs_scale_request_based" {
  name               = "sensor-app-request-based-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target_high_load.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target_high_load.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target_high_load.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = "${aws_lb.app_alb.arn_suffix}/${aws_lb_target_group.app_tg.arn_suffix}"
    }
    target_value       = 500.0  # 500 requests per target per minute
    scale_in_cooldown  = 180
    scale_out_cooldown = 30
  }
}

# Step Scaling for Extreme Load (backup policy)
resource "aws_appautoscaling_policy" "ecs_step_scaling" {
  name               = "sensor-app-step-scaling"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.ecs_target_high_load.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target_high_load.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target_high_load.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "PercentChangeInCapacity"
    cooldown                = 60
    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_lower_bound = 0
      metric_interval_upper_bound = 10
      scaling_adjustment          = 10  # Add 10% capacity
    }

    step_adjustment {
      metric_interval_lower_bound = 10
      metric_interval_upper_bound = 20
      scaling_adjustment          = 20  # Add 20% capacity
    }

    step_adjustment {
      metric_interval_lower_bound = 20
      scaling_adjustment          = 30  # Add 30% capacity
    }
  }
}

# CloudWatch Alarm for Step Scaling
resource "aws_cloudwatch_metric_alarm" "extreme_load" {
  alarm_name          = "sensor-app-extreme-load"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "Trigger step scaling for extreme load"
  alarm_actions       = [aws_appautoscaling_policy.ecs_step_scaling.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.app_cluster.name
    ServiceName = aws_ecs_service.app_service.name
  }
}

# ============================================================================
# DATABASE SCALING (Vertical)
# ============================================================================

# Larger RDS Instance for High Load
resource "aws_db_instance" "postgres_high_performance" {
  identifier           = "sensor-postgres-high-perf"
  engine               = "postgres"
  instance_class       = "db.t3.medium"  # Upgraded from db.t3.micro
  allocated_storage    = 100             # 100GB storage
  storage_type         = "gp3"           # GP3 for better IOPS
  iops                 = 3000            # Provisioned IOPS
  
  db_name  = "sensordb"
  username = "postgres"
  password = "postgresql9891"
  
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  
  publicly_accessible     = false
  skip_final_snapshot     = true
  backup_retention_period = 7
  
  # Performance optimizations
  max_allocated_storage = 200  # Auto-scaling storage
  
  performance_insights_enabled    = true
  performance_insights_retention_period = 7
  
  tags = {
    Name = "Sensor PostgreSQL High Performance"
  }
}

# Read Replica for Load Distribution
resource "aws_db_instance" "postgres_read_replica" {
  identifier          = "sensor-postgres-read-replica"
  replicate_source_db = aws_db_instance.postgres_high_performance.identifier
  instance_class      = "db.t3.medium"
  
  publicly_accessible = false
  skip_final_snapshot = true
  
  tags = {
    Name = "Sensor PostgreSQL Read Replica"
  }
}

# ============================================================================
# LOAD BALANCER OPTIMIZATIONS
# ============================================================================

# Enhanced Target Group with Connection Draining
resource "aws_lb_target_group" "app_tg_optimized" {
  name        = "sensor-app-tg-optimized"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.app_vpc.id
  target_type = "ip"

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  deregistration_delay = 30  # Fast connection draining

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }

  tags = {
    Name = "Sensor App Target Group Optimized"
  }
}

# ============================================================================
# MONITORING FOR HIGH LOAD
# ============================================================================

# High Request Rate Alarm
resource "aws_cloudwatch_metric_alarm" "high_request_rate" {
  alarm_name          = "sensor-app-high-request-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "RequestCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 50000  # 50k requests per minute
  alarm_description   = "Alert when request rate is very high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = aws_lb.app_alb.arn_suffix
  }
}

# Task Scaling Alarm
resource "aws_cloudwatch_metric_alarm" "max_tasks_reached" {
  alarm_name          = "sensor-app-max-tasks-reached"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "DesiredTaskCount"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 18  # Alert when near max (20)
  alarm_description   = "Alert when approaching max task count"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.app_cluster.name
    ServiceName = aws_ecs_service.app_service.name
  }
}

# ============================================================================
# OUTPUTS
# ============================================================================

output "high_load_config" {
  value = {
    min_tasks           = aws_appautoscaling_target.ecs_target_high_load.min_capacity
    max_tasks           = aws_appautoscaling_target.ecs_target_high_load.max_capacity
    task_cpu            = "1024"
    task_memory         = "2048"
    workers_per_task    = 4
    max_concurrent_reqs = "~1000 per task"
    total_capacity      = "~20,000 concurrent requests"
  }
  description = "High-load scaling configuration summary"
}

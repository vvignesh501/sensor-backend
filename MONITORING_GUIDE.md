# AWS Real-Time Monitoring Guide

Complete guide for monitoring your sensor backend infrastructure with CloudWatch, ALB, ECS, and RDS metrics.

---

## 📊 Overview

This monitoring setup provides:
- **Real-time dashboards** for CPU, memory, requests, and response times
- **Automated alarms** for critical thresholds
- **Log streaming** from ECS containers
- **Email notifications** via SNS
- **Custom CloudWatch queries** for troubleshooting

---

## 🚀 Quick Start

### 1. Deploy Monitoring Infrastructure

```bash
cd sensor-backend/terraform

# Deploy monitoring resources
terraform apply -target=aws_cloudwatch_dashboard.app_dashboard
terraform apply -target=aws_cloudwatch_metric_alarm.ecs_high_cpu
terraform apply -target=aws_sns_topic.alerts

# Or deploy everything
terraform apply
```

### 2. Configure Email Alerts

Update `terraform/variables.tf`:
```hcl
variable "alert_email" {
  default = "your-email@example.com"
}
```

Then apply:
```bash
terraform apply
```

**Important**: Check your email and confirm the SNS subscription!

### 3. Access CloudWatch Dashboard

```bash
# Get dashboard URL
terraform output cloudwatch_dashboard_url

# Or manually navigate to:
# https://console.aws.amazon.com/cloudwatch/home?region=us-east-2#dashboards:name=sensor-app-monitoring
```

---

## 🛠️ Monitoring Tools

### Tool 1: Python Real-Time Dashboard (Recommended)

Beautiful terminal-based dashboard with live metrics:

```bash
# Install boto3 if not already installed
pip install boto3

# Run the dashboard
python3 scripts/monitor_dashboard.py

# Or make it executable
chmod +x scripts/monitor_dashboard.py
./scripts/monitor_dashboard.py
```

**Features**:
- ✅ Live CPU/Memory metrics
- ✅ ALB request counts and response times
- ✅ RDS database metrics
- ✅ Active alarms
- ✅ Recent logs with color coding
- ✅ Auto-refresh every 5 seconds

### Tool 2: Bash Monitoring Script

Lightweight shell script for quick checks:

```bash
chmod +x scripts/monitor_realtime.sh
./scripts/monitor_realtime.sh
```

### Tool 3: Live Log Streaming

Stream logs in real-time with color coding:

```bash
chmod +x scripts/stream_logs.sh

# Stream all logs
./scripts/stream_logs.sh

# Filter for errors only
./scripts/stream_logs.sh "ERROR"

# Filter for specific patterns
./scripts/stream_logs.sh "sensor"
```

---

## 📈 CloudWatch Dashboard

### Widgets Included

1. **ECS CPU Utilization** - Average and maximum CPU usage
2. **ECS Memory Utilization** - Average and maximum memory usage
3. **ALB Request Count** - Total requests per minute
4. **ALB Response Time** - Average and p99 latency
5. **Target Health** - Healthy vs unhealthy targets
6. **HTTP Status Codes** - 2XX, 4XX, 5XX counts
7. **ECS Task Count** - Running vs desired tasks
8. **RDS CPU** - Database CPU utilization
9. **Recent Logs** - Last 100 log entries

### Access Dashboard

```bash
# Via AWS Console
aws cloudwatch get-dashboard \
  --dashboard-name sensor-app-monitoring \
  --region us-east-2

# Or use the URL from terraform output
terraform output cloudwatch_dashboard_url
```

---

## 🚨 CloudWatch Alarms

### Configured Alarms

| Alarm Name | Metric | Threshold | Action |
|------------|--------|-----------|--------|
| `sensor-app-high-cpu` | ECS CPU | > 80% for 2 min | Email alert |
| `sensor-app-high-memory` | ECS Memory | > 80% for 2 min | Email alert |
| `sensor-app-high-response-time` | ALB Response Time | > 2s for 2 min | Email alert |
| `sensor-app-unhealthy-targets` | Unhealthy Hosts | > 0 | Email alert |
| `sensor-app-high-5xx-errors` | 5XX Errors | > 10 per min | Email alert |
| `sensor-rds-high-cpu` | RDS CPU | > 80% for 5 min | Email alert |

### Check Alarm Status

```bash
# List all alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix "sensor-app" \
  --region us-east-2

# Check alarms in ALARM state
aws cloudwatch describe-alarms \
  --alarm-name-prefix "sensor-app" \
  --state-value ALARM \
  --region us-east-2
```

### Test Alarms

```bash
# Manually set alarm state (for testing)
aws cloudwatch set-alarm-state \
  --alarm-name sensor-app-high-cpu \
  --state-value ALARM \
  --state-reason "Testing alarm notification" \
  --region us-east-2
```

---

## 📋 CloudWatch Logs Insights

### Saved Queries

Three pre-configured queries are available:

#### 1. Error Logs
```sql
fields @timestamp, @message
| filter @message like /ERROR/ or @message like /Exception/ or @message like /Failed/
| sort @timestamp desc
| limit 100
```

#### 2. Slow Requests
```sql
fields @timestamp, @message
| filter @message like /duration/ or @message like /response_time/
| parse @message /duration[:\s]+(?<duration>\d+)/
| filter duration > 1000
| sort @timestamp desc
| limit 50
```

#### 3. Request Summary
```sql
fields @timestamp, @message
| filter @message like /GET/ or @message like /POST/ or @message like /PUT/ or @message like /DELETE/
| stats count() by bin(5m)
```

### Run Queries

```bash
# Via AWS Console
# Navigate to CloudWatch > Logs Insights
# Select log group: /ecs/sensor-app
# Choose saved query or write custom query

# Via CLI
aws logs start-query \
  --log-group-name /ecs/sensor-app \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | limit 20' \
  --region us-east-2
```

---

## 📊 Key Metrics to Monitor

### ECS Service Metrics

```bash
# CPU Utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ClusterName,Value=sensor-app-cluster Name=ServiceName,Value=sensor-app-service \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average Maximum \
  --region us-east-2

# Memory Utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ClusterName,Value=sensor-app-cluster Name=ServiceName,Value=sensor-app-service \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average Maximum \
  --region us-east-2
```

### ALB Metrics

```bash
# Get ALB ARN suffix first
ALB_ARN=$(aws elbv2 describe-load-balancers \
  --names sensor-app-alb \
  --region us-east-2 \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)

ALB_SUFFIX=$(echo $ALB_ARN | cut -d':' -f6 | cut -d'/' -f2-)

# Request Count
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name RequestCount \
  --dimensions Name=LoadBalancer,Value=$ALB_SUFFIX \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-east-2

# Response Time
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=$ALB_SUFFIX \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average \
  --region us-east-2
```

### RDS Metrics

```bash
# CPU Utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=sensor-postgres-v2 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average Maximum \
  --region us-east-2

# Database Connections
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=sensor-postgres-v2 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average Maximum \
  --region us-east-2
```

---

## 🔍 Troubleshooting

### High CPU Usage

```bash
# Check which tasks are consuming CPU
aws ecs list-tasks \
  --cluster sensor-app-cluster \
  --service-name sensor-app-service \
  --region us-east-2

# Get task details
aws ecs describe-tasks \
  --cluster sensor-app-cluster \
  --tasks <task-arn> \
  --region us-east-2

# Check logs for the specific task
aws logs tail /ecs/sensor-app \
  --since 10m \
  --filter-pattern "ERROR" \
  --region us-east-2
```

### High Response Times

```bash
# Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn> \
  --region us-east-2

# Check for slow queries in logs
aws logs start-query \
  --log-group-name /ecs/sensor-app \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /duration/ | sort @timestamp desc' \
  --region us-east-2
```

### Database Connection Issues

```bash
# Check RDS connections
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=sensor-postgres-v2 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Maximum \
  --region us-east-2

# Check for connection errors in logs
./scripts/stream_logs.sh "connection"
```

---

## 📧 Email Notifications

### Configure SNS Subscription

1. Deploy the monitoring infrastructure
2. Check your email for SNS subscription confirmation
3. Click "Confirm subscription" in the email

### Test Email Alerts

```bash
# Trigger a test alarm
aws cloudwatch set-alarm-state \
  --alarm-name sensor-app-high-cpu \
  --state-value ALARM \
  --state-reason "Testing email notification" \
  --region us-east-2

# Reset alarm
aws cloudwatch set-alarm-state \
  --alarm-name sensor-app-high-cpu \
  --state-value OK \
  --state-reason "Test complete" \
  --region us-east-2
```

---

## 🎯 Best Practices

### 1. Regular Monitoring
- Check dashboard daily
- Review alarms weekly
- Analyze trends monthly

### 2. Log Retention
- Current setting: 1 day (cost optimization)
- For production: Increase to 7-30 days
- Archive important logs to S3

### 3. Alarm Tuning
- Adjust thresholds based on actual usage
- Add custom metrics for business KPIs
- Set up escalation policies

### 4. Performance Baselines
- Document normal CPU/memory ranges
- Track response time trends
- Monitor request patterns

### 5. Cost Optimization
- Use metric filters to reduce log ingestion
- Set appropriate log retention periods
- Archive old metrics to S3

---

## 🔗 Useful Links

- [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=us-east-2#dashboards:)
- [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-2#logsV2:log-groups)
- [CloudWatch Alarms](https://console.aws.amazon.com/cloudwatch/home?region=us-east-2#alarmsV2:)
- [ECS Console](https://console.aws.amazon.com/ecs/home?region=us-east-2#/clusters)
- [ALB Console](https://console.aws.amazon.com/ec2/v2/home?region=us-east-2#LoadBalancers:)

---

## 📝 Summary

You now have:
- ✅ Real-time monitoring dashboard
- ✅ Automated alarms with email notifications
- ✅ Log streaming and analysis tools
- ✅ Python and Bash monitoring scripts
- ✅ CloudWatch Logs Insights queries
- ✅ Comprehensive troubleshooting guides

**Next Steps**:
1. Deploy monitoring infrastructure: `terraform apply`
2. Confirm SNS email subscription
3. Run monitoring dashboard: `python3 scripts/monitor_dashboard.py`
4. Access CloudWatch console and explore metrics

# Data Pipeline Monitoring Guide

Complete monitoring solution for tracking sensor data flow through PostgreSQL, Kafka, and S3 with failure detection and alerting.

---

## 🎯 Overview

This monitoring system tracks your entire sensor data pipeline:

```
Sensor Data → Ingestion → PostgreSQL → Kafka → S3
                ↓            ↓          ↓      ↓
            Monitoring   Monitoring  Monitoring Monitoring
```

**What's Tracked:**
- ✅ Success/failure rates for each stage
- ✅ Processing latency and throughput
- ✅ Failure types (connection, timeout, validation, network)
- ✅ Retry attempts and queue depths
- ✅ Data size and volume metrics
- ✅ Real-time error logs

---

## 🚀 Quick Start

### 1. Deploy Monitoring Infrastructure

```bash
cd sensor-backend/terraform

# Deploy data pipeline monitoring
terraform apply -target=aws_cloudwatch_dashboard.data_pipeline_dashboard
terraform apply -target=aws_cloudwatch_metric_alarm.pipeline_high_failure_rate

# Or deploy everything
terraform apply
```

### 2. Integrate Monitoring in Your Code

Add to your application:

```python
from app.monitoring import (
    monitor_pipeline_operation,
    PipelineStage,
    DataPipelineMetrics,
    failure_tracker
)

# Use decorator for automatic monitoring
@monitor_pipeline_operation(PipelineStage.POSTGRES_WRITE)
async def write_to_database(sensor_data):
    # Your code here
    pass

# Or manually track metrics
DataPipelineMetrics.record_success(PipelineStage.KAFKA_PUBLISH, sensor_id)
DataPipelineMetrics.record_failure(
    PipelineStage.S3_UPLOAD,
    FailureType.NETWORK_ERROR,
    sensor_id,
    error_message
)
```

### 3. Run Real-Time Monitor

```bash
# Install dependencies
pip install boto3

# Make executable
chmod +x scripts/monitor_pipeline.py

# Run the monitor
python3 scripts/monitor_pipeline.py
```

---

## 📊 CloudWatch Dashboard

### Access Dashboard

```bash
# Get dashboard URL
terraform output data_pipeline_dashboard_url

# Or navigate to:
# https://console.aws.amazon.com/cloudwatch/home?region=us-east-2#dashboards:name=sensor-data-pipeline
```

### Dashboard Widgets

1. **Pipeline Success vs Failures** - Overall health indicator
2. **Failures by Stage** - Identify bottlenecks (PostgreSQL, Kafka, S3)
3. **Processing Latency** - Average and p99 latency
4. **Data Throughput** - Bytes processed per stage
5. **PostgreSQL Operations** - Write success/failure rates
6. **Kafka Operations** - Publish rates and queue depth
7. **S3 Upload Operations** - Upload success/failure rates
8. **Failure Types** - Connection, timeout, validation errors
9. **Retry Attempts** - Track retry patterns
10. **Recent Errors** - Live error log stream

---

## 🔍 Monitoring Tools

### Tool 1: Real-Time Pipeline Monitor (Recommended)

Beautiful terminal dashboard showing live pipeline metrics:

```bash
python3 scripts/monitor_pipeline.py
```

**Features:**
- ✅ Overall pipeline health (success rate %)
- ✅ Per-stage metrics (ingestion, PostgreSQL, Kafka, S3)
- ✅ Failure breakdown by type
- ✅ Recent error logs with timestamps
- ✅ Color-coded health indicators
- ✅ Auto-refresh every 5 seconds

### Tool 2: CloudWatch Logs Insights

Pre-configured queries for troubleshooting:

#### Query 1: Pipeline Failures Summary
```sql
fields @timestamp, @message
| filter @message like /FAILURE_TRACKED/
| parse @message /Stage: (?<stage>\w+)/
| parse @message /FailureType: (?<failure_type>\w+)/
| stats count() by stage, failure_type
| sort count desc
```

#### Query 2: PostgreSQL Errors
```sql
fields @timestamp, @message
| filter @message like /postgres/ and (@message like /ERROR/ or @message like /Failed/)
| sort @timestamp desc
| limit 100
```

#### Query 3: Kafka Errors
```sql
fields @timestamp, @message
| filter @message like /kafka/ and (@message like /ERROR/ or @message like /Failed/)
| sort @timestamp desc
| limit 100
```

#### Query 4: S3 Upload Errors
```sql
fields @timestamp, @message
| filter @message like /s3/ and (@message like /ERROR/ or @message like /Failed/)
| sort @timestamp desc
| limit 100
```

#### Query 5: Latency Analysis
```sql
fields @timestamp, @message
| filter @message like /ProcessingLatency/
| parse @message /Stage: (?<stage>\w+)/
| parse @message /duration[:\s]+(?<duration>\d+)/
| stats avg(duration), max(duration), min(duration) by stage
```

---

## 🚨 Alarms & Alerts

### Configured Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| High Failure Rate | > 10% failures | Email alert |
| PostgreSQL Write Failures | > 5 failures in 5min | Email alert |
| Kafka Publish Failures | > 5 failures in 5min | Email alert |
| S3 Upload Failures | > 5 failures in 5min | Email alert |
| High Processing Latency | > 5 seconds average | Email alert |

### Check Alarm Status

```bash
# List all pipeline alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix "sensor-pipeline" \
  --region us-east-2

# Check active alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix "sensor-" \
  --state-value ALARM \
  --region us-east-2
```

---

## 📈 Custom Metrics

### Available Metrics

All metrics are published to namespace: `SensorBackend/DataPipeline`

| Metric Name | Description | Unit | Dimensions |
|-------------|-------------|------|------------|
| `SuccessCount` | Successful operations | Count | Stage, SensorId |
| `FailureCount` | Failed operations | Count | Stage, FailureType, SensorId |
| `ProcessingLatency` | Operation duration | Milliseconds | Stage, SensorId |
| `DataSize` | Data processed | Bytes | Stage |
| `QueueDepth` | Queue/buffer depth | Count | Queue |
| `RetryAttempts` | Retry count | Count | Stage |

### Query Metrics via CLI

```bash
# Get PostgreSQL write failures
aws cloudwatch get-metric-statistics \
  --namespace SensorBackend/DataPipeline \
  --metric-name FailureCount \
  --dimensions Name=Stage,Value=postgres_write \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-east-2

# Get Kafka publish latency
aws cloudwatch get-metric-statistics \
  --namespace SensorBackend/DataPipeline \
  --metric-name ProcessingLatency \
  --dimensions Name=Stage,Value=kafka_publish \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum \
  --region us-east-2
```

---

## 💻 Code Integration Examples

### Example 1: Basic Monitoring with Decorator

```python
from app.monitoring import monitor_pipeline_operation, PipelineStage

@monitor_pipeline_operation(PipelineStage.POSTGRES_WRITE)
async def save_sensor_data(sensor_id: str, data: dict):
    """Automatically tracked - success, failure, and latency"""
    async with db.begin():
        await db.execute(
            "INSERT INTO sensors (id, data) VALUES (:id, :data)",
            {"id": sensor_id, "data": data}
        )
```

### Example 2: Manual Metric Tracking

```python
from app.monitoring import DataPipelineMetrics, PipelineStage

async def process_batch(sensor_batch):
    # Track data size
    batch_size = len(json.dumps(sensor_batch).encode())
    DataPipelineMetrics.record_data_size(PipelineStage.INGESTION, batch_size)
    
    # Track queue depth
    queue_depth = await kafka_consumer.get_queue_depth()
    DataPipelineMetrics.record_queue_depth('sensor-data', queue_depth)
```

### Example 3: Failure Tracking with Context

```python
from app.monitoring import failure_tracker, PipelineStage, FailureType

try:
    await upload_to_s3(sensor_data)
except Exception as e:
    failure_tracker.log_failure(
        stage=PipelineStage.S3_UPLOAD,
        failure_type=FailureType.NETWORK_ERROR,
        sensor_id=sensor_data['id'],
        error_message=str(e),
        metadata={
            'bucket': 'my-bucket',
            'key': s3_key,
            'retry_count': 3
        }
    )
    raise
```

### Example 4: Complete Pipeline with Monitoring

```python
from app.sensor_pipeline import SensorDataPipeline

async def ingest_sensors(sensor_batch: List[dict]):
    pipeline = SensorDataPipeline(
        db_session=db,
        kafka_producer=kafka,
        s3_bucket='sensor-data-bucket'
    )
    
    # Process batch - all stages automatically monitored
    results = await pipeline.process_sensor_batch(sensor_batch)
    
    # Get failure summary
    summary = failure_tracker.get_failure_summary()
    
    return {
        'processed': results['successful'],
        'failed': results['failed'],
        'failure_summary': summary
    }
```

---

## 🔧 Troubleshooting

### High PostgreSQL Failure Rate

```bash
# Check database connections
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
aws logs tail /ecs/sensor-app \
  --since 30m \
  --filter-pattern "postgres connection" \
  --region us-east-2
```

**Common Causes:**
- Connection pool exhausted
- Database CPU/memory high
- Network issues
- Lock contention

### High Kafka Failure Rate

```bash
# Check Kafka-specific errors
aws logs start-query \
  --log-group-name /ecs/sensor-app \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /kafka/ and @message like /ERROR/' \
  --region us-east-2
```

**Common Causes:**
- Kafka broker unavailable
- Topic doesn't exist
- Message size too large
- Network timeout

### High S3 Upload Failures

```bash
# Check S3 errors
aws logs tail /ecs/sensor-app \
  --since 30m \
  --filter-pattern "s3 ERROR" \
  --region us-east-2
```

**Common Causes:**
- IAM permissions missing
- Bucket doesn't exist
- Network issues
- Rate limiting

### High Processing Latency

```bash
# Analyze latency by stage
aws logs start-query \
  --log-group-name /ecs/sensor-app \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp | filter @message like /ProcessingLatency/ | parse @message /duration[:\s]+(?<duration>\d+)/ | stats avg(duration), max(duration) by bin(5m)' \
  --region us-east-2
```

**Common Causes:**
- Database slow queries
- Network latency
- Large payload sizes
- Resource contention

---

## 📊 Performance Optimization

### Based on Monitoring Data

1. **If PostgreSQL writes are slow:**
   - Add database indexes
   - Implement connection pooling
   - Use batch inserts
   - Scale up RDS instance

2. **If Kafka publishes are failing:**
   - Increase timeout values
   - Add retry logic with exponential backoff
   - Check broker health
   - Increase producer buffer size

3. **If S3 uploads are slow:**
   - Use multipart uploads for large files
   - Implement parallel uploads
   - Use S3 Transfer Acceleration
   - Batch small files

4. **If overall latency is high:**
   - Process data asynchronously
   - Use background tasks
   - Implement caching
   - Scale ECS tasks

---

## 📧 Email Notifications

### Configure Alerts

Update `terraform/variables.tf`:
```hcl
variable "alert_email" {
  default = "your-team@example.com"
}
```

Deploy and confirm SNS subscription via email.

### Alert Examples

You'll receive emails for:
- Pipeline failure rate > 10%
- PostgreSQL write failures > 5 in 5 minutes
- Kafka publish failures > 5 in 5 minutes
- S3 upload failures > 5 in 5 minutes
- Processing latency > 5 seconds

---

## 🎯 Best Practices

1. **Monitor Continuously**
   - Run real-time monitor during deployments
   - Check dashboard daily
   - Review failure trends weekly

2. **Set Appropriate Thresholds**
   - Adjust alarm thresholds based on your traffic
   - Use percentiles (p95, p99) for latency
   - Account for peak hours

3. **Log Structured Data**
   - Use JSON logging for easier parsing
   - Include correlation IDs
   - Add context to error messages

4. **Implement Retry Logic**
   - Use exponential backoff
   - Track retry attempts
   - Set maximum retry limits

5. **Archive Metrics**
   - Export CloudWatch metrics to S3
   - Keep historical data for trend analysis
   - Use for capacity planning

---

## 📝 Summary

You now have:
- ✅ Custom CloudWatch metrics for each pipeline stage
- ✅ Real-time monitoring dashboard
- ✅ Automated failure detection and alerting
- ✅ Detailed error logging and analysis
- ✅ Python monitoring library for easy integration
- ✅ Pre-configured CloudWatch Logs Insights queries
- ✅ Email notifications for critical failures

**Next Steps:**
1. Deploy monitoring infrastructure: `terraform apply`
2. Integrate monitoring in your code (see examples above)
3. Run real-time monitor: `python3 scripts/monitor_pipeline.py`
4. Configure email alerts
5. Access CloudWatch dashboard and explore metrics

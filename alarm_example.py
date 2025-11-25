"""
Real CloudWatch Alarm Example - What You See When Data Fails
"""

# ============================================================================
# EMAIL YOU RECEIVE WHEN ALARM TRIGGERS
# ============================================================================

"""
From: AWS Notifications <no-reply@sns.amazonaws.com>
Subject: ALARM: "sensor-postgres-write-failures" in US East (Ohio)

You are receiving this email because your Amazon CloudWatch Alarm 
"sensor-postgres-write-failures" in the US East (Ohio) region has entered 
the ALARM state.

Alarm Details:
- Name:        sensor-postgres-write-failures
- Description: Alert on PostgreSQL write failures
- State:       ALARM (previously OK)
- Reason:      Threshold Crossed: 1 datapoint [8.0 (25/11/24 14:23:00)] 
               was greater than the threshold (5.0).

Monitored Metric:
- Namespace:   SensorBackend/DataPipeline
- Metric:      FailureCount
- Dimensions:  Stage = postgres_write
- Period:      300 seconds
- Statistic:   Sum
- Threshold:   > 5 failures in 5 minutes

Current Value: 8 failures

View this alarm in the AWS Console:
https://console.aws.amazon.com/cloudwatch/home?region=us-east-2#alarmsV2:alarm/sensor-postgres-write-failures
"""


# ============================================================================
# WHAT TO DO WHEN YOU GET THIS ALARM
# ============================================================================

import boto3

cloudwatch = boto3.client('cloudwatch', region_name='us-east-2')
logs = boto3.client('logs', region_name='us-east-2')

# Step 1: Check what failed
def investigate_postgres_failures():
    """Find out what's failing"""
    
    # Get recent error logs
    response = logs.filter_log_events(
        logGroupName='/ecs/sensor-app',
        filterPattern='FAILURE_TRACKED postgres_write',
        limit=10
    )
    
    for event in response['events']:
        print(event['message'])
        # Example output:
        # "FAILURE_TRACKED: Stage: postgres_write, FailureType: connection_error, 
        #  Sensor: sensor-123, Error: connection timeout after 30s"


# Step 2: Check database health
def check_database_health():
    """Check if database is the problem"""
    
    # Check RDS CPU
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/RDS',
        MetricName='CPUUtilization',
        Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': 'sensor-postgres-v2'}],
        StartTime=datetime.utcnow() - timedelta(minutes=30),
        EndTime=datetime.utcnow(),
        Period=300,
        Statistics=['Average']
    )
    
    if response['Datapoints']:
        cpu = response['Datapoints'][0]['Average']
        print(f"RDS CPU: {cpu}%")
        
        if cpu > 80:
            print("⚠️ DATABASE CPU HIGH - Scale up RDS instance")
        
    # Check database connections
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/RDS',
        MetricName='DatabaseConnections',
        Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': 'sensor-postgres-v2'}],
        StartTime=datetime.utcnow() - timedelta(minutes=30),
        EndTime=datetime.utcnow(),
        Period=300,
        Statistics=['Maximum']
    )
    
    if response['Datapoints']:
        connections = response['Datapoints'][0]['Maximum']
        print(f"DB Connections: {connections}")
        
        if connections > 80:  # Assuming max 100
            print("⚠️ CONNECTION POOL EXHAUSTED - Increase pool size")


# Step 3: Check application health
def check_application_health():
    """Check if your app is the problem"""
    
    # Check ECS task count
    ecs = boto3.client('ecs', region_name='us-east-2')
    response = ecs.describe_services(
        cluster='sensor-app-cluster',
        services=['sensor-app-service']
    )
    
    service = response['services'][0]
    running = service['runningCount']
    desired = service['desiredCount']
    
    print(f"ECS Tasks: {running}/{desired} running")
    
    if running < desired:
        print("⚠️ TASKS FAILING - Check ECS task logs")


# ============================================================================
# COMMON FAILURE SCENARIOS & FIXES
# ============================================================================

"""
SCENARIO 1: Connection Timeout
Alarm: sensor-postgres-write-failures
Logs: "connection timeout after 30s"

What Failed: App can't connect to PostgreSQL
Why: Database overloaded, network issue, or connection pool exhausted

Fix:
1. Check RDS CPU/memory → Scale up if needed
2. Check connection pool settings → Increase max connections
3. Check security groups → Ensure ECS can reach RDS
4. Check RDS status → Restart if needed

Command:
aws rds describe-db-instances --db-instance-identifier sensor-postgres-v2


SCENARIO 2: Kafka Publish Failures  
Alarm: sensor-kafka-publish-failures
Logs: "kafka broker not available"

What Failed: Can't send messages to Kafka
Why: Kafka broker down, topic doesn't exist, or network issue

Fix:
1. Check Kafka broker status
2. Verify topic exists
3. Check network connectivity
4. Increase timeout settings


SCENARIO 3: S3 Upload Failures
Alarm: sensor-s3-upload-failures  
Logs: "Access Denied"

What Failed: Can't upload to S3
Why: IAM permissions missing or bucket doesn't exist

Fix:
1. Check IAM role has s3:PutObject permission
2. Verify bucket exists
3. Check bucket policy

Command:
aws s3 ls s3://your-sensor-bucket/


SCENARIO 4: High Latency
Alarm: sensor-pipeline-high-latency
Logs: "processing took 8000ms"

What Failed: Operations taking too long
Why: Database slow queries, large payloads, or resource contention

Fix:
1. Add database indexes
2. Optimize queries
3. Reduce payload size
4. Scale up ECS tasks
"""


# ============================================================================
# AUTOMATED RESPONSE SCRIPT
# ============================================================================

def auto_respond_to_alarm(alarm_name):
    """Automatically investigate and suggest fixes"""
    
    if 'postgres' in alarm_name:
        print("🔍 Investigating PostgreSQL failures...")
        investigate_postgres_failures()
        check_database_health()
        
        print("\n💡 Suggested Actions:")
        print("1. Check logs: aws logs tail /ecs/sensor-app --filter-pattern 'postgres ERROR'")
        print("2. Check RDS: aws rds describe-db-instances --db-instance-identifier sensor-postgres-v2")
        print("3. Scale RDS: Modify instance class in AWS Console")
        print("4. Increase connection pool in app config")
        
    elif 'kafka' in alarm_name:
        print("🔍 Investigating Kafka failures...")
        print("\n💡 Suggested Actions:")
        print("1. Check Kafka broker status")
        print("2. Verify topic exists")
        print("3. Check network connectivity")
        print("4. Review Kafka logs")
        
    elif 's3' in alarm_name:
        print("🔍 Investigating S3 failures...")
        print("\n💡 Suggested Actions:")
        print("1. Check IAM permissions: aws iam get-role --role-name sensor-ecs-task-role")
        print("2. Verify bucket: aws s3 ls s3://your-bucket/")
        print("3. Test upload: aws s3 cp test.txt s3://your-bucket/")


# Run investigation
if __name__ == '__main__':
    # Simulate alarm trigger
    alarm_name = 'sensor-postgres-write-failures'
    auto_respond_to_alarm(alarm_name)

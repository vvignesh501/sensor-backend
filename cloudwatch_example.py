"""
Simple Example: How CloudWatch Tracks Real-Time Data
"""

import boto3
from datetime import datetime

# Step 1: Your app sends metrics to CloudWatch
cloudwatch = boto3.client('cloudwatch', region_name='us-east-2')

def process_sensor_data(sensor_id, value):
    """Your application processing sensor data"""
    
    # Do your work (save to DB, send to Kafka, etc.)
    result = save_to_database(sensor_id, value)
    
    if result == "success":
        # Send SUCCESS metric to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='SensorBackend/DataPipeline',
            MetricData=[
                {
                    'MetricName': 'SuccessCount',
                    'Value': 1.0,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'Stage', 'Value': 'postgres_write'}
                    ]
                }
            ]
        )
    else:
        # Send FAILURE metric to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='SensorBackend/DataPipeline',
            MetricData=[
                {
                    'MetricName': 'FailureCount',
                    'Value': 1.0,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'Stage', 'Value': 'postgres_write'},
                        {'Name': 'FailureType', 'Value': 'timeout'}
                    ]
                }
            ]
        )


# Step 2: CloudWatch Dashboard reads these metrics
def get_realtime_metrics():
    """Dashboard fetches metrics from CloudWatch"""
    
    response = cloudwatch.get_metric_statistics(
        Namespace='SensorBackend/DataPipeline',
        MetricName='SuccessCount',
        Dimensions=[
            {'Name': 'Stage', 'Value': 'postgres_write'}
        ],
        StartTime=datetime.utcnow() - timedelta(minutes=5),
        EndTime=datetime.utcnow(),
        Period=60,
        Statistics=['Sum']
    )
    
    # Display in dashboard
    if response['Datapoints']:
        success_count = response['Datapoints'][0]['Sum']
        print(f"Successful operations: {success_count}")


# Step 3: CloudWatch Alarms monitor thresholds
# (Configured in Terraform - triggers when failures > 5)

"""
FLOW:
1. Your app calls cloudwatch.put_metric_data() → Sends metric to AWS
2. CloudWatch stores and aggregates metrics → Available within 1-2 minutes
3. Dashboard calls cloudwatch.get_metric_statistics() → Reads metrics
4. Alarms check thresholds → Sends email if breached

REAL-TIME:
- Metrics appear in CloudWatch within 1-2 minutes
- Dashboards auto-refresh every 1-5 minutes
- Your monitoring script polls CloudWatch every 5 seconds
"""

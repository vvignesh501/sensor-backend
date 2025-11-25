#!/usr/bin/env python3
"""
Mock Demo: How CloudWatch Monitors Real-Time Processing Data

This demonstrates the flow:
1. Your app processes sensor data
2. Metrics are sent to CloudWatch
3. CloudWatch aggregates and displays them
4. Monitoring script reads and displays metrics
"""

import time
import random
from datetime import datetime
from typing import Dict

# Simulated CloudWatch (in reality, this is AWS CloudWatch service)
class MockCloudWatch:
    """Simulates AWS CloudWatch metric storage"""
    def __init__(self):
        self.metrics = []
    
    def put_metric_data(self, namespace: str, metric_data: list):
        """Store metrics (like AWS CloudWatch API)"""
        for metric in metric_data:
            self.metrics.append({
                'namespace': namespace,
                'timestamp': datetime.utcnow(),
                **metric
            })
        print(f"📊 CloudWatch: Stored {len(metric_data)} metrics in {namespace}")
    
    def get_recent_metrics(self, metric_name: str, dimensions: Dict = None):
        """Retrieve recent metrics (like CloudWatch GetMetricStatistics)"""
        filtered = [
            m for m in self.metrics[-50:]  # Last 50 metrics
            if m.get('MetricName') == metric_name
        ]
        
        if dimensions:
            filtered = [
                m for m in filtered
                if all(
                    any(d['Name'] == k and d['Value'] == v for d in m.get('Dimensions', []))
                    for k, v in dimensions.items()
                )
            ]
        
        return filtered


# Global CloudWatch instance (simulates AWS service)
cloudwatch = MockCloudWatch()


# Your Application Code
class SensorProcessor:
    """Your application that processes sensor data"""
    
    def process_sensor_data(self, sensor_id: str, value: float):
        """Process sensor data and send metrics to CloudWatch"""
        start_time = time.time()
        
        try:
            # Simulate processing
            time.sleep(random.uniform(0.1, 0.3))
            
            # Simulate random failures (10% chance)
            if random.random() < 0.1:
                raise Exception("Database connection timeout")
            
            # SUCCESS: Send success metric to CloudWatch
            duration_ms = (time.time() - start_time) * 1000
            
            cloudwatch.put_metric_data(
                namespace='SensorBackend/DataPipeline',
                metric_data=[
                    {
                        'MetricName': 'SuccessCount',
                        'Value': 1.0,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'Stage', 'Value': 'postgres_write'},
                            {'Name': 'SensorId', 'Value': sensor_id}
                        ]
                    },
                    {
                        'MetricName': 'ProcessingLatency',
                        'Value': duration_ms,
                        'Unit': 'Milliseconds',
                        'Dimensions': [
                            {'Name': 'Stage', 'Value': 'postgres_write'}
                        ]
                    }
                ]
            )
            
            print(f"✅ Processed sensor {sensor_id}: {value} ({duration_ms:.0f}ms)")
            return True
            
        except Exception as e:
            # FAILURE: Send failure metric to CloudWatch
            cloudwatch.put_metric_data(
                namespace='SensorBackend/DataPipeline',
                metric_data=[
                    {
                        'MetricName': 'FailureCount',
                        'Value': 1.0,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'Stage', 'Value': 'postgres_write'},
                            {'Name': 'FailureType', 'Value': 'timeout'}
                        ]
                    }
                ]
            )
            
            print(f"❌ Failed sensor {sensor_id}: {e}")
            return False


# Monitoring Dashboard
class MonitoringDashboard:
    """Reads metrics from CloudWatch and displays them"""
    
    def display_metrics(self):
        """Fetch and display real-time metrics"""
        # Get success count
        success_metrics = cloudwatch.get_recent_metrics(
            'SuccessCount',
            {'Stage': 'postgres_write'}
        )
        success_count = len(success_metrics)
        
        # Get failure count
        failure_metrics = cloudwatch.get_recent_metrics(
            'FailureCount',
            {'Stage': 'postgres_write'}
        )
        failure_count = len(failure_metrics)
        
        # Get latency metrics
        latency_metrics = cloudwatch.get_recent_metrics(
            'ProcessingLatency',
            {'Stage': 'postgres_write'}
        )
        
        if latency_metrics:
            latencies = [m['Value'] for m in latency_metrics]
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
        else:
            avg_latency = 0
            max_latency = 0
        
        # Calculate success rate
        total = success_count + failure_count
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        # Display dashboard
        print("\n" + "="*60)
        print("📊 CLOUDWATCH REAL-TIME DASHBOARD")
        print("="*60)
        print(f"Success Rate:     {success_rate:.1f}%")
        print(f"Total Operations: {total}")
        print(f"Successful:       {success_count}")
        print(f"Failed:           {failure_count}")
        print(f"Avg Latency:      {avg_latency:.0f}ms")
        print(f"Max Latency:      {max_latency:.0f}ms")
        print("="*60 + "\n")


# Demo Execution
def main():
    """Run the demo"""
    print("\n🚀 CloudWatch Real-Time Monitoring Demo\n")
    print("This shows how CloudWatch tracks your application metrics:\n")
    
    processor = SensorProcessor()
    dashboard = MonitoringDashboard()
    
    # Simulate processing 20 sensor readings
    print("📡 Processing sensor data...\n")
    
    for i in range(20):
        sensor_id = f"sensor-{random.randint(1, 5)}"
        value = random.uniform(20.0, 30.0)
        
        # Your app processes data and sends metrics to CloudWatch
        processor.process_sensor_data(sensor_id, value)
        
        # Every 5 readings, show the dashboard
        if (i + 1) % 5 == 0:
            time.sleep(0.5)
            # Dashboard reads from CloudWatch and displays
            dashboard.display_metrics()
            time.sleep(1)
    
    print("\n✅ Demo Complete!\n")
    print("📝 How it works:")
    print("1. Your app calls cloudwatch.put_metric_data() after each operation")
    print("2. CloudWatch stores and aggregates these metrics")
    print("3. Dashboard calls cloudwatch.get_metric_statistics() to read metrics")
    print("4. Metrics are displayed in real-time dashboards")
    print("\n💡 In production:")
    print("- Metrics appear in CloudWatch within 1-2 minutes")
    print("- Dashboards auto-refresh every 1-5 minutes")
    print("- Alarms trigger when thresholds are breached")
    print("- You can query metrics via AWS Console or CLI\n")


if __name__ == '__main__':
    main()

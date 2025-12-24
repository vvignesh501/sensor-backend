"""
Example: Integrating Slack Notifications into Sensor Backend
Shows how to use Slack SDK when sensors fail
"""
from slack_notifier import SlackNotifier
from datetime import datetime
import asyncio


class SensorMonitor:
    """
    Monitors sensors and sends Slack alerts on failures
    """
    
    def __init__(self):
        # Initialize Slack notifier with SDK
        self.slack = SlackNotifier()
    
    async def check_sensor_health(self, sensor_id: str, sensor_data: dict):
        """
        Check if sensor is healthy, send Slack alert if not
        
        Args:
            sensor_id: Sensor identifier
            sensor_data: Latest sensor reading
        """
        # Check temperature range
        if sensor_data.get('temperature'):
            temp = sensor_data['temperature']
            
            # Critical: Temperature too high
            if temp > 100:
                self.slack.send_sensor_failure_alert(
                    sensor_id=sensor_id,
                    sensor_type="Temperature",
                    error_message=f"CRITICAL: Temperature {temp}°C exceeds safe limit (100°C)",
                    severity="critical"
                )
            
            # High: Temperature concerning
            elif temp > 80:
                self.slack.send_sensor_failure_alert(
                    sensor_id=sensor_id,
                    sensor_type="Temperature",
                    error_message=f"WARNING: Temperature {temp}°C approaching limit",
                    severity="high"
                )
        
        # Check battery level
        if sensor_data.get('battery_level'):
            battery = sensor_data['battery_level']
            
            if battery < 10:
                self.slack.send_sensor_failure_alert(
                    sensor_id=sensor_id,
                    sensor_type="Battery",
                    error_message=f"Battery critically low: {battery}%",
                    severity="high"
                )
        
        # Check if sensor is offline
        last_seen = sensor_data.get('last_seen')
        if last_seen:
            minutes_offline = (datetime.utcnow() - last_seen).total_seconds() / 60
            
            if minutes_offline > 30:
                self.slack.send_sensor_failure_alert(
                    sensor_id=sensor_id,
                    sensor_type="Connectivity",
                    error_message=f"Sensor offline for {int(minutes_offline)} minutes",
                    severity="critical"
                )


# Integration with your FastAPI backend
async def sensor_test_with_slack_alerts(sensor_id: str):
    """
    Example: Run sensor test and send Slack alert on failure
    """
    slack = SlackNotifier()
    
    try:
        # Run sensor test
        result = await run_sensor_test(sensor_id)
        
        if result['status'] == 'FAIL':
            # Send Slack alert
            slack.send_sensor_failure_alert(
                sensor_id=sensor_id,
                sensor_type=result['sensor_type'],
                error_message=result['error_message'],
                severity="high"
            )
        
        return result
        
    except Exception as e:
        # Send Slack alert for unexpected errors
        slack.send_sensor_failure_alert(
            sensor_id=sensor_id,
            sensor_type="Unknown",
            error_message=f"Unexpected error during test: {str(e)}",
            severity="critical"
        )
        raise


async def run_sensor_test(sensor_id: str):
    """Dummy sensor test function"""
    return {
        'status': 'PASS',
        'sensor_type': 'Temperature',
        'error_message': None
    }


# Kafka consumer with Slack alerts
async def kafka_consumer_with_slack():
    """
    Example: Kafka consumer that sends Slack alerts for anomalies
    """
    slack = SlackNotifier()
    
    # Consume messages from Kafka
    while True:
        message = await consume_kafka_message()
        
        # Check for anomalies
        if message['temperature'] > 100:
            slack.send_sensor_failure_alert(
                sensor_id=message['sensor_id'],
                sensor_type="Temperature",
                error_message=f"Anomaly detected: {message['temperature']}°C",
                severity="critical"
            )


async def consume_kafka_message():
    """Dummy Kafka consumer"""
    await asyncio.sleep(1)
    return {'sensor_id': 'SENSOR-001', 'temperature': 25.5}


if __name__ == "__main__":
    # Test the integration
    monitor = SensorMonitor()
    
    # Simulate sensor failure
    asyncio.run(monitor.check_sensor_health(
        sensor_id="SENSOR-001",
        sensor_data={
            'temperature': 150,  # Too high!
            'battery_level': 5,  # Too low!
            'last_seen': datetime.utcnow()
        }
    ))

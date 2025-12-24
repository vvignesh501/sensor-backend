"""
Slack Integration for Sensor Failure Notifications
Uses Slack SDK to send alerts when sensors fail
"""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
from datetime import datetime
from typing import Optional, Dict


class SlackNotifier:
    """
    Sends sensor failure notifications to Slack
    Uses Slack's official Python SDK
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize Slack client
        
        Args:
            token: Slack Bot Token (starts with xoxb-)
                   Get from: https://api.slack.com/apps
        """
        self.token = token or os.getenv('SLACK_BOT_TOKEN')
        if not self.token:
            raise ValueError("Slack token required. Set SLACK_BOT_TOKEN env variable")
        
        # Initialize Slack SDK client
        self.client = WebClient(token=self.token)
        self.default_channel = os.getenv('SLACK_CHANNEL', '#sensor-alerts')
    
    def send_sensor_failure_alert(
        self,
        sensor_id: str,
        sensor_type: str,
        error_message: str,
        severity: str = "high",
        channel: Optional[str] = None
    ) -> bool:
        """
        Send sensor failure notification to Slack
        
        Args:
            sensor_id: ID of failed sensor
            sensor_type: Type of sensor
            error_message: Error description
            severity: Alert severity (low, medium, high, critical)
            channel: Slack channel (default: #sensor-alerts)
        
        Returns:
            True if sent successfully
        """
        channel = channel or self.default_channel
        
        # Color coding by severity
        colors = {
            "low": "#36a64f",      # Green
            "medium": "#ff9900",   # Orange
            "high": "#ff0000",     # Red
            "critical": "#8b0000"  # Dark Red
        }
        
        # Build rich message with Slack Block Kit
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 Sensor Failure Alert - {severity.upper()}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Sensor ID:*\n{sensor_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Sensor Type:*\n{sensor_type}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{severity.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error Details:*\n```{error_message}```"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Dashboard"
                        },
                        "url": f"https://dashboard.redlen.com/sensors/{sensor_id}",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Logs"
                        },
                        "url": f"https://dashboard.redlen.com/logs?sensor={sensor_id}"
                    }
                ]
            }
        ]
        
        try:
            # Use Slack SDK to send message
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"Sensor {sensor_id} failed: {error_message}"  # Fallback text
            )
            
            print(f"✅ Slack notification sent: {response['ts']}")
            return True
            
        except SlackApiError as e:
            print(f"❌ Slack API error: {e.response['error']}")
            return False
    
    def send_sensor_recovery_alert(
        self,
        sensor_id: str,
        sensor_type: str,
        downtime_minutes: int,
        channel: Optional[str] = None
    ) -> bool:
        """
        Send sensor recovery notification
        
        Args:
            sensor_id: ID of recovered sensor
            sensor_type: Type of sensor
            downtime_minutes: How long sensor was down
            channel: Slack channel
        
        Returns:
            True if sent successfully
        """
        channel = channel or self.default_channel
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✅ Sensor Recovered",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Sensor ID:*\n{sensor_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Sensor Type:*\n{sensor_type}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Downtime:*\n{downtime_minutes} minutes"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Recovered At:*\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            }
        ]
        
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"Sensor {sensor_id} has recovered after {downtime_minutes} minutes"
            )
            return True
        except SlackApiError as e:
            print(f"❌ Slack API error: {e.response['error']}")
            return False
    
    def send_daily_summary(
        self,
        total_sensors: int,
        active_sensors: int,
        failed_sensors: int,
        total_readings: int,
        channel: Optional[str] = None
    ) -> bool:
        """
        Send daily sensor summary report
        
        Args:
            total_sensors: Total number of sensors
            active_sensors: Number of active sensors
            failed_sensors: Number of failed sensors
            total_readings: Total readings processed today
            channel: Slack channel
        
        Returns:
            True if sent successfully
        """
        channel = channel or self.default_channel
        
        health_percentage = (active_sensors / total_sensors * 100) if total_sensors > 0 else 0
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Daily Sensor Report",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Sensors:*\n{total_sensors}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Active:*\n{active_sensors} ({health_percentage:.1f}%)"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Failed:*\n{failed_sensors}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Readings Today:*\n{total_readings:,}"
                    }
                ]
            }
        ]
        
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"Daily Report: {active_sensors}/{total_sensors} sensors active"
            )
            return True
        except SlackApiError as e:
            print(f"❌ Slack API error: {e.response['error']}")
            return False


# Example usage in your sensor monitoring code
if __name__ == "__main__":
    # Initialize notifier
    notifier = SlackNotifier()
    
    # Send test alert
    notifier.send_sensor_failure_alert(
        sensor_id="SENSOR-001",
        sensor_type="Temperature",
        error_message="Temperature reading out of range: 150°C (expected: 20-30°C)",
        severity="critical"
    )

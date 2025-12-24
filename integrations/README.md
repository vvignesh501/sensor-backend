# Slack Integration for Sensor Alerts

This integration uses **Slack's official Python SDK** to send notifications when sensors fail.

## Setup

### 1. Install Slack SDK
```bash
pip install slack-sdk
```

### 2. Create Slack App
1. Go to https://api.slack.com/apps
2. Click "Create New App"
3. Choose "From scratch"
4. Name it "Sensor Alert Bot"
5. Select your workspace

### 3. Add Bot Permissions
1. Go to "OAuth & Permissions"
2. Add these scopes:
   - `chat:write` - Send messages
   - `chat:write.public` - Send to public channels
3. Click "Install to Workspace"
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 4. Configure Environment
```bash
export SLACK_BOT_TOKEN="xoxb-your-token-here"
export SLACK_CHANNEL="#sensor-alerts"
```

### 5. Invite Bot to Channel
In Slack, type: `/invite @Sensor Alert Bot` in your #sensor-alerts channel

## Usage

### Basic Alert
```python
from slack_notifier import SlackNotifier

slack = SlackNotifier()

# Send sensor failure alert
slack.send_sensor_failure_alert(
    sensor_id="SENSOR-001",
    sensor_type="Temperature",
    error_message="Temperature exceeded safe limits: 150°C",
    severity="critical"
)
```

### Integration with FastAPI
```python
from fastapi import FastAPI
from slack_notifier import SlackNotifier

app = FastAPI()
slack = SlackNotifier()

@app.post("/test/sensor/{sensor_id}")
async def test_sensor(sensor_id: str):
    try:
        result = run_sensor_test(sensor_id)
        
        if result['status'] == 'FAIL':
            # Send Slack alert
            slack.send_sensor_failure_alert(
                sensor_id=sensor_id,
                sensor_type=result['type'],
                error_message=result['error'],
                severity="high"
            )
        
        return result
    except Exception as e:
        # Alert on unexpected errors
        slack.send_sensor_failure_alert(
            sensor_id=sensor_id,
            sensor_type="System",
            error_message=str(e),
            severity="critical"
        )
        raise
```

### Integration with Kafka Consumer
```python
from kafka import KafkaConsumer
from slack_notifier import SlackNotifier

slack = SlackNotifier()
consumer = KafkaConsumer('sensor-events')

for message in consumer:
    data = message.value
    
    # Check for anomalies
    if data['temperature'] > 100:
        slack.send_sensor_failure_alert(
            sensor_id=data['sensor_id'],
            sensor_type="Temperature",
            error_message=f"Anomaly: {data['temperature']}°C",
            severity="critical"
        )
```

## Alert Types

### 1. Sensor Failure Alert
Sent when a sensor fails or detects anomalies.

### 2. Sensor Recovery Alert
Sent when a failed sensor comes back online.

### 3. Daily Summary
Sent once per day with overall system health.

## Architecture

```
┌─────────────────────────────────────┐
│   Your Sensor Backend (FastAPI)    │
│                                     │
│   Detects sensor failure            │
│         ↓                           │
│   Uses SlackNotifier class          │
│         ↓                           │
│   Calls Slack SDK                   │
└─────────────────────────────────────┘
              ↓
         HTTP Request
              ↓
┌─────────────────────────────────────┐
│        Slack API                    │
│     (api.slack.com)                 │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│    Slack Workspace                  │
│    #sensor-alerts channel           │
│                                     │
│    🚨 Sensor Failure Alert          │
│    Sensor: SENSOR-001               │
│    Error: Temperature too high      │
└─────────────────────────────────────┘
```

## Key Concepts

- **SDK**: You use Slack's Python SDK (`slack-sdk`) in YOUR backend
- **Your Backend**: Detects failures and calls Slack SDK
- **Slack SDK**: Makes HTTP requests to Slack's API
- **Slack API**: Slack's servers that handle the message
- **Result**: Message appears in your Slack channel

## Testing

```bash
# Set environment variables
export SLACK_BOT_TOKEN="xoxb-your-token"
export SLACK_CHANNEL="#sensor-alerts"

# Run test
python slack_notifier.py
```

You should see a test alert in your Slack channel!

## Error Handling

The SDK handles:
- Network errors
- Rate limiting
- Invalid tokens
- Channel not found
- Permission errors

All errors are logged and return `False` so your app doesn't crash.

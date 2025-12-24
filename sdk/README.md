# Redlen Sensor SDK

Official Python SDK for Redlen Sensor API

## Installation

```bash
pip install redlen-sensor-sdk
```

## Quick Start

```python
from redlen_sdk import SensorClient

# Initialize client
client = SensorClient(
    api_key="your-api-key",
    base_url="https://api.redlen.com"
)

# Get all sensors
sensors = client.sensors.list()

# Get specific sensor
sensor = client.sensors.get("SENSOR_001")

# Add sensor reading
reading = client.readings.create(
    sensor_id="SENSOR_001",
    temperature=22.5,
    humidity=45.0
)

# Get analytics
stats = client.analytics.get_statistics("SENSOR_001")
```

## Features

- ✅ Type-safe API client
- ✅ Automatic authentication
- ✅ Retry logic with exponential backoff
- ✅ Rate limiting
- ✅ Async support
- ✅ Comprehensive error handling
- ✅ Full test coverage

## Documentation

See [docs/](docs/) for detailed documentation.

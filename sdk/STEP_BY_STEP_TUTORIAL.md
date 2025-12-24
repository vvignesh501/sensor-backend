# Step-by-Step: Build Your First SDK

Let's build a simple SDK from scratch for your sensor API.

## Starting Point: Your API

You have a FastAPI backend with these endpoints:

```python
# app/main.py
@app.post("/api/v1/sensors")
def create_sensor(sensor_id: str, sensor_type: str):
    # Creates a sensor
    return {"sensor_id": sensor_id, "status": "created"}

@app.get("/api/v1/sensors/{sensor_id}")
def get_sensor(sensor_id: str):
    # Gets sensor details
    return {"sensor_id": sensor_id, "temperature": 25.5}
```

## Goal: Make it Easy for Customers

Instead of customers writing:
```python
import requests
response = requests.post("https://api.redlen.com/api/v1/sensors", ...)
```

They write:
```python
from redlen_sdk import Client
client = Client(api_key="...")
client.sensors.create(sensor_id="SENSOR-001")
```

## Let's Build It!

### Step 1: Create Basic Client (5 minutes)

Create `my_sdk/client.py`:

```python
import requests

class Client:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.redlen.com"
    
    def _request(self, method: str, path: str, **kwargs):
        """Make HTTP request"""
        url = f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            **kwargs
        )
        
        if response.status_code >= 400:
            raise Exception(f"API Error: {response.text}")
        
        return response.json()
```

**Test it:**
```python
client = Client(api_key="test-key")
result = client._request("GET", "/api/v1/sensors/SENSOR-001")
print(result)
```

### Step 2: Add Sensor Methods (5 minutes)

Add to `client.py`:

```python
class Client:
    # ... previous code ...
    
    def create_sensor(self, sensor_id: str, sensor_type: str):
        """Create a new sensor"""
        return self._request(
            "POST",
            "/api/v1/sensors",
            json={"sensor_id": sensor_id, "sensor_type": sensor_type}
        )
    
    def get_sensor(self, sensor_id: str):
        """Get sensor details"""
        return self._request("GET", f"/api/v1/sensors/{sensor_id}")
    
    def list_sensors(self):
        """List all sensors"""
        return self._request("GET", "/api/v1/sensors")
```

**Test it:**
```python
client = Client(api_key="test-key")

# Create sensor
sensor = client.create_sensor("SENSOR-001", "temperature")
print(sensor)

# Get sensor
details = client.get_sensor("SENSOR-001")
print(details)
```

### Step 3: Organize with Resources (10 minutes)

Create `my_sdk/resources.py`:

```python
class SensorResource:
    """Handles all sensor-related operations"""
    
    def __init__(self, client):
        self.client = client
    
    def create(self, sensor_id: str, sensor_type: str):
        return self.client._request(
            "POST",
            "/api/v1/sensors",
            json={"sensor_id": sensor_id, "sensor_type": sensor_type}
        )
    
    def get(self, sensor_id: str):
        return self.client._request("GET", f"/api/v1/sensors/{sensor_id}")
    
    def list(self):
        return self.client._request("GET", "/api/v1/sensors")
```

Update `client.py`:

```python
from .resources import SensorResource

class Client:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.redlen.com"
        
        # Initialize resources
        self.sensors = SensorResource(self)
    
    def _request(self, method: str, path: str, **kwargs):
        # ... same as before ...
```

**Test it:**
```python
client = Client(api_key="test-key")

# Now use resources
sensor = client.sensors.create("SENSOR-001", "temperature")
details = client.sensors.get("SENSOR-001")
all_sensors = client.sensors.list()
```

### Step 4: Add Error Handling (5 minutes)

Create `my_sdk/exceptions.py`:

```python
class SDKError(Exception):
    """Base SDK exception"""
    pass

class AuthenticationError(SDKError):
    """Invalid API key"""
    pass

class NotFoundError(SDKError):
    """Resource not found"""
    pass
```

Update `client.py`:

```python
from .exceptions import AuthenticationError, NotFoundError, SDKError

class Client:
    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        response = requests.request(method, url, headers=headers, **kwargs)
        
        # Better error handling
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 404:
            raise NotFoundError("Resource not found")
        elif response.status_code >= 400:
            raise SDKError(f"API Error: {response.text}")
        
        return response.json()
```

### Step 5: Make it Installable (5 minutes)

Create `setup.py`:

```python
from setuptools import setup, find_packages

setup(
    name="redlen-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["requests>=2.28.0"],
)
```

Create `my_sdk/__init__.py`:

```python
from .client import Client
from .exceptions import SDKError, AuthenticationError, NotFoundError

__version__ = "0.1.0"
```

**Install it:**
```bash
pip install -e .
```

**Use it:**
```python
from my_sdk import Client

client = Client(api_key="test-key")
sensor = client.sensors.create("SENSOR-001", "temperature")
```

### Step 6: Add Documentation (5 minutes)

Create `README.md`:

```markdown
# Redlen SDK

Python SDK for Redlen Sensor API

## Installation

```bash
pip install redlen-sdk
```

## Quick Start

```python
from redlen_sdk import Client

# Initialize
client = Client(api_key="your-api-key")

# Create sensor
sensor = client.sensors.create(
    sensor_id="SENSOR-001",
    sensor_type="temperature"
)

# Get sensor
details = client.sensors.get("SENSOR-001")

# List sensors
all_sensors = client.sensors.list()
```

## Documentation

See full docs at: https://docs.redlen.com
```

## Final Structure

```
my_sdk/
├── my_sdk/
│   ├── __init__.py       # Package entry
│   ├── client.py         # Main client
│   ├── resources.py      # Resource classes
│   └── exceptions.py     # Custom errors
├── setup.py              # Installation config
└── README.md             # Documentation
```

## What You Built

1. **Client class** - Handles HTTP requests and authentication
2. **Resource classes** - Organize endpoints logically
3. **Error handling** - Clear exceptions for customers
4. **Package structure** - Installable with pip
5. **Documentation** - Easy to understand

## How It Works

```
Customer Code
    ↓
client.sensors.create(...)
    ↓
SensorResource.create()
    ↓
Client._request()
    ↓
HTTP POST to your API
    ↓
Your FastAPI Backend
    ↓
Response back to customer
```

## Next Steps

### Add More Features:
- Retry logic for failed requests
- Pagination for list endpoints
- Async support with httpx
- Type hints with Pydantic
- Unit tests with pytest

### Publish to PyPI:
```bash
python setup.py sdist bdist_wheel
twine upload dist/*
```

Now anyone can:
```bash
pip install redlen-sdk
```

## Key Takeaway

An SDK is just a Python package that:
1. Makes HTTP requests to your API
2. Wraps them in easy-to-use methods
3. Handles errors gracefully
4. Provides good documentation

You've built one in 30 minutes! 🎉

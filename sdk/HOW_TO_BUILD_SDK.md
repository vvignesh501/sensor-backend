# How to Build an SDK for Your Web Application

This guide shows you how to create an SDK from your FastAPI backend so customers can easily integrate with your API.

## What You're Building

```
Your FastAPI Backend (api.redlen.com)
         ↓
    Create SDK
         ↓
Customers install: pip install redlen-sdk
         ↓
Customers use: client.sensors.create(...)
```

## Step-by-Step Process

### Step 1: Identify Your API Endpoints

First, look at your FastAPI backend and list all endpoints:

```python
# Your FastAPI Backend (app/main.py)
@app.post("/api/v1/sensors")           # Create sensor
@app.get("/api/v1/sensors")            # List sensors
@app.get("/api/v1/sensors/{id}")       # Get sensor
@app.post("/api/v1/sensors/{id}/readings")  # Create reading
@app.post("/auth/token")               # Login
```

### Step 2: Create SDK Project Structure

```
sdk/
├── redlen_sdk/              # Main package
│   ├── __init__.py         # Package entry point
│   ├── client.py           # Main client class
│   ├── resources.py        # Resource classes (sensors, readings)
│   ├── models.py           # Data models
│   └── exceptions.py       # Custom exceptions
├── examples/               # Usage examples
│   └── basic_usage.py
├── tests/                  # Unit tests
│   └── test_client.py
├── setup.py               # Package configuration
├── README.md              # Documentation
└── requirements.txt       # Dependencies
```

### Step 3: Build the Core Client

**File: `redlen_sdk/client.py`**

This is the main class customers will use:

```python
import requests
from .resources import SensorResource, ReadingResource

class RedlenClient:
    """Main SDK client"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.redlen.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
        
        # Initialize resources
        self.sensors = SensorResource(self)
        self.readings = ReadingResource(self)
    
    def request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request to API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
```

### Step 4: Create Resource Classes

**File: `redlen_sdk/resources.py`**

Each resource maps to API endpoints:

```python
class SensorResource:
    """Handles /api/v1/sensors endpoints"""
    
    def __init__(self, client):
        self.client = client
    
    def create(self, sensor_id: str, sensor_type: str, location: str):
        """Create a new sensor"""
        data = {
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "location": location
        }
        return self.client.request("POST", "/api/v1/sensors", json=data)
    
    def list(self, page: int = 1, page_size: int = 100):
        """List all sensors"""
        params = {"page": page, "page_size": page_size}
        return self.client.request("GET", "/api/v1/sensors", params=params)
    
    def get(self, sensor_id: str):
        """Get specific sensor"""
        return self.client.request("GET", f"/api/v1/sensors/{sensor_id}")


class ReadingResource:
    """Handles /api/v1/sensors/{id}/readings endpoints"""
    
    def __init__(self, client):
        self.client = client
    
    def create(self, sensor_id: str, temperature: float, humidity: float):
        """Create sensor reading"""
        data = {
            "sensor_id": sensor_id,
            "temperature": temperature,
            "humidity": humidity
        }
        return self.client.request(
            "POST", 
            f"/api/v1/sensors/{sensor_id}/readings",
            json=data
        )
```

### Step 5: Define Data Models

**File: `redlen_sdk/models.py`**

Use Pydantic for type validation:

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Sensor(BaseModel):
    sensor_id: str
    sensor_type: str
    location: str
    status: str = "active"
    created_at: datetime

class SensorReading(BaseModel):
    sensor_id: str
    temperature: Optional[float]
    humidity: Optional[float]
    timestamp: datetime
```

### Step 6: Create Custom Exceptions

**File: `redlen_sdk/exceptions.py`**

```python
class RedlenSDKError(Exception):
    """Base exception for SDK"""
    pass

class AuthenticationError(RedlenSDKError):
    """Invalid API key"""
    pass

class NotFoundError(RedlenSDKError):
    """Resource not found"""
    pass

class RateLimitError(RedlenSDKError):
    """Rate limit exceeded"""
    pass
```

### Step 7: Package Entry Point

**File: `redlen_sdk/__init__.py`**

```python
"""Redlen Sensor SDK"""

__version__ = "1.0.0"

from .client import RedlenClient
from .models import Sensor, SensorReading
from .exceptions import (
    RedlenSDKError,
    AuthenticationError,
    NotFoundError,
    RateLimitError
)

__all__ = [
    "RedlenClient",
    "Sensor",
    "SensorReading",
    "RedlenSDKError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError"
]
```

### Step 8: Create setup.py for Distribution

**File: `setup.py`**

```python
from setuptools import setup, find_packages

setup(
    name="redlen-sdk",
    version="1.0.0",
    description="Python SDK for Redlen Sensor API",
    author="Your Name",
    author_email="you@redlen.com",
    url="https://github.com/yourcompany/redlen-sdk",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "pydantic>=2.0.0"
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ]
)
```

### Step 9: Write Usage Examples

**File: `examples/basic_usage.py`**

```python
from redlen_sdk import RedlenClient

# Initialize client
client = RedlenClient(api_key="your-api-key-here")

# Create a sensor
sensor = client.sensors.create(
    sensor_id="SENSOR-001",
    sensor_type="temperature",
    location="Building A"
)
print(f"Created sensor: {sensor}")

# List all sensors
sensors = client.sensors.list()
print(f"Total sensors: {len(sensors)}")

# Create a reading
reading = client.readings.create(
    sensor_id="SENSOR-001",
    temperature=25.5,
    humidity=60.0
)
print(f"Created reading: {reading}")
```

### Step 10: Test Your SDK

**File: `tests/test_client.py`**

```python
import pytest
from redlen_sdk import RedlenClient

def test_create_sensor():
    client = RedlenClient(api_key="test-key")
    sensor = client.sensors.create(
        sensor_id="TEST-001",
        sensor_type="temperature",
        location="Test Lab"
    )
    assert sensor['sensor_id'] == "TEST-001"
```

### Step 11: Publish Your SDK

```bash
# Build the package
python setup.py sdist bdist_wheel

# Upload to PyPI (Python Package Index)
pip install twine
twine upload dist/*

# Now anyone can install:
pip install redlen-sdk
```

## How Customers Use Your SDK

### Without SDK (Hard Way):
```python
import requests

response = requests.post(
    "https://api.redlen.com/api/v1/sensors",
    headers={"Authorization": "Bearer my-key"},
    json={"sensor_id": "SENSOR-001", "sensor_type": "temp", "location": "Lab"}
)
data = response.json()
```

### With Your SDK (Easy Way):
```python
from redlen_sdk import RedlenClient

client = RedlenClient(api_key="my-key")
sensor = client.sensors.create(
    sensor_id="SENSOR-001",
    sensor_type="temp",
    location="Lab"
)
```

## Key Concepts

### 1. SDK = Wrapper Around Your API
- Your FastAPI backend has endpoints
- SDK makes HTTP requests to those endpoints
- SDK hides complexity from customers

### 2. Resources Pattern
- Group related endpoints into resource classes
- `client.sensors.*` for sensor endpoints
- `client.readings.*` for reading endpoints

### 3. Error Handling
- Catch HTTP errors
- Convert to meaningful exceptions
- Customers get clear error messages

### 4. Type Safety
- Use Pydantic models
- Customers get IDE autocomplete
- Catch errors before API call

## Advanced Features

### Authentication
```python
class RedlenClient:
    def __init__(self, api_key: str = None, username: str = None, password: str = None):
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"
        elif username and password:
            # Login and get token
            token = self._login(username, password)
            self.session.headers["Authorization"] = f"Bearer {token}"
```

### Retry Logic
```python
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
self.session.mount("https://", adapter)
```

### Pagination
```python
def list_all(self):
    """Auto-paginate through all results"""
    page = 1
    all_items = []
    while True:
        response = self.list(page=page)
        all_items.extend(response['items'])
        if not response['has_more']:
            break
        page += 1
    return all_items
```

### Async Support
```python
import httpx

class AsyncRedlenClient:
    async def request(self, method: str, endpoint: str, **kwargs):
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, **kwargs)
            return response.json()
```

## Summary

Building an SDK is:
1. **Identify** your API endpoints
2. **Create** a Python package structure
3. **Write** client class that makes HTTP requests
4. **Organize** endpoints into resource classes
5. **Add** error handling and type safety
6. **Package** with setup.py
7. **Publish** to PyPI
8. **Document** with examples

Your SDK is just a Python package that makes it easier for customers to call your API!

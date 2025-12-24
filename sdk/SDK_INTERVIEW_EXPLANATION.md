# How to Explain SDKs in an Interview

## Question: "Can you explain what an SDK is and how you would build one?"

### Your Answer (2-3 minutes):

"Sure! An SDK - Software Development Kit - is essentially a client library that makes it easier for developers to integrate with an API. Let me explain with a concrete example.

## The Problem

Say I've built a sensor monitoring API with FastAPI. Without an SDK, every developer who wants to use my API has to write code like this:

```python
import requests

response = requests.post(
    'https://api.mycompany.com/sensors',
    headers={'Authorization': 'Bearer api-key-123'},
    json={'sensor_id': 'SENSOR-001', 'type': 'temperature'}
)

if response.status_code == 401:
    # Handle auth error
elif response.status_code == 429:
    # Handle rate limit
# ... more error handling

data = response.json()
```

That's tedious and error-prone. Every developer has to handle authentication, errors, retries, and understand the exact API structure.

## The Solution: Build an SDK

An SDK wraps all that complexity. With my SDK, developers just write:

```python
from my_sdk import Client

client = Client(api_key='api-key-123')
sensor = client.sensors.create(sensor_id='SENSOR-001', type='temperature')
```

Much cleaner! The SDK handles everything behind the scenes.

## How I Build an SDK

I follow a four-layer architecture:

### 1. Client Layer
The main entry point that handles authentication and HTTP requests:

```python
class Client:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers['Authorization'] = f'Bearer {api_key}'
        
        # Initialize resources
        self.sensors = SensorResource(self)
        self.readings = ReadingResource(self)
```

### 2. Resource Layer
Organizes endpoints by domain:

```python
class SensorResource:
    def __init__(self, client):
        self.client = client
    
    def create(self, sensor_id: str, type: str):
        return self.client.request('POST', '/sensors', 
                                   json={'sensor_id': sensor_id, 'type': type})
    
    def get(self, sensor_id: str):
        return self.client.request('GET', f'/sensors/{sensor_id}')
    
    def list(self, page: int = 1):
        return self.client.request('GET', '/sensors', params={'page': page})
```

### 3. Model Layer
Type-safe data models using Pydantic:

```python
from pydantic import BaseModel

class Sensor(BaseModel):
    sensor_id: str
    type: str
    status: str
    created_at: datetime
```

### 4. Exception Layer
Custom exceptions for better error handling:

```python
class SDKError(Exception):
    pass

class AuthenticationError(SDKError):
    pass

class RateLimitError(SDKError):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
```

## Key Features I Include

**1. Automatic Retries**
```python
from urllib3.util.retry import Retry

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503]
)
```

**2. Error Handling**
```python
if response.status_code == 401:
    raise AuthenticationError('Invalid API key')
elif response.status_code == 429:
    raise RateLimitError(retry_after=response.headers.get('Retry-After'))
```

**3. Pagination Support**
```python
def list_all(self):
    page = 1
    all_items = []
    while True:
        response = self.list(page=page)
        all_items.extend(response['items'])
        if not response.get('has_more'):
            break
        page += 1
    return all_items
```

## Distribution

I package it with setup.py and publish to PyPI:

```python
setup(
    name='my-company-sdk',
    version='1.0.0',
    packages=find_packages(),
    install_requires=['requests>=2.28.0', 'pydantic>=2.0.0']
)
```

Then developers can simply:
```bash
pip install my-company-sdk
```

## Real-World Examples

This is exactly how companies like Stripe, Twilio, and AWS distribute their SDKs. For instance:
- `pip install stripe` - Stripe's SDK
- `pip install twilio` - Twilio's SDK  
- `pip install boto3` - AWS's SDK

Each wraps their respective APIs to make integration easier.

## Benefits

1. **Developer Experience** - Clean, intuitive API
2. **Type Safety** - IDE autocomplete and type checking
3. **Error Handling** - Meaningful exceptions instead of HTTP codes
4. **Maintenance** - We can update the SDK without breaking customer code
5. **Documentation** - Built-in docstrings and examples

## Testing Strategy

I write unit tests that mock HTTP responses:

```python
def test_create_sensor(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {'sensor_id': 'SENSOR-001'}
    mocker.patch('requests.Session.request', return_value=mock_response)
    
    client = Client(api_key='test')
    sensor = client.sensors.create('SENSOR-001', 'temperature')
    
    assert sensor['sensor_id'] == 'SENSOR-001'
```

That's my approach to building SDKs - create a clean abstraction layer that makes API integration simple and reliable for developers."

---

## Follow-Up Questions You Might Get

### Q: "How is an SDK different from just making HTTP requests?"

**A:** "An SDK is essentially a wrapper around HTTP requests, but it provides significant value:

- **Abstraction**: Developers don't need to know HTTP details
- **Error Handling**: Converts HTTP status codes to meaningful exceptions
- **Retry Logic**: Automatically retries failed requests
- **Type Safety**: Validates data before sending
- **Documentation**: Built-in help and examples
- **Versioning**: We can update internals without breaking customer code

Think of it like the difference between writing raw SQL versus using an ORM like SQLAlchemy. Both talk to the database, but the ORM makes it much easier."

### Q: "How do you handle versioning in an SDK?"

**A:** "I use semantic versioning and maintain backward compatibility:

```python
# Version 1.0.0
client.sensors.create(sensor_id='S1', type='temp')

# Version 2.0.0 - add optional parameter, keep old signature working
client.sensors.create(sensor_id='S1', type='temp', location='Lab A')
```

For breaking changes, I:
1. Deprecate old methods with warnings
2. Release new major version
3. Maintain old version for 6-12 months
4. Provide migration guide

I also version the API endpoints:
```python
base_url = 'https://api.company.com/v1'  # or /v2, /v3
```

This lets customers upgrade at their own pace."

### Q: "How would you handle authentication in an SDK?"

**A:** "I support multiple auth methods:

```python
# API Key (simplest)
client = Client(api_key='key-123')

# OAuth2 (for user-specific access)
client = Client(access_token='oauth-token')

# Username/Password (auto-login)
client = Client(username='user', password='pass')
# SDK calls /auth/token internally and stores token

# Service Account (for server-to-server)
client = Client(service_account_file='credentials.json')
```

I also handle token refresh automatically:

```python
def request(self, method, endpoint, **kwargs):
    response = self.session.request(method, url, **kwargs)
    
    if response.status_code == 401:
        # Token expired, refresh it
        self.refresh_token()
        # Retry request
        response = self.session.request(method, url, **kwargs)
    
    return response
```

This is how Google's SDKs work - they handle OAuth refresh transparently."

### Q: "What about async support?"

**A:** "I provide both sync and async versions:

```python
# Sync version
from my_sdk import Client
client = Client(api_key='key')
sensor = client.sensors.create('S1', 'temp')

# Async version
from my_sdk import AsyncClient
client = AsyncClient(api_key='key')
sensor = await client.sensors.create('S1', 'temp')
```

Implementation uses httpx for async:

```python
class AsyncClient:
    async def request(self, method, endpoint, **kwargs):
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, **kwargs)
            return response.json()
```

This is important for high-performance applications that need to make many concurrent API calls."

### Q: "How do you test an SDK?"

**A:** "I use a multi-layer testing strategy:

**1. Unit Tests** - Mock HTTP responses:
```python
def test_create_sensor(mocker):
    mocker.patch('requests.post', return_value=mock_response)
    sensor = client.sensors.create('S1', 'temp')
    assert sensor.sensor_id == 'S1'
```

**2. Integration Tests** - Test against real API (staging):
```python
def test_integration():
    client = Client(api_key=STAGING_KEY, base_url=STAGING_URL)
    sensor = client.sensors.create('TEST-1', 'temp')
    assert sensor.status == 'active'
```

**3. Contract Tests** - Verify API hasn't changed:
```python
def test_api_contract():
    response = client.sensors.create('S1', 'temp')
    assert 'sensor_id' in response
    assert 'created_at' in response
```

**4. Example Tests** - Ensure documentation examples work:
```python
def test_readme_example():
    # Run code from README.md
    exec(open('examples/quickstart.py').read())
```

I also use tools like VCR.py to record/replay HTTP interactions for deterministic tests."

---

## Key Points to Emphasize

1. **SDK = Convenience Layer** - It's just a Python package that wraps HTTP calls
2. **Developer Experience** - The goal is to make integration easy
3. **Real Examples** - Reference Stripe, AWS, Twilio SDKs
4. **Architecture** - Client → Resources → Models → Exceptions
5. **Best Practices** - Error handling, retries, type safety, testing

## Pro Tip

If you have time, mention you've actually built one:

"I actually built an SDK for a sensor monitoring system I developed. It wraps a FastAPI backend and provides a clean interface for creating sensors, submitting readings, and querying analytics. I published it as a Python package and wrote comprehensive documentation with examples. The SDK reduced integration time for new users from hours to minutes."

This shows practical experience, not just theoretical knowledge!

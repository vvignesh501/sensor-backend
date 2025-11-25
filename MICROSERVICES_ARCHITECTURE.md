# Microservices Architecture

## Overview

Your application is now split into **4 independent microservices** with resilience patterns to ensure one service failure doesn't bring down the entire system.

## Architecture Diagram

```
                    ┌─────────────────┐
                    │   API Gateway   │
                    │   Port: 8000    │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
    ┌───────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┐
    │ Auth Service │  │   Sensor   │  │   Kafka    │
    │  Port: 8001  │  │  Service   │  │  Service   │
    │              │  │ Port: 8002 │  │ Port: 8003 │
    └──────┬───────┘  └─────┬──────┘  └─────┬──────┘
           │                │                │
           │                │                │
    ┌──────▼────────────────▼────────────────▼──────┐
    │            PostgreSQL Database                 │
    │               Port: 5434                       │
    └────────────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Kafka Broker   │
                    │   Port: 9092    │
                    └─────────────────┘
```

## Services

### 1. API Gateway (Port 8000)
**Purpose**: Single entry point, routes requests to microservices

**Features**:
- Circuit breaker pattern for each service
- Request routing and load balancing
- Aggregated health checks
- Automatic failover

**Resilience**:
- If Auth Service is down → Uses JWT fallback validation
- If Sensor Service is down → Returns 503 with retry message
- If Kafka Service is down → Queues events for later processing

### 2. Auth Service (Port 8001)
**Purpose**: User authentication and JWT token management

**Endpoints**:
- `POST /register` - User registration
- `POST /token` - Login and get JWT token
- `GET /verify` - Verify JWT token
- `GET /health` - Health check

**Resilience**:
- Database circuit breaker (opens after 3 failures)
- Graceful degradation when DB is down
- Independent failure domain

### 3. Sensor Service (Port 8002)
**Purpose**: Sensor testing and data processing

**Endpoints**:
- `POST /test/{sensor_type}` - Run sensor test
- `GET /test/{test_id}` - Get test results
- `GET /health` - Health check

**Resilience**:
- Background task processing (non-blocking)
- Fallback JWT validation if Auth Service is down
- Continues working even if Kafka Service is unavailable
- Database failures don't crash the service

### 4. Kafka Service (Port 8003)
**Purpose**: Event streaming and message queue

**Endpoints**:
- `POST /send-event` - Send event to Kafka
- `GET /stats` - Get processing statistics
- `GET /logs` - Get processing logs
- `GET /health` - Health check

**Resilience**:
- In-memory queue when Kafka broker is down
- Circuit breaker for Kafka connection
- Automatic retry mechanism
- Graceful degradation

## Resilience Patterns Implemented

### 1. Circuit Breaker Pattern
```python
# Opens after N failures, prevents cascading failures
if circuit_breaker["open"]:
    return "Service unavailable"
```

**Benefits**:
- Prevents cascading failures
- Fast failure response
- Automatic recovery detection

### 2. Graceful Degradation
```python
# Service continues with reduced functionality
if kafka_unavailable:
    queue_event_for_later()
    return "Event queued"
```

**Benefits**:
- System stays partially functional
- Better user experience
- No complete outages

### 3. Timeout & Retry
```python
# Prevents hanging requests
httpx.AsyncClient(timeout=5.0)
```

**Benefits**:
- Prevents resource exhaustion
- Fast failure detection
- Automatic recovery

### 4. Health Checks
```python
# Each service exposes /health endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

**Benefits**:
- Easy monitoring
- Automatic service discovery
- Load balancer integration

## Running the Microservices

### Option 1: Docker Compose (Recommended)
```bash
cd sensor-backend
docker-compose -f docker-compose.microservices.yml up --build
```

### Option 2: Run Individually (Development)
```bash
# Terminal 1 - Auth Service
cd sensor-backend/services/auth-service
python main.py

# Terminal 2 - Sensor Service
cd sensor-backend/services/sensor-service
python main.py

# Terminal 3 - Kafka Service
cd sensor-backend/services/kafka-service
python main.py

# Terminal 4 - API Gateway
cd sensor-backend/services/api-gateway
python main.py
```

## Testing Resilience

### Test 1: Kill Auth Service
```bash
# Stop auth service
docker stop auth-service

# Try to test sensor (should still work with fallback)
curl -X POST http://localhost:8000/test/sensor/temperature \
  -H "Authorization: Bearer <token>"

# Result: ✅ Works with JWT fallback validation
```

### Test 2: Kill Kafka Service
```bash
# Stop Kafka service
docker stop kafka-service

# Try to test sensor
curl -X POST http://localhost:8000/test/sensor/temperature \
  -H "Authorization: Bearer <token>"

# Result: ✅ Works, events queued for later
```

### Test 3: Kill Database
```bash
# Stop database
docker stop sensor-postgres

# Try to test sensor
curl -X POST http://localhost:8000/test/sensor/temperature \
  -H "Authorization: Bearer <token>"

# Result: ✅ Returns 503 but doesn't crash
```

### Test 4: Check Health
```bash
# Check overall system health
curl http://localhost:8000/health

# Response shows status of each service:
{
  "gateway": "healthy",
  "overall_status": "degraded",
  "services": {
    "auth": {"status": "unavailable"},
    "sensor": {"status": "healthy"},
    "kafka": {"status": "healthy"}
  },
  "circuit_breakers": {
    "auth": {"open": true, "failures": 5}
  }
}
```

## Monitoring

### Health Check Endpoints
- Gateway: `http://localhost:8000/health`
- Auth: `http://localhost:8001/health`
- Sensor: `http://localhost:8002/health`
- Kafka: `http://localhost:8003/health`

### Circuit Breaker Status
```bash
curl http://localhost:8000/health | jq '.circuit_breakers'
```

### Reset Circuit Breaker
```bash
curl -X POST http://localhost:8000/circuit-breaker/reset/auth
```

## Scaling

### Horizontal Scaling
```yaml
# In docker-compose.microservices.yml
sensor-service:
  deploy:
    replicas: 3  # Run 3 instances
```

### Load Balancing
Add nginx or traefik in front of API Gateway:
```nginx
upstream sensor_backend {
    server api-gateway-1:8000;
    server api-gateway-2:8000;
    server api-gateway-3:8000;
}
```

## Benefits of This Architecture

1. **Fault Isolation**: One service failure doesn't crash others
2. **Independent Deployment**: Deploy services separately
3. **Technology Flexibility**: Each service can use different tech
4. **Scalability**: Scale services independently based on load
5. **Maintainability**: Smaller, focused codebases
6. **Resilience**: Circuit breakers prevent cascading failures
7. **Observability**: Clear service boundaries and health checks

## Migration from Monolith

Your original `app/main.py` is now split into:
- Auth logic → `services/auth-service/main.py`
- Sensor logic → `services/sensor-service/main.py`
- Kafka logic → `services/kafka-service/main.py`
- Routing → `services/api-gateway/main.py`

All services can run independently and communicate via HTTP/REST APIs.

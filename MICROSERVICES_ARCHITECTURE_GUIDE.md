# How to Architect a Microservice

## Table of Contents
1. [Core Principles](#core-principles)
2. [Service Boundaries](#service-boundaries)
3. [Communication Patterns](#communication-patterns)
4. [Data Management](#data-management)
5. [Resilience Patterns](#resilience-patterns)
6. [Deployment Strategy](#deployment-strategy)
7. [Monitoring & Observability](#monitoring--observability)
8. [Security](#security)
9. [Common Pitfalls](#common-pitfalls)
10. [Real Example Walkthrough](#real-example-walkthrough)

---

## Core Principles

### 1. Single Responsibility Principle
Each microservice should do **one thing well**.

**❌ Bad Example**:
```python
# UserService that does everything
class UserService:
    def register_user()
    def authenticate_user()
    def process_payments()
    def send_emails()
    def generate_reports()
```

**✅ Good Example**:
```python
# Separate services
AuthService:      register_user(), authenticate_user()
PaymentService:   process_payments()
NotificationService: send_emails()
ReportService:    generate_reports()
```

### 2. Loose Coupling
Services should be independent and communicate through well-defined APIs.

**❌ Bad Example**:
```python
# Direct database access across services
class OrderService:
    def create_order(self):
        # Directly accessing user database
        user = UserDatabase.query("SELECT * FROM users WHERE id=?")
```

**✅ Good Example**:
```python
# API communication
class OrderService:
    async def create_order(self):
        # Call User Service API
        user = await http_client.get(f"{USER_SERVICE}/users/{user_id}")
```

### 3. High Cohesion
Related functionality should be grouped together.

**✅ Good Example**:
```python
# Auth Service - all auth-related functionality together
class AuthService:
    def register()
    def login()
    def verify_token()
    def refresh_token()
    def logout()
    def reset_password()
```

---

## Service Boundaries

### How to Identify Service Boundaries

#### 1. Domain-Driven Design (DDD)
Identify **bounded contexts** in your domain.

**Example: E-commerce System**
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  User Context   │  │  Order Context  │  │ Payment Context │
│                 │  │                 │  │                 │
│ - Registration  │  │ - Create Order  │  │ - Process Pay   │
│ - Login         │  │ - Track Order   │  │ - Refund        │
│ - Profile       │  │ - Cancel Order  │  │ - Verify        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

Each bounded context becomes a microservice.

#### 2. Business Capabilities
Organize around business functions.

**Example: Sensor Backend**
```
Authentication Capability  → Auth Service
Sensor Testing Capability  → Sensor Service
Event Streaming Capability → Kafka Service
```

#### 3. Data Ownership
Each service owns its data.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Auth Service │     │Sensor Service│     │Kafka Service │
│              │     │              │     │              │
│ ┌──────────┐ │     │ ┌──────────┐ │     │ ┌──────────┐ │
│ │Users DB  │ │     │ │Tests DB  │ │     │ │Events DB │ │
│ └──────────┘ │     │ └──────────┘ │     │ └──────────┘ │
└──────────────┘     └──────────────┘     └──────────────┘
```

**Rule**: Never access another service's database directly!

#### 4. Team Structure (Conway's Law)
Services should align with team boundaries.

```
Team A → Auth Service
Team B → Sensor Service
Team C → Kafka Service
```

### Service Size Guidelines

**Micro** doesn't mean tiny. Consider:

- **Lines of Code**: 1,000 - 10,000 lines
- **Team Size**: 2-5 developers can maintain it
- **Deployment Time**: < 15 minutes
- **Startup Time**: < 30 seconds
- **Cognitive Load**: One developer can understand it in a week

---

## Communication Patterns

### 1. Synchronous Communication (REST/HTTP)

**When to Use**:
- Need immediate response
- Simple request-response
- User-facing operations

**Example**:
```python
# API Gateway calling Auth Service
@app.post("/auth/login")
async def login(credentials):
    # Synchronous HTTP call
    response = await http_client.post(
        f"{AUTH_SERVICE}/token",
        data=credentials
    )
    return response.json()
```

**Pros**:
- Simple to implement
- Easy to debug
- Immediate feedback

**Cons**:
- Tight coupling
- Cascading failures
- Higher latency

### 2. Asynchronous Communication (Message Queue)

**When to Use**:
- Don't need immediate response
- Event-driven workflows
- High throughput needed

**Example**:
```python
# Sensor Service publishing event
@app.post("/test/sensor")
async def test_sensor():
    # Process test
    result = process_test()
    
    # Publish event (fire and forget)
    await kafka_producer.send("sensor-tested", result)
    
    return {"status": "processing"}
```

**Pros**:
- Loose coupling
- Better resilience
- Higher throughput

**Cons**:
- More complex
- Eventual consistency
- Harder to debug

### 3. Hybrid Approach (Recommended)

```python
# Synchronous for critical path
user = await auth_service.verify_token(token)  # Must succeed

# Asynchronous for side effects
await event_bus.publish("user-logged-in", user)  # Can fail
await notification_service.send_email(user)  # Can fail
```

### Communication Patterns Comparison

| Pattern | Use Case | Example |
|---------|----------|---------|
| **REST API** | CRUD operations | Get user profile |
| **GraphQL** | Complex queries | Fetch nested data |
| **gRPC** | High performance | Internal service calls |
| **Message Queue** | Events | Order placed |
| **WebSocket** | Real-time | Live updates |
| **Server-Sent Events** | One-way streaming | Notifications |

---

## Data Management

### 1. Database Per Service Pattern

**✅ Recommended**:
```
Auth Service    → PostgreSQL (users table)
Sensor Service  → PostgreSQL (tests table)
Kafka Service   → MongoDB (events collection)
```

**Benefits**:
- Service independence
- Technology flexibility
- Easier scaling

### 2. Shared Database Anti-Pattern

**❌ Avoid**:
```
All Services → Single PostgreSQL Database
```

**Problems**:
- Tight coupling
- Schema changes affect all services
- Scaling bottleneck

### 3. Data Consistency Strategies

#### Eventual Consistency (Recommended for Microservices)

```python
# Order Service
@app.post("/orders")
async def create_order(order_data):
    # 1. Create order locally
    order = await db.create_order(order_data)
    
    # 2. Publish event
    await event_bus.publish("order-created", order)
    
    # 3. Return immediately
    return {"order_id": order.id, "status": "pending"}

# Inventory Service (listens to events)
@event_handler("order-created")
async def handle_order_created(order):
    # Eventually update inventory
    await db.update_inventory(order.items)
```

#### Saga Pattern (for Distributed Transactions)

```python
# Orchestration-based Saga
class OrderSaga:
    async def execute(self, order):
        try:
            # Step 1: Reserve inventory
            await inventory_service.reserve(order.items)
            
            # Step 2: Process payment
            await payment_service.charge(order.total)
            
            # Step 3: Create shipment
            await shipping_service.create(order)
            
            return {"status": "success"}
        except Exception as e:
            # Compensating transactions
            await self.rollback(order)
            return {"status": "failed"}
    
    async def rollback(self, order):
        await inventory_service.release(order.items)
        await payment_service.refund(order.total)
```

### 4. Data Synchronization

**Event Sourcing**:
```python
# Store events instead of current state
events = [
    {"type": "OrderCreated", "data": {...}},
    {"type": "PaymentProcessed", "data": {...}},
    {"type": "OrderShipped", "data": {...}}
]

# Rebuild state from events
def get_order_state(order_id):
    events = event_store.get_events(order_id)
    state = {}
    for event in events:
        state = apply_event(state, event)
    return state
```

**CQRS (Command Query Responsibility Segregation)**:
```python
# Write Model (Commands)
class OrderWriteService:
    async def create_order(self, data):
        order = Order(**data)
        await db.save(order)
        await event_bus.publish("order-created", order)

# Read Model (Queries)
class OrderReadService:
    async def get_order(self, order_id):
        # Optimized read-only view
        return await read_db.query(order_id)
```

---

## Resilience Patterns

### 1. Circuit Breaker Pattern

**Purpose**: Prevent cascading failures

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time = None
    
    async def call(self, func, *args, **kwargs):
        # Check if circuit is open
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError("Service unavailable")
        
        try:
            result = await func(*args, **kwargs)
            
            # Success - reset circuit
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
            self.failure_count = 0
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            # Open circuit if threshold reached
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                print(f"Circuit breaker OPENED")
            
            raise e

# Usage
circuit_breaker = CircuitBreaker()

@app.get("/users/{user_id}")
async def get_user(user_id):
    return await circuit_breaker.call(
        user_service.get_user,
        user_id
    )
```

### 2. Retry Pattern

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def call_external_service():
    response = await http_client.get(url)
    return response.json()
```

### 3. Timeout Pattern

```python
import asyncio

async def call_with_timeout(func, timeout=5.0):
    try:
        return await asyncio.wait_for(func(), timeout=timeout)
    except asyncio.TimeoutError:
        raise HTTPException(504, "Service timeout")

# Usage
@app.get("/data")
async def get_data():
    return await call_with_timeout(
        lambda: external_service.fetch_data(),
        timeout=5.0
    )
```

### 4. Bulkhead Pattern

**Purpose**: Isolate resources to prevent total failure

```python
# Separate connection pools for different services
auth_pool = asyncpg.create_pool(min_size=5, max_size=10)
sensor_pool = asyncpg.create_pool(min_size=10, max_size=20)

# If auth pool exhausted, sensor pool still works
```

### 5. Rate Limiting

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/resource")
@limiter.limit("10/minute")
async def create_resource():
    return {"status": "created"}
```

### 6. Graceful Degradation

```python
@app.get("/recommendations")
async def get_recommendations(user_id):
    try:
        # Try ML service
        return await ml_service.get_recommendations(user_id)
    except Exception:
        # Fallback to simple algorithm
        return await simple_recommendations(user_id)
```

---

## Deployment Strategy

### 1. Containerization (Docker)

```dockerfile
# Dockerfile for each service
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Orchestration (Kubernetes)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  replicas: 3  # Run 3 instances
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: auth-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: auth-service
spec:
  selector:
    app: auth-service
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP
```

### 3. Service Mesh (Istio)

```yaml
# Virtual Service for traffic management
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: auth-service
spec:
  hosts:
  - auth-service
  http:
  - match:
    - headers:
        version:
          exact: v2
    route:
    - destination:
        host: auth-service
        subset: v2
  - route:
    - destination:
        host: auth-service
        subset: v1
      weight: 90
    - destination:
        host: auth-service
        subset: v2
      weight: 10  # Canary deployment
```

### 4. CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy Microservice

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest tests/
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: docker build -t auth-service:${{ github.sha }} .
      
      - name: Push to registry
        run: docker push auth-service:${{ github.sha }}
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/auth-service \
            auth-service=auth-service:${{ github.sha }}
          kubectl rollout status deployment/auth-service
```

---

## Monitoring & Observability

### 1. Health Checks

```python
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database(),
        "cache": await check_cache(),
        "external_api": await check_external_api()
    }
    
    status = "healthy" if all(checks.values()) else "degraded"
    
    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

async def check_database():
    try:
        await db.execute("SELECT 1")
        return True
    except:
        return False
```

### 2. Metrics (Prometheus)

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
active_connections = Gauge('active_connections', 'Active database connections')

# Instrument code
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    request_duration.observe(duration)
    
    return response
```

### 3. Logging (Structured)

```python
import structlog

logger = structlog.get_logger()

@app.post("/orders")
async def create_order(order_data):
    logger.info(
        "order_created",
        order_id=order.id,
        user_id=order.user_id,
        total=order.total,
        items_count=len(order.items)
    )
```

### 4. Distributed Tracing (Jaeger)

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

tracer = trace.get_tracer(__name__)

@app.get("/users/{user_id}")
async def get_user(user_id):
    with tracer.start_as_current_span("get_user") as span:
        span.set_attribute("user_id", user_id)
        
        # Call database
        with tracer.start_as_current_span("db_query"):
            user = await db.fetch_user(user_id)
        
        # Call cache
        with tracer.start_as_current_span("cache_set"):
            await cache.set(f"user:{user_id}", user)
        
        return user
```

---

## Security

### 1. Authentication & Authorization

```python
# JWT-based authentication
from jose import jwt

def create_token(user_id: str, scopes: List[str]):
    payload = {
        "sub": user_id,
        "scopes": scopes,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str, required_scopes: List[str]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        # Check scopes
        token_scopes = payload.get("scopes", [])
        if not all(scope in token_scopes for scope in required_scopes):
            raise HTTPException(403, "Insufficient permissions")
        
        return payload
    except jwt.JWTError:
        raise HTTPException(401, "Invalid token")

# Usage
@app.get("/admin/users")
async def get_all_users(token: str = Depends(oauth2_scheme)):
    verify_token(token, required_scopes=["admin"])
    return await db.fetch_all_users()
```

### 2. API Gateway Security

```python
# Rate limiting
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    client_ip = request.client.host
    
    # Check rate limit
    requests = await redis.incr(f"rate_limit:{client_ip}")
    await redis.expire(f"rate_limit:{client_ip}", 60)
    
    if requests > 100:  # 100 requests per minute
        raise HTTPException(429, "Too many requests")
    
    return await call_next(request)

# Input validation
from pydantic import BaseModel, validator

class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    
    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum(), 'must be alphanumeric'
        return v
    
    @validator('password')
    def password_strength(cls, v):
        assert len(v) >= 8, 'must be at least 8 characters'
        return v
```

### 3. Service-to-Service Authentication

```python
# mTLS (Mutual TLS)
import ssl

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain('service.crt', 'service.key')
ssl_context.load_verify_locations('ca.crt')

# Use in HTTP client
async with httpx.AsyncClient(verify=ssl_context) as client:
    response = await client.get(url)
```

---

## Common Pitfalls

### 1. ❌ Too Many Microservices

**Problem**: Creating a microservice for every function

**Solution**: Start with a monolith, split when needed

### 2. ❌ Distributed Monolith

**Problem**: Services that are tightly coupled

```python
# Bad: Service A directly depends on Service B's database
class ServiceA:
    def process(self):
        data = ServiceBDatabase.query(...)  # ❌
```

**Solution**: Use APIs, not shared databases

### 3. ❌ Chatty Services

**Problem**: Too many inter-service calls

```python
# Bad: N+1 problem
for order in orders:
    user = await user_service.get_user(order.user_id)  # ❌
    product = await product_service.get_product(order.product_id)  # ❌
```

**Solution**: Batch requests or denormalize data

```python
# Good: Batch request
user_ids = [order.user_id for order in orders]
users = await user_service.get_users_batch(user_ids)  # ✅
```

### 4. ❌ No Monitoring

**Problem**: Can't see what's happening

**Solution**: Implement logging, metrics, and tracing from day one

### 5. ❌ Ignoring Data Consistency

**Problem**: Assuming strong consistency

**Solution**: Design for eventual consistency

---

## Real Example Walkthrough

Let's architect a **Payment Processing System**:

### Step 1: Identify Services

```
1. User Service - User management
2. Payment Service - Process payments
3. Order Service - Manage orders
4. Notification Service - Send emails/SMS
5. Fraud Detection Service - Check for fraud
```

### Step 2: Define APIs

```python
# User Service
GET    /users/{id}
POST   /users
PUT    /users/{id}

# Payment Service
POST   /payments
GET    /payments/{id}
POST   /payments/{id}/refund

# Order Service
POST   /orders
GET    /orders/{id}
PUT    /orders/{id}/status

# Notification Service
POST   /notifications/email
POST   /notifications/sms

# Fraud Detection Service
POST   /fraud/check
```

### Step 3: Design Communication

```python
# Synchronous: Order → Payment
@app.post("/orders")
async def create_order(order_data):
    # 1. Validate user
    user = await user_service.get_user(order_data.user_id)
    
    # 2. Check fraud (synchronous - must pass)
    fraud_check = await fraud_service.check(order_data)
    if fraud_check.is_fraud:
        raise HTTPException(400, "Fraud detected")
    
    # 3. Process payment (synchronous - must succeed)
    payment = await payment_service.charge(order_data.total)
    
    # 4. Create order
    order = await db.create_order(order_data)
    
    # 5. Send notification (asynchronous - can fail)
    await event_bus.publish("order-created", order)
    
    return order
```

### Step 4: Implement Resilience

```python
# Circuit breaker for payment service
payment_circuit = CircuitBreaker(failure_threshold=5)

@app.post("/orders")
async def create_order(order_data):
    try:
        payment = await payment_circuit.call(
            payment_service.charge,
            order_data.total
        )
    except CircuitBreakerOpenError:
        # Fallback: Queue for later processing
        await queue.enqueue("pending-payments", order_data)
        return {"status": "pending", "message": "Payment queued"}
```

### Step 5: Deploy

```yaml
# docker-compose.yml
version: '3.8'
services:
  user-service:
    build: ./user-service
    ports: ["8001:8001"]
  
  payment-service:
    build: ./payment-service
    ports: ["8002:8002"]
  
  order-service:
    build: ./order-service
    ports: ["8003:8003"]
  
  notification-service:
    build: ./notification-service
    ports: ["8004:8004"]
  
  fraud-service:
    build: ./fraud-service
    ports: ["8005:8005"]
```

---

## Summary Checklist

When architecting a microservice, ensure:

- [ ] **Single Responsibility**: Does one thing well
- [ ] **Loose Coupling**: Independent of other services
- [ ] **High Cohesion**: Related functionality grouped
- [ ] **Own Database**: Doesn't share data store
- [ ] **API Contract**: Well-defined interface
- [ ] **Resilience**: Circuit breakers, retries, timeouts
- [ ] **Monitoring**: Health checks, metrics, logs
- [ ] **Security**: Authentication, authorization, encryption
- [ ] **Documentation**: API docs, architecture diagrams
- [ ] **Testing**: Unit, integration, contract tests
- [ ] **Deployment**: Containerized, automated CI/CD
- [ ] **Scalability**: Can scale independently

---

## Further Reading

- **Books**:
  - "Building Microservices" by Sam Newman
  - "Microservices Patterns" by Chris Richardson
  - "Domain-Driven Design" by Eric Evans

- **Patterns**:
  - https://microservices.io/patterns
  - https://martinfowler.com/microservices

- **Tools**:
  - Docker, Kubernetes
  - Istio, Linkerd (Service Mesh)
  - Prometheus, Grafana (Monitoring)
  - Jaeger, Zipkin (Tracing)

Your sensor backend implementation demonstrates these principles in action! 🚀

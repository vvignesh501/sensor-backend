# Distributed Systems Interview Guide

Complete guide to explaining distributed systems concepts using your sensor backend project.

## Table of Contents
1. [What is a Distributed System?](#what-is-a-distributed-system)
2. [Core Concepts](#core-concepts)
3. [Your Project Examples](#your-project-examples)
4. [Common Interview Questions](#common-interview-questions)
5. [Design Patterns](#design-patterns)
6. [Trade-offs and Challenges](#trade-offs-and-challenges)

---

## What is a Distributed System?

### Simple Definition
"A distributed system is a collection of independent computers that appear to users as a single coherent system."

### Your Answer for Interview
"A distributed system is when you have multiple services running on different machines that work together to accomplish a task. In my sensor monitoring project, I have:
- Multiple API servers handling requests
- A Kafka message queue for async processing
- PostgreSQL database for storage
- Lambda functions for data processing
- Redis for caching

These all run independently but coordinate to provide a unified sensor monitoring platform."

---

## Core Concepts

### 1. Scalability

**What it means:** Ability to handle increased load by adding resources.

**Types:**
- **Vertical Scaling (Scale Up):** Bigger machine (more CPU/RAM)
- **Horizontal Scaling (Scale Out):** More machines

**Your Example:**
```
Interview: "How did you handle scalability?"

You: "I implemented horizontal scaling using AWS ECS with auto-scaling. 
When CPU usage exceeds 70%, ECS automatically spins up additional 
containers. I also used a load balancer (ALB) to distribute traffic 
across multiple instances.

For the database, I used connection pooling to handle 1000+ concurrent 
requests efficiently. I tested this with load tests that simulated 
1000 concurrent users."
```

**Code Reference:**
```python
# Your scaling implementation
class ScaledAsyncDatabase:
    def __init__(self):
        self.pool = await asyncpg.create_pool(
            min_size=1,
            max_size=5,  # Scales connections based on load
            max_inactive_connection_lifetime=60
        )
```

### 2. Availability

**What it means:** System remains operational even when components fail.

**Measured as:** Uptime percentage (99.9% = "three nines")

**Your Example:**
```
Interview: "How did you ensure high availability?"

You: "I implemented several strategies:

1. **Multiple Instances:** Run 3+ API servers behind a load balancer. 
   If one fails, others handle traffic.

2. **Health Checks:** Load balancer pings /health endpoint every 30s. 
   Unhealthy instances are removed from rotation.

3. **Graceful Degradation:** If Kafka is down, I queue messages in 
   memory and retry. System stays operational.

4. **Database Failover:** PostgreSQL with read replicas. If primary 
   fails, promote replica.

5. **Circuit Breaker Pattern:** If external service fails, stop 
   calling it to prevent cascading failures."
```

**Code Reference:**
```python
# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        await db.fetch_one("SELECT 1")
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database unhealthy")
```

### 3. Consistency

**What it means:** All nodes see the same data at the same time.

**CAP Theorem:** You can only have 2 of 3:
- **C**onsistency
- **A**vailability  
- **P**artition Tolerance

**Your Example:**
```
Interview: "How did you handle data consistency?"

You: "I used different consistency models for different use cases:

1. **Strong Consistency (PostgreSQL):** For critical data like user 
   accounts and sensor configurations. ACID transactions ensure 
   consistency.

2. **Eventual Consistency (Kafka):** For sensor readings. It's okay 
   if analytics are delayed by a few seconds. This gives us better 
   availability and throughput.

3. **Idempotency:** All API endpoints are idempotent. If a request 
   is retried, it produces the same result. This prevents duplicate 
   sensor readings.

I chose availability over immediate consistency for sensor data 
because it's more important that the system stays up than that 
analytics are real-time."
```

**Code Reference:**
```python
# Idempotent sensor creation
@app.post("/api/v1/sensors")
async def create_sensor(sensor_id: str):
    # Check if exists first (idempotent)
    existing = await db.fetch_one(
        "SELECT * FROM sensors WHERE sensor_id = $1", 
        sensor_id
    )
    if existing:
        return existing  # Return existing, don't create duplicate
    
    # Create new
    return await db.execute_transaction([
        ("INSERT INTO sensors ...", (sensor_id, ...))
    ])
```

### 4. Partition Tolerance

**What it means:** System continues working even if network splits.

**Your Example:**
```
Interview: "How did you handle network partitions?"

You: "I designed for partition tolerance in several ways:

1. **Async Communication:** Used Kafka for inter-service communication. 
   If network is slow, messages queue up and process when available.

2. **Timeouts:** All HTTP requests have timeouts (30s). Don't wait 
   forever for a response.

3. **Retry Logic:** Exponential backoff for failed requests. Retry 
   3 times with increasing delays (1s, 2s, 4s).

4. **Circuit Breaker:** After 5 consecutive failures, stop trying 
   for 60s. Prevents overwhelming a struggling service.

5. **Local Caching:** Cache frequently accessed data (user sessions, 
   sensor metadata) so we can operate even if database is unreachable."
```

### 5. Load Balancing

**What it means:** Distribute work across multiple servers.

**Algorithms:**
- Round Robin: Server 1, 2, 3, 1, 2, 3...
- Least Connections: Send to server with fewest active connections
- IP Hash: Same client always goes to same server

**Your Example:**
```
Interview: "How did you implement load balancing?"

You: "I used AWS Application Load Balancer (ALB) with these features:

1. **Round Robin Distribution:** Requests distributed evenly across 
   3 backend instances.

2. **Health Checks:** ALB pings /health every 30s. Unhealthy instances 
   removed automatically.

3. **Sticky Sessions:** For authenticated users, ALB uses cookies to 
   route to same instance (for session consistency).

4. **SSL Termination:** ALB handles HTTPS, backends use HTTP. Reduces 
   CPU load on application servers.

I also implemented Nginx as a reverse proxy for advanced features 
like rate limiting and request buffering."
```

**Code Reference (nginx.conf):**
```nginx
upstream backend {
    least_conn;  # Load balancing algorithm
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://backend;
        proxy_next_upstream error timeout;  # Retry on failure
    }
}
```

### 6. Message Queues

**What it means:** Async communication between services.

**Benefits:**
- Decoupling: Services don't need to know about each other
- Buffering: Handle traffic spikes
- Reliability: Messages persist if consumer is down

**Your Example:**
```
Interview: "Why did you use Kafka?"

You: "I used Kafka for asynchronous sensor data processing:

1. **Decoupling:** API servers publish sensor readings to Kafka. 
   They don't wait for processing to complete. This keeps API 
   response times fast (<100ms).

2. **Scalability:** Can add more consumers to process messages faster. 
   Started with 1 consumer, scaled to 3 during high load.

3. **Reliability:** Messages persist in Kafka for 7 days. If a 
   consumer crashes, it can resume from where it left off.

4. **Ordering:** Kafka guarantees message order within a partition. 
   All readings from sensor-001 go to same partition, maintaining 
   time-series order.

5. **Backpressure:** If database is slow, messages queue in Kafka 
   instead of overwhelming the API."
```

**Code Reference:**
```python
# Producer (API server)
class SensorEventProducer:
    def send_test_event(self, event: dict):
        self.producer.send(
            'sensor-events',
            value=event,
            key=event['sensor_id'].encode()  # Partition by sensor_id
        )

# Consumer (separate service)
consumer = KafkaConsumer('sensor-events')
for message in consumer:
    process_sensor_reading(message.value)
    # Commit offset after successful processing
    consumer.commit()
```

### 7. Caching

**What it means:** Store frequently accessed data in fast storage.

**Levels:**
- Application Cache (in-memory)
- Distributed Cache (Redis)
- CDN Cache (for static assets)

**Your Example:**
```
Interview: "How did you use caching?"

You: "I implemented multi-level caching:

1. **Application Cache:** In-memory cache for JWT tokens and user 
   sessions. Avoids database lookup on every request. 99% hit rate.

2. **Database Connection Pool:** Reuse database connections instead 
   of creating new ones. Reduced connection overhead by 90%.

3. **Query Result Cache:** Cache sensor metadata (rarely changes) 
   for 5 minutes. Reduced database load by 60%.

4. **CDN Caching:** Static assets (dashboard UI) cached at edge 
   locations. Reduced latency from 200ms to 20ms for global users.

Cache invalidation strategy: Time-based expiry (TTL) for most data, 
explicit invalidation for critical updates."
```

**Code Reference:**
```python
# Simple in-memory cache
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_sensor_metadata(sensor_id: str):
    return db.fetch_one(
        "SELECT * FROM sensors WHERE sensor_id = $1",
        sensor_id
    )

# Cache expires after 5 minutes
@app.get("/sensors/{sensor_id}")
async def get_sensor(sensor_id: str):
    # Check cache first
    cached = cache.get(f"sensor:{sensor_id}")
    if cached:
        return cached
    
    # Cache miss - fetch from DB
    sensor = await db.fetch_one(...)
    cache.set(f"sensor:{sensor_id}", sensor, ttl=300)
    return sensor
```

### 8. Database Sharding

**What it means:** Split database across multiple servers.

**Types:**
- Horizontal: Split rows (users 1-1000 on DB1, 1001-2000 on DB2)
- Vertical: Split tables (users on DB1, orders on DB2)

**Your Example:**
```
Interview: "How would you shard your database?"

You: "For my sensor system, I'd use horizontal sharding by sensor_id:

1. **Sharding Key:** sensor_id (e.g., SENSOR-001)
2. **Hash Function:** hash(sensor_id) % num_shards
3. **Shard Assignment:**
   - Shard 0: SENSOR-001 to SENSOR-333
   - Shard 1: SENSOR-334 to SENSOR-666
   - Shard 2: SENSOR-667 to SENSOR-999

Benefits:
- Each shard handles 1/3 of traffic
- Queries for single sensor hit only one shard
- Can scale to millions of sensors

Challenges:
- Cross-shard queries are expensive (e.g., 'get all sensors')
- Rebalancing when adding shards is complex
- Need consistent hashing to minimize data movement

For now, I use read replicas instead of sharding since we're under 
1M sensors. Sharding would be the next step."
```

### 9. Microservices Architecture

**What it means:** Break application into small, independent services.

**Your Example:**
```
Interview: "Explain your microservices architecture."

You: "I designed a microservices architecture with 4 services:

1. **API Gateway (Port 8000)**
   - Entry point for all requests
   - Authentication/authorization
   - Rate limiting
   - Routes to appropriate service

2. **Sensor Service (Port 8001)**
   - Manages sensor CRUD operations
   - Validates sensor data
   - Publishes events to Kafka

3. **Auth Service (Port 8002)**
   - User authentication (JWT)
   - Role-based access control
   - Token refresh

4. **Kafka Service (Port 8003)**
   - Consumes sensor events
   - Processes and stores in database
   - Triggers alerts for anomalies

Communication:
- Synchronous: HTTP/REST between services
- Asynchronous: Kafka for event-driven workflows

Benefits:
- Independent deployment (update one service without affecting others)
- Technology flexibility (could use Go for high-performance service)
- Team autonomy (different teams own different services)
- Fault isolation (if auth service fails, sensor reads still work)

Challenges:
- Network latency between services
- Distributed tracing needed (implemented with OpenTelemetry)
- More complex deployment (using Docker Compose + Kubernetes)"
```

**Code Reference (docker-compose.microservices.yml):**
```yaml
services:
  api-gateway:
    build: ./services/api-gateway
    ports: ["8000:8000"]
    
  sensor-service:
    build: ./services/sensor-service
    ports: ["8001:8001"]
    
  auth-service:
    build: ./services/auth-service
    ports: ["8002:8002"]
    
  kafka-service:
    build: ./services/kafka-service
    ports: ["8003:8003"]
```

### 10. Monitoring & Observability

**What it means:** Understanding what's happening in your system.

**Three Pillars:**
- **Metrics:** Numbers (CPU, memory, request rate)
- **Logs:** Text records of events
- **Traces:** Request flow through services

**Your Example:**
```
Interview: "How did you monitor your distributed system?"

You: "I implemented comprehensive observability:

1. **Metrics (CloudWatch)**
   - Request rate, latency, error rate
   - Database connection pool usage
   - Kafka consumer lag
   - Custom metrics: sensors_processed_per_minute

2. **Logs (Structured Logging)**
   - JSON format for easy parsing
   - Correlation IDs to track requests across services
   - Log levels: DEBUG, INFO, WARNING, ERROR

3. **Distributed Tracing (OpenTelemetry + Jaeger)**
   - Trace requests across all microservices
   - Identify bottlenecks (e.g., slow database query)
   - Visualize service dependencies

4. **Alerting**
   - CloudWatch alarms for high error rates
   - Slack notifications for critical issues
   - PagerDuty for on-call escalation

5. **Dashboards**
   - Real-time dashboard showing system health
   - Kafka processing stats
   - Database performance metrics

This helped me identify and fix a connection leak that was causing 
memory issues in production."
```

**Code Reference:**
```python
# Structured logging
import logging
import json

logger = logging.getLogger(__name__)

@app.post("/sensors")
async def create_sensor(sensor_id: str, request_id: str):
    logger.info(json.dumps({
        "event": "sensor_created",
        "sensor_id": sensor_id,
        "request_id": request_id,  # Correlation ID
        "timestamp": datetime.utcnow().isoformat()
    }))
```

---

## Common Interview Questions

### Q1: "Design a URL shortener like bit.ly"

**Your Answer:**
```
"I'd design it as a distributed system with these components:

1. **API Servers (Multiple Instances)**
   - Generate short URLs
   - Redirect short URLs to original
   - Load balanced with ALB

2. **Database (PostgreSQL with Sharding)**
   - Store mappings: short_url → original_url
   - Shard by hash(short_url) for horizontal scaling
   - Read replicas for redirect traffic (read-heavy)

3. **Cache (Redis)**
   - Cache popular URLs (80/20 rule)
   - TTL: 24 hours
   - Reduces database load by 90%

4. **URL Generation**
   - Base62 encoding of auto-increment ID
   - Distributed ID generation (Snowflake algorithm)
   - Ensures uniqueness across servers

5. **Analytics (Kafka + Data Warehouse)**
   - Track clicks asynchronously
   - Don't slow down redirects
   - Process in batch for analytics

Scalability:
- Handle 10,000 requests/sec with 10 API servers
- 1 billion URLs stored across 10 database shards
- 99.99% availability with multi-region deployment

This is similar to how I designed my sensor system with load 
balancing, caching, and async processing."
```

### Q2: "How do you handle distributed transactions?"

**Your Answer:**
```
"Distributed transactions are challenging. I use these patterns:

1. **Saga Pattern (My Preferred Approach)**
   - Break transaction into steps
   - Each step is a local transaction
   - If step fails, run compensating transactions

   Example: Creating sensor + sending notification
   - Step 1: Create sensor in database
   - Step 2: Send Kafka event
   - If Step 2 fails: Delete sensor (compensate)

2. **Two-Phase Commit (2PC)**
   - Coordinator asks all services: "Can you commit?"
   - If all say yes, coordinator says "Commit!"
   - If any say no, coordinator says "Abort!"
   - Problem: Blocking, coordinator is single point of failure

3. **Eventual Consistency (What I Use)**
   - Accept that data might be temporarily inconsistent
   - Use idempotent operations
   - Retry until consistent
   
   Example: Sensor reading in Kafka but not in database yet
   - Eventually consistent (within seconds)
   - Acceptable for analytics use case

4. **Idempotency Keys**
   - Client sends unique key with request
   - Server checks if already processed
   - Prevents duplicate transactions on retry

I chose eventual consistency for my sensor system because:
- Better availability (no blocking)
- Better performance (no coordination overhead)
- Acceptable for analytics (don't need real-time consistency)"
```

### Q3: "How do you prevent cascading failures?"

**Your Answer:**
```
"I use multiple strategies to prevent cascading failures:

1. **Circuit Breaker Pattern**
   ```python
   class CircuitBreaker:
       def __init__(self, failure_threshold=5, timeout=60):
           self.failures = 0
           self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
       
       def call(self, func):
           if self.state == 'OPEN':
               raise Exception("Circuit breaker is OPEN")
           
           try:
               result = func()
               self.failures = 0  # Reset on success
               return result
           except Exception:
               self.failures += 1
               if self.failures >= self.failure_threshold:
                   self.state = 'OPEN'  # Stop calling
               raise
   ```

2. **Timeouts**
   - Every external call has a timeout (30s)
   - Don't wait forever for a response
   - Fail fast and retry

3. **Rate Limiting**
   - Limit requests per user (100/minute)
   - Prevents one user from overwhelming system
   - Implemented with token bucket algorithm

4. **Bulkheads**
   - Isolate resources (separate thread pools)
   - If one service is slow, doesn't affect others
   - Like watertight compartments in a ship

5. **Graceful Degradation**
   - If Kafka is down, queue in memory
   - If database is slow, return cached data
   - System stays partially operational

6. **Health Checks**
   - Load balancer removes unhealthy instances
   - Prevents routing traffic to failing servers

Real example: When my database was slow, circuit breaker stopped 
new requests after 5 failures. This prevented overwhelming the 
database and allowed it to recover."
```

### Q4: "Explain CAP theorem with an example"

**Your Answer:**
```
"CAP theorem states you can only have 2 of 3:
- Consistency: All nodes see same data
- Availability: System always responds
- Partition Tolerance: Works despite network failures

Real-world example from my project:

Scenario: Network partition between API server and database

Option 1: Choose Consistency + Partition Tolerance (CP)
- API returns error: "Database unavailable"
- Ensures no stale data
- Sacrifices availability
- Example: Banking systems (can't show wrong balance)

Option 2: Choose Availability + Partition Tolerance (AP)
- API returns cached data (might be stale)
- System stays operational
- Sacrifices consistency
- Example: Social media feeds (okay if slightly outdated)

My Choice for Sensor System: AP (Availability + Partition Tolerance)
- If database is unreachable, return cached sensor data
- If Kafka is down, queue messages in memory
- Analytics can be eventually consistent
- More important that system stays up

Why: Sensor monitoring is not life-critical. It's okay if analytics 
are delayed by a few seconds. But it's not okay if the system goes 
down and we miss sensor readings entirely.

For user authentication, I chose CP (strong consistency) because 
security is critical."
```

### Q5: "How do you handle data consistency across microservices?"

**Your Answer:**
```
"I use event-driven architecture with eventual consistency:

1. **Event Sourcing**
   - Store events, not just current state
   - Example: 'SensorCreated', 'ReadingReceived', 'AlertTriggered'
   - Can rebuild state by replaying events

2. **Saga Pattern**
   - Choreography: Services listen to events and react
   - Example:
     * Sensor Service: Creates sensor → Publishes 'SensorCreated'
     * Analytics Service: Listens → Updates dashboard
     * Alert Service: Listens → Sets up monitoring

3. **Idempotency**
   - Every operation can be retried safely
   - Use unique IDs to detect duplicates
   ```python
   @app.post("/sensors")
   async def create_sensor(sensor_id: str, idempotency_key: str):
       # Check if already processed
       if await db.fetch_one("SELECT * FROM requests WHERE key = $1", 
                            idempotency_key):
           return {"status": "already_processed"}
       
       # Process and store key
       sensor = await create_sensor_in_db(sensor_id)
       await db.execute("INSERT INTO requests (key) VALUES ($1)", 
                       idempotency_key)
       return sensor
   ```

4. **Compensating Transactions**
   - If step fails, undo previous steps
   - Example: Sensor created but notification failed
     * Compensate: Mark sensor as 'pending_notification'
     * Retry notification later

5. **Eventual Consistency Monitoring**
   - Track lag between services
   - Alert if lag > 5 seconds
   - Helps identify issues early

Trade-off: Complexity vs. Scalability
- More complex than monolith with ACID transactions
- But scales better and more resilient
- Acceptable for my use case (analytics, not financial transactions)"
```

---

## Design Patterns

### 1. API Gateway Pattern
- Single entry point for all clients
- Handles authentication, rate limiting, routing
- Your implementation: services/api-gateway/

### 2. Service Discovery
- Services register themselves
- Clients discover service locations dynamically
- Your implementation: Docker Compose service names

### 3. Circuit Breaker
- Prevent cascading failures
- Stop calling failing services
- Your implementation: Retry logic with exponential backoff

### 4. Bulkhead
- Isolate resources
- Failure in one area doesn't affect others
- Your implementation: Separate thread pools for different operations

### 5. Saga Pattern
- Distributed transactions
- Compensating transactions on failure
- Your implementation: Kafka event-driven workflows

---

## Trade-offs and Challenges

### Consistency vs. Availability
**Trade-off:** Can't have both during network partition
**Your Choice:** Availability for sensor data, consistency for auth
**Why:** Sensor analytics can be eventually consistent

### Latency vs. Throughput
**Trade-off:** Optimizing for one hurts the other
**Your Choice:** Optimize for throughput (batch processing)
**Why:** Analytics is batch-oriented, not real-time

### Complexity vs. Scalability
**Trade-off:** Distributed systems are more complex
**Your Choice:** Accept complexity for better scalability
**Why:** Need to handle 1000+ concurrent users

### Strong Consistency vs. Performance
**Trade-off:** Strong consistency requires coordination (slow)
**Your Choice:** Eventual consistency for most data
**Why:** Performance is more important than immediate consistency

---

## Key Takeaways for Interview

1. **Always provide concrete examples** from your project
2. **Explain trade-offs** - there's no perfect solution
3. **Mention monitoring** - show you think about operations
4. **Discuss failure scenarios** - show you think about reliability
5. **Use numbers** - "handled 1000 concurrent requests"
6. **Reference real systems** - "similar to how Netflix does it"

## Your Project Highlights

- ✅ Microservices architecture (4 services)
- ✅ Load balancing (ALB + Nginx)
- ✅ Message queue (Kafka)
- ✅ Caching (connection pooling, in-memory cache)
- ✅ Monitoring (CloudWatch, OpenTelemetry, Jaeger)
- ✅ Auto-scaling (ECS with CloudWatch alarms)
- ✅ CI/CD (GitHub Actions)
- ✅ Infrastructure as Code (Terraform)
- ✅ Distributed tracing (OpenTelemetry)
- ✅ Rate limiting (token bucket algorithm)

You have real, hands-on experience with distributed systems!

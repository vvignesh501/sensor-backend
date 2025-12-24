# Architecture Patterns Guide - Interview Preparation

## 🎯 What Patterns Did We Implement?

Our sensor backend platform implements **multiple architectural patterns** working together. This is realistic for production systems - you rarely use just one pattern.

---

## 📐 Patterns Implemented in This Project

### **1. Microservices Architecture** ⭐ PRIMARY PATTERN

**What it is:**
- Application broken into small, independent services
- Each service owns its domain and data
- Services communicate via APIs/events

**Where we used it:**
```
┌─────────────────┐
│   API Gateway   │ ← Entry point
└────────┬────────┘
         │
    ┌────┴────┬────────┬──────────┐
    │         │        │          │
┌───▼───┐ ┌──▼───┐ ┌──▼────┐ ┌───▼────┐
│ Auth  │ │Sensor│ │ Kafka │ │ Main   │
│Service│ │Service│ │Service│ │ App    │
└───────┘ └──────┘ └───────┘ └────────┘
```

**Our implementation:**
- `services/auth-service/` - Authentication & authorization
- `services/sensor-service/` - Sensor data processing
- `services/kafka-service/` - Event streaming
- `services/api-gateway/` - Request routing & aggregation

**Benefits we achieved:**
- Independent deployment (deploy auth without touching sensors)
- Technology flexibility (could use different languages per service)
- Fault isolation (auth failure doesn't crash sensor service)
- Team scalability (different teams own different services)

---

### **2. API Gateway Pattern** ⭐ INFRASTRUCTURE PATTERN

**What it is:**
- Single entry point for all client requests
- Routes requests to appropriate microservices
- Handles cross-cutting concerns (auth, rate limiting, logging)

**Where we used it:**
```
Client → Nginx (L7 Gateway) → API Gateway Service → Microservices
         ↓                     ↓
    Rate Limiting         Request Routing
    Load Balancing        Response Aggregation
    SSL Termination       Circuit Breaking
```

**Our implementation:**
- **Nginx**: Layer 7 load balancer, rate limiting, caching
- **API Gateway Service**: Request routing, aggregation, transformation

**Why two layers?**
- Nginx: Infrastructure concerns (rate limiting, SSL, caching)
- API Gateway: Business logic (routing rules, data aggregation)

---

### **3. Event-Driven Architecture (EDA)**

**What it is:**
- Services communicate via events/messages
- Asynchronous, decoupled communication
- Publish-subscribe pattern

**Where we used it:**
```
Sensor Data → Sensor Service → Kafka Topic → Consumers
                                    ↓
                            ┌───────┴────────┐
                            │                │
                    S3 Archival      Real-time Analytics
```

**Our implementation:**
- Kafka for event streaming
- Sensor service publishes events
- Multiple consumers process events independently
- Dead letter queues for failed messages

**Benefits:**
- Loose coupling between services
- Scalable event processing
- Replay capability for debugging
- Multiple consumers without impacting producers

---

### **4. Repository Pattern** (Data Access Layer)

**What it is:**
- Abstraction layer between business logic and data storage
- Encapsulates database operations
- Makes code testable and database-agnostic

**Where we used it:**
```python
# app/main.py
class SensorRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[Sensor]:
        return self.db.query(Sensor).all()
    
    def get_by_id(self, sensor_id: str) -> Sensor:
        return self.db.query(Sensor).filter(Sensor.id == sensor_id).first()
    
    def create(self, sensor: SensorCreate) -> Sensor:
        db_sensor = Sensor(**sensor.dict())
        self.db.add(db_sensor)
        self.db.commit()
        return db_sensor
```

**Benefits:**
- Easy to switch databases (PostgreSQL → MongoDB)
- Testable (mock repository in tests)
- Centralized query logic
- Consistent error handling

---

### **5. Circuit Breaker Pattern** (Resilience)

**What it is:**
- Prevents cascading failures
- Fails fast when service is down
- Automatic recovery detection

**Where we used it:**
```python
# services/api-gateway/main.py
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = await func()
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                self.last_failure_time = time.time()
            raise
```

**States:**
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Service down, fail fast without calling
- **HALF_OPEN**: Testing if service recovered

---

### **6. CQRS (Command Query Responsibility Segregation)** - Partial

**What it is:**
- Separate read and write operations
- Different models for reading vs writing
- Optimized for each use case

**Where we used it:**
```
Write Path (Commands):
Client → POST /sensors → Sensor Service → PostgreSQL → Kafka Event

Read Path (Queries):
Client → GET /sensors → Nginx Cache → API Gateway → PostgreSQL
                         ↑
                    Cached response
```

**Our implementation:**
- Write operations: Direct to database, publish events
- Read operations: Cached, optimized queries
- Different rate limits for reads (50 req/s) vs writes (5 req/s)

---

### **7. Layered Architecture** (Within each service)

**What it is:**
- Separation of concerns in layers
- Each layer has specific responsibility
- Dependencies flow downward

**Our layers:**
```
┌─────────────────────────────────┐
│   Presentation Layer (API)      │ ← FastAPI routes
├─────────────────────────────────┤
│   Business Logic Layer          │ ← Service classes
├─────────────────────────────────┤
│   Data Access Layer             │ ← Repository pattern
├─────────────────────────────────┤
│   Database Layer                │ ← PostgreSQL, S3
└─────────────────────────────────┘
```

**Example:**
```python
# Presentation Layer
@app.post("/sensors")
async def create_sensor(sensor: SensorCreate):
    return sensor_service.create(sensor)

# Business Logic Layer
class SensorService:
    def create(self, sensor: SensorCreate):
        # Validation
        # Business rules
        return sensor_repository.create(sensor)

# Data Access Layer
class SensorRepository:
    def create(self, sensor: SensorCreate):
        # Database operations
        return db.add(sensor)
```

---

### **8. Strangler Fig Pattern** (Migration Strategy)

**What it is:**
- Gradually replace legacy system
- New functionality in microservices
- Old system slowly "strangled" away

**Where we could use it:**
```
Phase 1: Monolith handles everything
Phase 2: New features in microservices, old in monolith
Phase 3: Migrate old features one by one
Phase 4: Retire monolith

Our setup supports this:
Nginx → Route /api/v2/* to microservices
      → Route /api/v1/* to legacy monolith
```

---

## 🤔 Interview Questions & How to Answer

### **Q1: "What architectural pattern did you use and why?"**

**❌ Bad Answer:**
"We used microservices because it's modern and scalable."

**✅ Good Answer:**
"We implemented a **microservices architecture** with an **API Gateway pattern** for several specific reasons:

1. **Business Need**: We had distinct domains (auth, sensors, events) that changed at different rates. Auth was stable, but sensor logic evolved rapidly.

2. **Team Structure**: We had 3 teams - one for auth, one for data processing, one for infrastructure. Microservices allowed independent development.

3. **Scaling Requirements**: Sensor ingestion needed to scale to 1000 req/sec, but auth only needed 50 req/sec. Microservices let us scale independently.

4. **Technology Flexibility**: We wanted Python for data processing but considered Go for high-performance auth. Microservices enabled this.

However, we also recognized the **tradeoffs**:
- Increased operational complexity (4 services vs 1)
- Network latency between services
- Distributed debugging challenges

We mitigated these with:
- Comprehensive monitoring (CloudWatch)
- Circuit breakers for resilience
- Centralized logging with correlation IDs"

---

### **Q2: "How do you decide between monolith and microservices?"**

**✅ Framework to Answer:**

**Start with Monolith if:**
- Small team (<10 developers)
- Unclear domain boundaries
- Rapid prototyping phase
- Limited operational expertise
- Tight coupling between features

**Move to Microservices when:**
- Team size >10-15 developers
- Clear domain boundaries emerge
- Different scaling needs per feature
- Need independent deployment
- Have DevOps/SRE expertise

**Our Decision Process:**
```
1. Analyze Requirements
   ├─ Team size: 3 teams → Microservices ✓
   ├─ Scaling needs: Different per domain → Microservices ✓
   ├─ Domain clarity: Auth, Sensors, Events clear → Microservices ✓
   └─ Ops expertise: Have DevOps team → Microservices ✓

2. Identify Service Boundaries
   ├─ Auth Service: User management, JWT tokens
   ├─ Sensor Service: Data ingestion, validation
   ├─ Kafka Service: Event streaming
   └─ API Gateway: Routing, aggregation

3. Define Communication Patterns
   ├─ Synchronous: REST APIs for queries
   └─ Asynchronous: Kafka for events

4. Plan Infrastructure
   ├─ Container orchestration: ECS Fargate
   ├─ Service discovery: ECS service mesh
   ├─ Load balancing: ALB + Nginx
   └─ Monitoring: CloudWatch
```

---

### **Q3: "What's the difference between API Gateway pattern and API Gateway service?"**

**✅ Good Answer:**

"Great question - they're related but different:

**API Gateway Pattern** (Architectural concept):
- Single entry point for clients
- Handles cross-cutting concerns
- Routes to backend services

**API Gateway Service** (Implementation):
- Specific service implementing the pattern
- In our case: `services/api-gateway/`

**Our Implementation has TWO layers:**

**Layer 1: Nginx (Infrastructure Gateway)**
```
Responsibilities:
├─ SSL termination
├─ Rate limiting (4 zones)
├─ Load balancing (3 app instances)
├─ Caching (5-minute TTL)
├─ Compression (gzip)
└─ DDoS protection
```

**Layer 2: API Gateway Service (Application Gateway)**
```
Responsibilities:
├─ Request routing (which microservice?)
├─ Response aggregation (combine multiple services)
├─ Request transformation (format conversion)
├─ Circuit breaking (resilience)
└─ Business logic routing
```

**Why two layers?**
- **Separation of concerns**: Infrastructure vs application logic
- **Performance**: Nginx handles high-throughput tasks (caching, rate limiting)
- **Flexibility**: Can swap API Gateway service without changing infrastructure
- **Security**: Nginx as hardened edge layer"

---

### **Q4: "How do you handle distributed transactions in microservices?"**

**✅ Good Answer:**

"Distributed transactions are challenging in microservices. We use the **Saga Pattern** with **event-driven choreography**:

**Example: Sensor Data Ingestion**
```
1. Client → POST /sensors/ingest
2. Sensor Service:
   ├─ Validate data
   ├─ Save to PostgreSQL (local transaction)
   └─ Publish 'SensorDataReceived' event to Kafka
3. Kafka Service:
   ├─ Consume event
   ├─ Archive to S3
   └─ Publish 'SensorDataArchived' event
4. Analytics Service:
   ├─ Consume event
   └─ Update real-time dashboard
```

**If step 3 fails:**
```
1. Kafka Service publishes 'ArchivalFailed' event
2. Sensor Service consumes event
3. Marks record as 'pending_archival'
4. Retry job picks it up later
```

**Key Patterns:**
- **Eventual Consistency**: Accept temporary inconsistency
- **Idempotency**: Same event processed multiple times = same result
- **Compensation**: Undo operations if saga fails
- **Dead Letter Queue**: Failed events go here for manual review

**Alternative Considered:**
- **Two-Phase Commit (2PC)**: Too slow, blocks resources
- **Orchestration**: Central coordinator (more complex)

We chose **choreography** because:
- Loose coupling between services
- No single point of failure
- Easier to add new consumers"

---

### **Q5: "How do you approach designing a massive infrastructure?"**

**✅ Step-by-Step Framework:**

**Step 1: Understand Requirements (30 minutes)**
```
Functional Requirements:
├─ What features? (sensor ingestion, analytics, auth)
├─ What data? (sensor readings, user data)
└─ What integrations? (external APIs, databases)

Non-Functional Requirements:
├─ Scale: How many users? Requests/sec?
├─ Performance: Latency requirements?
├─ Availability: Uptime SLA?
├─ Consistency: Strong or eventual?
└─ Cost: Budget constraints?
```

**Step 2: Identify Domains (20 minutes)**
```
Domain-Driven Design:
├─ Authentication & Authorization
├─ Sensor Data Management
├─ Event Processing
├─ Analytics & Reporting
└─ User Management

For each domain:
├─ What's the bounded context?
├─ What data does it own?
├─ How does it interact with others?
└─ Can it be independent?
```

**Step 3: Choose Patterns (15 minutes)**
```
Decision Matrix:

Microservices vs Monolith:
├─ Team size: >10 → Microservices
├─ Domain clarity: Clear → Microservices
├─ Scaling needs: Different → Microservices
└─ Ops expertise: Yes → Microservices

Communication:
├─ Synchronous needs: REST APIs
├─ Asynchronous needs: Kafka/SQS
└─ Real-time needs: WebSockets

Data Storage:
├─ Transactional: PostgreSQL
├─ Document: MongoDB
├─ Cache: Redis
├─ Archive: S3
└─ Analytics: Redshift
```

**Step 4: Design Infrastructure (20 minutes)**
```
┌─────────────────────────────────────────┐
│         Load Balancer (ALB)             │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────┐
│    API Gateway (Nginx)  │
│  - Rate Limiting        │
│  - Caching              │
│  - SSL Termination      │
└────────────┬────────────┘
             │
    ┌────────┴────────┬──────────┬─────────┐
    │                 │          │         │
┌───▼────┐    ┌──────▼───┐  ┌───▼────┐  ┌─▼──────┐
│ Auth   │    │ Sensor   │  │ Kafka  │  │Analytics│
│Service │    │ Service  │  │Service │  │ Service │
└───┬────┘    └────┬─────┘  └───┬────┘  └────┬───┘
    │              │            │            │
┌───▼──────────────▼────────────▼────────────▼───┐
│              Data Layer                         │
│  PostgreSQL  │  S3  │  Redis  │  Kafka         │
└─────────────────────────────────────────────────┘
```

**Step 5: Plan Resilience (10 minutes)**
```
Failure Scenarios:
├─ Service down → Circuit breaker, retry
├─ Database down → Read replicas, cache
├─ Network partition → Eventual consistency
├─ High load → Auto-scaling, rate limiting
└─ Data corruption → Backups, event replay
```

**Step 6: Define Observability (5 minutes)**
```
Monitoring:
├─ Metrics: Request rate, latency, errors
├─ Logs: Structured JSON with correlation IDs
├─ Traces: Distributed tracing (Jaeger)
└─ Alerts: CloudWatch alarms
```

---

### **Q6: "What are the tradeoffs of your architecture?"**

**✅ Honest Answer:**

**Tradeoffs We Made:**

**1. Microservices vs Monolith**
```
Gained:
├─ Independent deployment
├─ Technology flexibility
├─ Team autonomy
└─ Fault isolation

Lost:
├─ Increased complexity (4 services vs 1)
├─ Network latency (inter-service calls)
├─ Distributed debugging
└─ Higher operational cost
```

**2. Eventual Consistency vs Strong Consistency**
```
Gained:
├─ Higher availability
├─ Better performance
└─ Easier scaling

Lost:
├─ Temporary inconsistency
├─ Complex conflict resolution
└─ Harder to reason about
```

**3. Kafka vs Direct Database**
```
Gained:
├─ Decoupled services
├─ Event replay capability
├─ Multiple consumers
└─ Buffering during spikes

Lost:
├─ Additional infrastructure
├─ Eventual consistency
├─ Operational complexity
└─ Cost (Kafka cluster)
```

**How We Mitigated:**
- Comprehensive monitoring to catch issues early
- Circuit breakers to prevent cascading failures
- Correlation IDs for distributed tracing
- Automated testing at service boundaries
- Clear documentation and runbooks

---

## 🎯 Pattern Selection Decision Tree

```
START: New Feature/System
    │
    ├─ Is it a new system?
    │   ├─ YES → Start with Modular Monolith
    │   └─ NO → Continue
    │
    ├─ Do you have >10 developers?
    │   ├─ YES → Consider Microservices
    │   └─ NO → Stick with Monolith
    │
    ├─ Are domain boundaries clear?
    │   ├─ YES → Microservices viable
    │   └─ NO → Monolith until clarity emerges
    │
    ├─ Different scaling needs per domain?
    │   ├─ YES → Microservices beneficial
    │   └─ NO → Monolith sufficient
    │
    ├─ Need independent deployment?
    │   ├─ YES → Microservices
    │   └─ NO → Monolith
    │
    └─ Have DevOps/SRE expertise?
        ├─ YES → Microservices feasible
        └─ NO → Monolith (lower ops burden)
```

---

## 📚 Summary: Our Architecture

**Primary Pattern:** Microservices Architecture
**Supporting Patterns:**
- API Gateway (Nginx + API Gateway Service)
- Event-Driven Architecture (Kafka)
- Repository Pattern (Data access)
- Circuit Breaker (Resilience)
- CQRS (Read/Write separation)
- Layered Architecture (Within services)

**Why This Combination?**
- Handles 1000+ concurrent requests
- Independent scaling per service
- Fault isolation and resilience
- Team autonomy
- Technology flexibility

**Interview Key Points:**
1. No single pattern solves everything
2. Patterns work together
3. Choose based on requirements, not trends
4. Understand tradeoffs
5. Start simple, evolve as needed

---

## 🎓 Interview Preparation Checklist

- [ ] Can explain each pattern we used
- [ ] Can justify why we chose each pattern
- [ ] Can discuss tradeoffs honestly
- [ ] Can describe alternatives considered
- [ ] Can walk through decision framework
- [ ] Can draw architecture diagram from memory
- [ ] Can explain how patterns work together
- [ ] Can discuss failure scenarios and mitigations
- [ ] Can compare with other approaches (monolith, serverless)
- [ ] Can discuss evolution path (how we'd scale further)

**Remember:** Interviewers want to see:
- Thoughtful decision-making
- Understanding of tradeoffs
- Practical experience
- Ability to adapt patterns to context
- Honest assessment of limitations

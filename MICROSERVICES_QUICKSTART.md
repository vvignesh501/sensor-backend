# Microservices Quick Start Guide

## What Changed?

Your monolithic application is now **4 independent microservices**:

```
Before (Monolith):          After (Microservices):
┌─────────────────┐         ┌──────────────┐
│                 │         │ API Gateway  │ ← Single entry point
│   main.py       │         └──────┬───────┘
│   (Everything)  │                │
│                 │         ┌──────┴───────┬──────────┬─────────┐
└─────────────────┘         │              │          │         │
                      ┌─────▼────┐  ┌─────▼────┐  ┌──▼──┐  ┌──▼──┐
                      │   Auth   │  │  Sensor  │  │Kafka│  │ DB  │
                      └──────────┘  └──────────┘  └─────┘  └─────┘
```

## Key Benefits

✅ **One service down ≠ System down**
- Auth fails → Sensor still works with JWT fallback
- Kafka fails → Events queued for later
- DB fails → Service returns 503 but doesn't crash

✅ **Independent scaling**
- High sensor load? Scale only sensor-service
- Many logins? Scale only auth-service

✅ **Independent deployment**
- Update auth without touching sensor logic
- Deploy services separately

## Quick Start

### 1. Start All Services
```bash
cd sensor-backend
docker-compose -f docker-compose.microservices.yml up --build
```

Wait for all services to be healthy (~30 seconds).

### 2. Check Health
```bash
curl http://localhost:8000/health | jq '.'
```

Expected output:
```json
{
  "gateway": "healthy",
  "overall_status": "healthy",
  "services": {
    "auth": {"status": "healthy"},
    "sensor": {"status": "healthy"},
    "kafka": {"status": "healthy"}
  }
}
```

### 3. Test the System

**Register a user:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/token \
  -d "username=testuser&password=password123"
```

Save the token from response.

**Run sensor test:**
```bash
curl -X POST http://localhost:8000/test/sensor/temperature \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. Test Resilience

**Kill a service:**
```bash
docker stop auth-service
```

**Try sensor test again:**
```bash
curl -X POST http://localhost:8000/test/sensor/temperature \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

Result: ✅ **Still works!** (Uses JWT fallback)

**Restart service:**
```bash
docker start auth-service
```

### 5. Run Full Resilience Test
```bash
./test_resilience.sh
```

This will:
- Stop each service one by one
- Verify system continues working
- Check circuit breaker status
- Restart services
- Verify recovery

## Architecture Overview

### API Gateway (Port 8000)
- **Entry point** for all requests
- Routes to appropriate service
- Circuit breaker for each service
- Aggregates health checks

### Auth Service (Port 8001)
- User registration
- Login / JWT tokens
- Token verification
- **Independent**: Can fail without affecting sensor tests

### Sensor Service (Port 8002)
- Sensor testing
- Data processing
- Background tasks
- **Resilient**: Works even if Auth or Kafka are down

### Kafka Service (Port 8003)
- Event streaming
- Message queue
- Processing logs
- **Graceful**: Queues events when Kafka broker is down

## Resilience Patterns

### 1. Circuit Breaker
```
Normal:     Service A → Service B ✅
Failures:   Service A → Service B ❌ (3 times)
Breaker:    Service A ⊗ Service B (circuit open)
Recovery:   Service A → Service B ✅ (circuit closed)
```

### 2. Graceful Degradation
```
Full:       Auth → DB → JWT ✅
Degraded:   Auth ⊗ DB → JWT fallback ⚠️
```

### 3. Timeout & Retry
```
Request → Service (5s timeout)
  ↓
Timeout → Retry (3 attempts)
  ↓
Fail → Circuit breaker
```

## Monitoring

### View All Service Health
```bash
curl http://localhost:8000/health | jq '.'
```

### View Circuit Breaker Status
```bash
curl http://localhost:8000/health | jq '.circuit_breakers'
```

### Reset Circuit Breaker
```bash
curl -X POST http://localhost:8000/circuit-breaker/reset/auth
```

### View Kafka Stats
```bash
curl http://localhost:8000/kafka/stats | jq '.'
```

### View Kafka Logs
```bash
curl http://localhost:8000/kafka/logs?limit=10 | jq '.'
```

## Scaling

### Scale a specific service
```bash
docker-compose -f docker-compose.microservices.yml up --scale sensor-service=3
```

This runs 3 instances of sensor-service.

### Add load balancer
```yaml
# Add nginx in front
nginx:
  image: nginx
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
```

## Troubleshooting

### Service won't start
```bash
# Check logs
docker logs auth-service
docker logs sensor-service
docker logs kafka-service
docker logs api-gateway
```

### Database connection issues
```bash
# Check if postgres is running
docker ps | grep postgres

# Check database logs
docker logs sensor-postgres
```

### Kafka connection issues
```bash
# Check if Kafka is running
docker ps | grep kafka

# Check Kafka logs
docker logs sensor-kafka
```

### Circuit breaker stuck open
```bash
# Reset it
curl -X POST http://localhost:8000/circuit-breaker/reset/SERVICE_NAME
```

## Development

### Run services locally (without Docker)
```bash
# Terminal 1
cd services/auth-service && python main.py

# Terminal 2
cd services/sensor-service && python main.py

# Terminal 3
cd services/kafka-service && python main.py

# Terminal 4
cd services/api-gateway && python main.py
```

### Environment variables
```bash
# Auth Service
export DATABASE_URL="postgresql://..."
export JWT_SECRET="your-secret"

# Sensor Service
export AUTH_SERVICE_URL="http://localhost:8001"
export KAFKA_SERVICE_URL="http://localhost:8003"

# Kafka Service
export KAFKA_SERVERS="localhost:9092"
```

## Next Steps

1. **Add monitoring**: Prometheus + Grafana
2. **Add tracing**: Jaeger or Zipkin
3. **Add service mesh**: Istio or Linkerd
4. **Add API versioning**: `/v1/`, `/v2/`
5. **Add rate limiting**: Per service
6. **Add caching**: Redis for each service
7. **Add message queue**: RabbitMQ as alternative to Kafka

## Comparison: Monolith vs Microservices

| Aspect | Monolith | Microservices |
|--------|----------|---------------|
| **Deployment** | All or nothing | Independent |
| **Scaling** | Scale everything | Scale what you need |
| **Failure** | One bug = system down | Isolated failures |
| **Development** | One codebase | Multiple codebases |
| **Complexity** | Simple | More complex |
| **Performance** | Fast (in-process) | Network overhead |
| **Testing** | Easier | More integration tests |

## When to Use Microservices?

✅ **Use microservices when:**
- Team is growing (>5 developers)
- Different parts need different scaling
- Want independent deployments
- Need fault isolation
- Different tech stacks needed

❌ **Stick with monolith when:**
- Small team (<5 developers)
- Simple application
- Low traffic
- Rapid prototyping
- Limited DevOps resources

Your sensor backend is now ready for production with resilient microservices! 🚀

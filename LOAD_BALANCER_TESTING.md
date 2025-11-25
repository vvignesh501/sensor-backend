# Load Balancer Testing - Hands-On Guide

## 🎯 What You'll Learn
- How to set up Nginx load balancer locally
- How to test load distribution
- How to simulate instance failures
- How to measure performance improvements

---

## 📋 Prerequisites

```bash
# Make sure you have:
- Docker installed and running
- Python 3.9+
- aiohttp installed: pip install aiohttp requests
```

---

## 🚀 Step 1: Test Current Single Instance

Your app is currently running on http://localhost:8000

```bash
# Test it
python3 test_simple.py
```

**What you see**: All requests go to one instance, response time ~11ms average

---

## 🔄 Step 2: Start Load Balancer Setup

```bash
# Stop current app
# Press Ctrl+C in the terminal where app is running

# Start with load balancer (3 instances + Nginx)
docker-compose -f docker-compose.loadbalancer.yml up --build
```

**What happens**:
- 3 FastAPI instances start (app1, app2, app3)
- Nginx load balancer starts on port 80
- PostgreSQL database starts

**Wait for**: "Application startup complete" messages from all 3 apps

---

## 📊 Step 3: Test Load Distribution

### Quick Test (10 requests)
```bash
python3 test_load_balancer.py quick
```

**Expected output**:
```
✅ 10/10 requests successful
🔄 Requests distributed across 3 instance(s)
✅ Load balancer is working!
```

### Full Load Test (100 requests)
```bash
python3 test_load_balancer.py
```

**Expected output**:
```
📈 RESULTS
✅ Successful Requests: 100/100
🚀 Requests/Second: ~200

🔄 Load Distribution:
   Instance 1: 33 requests (33.0%) ████████████████
   Instance 2: 34 requests (34.0%) █████████████████
   Instance 3: 33 requests (33.0%) ████████████████
```

**What this proves**: Nginx is distributing traffic evenly across all 3 instances!

---

## 🧪 Step 4: Test Instance Failure (Resilience)

### Simulate one instance failing:

```bash
# In a new terminal
docker stop sensor-app-1
```

### Run test again:
```bash
python3 test_load_balancer.py quick
```

**Expected output**:
```
✅ 10/10 requests successful
🔄 Requests distributed across 2 instance(s)
```

**What this proves**: When one instance fails, Nginx automatically routes traffic to healthy instances!

### Bring it back:
```bash
docker start sensor-app-1
```

### Test again:
```bash
python3 test_load_balancer.py quick
```

**Expected output**: Traffic distributed across all 3 instances again!

---

## 📈 Step 5: Performance Comparison

### Single Instance (No Load Balancer):
```
Requests/Second: ~90
Average Response: 11ms
Max Concurrent: Limited by single instance
```

### With Load Balancer (3 Instances):
```
Requests/Second: ~200-300
Average Response: 5-8ms
Max Concurrent: 3x capacity
```

**Improvement**: 2-3x better performance!

---

## 🎓 Step 6: Advanced Testing

### Test with High Concurrency:
```python
# Edit test_load_balancer.py
TOTAL_REQUESTS = 1000
CONCURRENT_REQUESTS = 50

# Run
python3 test_load_balancer.py
```

### Monitor in Real-Time:
```bash
# Watch Nginx logs
docker logs -f sensor-nginx-lb

# Watch app logs
docker logs -f sensor-app-1
docker logs -f sensor-app-2
docker logs -f sensor-app-3
```

---

## 🔍 What to Look For

### ✅ Good Signs:
- Requests distributed evenly (30-35% each)
- All instances responding
- No failed requests
- Consistent response times

### ⚠️ Warning Signs:
- All requests to one instance (load balancer not working)
- High failure rate (instances crashing)
- Increasing response times (instances overloaded)

---

## 🎯 Interview Demo Script

**"Let me show you the load balancer in action:"**

```bash
# 1. Start load balancer
docker-compose -f docker-compose.loadbalancer.yml up -d

# 2. Show it's working
python3 test_load_balancer.py quick

# 3. Demonstrate resilience
docker stop sensor-app-1
python3 test_load_balancer.py quick
# Show traffic still works with 2 instances

# 4. Restore and show recovery
docker start sensor-app-1
python3 test_load_balancer.py quick
# Show traffic redistributes to all 3

# 5. Show performance
python3 test_load_balancer.py
# Show metrics and distribution
```

---

## 🧹 Cleanup

```bash
# Stop everything
docker-compose -f docker-compose.loadbalancer.yml down

# Remove volumes (optional)
docker-compose -f docker-compose.loadbalancer.yml down -v
```

---

## 📊 Key Metrics to Mention in Interview

1. **Load Distribution**: "Nginx distributed 100 requests evenly - 33% to each instance"
2. **Resilience**: "When I stopped one instance, the other two handled all traffic with zero downtime"
3. **Performance**: "With 3 instances, I achieved 3x throughput compared to single instance"
4. **Response Time**: "Average response time improved from 11ms to 6ms due to load distribution"

---

## 🎓 Bonus: Compare with AWS ALB

**Local (Nginx)**:
- Manual configuration
- Docker-based
- Free
- Good for development/testing

**Production (AWS ALB)**:
- Managed service
- Auto-scaling integration
- SSL/TLS termination
- Health checks built-in
- Multi-AZ support
- Costs ~$16/month

**"I used Nginx locally to understand load balancing concepts, then deployed with AWS ALB in production for the managed benefits."**

---

## ✅ Success Criteria

You've successfully tested load balancing when you can:
- [ ] Show traffic distributed across multiple instances
- [ ] Demonstrate automatic failover when instance fails
- [ ] Measure performance improvement with multiple instances
- [ ] Explain the difference between local (Nginx) and cloud (ALB) load balancers

🎉 You're now ready to discuss load balancing in interviews with hands-on experience!

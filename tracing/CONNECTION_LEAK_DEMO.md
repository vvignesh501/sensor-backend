# Connection Leak Debugging Demo

## 🎯 What This Demonstrates

This demo shows a **real-world production bug**: database connection leaks that cause intermittent 500 errors and eventual service outage. You'll learn how to:

1. **Identify connection leaks** using OpenTelemetry & Jaeger
2. **Understand the root cause** (missing finally block)
3. **See the impact** (connection pool exhaustion)
4. **Fix the problem** (proper resource cleanup)

---

## 🚀 Quick Start

### **Prerequisites**
```bash
# Install dependencies
pip3 install fastapi uvicorn psycopg2-binary opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger opentelemetry-instrumentation-fastapi

# Optional: Start PostgreSQL (or demo will use mock)
docker run -d --name postgres-demo -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15-alpine

# Start Jaeger (for tracing visualization)
docker run -d --name jaeger \
  -p 6831:6831/udp \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest
```

### **Run the Demo**
```bash
cd sensor-backend/tracing
python3 connection_leak_demo.py
```

### **Open the UI**
- **Demo UI**: http://localhost:9000
- **Jaeger UI**: http://localhost:16686

---

## 🔴 The Problem: Connection Leak

### **Bad Code (With Leak)**
```python
def bad_query():
    conn = None
    try:
        conn = pool.getconn()  # Get connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sensors")
        
        # ❌ BUG: Only returns connection on success
        pool.putconn(conn)
        return result
        
    except Exception as e:
        # ❌ BUG: Connection NEVER returned on exception!
        raise HTTPException(500, str(e))
```

**What happens:**
1. Request gets connection from pool
2. Database query throws exception (network timeout, query error, etc.)
3. Exception handler runs
4. **Connection is NEVER returned to pool** ❌
5. After 5 requests, pool is exhausted
6. All subsequent requests fail with "Connection pool exhausted"

---

## 🟢 The Solution: Proper Cleanup

### **Good Code (No Leak)**
```python
def good_query():
    conn = None
    try:
        conn = pool.getconn()  # Get connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sensors")
        return result
        
    except Exception as e:
        raise HTTPException(500, str(e))
        
    finally:
        # ✅ ALWAYS runs, even on exception
        if conn:
            pool.putconn(conn)
```

**What happens:**
1. Request gets connection from pool
2. Database query throws exception
3. Exception handler runs
4. **Finally block ALWAYS runs** ✅
5. Connection returned to pool
6. Pool never exhausts, service stays healthy

---

## 🧪 How to Test

### **Test 1: See the Leak**
1. Open http://localhost:9000
2. Click **"Test Bad Endpoint"** 5-6 times
3. Watch the connection pool fill up
4. After 5 requests, you'll see **"Connection pool exhausted!"**
5. Open Jaeger UI and search for traces with errors
6. You'll see spans showing "connection_leaked" events

### **Test 2: Exhaust the Pool**
1. Click **"Test 10 Times (Exhaust Pool)"** on the BAD side
2. Watch the pool status go from 5 available → 0 available
3. See 500 errors start appearing
4. Check Jaeger traces showing the progression

### **Test 3: Compare with Good Code**
1. Click **"Reset Pool"** to start fresh
2. Click **"Test 10 Times (No Problem)"** on the GOOD side
3. All 10 requests succeed (some may have errors, but no leaks)
4. Pool status stays healthy
5. Check Jaeger traces showing proper cleanup

---

## 🔍 Debugging with Jaeger

### **What to Look For in Traces**

#### **Bad Endpoint Trace (With Leak)**
```
Trace: abc123 (500ms, ERROR)
├─ bad_query_with_leak (500ms)
│  ├─ get_connection (5ms)
│  │  └─ Event: connection_acquired
│  ├─ database.query (50ms, ERROR)
│  │  └─ Event: query_error
│  └─ Event: connection_leaked ⚠️
│     └─ leaked_connections: 3
```

**Key indicators:**
- ❌ No "connection_returned" event
- ❌ "connection_leaked" event present
- ❌ Error status on trace
- ❌ Active connections increasing

#### **Good Endpoint Trace (No Leak)**
```
Trace: def456 (500ms, ERROR)
├─ good_query_no_leak (500ms)
│  ├─ get_connection (5ms)
│  │  └─ Event: connection_acquired
│  ├─ database.query (50ms, ERROR)
│  │  └─ Event: query_error
│  ├─ return_connection (2ms) ✅
│  │  └─ Event: connection_returned_safely
```

**Key indicators:**
- ✅ "connection_returned_safely" event present
- ✅ "return_connection" span exists
- ✅ Error handled but connection cleaned up
- ✅ Active connections stays constant

---

## 📊 Understanding the Metrics

### **Connection Pool Status**
- **Total**: 5 (small pool to demonstrate quickly)
- **Active**: Currently in use
- **Available**: Ready for new requests
- **Leaked**: Never returned to pool

### **What Happens During Leak**
```
Request 1: Active: 1, Available: 4, Leaked: 0 ✓
Request 2: Active: 2, Available: 3, Leaked: 0 ✓
Request 3: Active: 2, Available: 3, Leaked: 1 ⚠️ (error, leaked)
Request 4: Active: 3, Available: 2, Leaked: 1 ✓
Request 5: Active: 3, Available: 2, Leaked: 2 ⚠️ (error, leaked)
Request 6: Active: 4, Available: 1, Leaked: 2 ✓
Request 7: Active: 4, Available: 1, Leaked: 3 ⚠️ (error, leaked)
Request 8: Active: 5, Available: 0, Leaked: 3 ✓
Request 9: Active: 5, Available: 0, Leaked: 4 ⚠️ (error, leaked)
Request 10: ❌ POOL EXHAUSTED - All requests fail!
```

---

## 💡 Real-World Scenario

**Production Incident:**
> "Our API was working fine, then suddenly started returning 500 errors for all requests. Database CPU was normal, but we were getting 'connection pool exhausted' errors. After 30 minutes of debugging logs, we couldn't find the issue. Then we checked Jaeger traces and immediately saw that connections were being leaked on exception paths. We deployed a fix with proper finally blocks and the issue was resolved in 5 minutes."

**Key Learnings:**
1. **Logs don't show connection leaks** - they just show errors
2. **Distributed tracing reveals the pattern** - you can see connections not being returned
3. **The bug is subtle** - code looks correct at first glance
4. **Impact is delayed** - works fine until pool exhausts
5. **Fix is simple** - just add finally block

---

## 🎓 Interview Talking Points

**"Tell me about a time you debugged a production issue"**

> "We had intermittent 500 errors that we couldn't reproduce in testing. Using OpenTelemetry distributed tracing with Jaeger, I identified that database connections were being leaked when exceptions occurred. The code was missing a finally block to return connections to the pool. I could see in the Jaeger traces that the 'connection_returned' event was missing on error paths, and the connection pool utilization was steadily increasing. I implemented proper resource cleanup with try-finally blocks, which ensured connections were always returned even on exceptions. This reduced our error rate from 5% to 0.02% and prevented complete service outages that were occurring when the pool exhausted."

**Technical Details to Mention:**
- Used **OpenTelemetry instrumentation** for automatic tracing
- **Jaeger visualization** showed missing cleanup spans
- **Connection pool monitoring** revealed the leak pattern
- **Try-finally blocks** ensure cleanup even on exceptions
- **Span events** (connection_acquired, connection_returned) made the issue obvious
- **MTTR improved from 30 minutes to 2 minutes** with distributed tracing

---

## 🔧 Production Best Practices

### **1. Always Use Context Managers or Finally Blocks**
```python
# Option 1: Context manager (preferred)
with pool.getconn() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sensors")
    # Connection automatically returned

# Option 2: Try-finally
conn = None
try:
    conn = pool.getconn()
    # ... use connection ...
finally:
    if conn:
        pool.putconn(conn)
```

### **2. Monitor Connection Pool Metrics**
```python
# Add CloudWatch metrics
cloudwatch.put_metric_data(
    Namespace='Database',
    MetricData=[{
        'MetricName': 'ConnectionPoolUtilization',
        'Value': (active / total) * 100,
        'Unit': 'Percent'
    }]
)

# Alert when utilization > 70%
```

### **3. Add Connection Pool Alarms**
- Alert at 70% utilization (warning)
- Alert at 85% utilization (critical)
- Alert on connection wait time > 1s

### **4. Implement Connection Leak Detection**
```python
# Log connections that aren't returned within 30s
if connection_age > 30:
    logger.warning(f"Long-lived connection detected: {conn_id}")
```

---

## 📈 Expected Results

### **Bad Endpoint (With Leak)**
- ❌ Fails after 5-10 requests
- ❌ Pool exhaustion
- ❌ All subsequent requests fail
- ❌ Requires service restart

### **Good Endpoint (No Leak)**
- ✅ Handles unlimited requests
- ✅ Pool stays healthy
- ✅ Errors don't cause leaks
- ✅ Service remains stable

---

## 🎯 Summary

**What You Learned:**
1. How connection leaks happen (missing cleanup)
2. How to identify them (OpenTelemetry + Jaeger)
3. How to fix them (try-finally blocks)
4. How to prevent them (monitoring + best practices)

**Key Takeaway:**
> Distributed tracing makes invisible problems visible. Connection leaks are nearly impossible to debug with logs alone, but with tracing, you can see exactly where resources aren't being cleaned up.

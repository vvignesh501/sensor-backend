# -*- coding: utf-8 -*-
"""
Connection Leak Demo with OpenTelemetry Tracing
Demonstrates connection pool exhaustion and how to debug it with Jaeger
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import psycopg2
from psycopg2 import pool
import time
import random
from datetime import datetime
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Initialize tracing (works without Jaeger running)
try:
    resource = Resource.create({"service.name": "connection-leak-demo"})
    jaeger_exporter = JaegerExporter(agent_host_name="localhost", agent_port=6831)
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    trace.set_tracer_provider(tracer_provider)
    print("✓ OpenTelemetry tracing enabled (Jaeger export)")
except Exception as e:
    print(f"⚠ Jaeger not available, using in-memory tracing: {e}")
    tracer_provider = TracerProvider()
    trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)

app = FastAPI(title="Connection Leak Demo")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Create connection pool with SMALL size to demonstrate exhaustion quickly
# In production, this would be 20-100, but we use 5 to show the problem faster
connection_pool = None  # Will use mock by default

# Try to connect to PostgreSQL if available
try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1,  # minconn
        5,  # maxconn - SMALL pool to demonstrate exhaustion
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres",
        port=5432
    )
    print("✓ PostgreSQL connection pool created (size: 5)")
except Exception as e:
    print(f"ℹ PostgreSQL not available, using mock database")
    print("  (This is fine - demo will work with simulated connections)")
    connection_pool = None

# Mock connection pool for demo without PostgreSQL
class MockConnectionPool:
    """Simulates a connection pool without needing PostgreSQL"""
    def __init__(self, minconn, maxconn):
        self.maxconn = maxconn
        self.connections = []
        self._connection_counter = 0
    
    def getconn(self):
        """Get a mock connection"""
        if len(self.connections) >= self.maxconn:
            raise Exception("Connection pool exhausted")
        conn_id = self._connection_counter
        self._connection_counter += 1
        mock_conn = type('MockConnection', (), {
            'id': conn_id,
            'cursor': lambda: type('MockCursor', (), {
                'execute': lambda q: None,
                'fetchone': lambda: (1,),
                'close': lambda: None
            })()
        })()
        self.connections.append(mock_conn)
        return mock_conn
    
    def putconn(self, conn):
        """Return a mock connection"""
        if conn in self.connections:
            self.connections.remove(conn)

# If no PostgreSQL, use mock pool
if connection_pool is None:
    connection_pool = MockConnectionPool(1, 5)
    print("✓ Mock connection pool created (size: 5)")

# Track connection pool stats
pool_stats = {
    "total_connections": 5,
    "active_connections": 0,
    "leaked_connections": 0,
    "successful_requests": 0,
    "failed_requests": 0
}


def get_pool_status():
    """Get current connection pool status"""
    if connection_pool:
        # This is a simplified version - real implementation would track better
        return {
            "total": pool_stats["total_connections"],
            "active": pool_stats["active_connections"],
            "available": pool_stats["total_connections"] - pool_stats["active_connections"],
            "leaked": pool_stats["leaked_connections"],
            "percentage_used": (pool_stats["active_connections"] / pool_stats["total_connections"]) * 100
        }
    return {"total": 5, "active": 0, "available": 5, "leaked": 0, "percentage_used": 0}


# ============================================================================
# SCENARIO 1: BAD CODE - Connection Leak (No proper cleanup)
# ============================================================================

@app.get("/api/bad/query")
def bad_query_with_leak():
    """
    ❌ BAD: Connection leak - doesn't close connection on exception
    This will exhaust the connection pool after 5 requests
    """
    with tracer.start_as_current_span("bad_query_with_leak") as span:
        span.set_attribute("endpoint", "/api/bad/query")
        span.set_attribute("connection_management", "BAD - No cleanup")
        
        if not connection_pool:
            # Mock response if no database
            time.sleep(0.1)
            return {"message": "Mock data (no database)", "leak": "simulated"}
        
        conn = None
        try:
            # Get connection from pool
            with tracer.start_as_current_span("get_connection"):
                conn = connection_pool.getconn()
                pool_stats["active_connections"] += 1
                span.set_attribute("pool.active_connections", pool_stats["active_connections"])
                span.add_event("connection_acquired")
            
            # Simulate query
            with tracer.start_as_current_span("database.query") as db_span:
                db_span.set_attribute("db.system", "postgresql")
                db_span.set_attribute("db.statement", "SELECT * FROM sensors")
                
                cursor = conn.cursor()
                time.sleep(0.05)  # Simulate query time
                
                # Randomly throw exception (50% chance)
                if random.random() > 0.5:
                    db_span.add_event("query_error", {"error": "Simulated database error"})
                    raise Exception("Simulated database error")
                
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                db_span.add_event("query_success")
            
            # ❌ BUG: Only returns connection on success
            # If exception occurs above, connection is NEVER returned!
            connection_pool.putconn(conn)
            pool_stats["active_connections"] -= 1
            pool_stats["successful_requests"] += 1
            
            span.add_event("connection_returned")
            return {
                "status": "success",
                "data": "Query executed",
                "pool_status": get_pool_status()
            }
            
        except Exception as e:
            # ❌ BUG: Connection is NOT returned to pool on exception!
            # This causes connection leak
            pool_stats["leaked_connections"] += 1
            pool_stats["failed_requests"] += 1
            
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            span.record_exception(e)
            span.add_event("connection_leaked", {
                "error": str(e),
                "leaked_connections": pool_stats["leaked_connections"]
            })
            
            # Check if pool is exhausted
            status = get_pool_status()
            if status["available"] <= 0:
                span.add_event("pool_exhausted", {
                    "active": status["active"],
                    "leaked": status["leaked"]
                })
                raise HTTPException(
                    status_code=500,
                    detail=f"Connection pool exhausted! Active: {status['active']}, Leaked: {status['leaked']}"
                )
            
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ============================================================================
# SCENARIO 2: GOOD CODE - Proper Connection Management
# ============================================================================

@app.get("/api/good/query")
def good_query_no_leak():
    """
    ✅ GOOD: Proper connection management with try-finally
    Always returns connection to pool, even on exception
    """
    with tracer.start_as_current_span("good_query_no_leak") as span:
        span.set_attribute("endpoint", "/api/good/query")
        span.set_attribute("connection_management", "GOOD - Proper cleanup")
        
        if not connection_pool:
            # Mock response if no database
            time.sleep(0.1)
            return {"message": "Mock data (no database)", "leak": "none"}
        
        conn = None
        try:
            # Get connection from pool
            with tracer.start_as_current_span("get_connection"):
                conn = connection_pool.getconn()
                pool_stats["active_connections"] += 1
                span.set_attribute("pool.active_connections", pool_stats["active_connections"])
                span.add_event("connection_acquired")
            
            # Simulate query
            with tracer.start_as_current_span("database.query") as db_span:
                db_span.set_attribute("db.system", "postgresql")
                db_span.set_attribute("db.statement", "SELECT * FROM sensors")
                
                cursor = conn.cursor()
                time.sleep(0.05)  # Simulate query time
                
                # Randomly throw exception (50% chance)
                if random.random() > 0.5:
                    db_span.add_event("query_error", {"error": "Simulated database error"})
                    raise Exception("Simulated database error")
                
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                db_span.add_event("query_success")
            
            pool_stats["successful_requests"] += 1
            return {
                "status": "success",
                "data": "Query executed",
                "pool_status": get_pool_status()
            }
            
        except Exception as e:
            pool_stats["failed_requests"] += 1
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            span.record_exception(e)
            span.add_event("error_handled", {"error": str(e)})
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
            
        finally:
            # ✅ CRITICAL: Always return connection to pool
            # This runs even if exception occurs
            if conn:
                with tracer.start_as_current_span("return_connection"):
                    connection_pool.putconn(conn)
                    pool_stats["active_connections"] -= 1
                    span.add_event("connection_returned_safely")


# ============================================================================
# Utility Endpoints
# ============================================================================

@app.get("/api/pool/status")
def get_pool_stats():
    """Get current connection pool statistics"""
    return {
        "pool": get_pool_status(),
        "stats": pool_stats,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/pool/reset")
def reset_pool():
    """Reset connection pool statistics"""
    pool_stats["active_connections"] = 0
    pool_stats["leaked_connections"] = 0
    pool_stats["successful_requests"] = 0
    pool_stats["failed_requests"] = 0
    return {"message": "Pool stats reset", "status": get_pool_status()}


@app.get("/health")
def health():
    return {"status": "healthy", "pool": get_pool_status()}


# ============================================================================
# Interactive UI
# ============================================================================

@app.get("/", response_class=HTMLResponse)
def demo_ui():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Connection Leak Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 30px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .scenario {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .scenario.bad {
            border-top: 5px solid #dc3545;
        }
        .scenario.good {
            border-top: 5px solid #28a745;
        }
        .scenario h2 {
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        .scenario.bad h2 { color: #dc3545; }
        .scenario.good h2 { color: #28a745; }
        .test-btn {
            width: 100%;
            padding: 15px;
            margin-bottom: 15px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        .test-btn.bad {
            background: #dc3545;
            color: white;
        }
        .test-btn.good {
            background: #28a745;
            color: white;
        }
        .test-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .results {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            min-height: 200px;
            max-height: 400px;
            overflow-y: auto;
        }
        .result-item {
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            font-size: 14px;
        }
        .result-item.success {
            background: #d4edda;
            border-left: 4px solid #28a745;
        }
        .result-item.error {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
        }
        .pool-status {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        .pool-status h2 {
            color: #667eea;
            margin-bottom: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            color: white;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-top: 5px;
        }
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #ffc107 50%, #dc3545 100%);
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        .code-block {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            overflow-x: auto;
        }
        .code-block .comment { color: #6a9955; }
        .code-block .keyword { color: #569cd6; }
        .code-block .error { color: #f44747; }
        .code-block .success { color: #4ec9b0; }
        .reset-btn {
            background: #ffc107;
            color: #333;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 10px;
        }
        .jaeger-link {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            margin-top: 10px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Connection Leak Debugging Demo</h1>
            <p>Learn how to identify and fix connection leaks using OpenTelemetry tracing</p>
            <p style="margin-top: 10px; color: #666;">
                ✓ Running locally without Docker | ✓ Mock database simulation | ✓ Real connection pool behavior
            </p>
        </div>

        <div class="pool-status">
            <h2>📊 Connection Pool Status</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="totalConn">5</div>
                    <div class="stat-label">Total Connections</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="activeConn">0</div>
                    <div class="stat-label">Active</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="availableConn">5</div>
                    <div class="stat-label">Available</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="leakedConn">0</div>
                    <div class="stat-label">Leaked</div>
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="poolProgress" style="width: 0%">0% Used</div>
            </div>
            <button class="reset-btn" onclick="resetPool()">🔄 Reset Pool</button>
        </div>

        <div class="grid">
            <div class="scenario bad">
                <h2>❌ BAD: Connection Leak</h2>
                <p style="margin-bottom: 20px;">
                    This endpoint has a bug - it doesn't return connections to the pool when exceptions occur.
                    After 5 requests, the pool will be exhausted!
                </p>
                
                <div class="code-block">
<span class="keyword">try</span>:
    conn = pool.getconn()
    cursor.execute("SELECT * FROM sensors")
    pool.putconn(conn)  <span class="comment"># Only runs on success</span>
<span class="keyword">except</span> Exception:
    <span class="error"># BUG: Connection never returned!</span>
    <span class="keyword">raise</span>
                </div>

                <button class="test-btn bad" onclick="testBadEndpoint()">
                    🔴 Test Bad Endpoint (With Leak)
                </button>
                <button class="test-btn bad" onclick="testBadMultiple()">
                    💥 Test 10 Times (Exhaust Pool)
                </button>
                
                <div class="results" id="badResults"></div>
            </div>

            <div class="scenario good">
                <h2>✅ GOOD: Proper Cleanup</h2>
                <p style="margin-bottom: 20px;">
                    This endpoint properly returns connections using try-finally.
                    It can handle unlimited requests without leaking!
                </p>
                
                <div class="code-block">
<span class="keyword">try</span>:
    conn = pool.getconn()
    cursor.execute("SELECT * FROM sensors")
<span class="keyword">except</span> Exception:
    <span class="keyword">raise</span>
<span class="keyword">finally</span>:
    <span class="success"># ALWAYS runs, even on exception</span>
    <span class="keyword">if</span> conn:
        pool.putconn(conn)
                </div>

                <button class="test-btn good" onclick="testGoodEndpoint()">
                    🟢 Test Good Endpoint (No Leak)
                </button>
                <button class="test-btn good" onclick="testGoodMultiple()">
                    ✨ Test 10 Times (No Problem)
                </button>
                
                <div class="results" id="goodResults"></div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:9000';
        let badCount = 0;
        let goodCount = 0;

        async function updatePoolStatus() {
            try {
                const response = await fetch(`${API_BASE}/api/pool/status`);
                const data = await response.json();
                
                document.getElementById('totalConn').textContent = data.pool.total;
                document.getElementById('activeConn').textContent = data.pool.active;
                document.getElementById('availableConn').textContent = data.pool.available;
                document.getElementById('leakedConn').textContent = data.pool.leaked;
                
                const percentage = data.pool.percentage_used;
                const progressBar = document.getElementById('poolProgress');
                progressBar.style.width = percentage + '%';
                progressBar.textContent = Math.round(percentage) + '% Used';
            } catch (error) {
                console.error('Error updating pool status:', error);
            }
        }

        async function testBadEndpoint() {
            badCount++;
            const resultsDiv = document.getElementById('badResults');
            const timestamp = new Date().toLocaleTimeString();
            
            try {
                const response = await fetch(`${API_BASE}/api/bad/query`);
                const data = await response.json();
                
                if (response.ok) {
                    resultsDiv.innerHTML = `
                        <div class="result-item success">
                            [${timestamp}] Request #${badCount}: ✓ Success
                            <br>Pool: ${data.pool_status.available}/${data.pool_status.total} available
                        </div>
                    ` + resultsDiv.innerHTML;
                } else {
                    resultsDiv.innerHTML = `
                        <div class="result-item error">
                            [${timestamp}] Request #${badCount}: ✗ ${data.detail}
                        </div>
                    ` + resultsDiv.innerHTML;
                }
            } catch (error) {
                resultsDiv.innerHTML = `
                    <div class="result-item error">
                        [${timestamp}] Request #${badCount}: ✗ ${error.message}
                    </div>
                ` + resultsDiv.innerHTML;
            }
            
            await updatePoolStatus();
        }

        async function testGoodEndpoint() {
            goodCount++;
            const resultsDiv = document.getElementById('goodResults');
            const timestamp = new Date().toLocaleTimeString();
            
            try {
                const response = await fetch(`${API_BASE}/api/good/query`);
                const data = await response.json();
                
                if (response.ok) {
                    resultsDiv.innerHTML = `
                        <div class="result-item success">
                            [${timestamp}] Request #${goodCount}: ✓ Success
                            <br>Pool: ${data.pool_status.available}/${data.pool_status.total} available
                        </div>
                    ` + resultsDiv.innerHTML;
                } else {
                    resultsDiv.innerHTML = `
                        <div class="result-item error">
                            [${timestamp}] Request #${goodCount}: ✗ ${data.detail}
                        </div>
                    ` + resultsDiv.innerHTML;
                }
            } catch (error) {
                resultsDiv.innerHTML = `
                    <div class="result-item error">
                        [${timestamp}] Request #${goodCount}: ✗ ${error.message}
                    </div>
                ` + resultsDiv.innerHTML;
            }
            
            await updatePoolStatus();
        }

        async function testBadMultiple() {
            for (let i = 0; i < 10; i++) {
                await testBadEndpoint();
                await new Promise(resolve => setTimeout(resolve, 200));
            }
        }

        async function testGoodMultiple() {
            for (let i = 0; i < 10; i++) {
                await testGoodEndpoint();
                await new Promise(resolve => setTimeout(resolve, 200));
            }
        }

        async function resetPool() {
            try {
                await fetch(`${API_BASE}/api/pool/reset`, { method: 'POST' });
                document.getElementById('badResults').innerHTML = '';
                document.getElementById('goodResults').innerHTML = '';
                badCount = 0;
                goodCount = 0;
                await updatePoolStatus();
                alert('Pool reset successfully!');
            } catch (error) {
                alert('Error resetting pool: ' + error.message);
            }
        }

        // Update pool status every 2 seconds
        setInterval(updatePoolStatus, 2000);
        updatePoolStatus();
    </script>
</body>
</html>
    """


if __name__ == "__main__":
    import uvicorn
    print("\n🔍 Starting Connection Leak Demo...")
    print("📊 Demo UI: http://localhost:9000")
    print("🔍 Jaeger UI: http://localhost:16686")
    print("\n💡 Instructions:")
    print("1. Open the demo UI")
    print("2. Click 'Test Bad Endpoint' multiple times")
    print("3. Watch the connection pool get exhausted")
    print("4. Open Jaeger to see the traces showing leaked connections")
    print("5. Compare with 'Test Good Endpoint' which never leaks\n")
    uvicorn.run(app, host="0.0.0.0", port=9000)

# -*- coding: utf-8 -*-
"""
Connection Leak Demo - Simplified (No External Dependencies)
Demonstrates connection pool exhaustion without needing PostgreSQL or Jaeger
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import time
import random
from datetime import datetime
from typing import List, Dict

app = FastAPI(title="Connection Leak Demo")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Mock Connection Pool (Simulates PostgreSQL without needing it)
# ============================================================================

class MockConnection:
    """Simulates a database connection"""
    def __init__(self, conn_id):
        self.id = conn_id
        self.in_use = True
        self.created_at = time.time()
    
    def cursor(self):
        return MockCursor()
    
    def close(self):
        self.in_use = False


class MockCursor:
    """Simulates a database cursor"""
    def execute(self, query):
        time.sleep(0.05)  # Simulate query time
        # Randomly throw exception (50% chance)
        if random.random() > 0.5:
            raise Exception("Simulated database error")
    
    def fetchone(self):
        return (1,)
    
    def close(self):
        pass


class MockConnectionPool:
    """Simulates a connection pool"""
    def __init__(self, minconn, maxconn):
        self.maxconn = maxconn
        self.active_connections: List[MockConnection] = []  # Currently in use
        self.all_connections: List[MockConnection] = []  # All ever created
        self._connection_counter = 0
    
    def getconn(self):
        """Get a connection from pool"""
        # Check if pool is exhausted
        if len(self.active_connections) >= self.maxconn:
            raise Exception(f"Connection pool exhausted! {len(self.active_connections)}/{self.maxconn} in use")
        
        # Create new connection
        conn = MockConnection(self._connection_counter)
        self._connection_counter += 1
        self.active_connections.append(conn)
        self.all_connections.append(conn)
        return conn
    
    def putconn(self, conn):
        """Return connection to pool"""
        # Remove from active connections
        if conn in self.active_connections:
            self.active_connections.remove(conn)
            conn.in_use = False
    
    def get_stats(self):
        """Get pool statistics"""
        active = len(self.active_connections)
        return {
            "total": self.maxconn,
            "active": active,
            "available": self.maxconn - active,
            "percentage_used": (active / self.maxconn) * 100
        }


# Create connection pool
connection_pool = MockConnectionPool(1, 5)  # Small pool to demonstrate quickly

# Track statistics
stats = {
    "successful_requests": 0,
    "failed_requests": 0,
    "leaked_connections": 0,
    "traces": []  # Store trace information
}


def add_trace(endpoint, success, leaked, duration, error=None):
    """Add trace information"""
    trace = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "endpoint": endpoint,
        "success": success,
        "leaked": leaked,
        "duration_ms": int(duration * 1000),
        "error": error,
        "pool_status": connection_pool.get_stats()
    }
    stats["traces"].insert(0, trace)  # Add to beginning
    if len(stats["traces"]) > 50:  # Keep last 50 traces
        stats["traces"].pop()
    return trace


# ============================================================================
# SCENARIO 1: BAD CODE - Connection Leak
# ============================================================================

@app.get("/api/bad/query")
def bad_query_with_leak():
    """
    ❌ BAD: Connection leak - doesn't close connection on exception
    """
    start_time = time.time()
    conn = None
    
    try:
        # Get connection from pool
        conn = connection_pool.getconn()
        
        # Simulate query
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sensors")
        result = cursor.fetchone()
        cursor.close()
        
        # ❌ BUG: Only returns connection on success
        connection_pool.putconn(conn)
        
        stats["successful_requests"] += 1
        duration = time.time() - start_time
        
        trace = add_trace("/api/bad/query", True, False, duration)
        
        return {
            "status": "success",
            "data": "Query executed",
            "pool_status": connection_pool.get_stats(),
            "trace": trace
        }
        
    except Exception as e:
        # ❌ BUG: Connection is NOT returned to pool on exception!
        stats["failed_requests"] += 1
        stats["leaked_connections"] += 1
        
        duration = time.time() - start_time
        trace = add_trace("/api/bad/query", False, True, duration, str(e))
        
        # Check if pool is exhausted
        pool_status = connection_pool.get_stats()
        if pool_status["available"] <= 0:
            raise HTTPException(
                status_code=500,
                detail=f"💥 Connection pool exhausted! Active: {pool_status['active']}, Leaked: {stats['leaked_connections']}"
            )
        
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ============================================================================
# SCENARIO 2: GOOD CODE - Proper Connection Management
# ============================================================================

@app.get("/api/good/query")
def good_query_no_leak():
    """
    ✅ GOOD: Proper connection management with try-finally
    """
    start_time = time.time()
    conn = None
    
    try:
        # Get connection from pool
        conn = connection_pool.getconn()
        
        # Simulate query
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sensors")
        result = cursor.fetchone()
        cursor.close()
        
        stats["successful_requests"] += 1
        duration = time.time() - start_time
        
        trace = add_trace("/api/good/query", True, False, duration)
        
        return {
            "status": "success",
            "data": "Query executed",
            "pool_status": connection_pool.get_stats(),
            "trace": trace
        }
        
    except Exception as e:
        stats["failed_requests"] += 1
        duration = time.time() - start_time
        
        trace = add_trace("/api/good/query", False, False, duration, str(e))
        
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
    finally:
        # ✅ CRITICAL: Always return connection to pool
        if conn:
            connection_pool.putconn(conn)


# ============================================================================
# Utility Endpoints
# ============================================================================

@app.get("/api/pool/status")
def get_pool_status():
    """Get current connection pool statistics"""
    return {
        "pool": connection_pool.get_stats(),
        "stats": {
            "successful_requests": stats["successful_requests"],
            "failed_requests": stats["failed_requests"],
            "leaked_connections": stats["leaked_connections"]
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/traces")
def get_traces():
    """Get recent traces"""
    return {"traces": stats["traces"][:20]}  # Return last 20 traces


@app.post("/api/pool/reset")
def reset_pool():
    """Reset connection pool and statistics"""
    global connection_pool
    connection_pool = MockConnectionPool(1, 5)
    stats["successful_requests"] = 0
    stats["failed_requests"] = 0
    stats["leaked_connections"] = 0
    stats["traces"] = []
    return {"message": "Pool and stats reset", "status": connection_pool.get_stats()}


@app.get("/health")
def health():
    return {"status": "healthy", "pool": connection_pool.get_stats()}


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
            max-width: 1600px;
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
        .badge {
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin: 5px;
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
        .traces-section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-top: 20px;
        }
        .traces-section h2 {
            color: #667eea;
            margin-bottom: 20px;
        }
        .trace-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
        }
        .trace-item.leaked {
            border-left-color: #dc3545;
            background: #fff5f5;
        }
        .trace-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-weight: bold;
        }
        .trace-details {
            font-size: 0.9em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Connection Leak Debugging Demo</h1>
            <p>Learn how to identify and fix connection leaks</p>
            <div style="margin-top: 15px;">
                <span class="badge">✓ No Docker Required</span>
                <span class="badge">✓ No PostgreSQL Required</span>
                <span class="badge">✓ Pure Python Simulation</span>
            </div>
        </div>

        <div class="pool-status">
            <h2>📊 Connection Pool Status (Max: 5 connections)</h2>
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
            <button class="reset-btn" onclick="resetPool()">🔄 Reset Pool & Clear Traces</button>
        </div>

        <div class="grid">
            <div class="scenario bad">
                <h2>❌ BAD: Connection Leak</h2>
                <p style="margin-bottom: 20px;">
                    This endpoint has a bug - it doesn't return connections to the pool when exceptions occur.
                    After 5 requests with errors, the pool will be exhausted!
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

        <div class="traces-section">
            <h2>🔍 Recent Traces (Last 10)</h2>
            <div id="tracesContainer"></div>
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
                document.getElementById('leakedConn').textContent = data.stats.leaked_connections;
                
                const percentage = data.pool.percentage_used;
                const progressBar = document.getElementById('poolProgress');
                progressBar.style.width = percentage + '%';
                progressBar.textContent = Math.round(percentage) + '% Used';
            } catch (error) {
                console.error('Error updating pool status:', error);
            }
        }

        async function updateTraces() {
            try {
                const response = await fetch(`${API_BASE}/api/traces`);
                const data = await response.json();
                const container = document.getElementById('tracesContainer');
                
                if (data.traces.length === 0) {
                    container.innerHTML = '<p style="color: #999; text-align: center;">No traces yet. Click a button to start testing!</p>';
                    return;
                }
                
                container.innerHTML = data.traces.slice(0, 10).map(trace => `
                    <div class="trace-item ${trace.leaked ? 'leaked' : ''}">
                        <div class="trace-header">
                            <span>${trace.timestamp} - ${trace.endpoint}</span>
                            <span>${trace.success ? '✓ Success' : '✗ Error'} (${trace.duration_ms}ms)</span>
                        </div>
                        <div class="trace-details">
                            ${trace.leaked ? '⚠️ <strong>CONNECTION LEAKED!</strong> | ' : ''}
                            Pool: ${trace.pool_status.active}/${trace.pool_status.total} active, 
                            ${trace.pool_status.available} available
                            ${trace.error ? `<br>Error: ${trace.error}` : ''}
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error updating traces:', error);
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
            await updateTraces();
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
            await updateTraces();
        }

        async function testBadMultiple() {
            for (let i = 0; i < 10; i++) {
                await testBadEndpoint();
                await new Promise(resolve => setTimeout(resolve, 300));
            }
        }

        async function testGoodMultiple() {
            for (let i = 0; i < 10; i++) {
                await testGoodEndpoint();
                await new Promise(resolve => setTimeout(resolve, 300));
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
                await updateTraces();
                alert('✓ Pool reset successfully!');
            } catch (error) {
                alert('Error resetting pool: ' + error.message);
            }
        }

        // Update status and traces every 2 seconds
        setInterval(() => {
            updatePoolStatus();
            updateTraces();
        }, 2000);
        
        updatePoolStatus();
        updateTraces();
    </script>
</body>
</html>
    """


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🔍 Connection Leak Demo - Starting...")
    print("="*60)
    print("\n✓ No Docker required")
    print("✓ No PostgreSQL required")
    print("✓ Pure Python simulation\n")
    print("📊 Demo UI: http://localhost:9000")
    print("\n💡 Instructions:")
    print("1. Open http://localhost:9000 in your browser")
    print("2. Click 'Test Bad Endpoint' to see connection leaks")
    print("3. Watch the pool get exhausted after 5 leaked connections")
    print("4. Compare with 'Test Good Endpoint' which never leaks")
    print("5. Check the traces section to see leak details\n")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=9000)

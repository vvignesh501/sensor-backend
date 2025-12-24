# -*- coding: utf-8 -*-
"""
OpenTelemetry + Jaeger Visual Demo UI
Interactive demonstration of distributed tracing
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="OpenTelemetry Tracing Demo")

@app.get("/", response_class=HTMLResponse)
def demo_ui():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>OpenTelemetry + Jaeger Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 30px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .header p {
            font-size: 1.3em;
            opacity: 0.9;
        }
        .main-grid {
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .sidebar {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            color: #333;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .sidebar h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        .action-btn {
            width: 100%;
            padding: 15px;
            margin-bottom: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 10px;
            color: white;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        .action-btn:active {
            transform: translateY(0);
        }
        .action-btn.slow {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .action-btn.error {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }
        .info-box {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            border-left: 4px solid #667eea;
        }
        .info-box h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        .info-box ul {
            list-style: none;
            padding-left: 0;
        }
        .info-box li {
            padding: 5px 0;
            color: #666;
            font-size: 14px;
        }
        .info-box li:before {
            content: "✓ ";
            color: #48bb78;
            font-weight: bold;
        }
        .trace-area {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            color: #333;
            min-height: 600px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .trace-visualization {
            margin-top: 20px;
        }
        .trace-item {
            background: #fff;
            border-left: 4px solid #667eea;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            animation: slideIn 0.5s ease-out;
        }
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        .trace-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .trace-id {
            font-family: monospace;
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
        }
        .trace-duration {
            background: #48bb78;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
        }
        .trace-duration.slow {
            background: #f56565;
        }
        .span-timeline {
            margin-top: 15px;
        }
        .span {
            margin-bottom: 10px;
        }
        .span-info {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        .span-name {
            font-weight: 600;
            color: #667eea;
            min-width: 200px;
        }
        .span-bar-container {
            flex: 1;
            height: 30px;
            background: #e2e8f0;
            border-radius: 5px;
            position: relative;
            overflow: hidden;
        }
        .span-bar {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 5px;
            display: flex;
            align-items: center;
            padding: 0 10px;
            color: white;
            font-size: 12px;
            font-weight: bold;
            transition: width 0.5s ease-out;
        }
        .span-bar.slow {
            background: linear-gradient(90deg, #f56565 0%, #ed8936 100%);
        }
        .span-bar.fast {
            background: linear-gradient(90deg, #48bb78 0%, #38a169 100%);
        }
        .span-details {
            font-size: 12px;
            color: #666;
            margin-left: 210px;
            margin-top: 5px;
        }
        .span-tag {
            display: inline-block;
            background: #e2e8f0;
            padding: 2px 8px;
            border-radius: 3px;
            margin-right: 5px;
            font-size: 11px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        .empty-state {
            text-align: center;
            padding: 100px 20px;
            color: #999;
        }
        .empty-state h2 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .loading {
            text-align: center;
            padding: 50px;
        }
        .loading-spinner {
            border: 4px solid #e2e8f0;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .jaeger-link {
            display: block;
            text-align: center;
            padding: 15px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            color: #667eea;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.1em;
            margin-top: 20px;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .jaeger-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        .architecture-diagram {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            color: #333;
        }
        .architecture-diagram pre {
            font-size: 12px;
            line-height: 1.6;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 OpenTelemetry + Jaeger Demo</h1>
            <p>Interactive Distributed Tracing Visualization</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="totalTraces">0</div>
                <div class="stat-label">Total Traces</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="avgDuration">0ms</div>
                <div class="stat-label">Avg Duration</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="slowTraces">0</div>
                <div class="stat-label">Slow Traces</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="errorTraces">0</div>
                <div class="stat-label">Errors</div>
            </div>
        </div>

        <div class="main-grid">
            <div class="sidebar">
                <h2>🎮 Actions</h2>
                
                <button class="action-btn" onclick="makeRequest('/api/sensors')">
                    📊 Get All Sensors
                </button>
                
                <button class="action-btn" onclick="makeRequest('/api/sensors/sensor-1')">
                    🔍 Get Sensor Details
                </button>
                
                <button class="action-btn" onclick="makeRequest('/api/sensors/sensor-1/aggregate')">
                    📈 Aggregate Data (Multi-Service)
                </button>
                
                <button class="action-btn" onclick="createSensor()">
                    ➕ Create New Sensor
                </button>
                
                <button class="action-btn slow" onclick="makeRequest('/api/slow-endpoint')">
                    🐌 Slow Endpoint (Profiling)
                </button>
                
                <button class="action-btn error" onclick="makeRequest('/api/error-endpoint')">
                    ❌ Error Endpoint (Error Tracking)
                </button>

                <div class="info-box">
                    <h3>💡 What You'll See</h3>
                    <ul>
                        <li>Trace ID & Duration</li>
                        <li>Span Timeline</li>
                        <li>Database Queries</li>
                        <li>Cache Operations</li>
                        <li>External API Calls</li>
                        <li>Performance Metrics</li>
                    </ul>
                </div>

                <a href="http://localhost:16686" target="_blank" class="jaeger-link">
                    🚀 Open Jaeger UI
                </a>

                <div class="architecture-diagram">
                    <h3 style="color: #667eea; margin-bottom: 10px;">Architecture</h3>
                    <pre style="color: #666;">
Client
  ↓
API Gateway
  ├─ Auth Service
  │  └─ PostgreSQL
  ├─ Sensor Service
  │  ├─ Redis Cache
  │  └─ PostgreSQL
  └─ Kafka Service
     └─ Kafka Broker
  ↓
Jaeger Collector
  ↓
Jaeger UI
                    </pre>
                </div>
            </div>

            <div class="trace-area">
                <h2 style="color: #667eea; margin-bottom: 20px;">📊 Live Traces</h2>
                
                <div id="emptyState" class="empty-state">
                    <h2>👈 Click an action to start</h2>
                    <p>Watch distributed tracing in action!</p>
                </div>

                <div id="loading" class="loading" style="display: none;">
                    <div class="loading-spinner"></div>
                    <p style="color: #666;">Processing request...</p>
                </div>

                <div id="traceVisualization" class="trace-visualization"></div>
            </div>
        </div>
    </div>

    <script>
        let traceCount = 0;
        let totalDuration = 0;
        let slowCount = 0;
        let errorCount = 0;

        const API_BASE = 'http://localhost:8000';

        function updateStats() {
            document.getElementById('totalTraces').textContent = traceCount;
            const avgDur = traceCount > 0 ? Math.round(totalDuration / traceCount) : 0;
            document.getElementById('avgDuration').textContent = avgDur + 'ms';
            document.getElementById('slowTraces').textContent = slowCount;
            document.getElementById('errorTraces').textContent = errorCount;
        }

        async function makeRequest(endpoint) {
            document.getElementById('emptyState').style.display = 'none';
            document.getElementById('loading').style.display = 'block';

            const startTime = Date.now();
            
            try {
                const response = await fetch(API_BASE + endpoint);
                const duration = Date.now() - startTime;
                const data = await response.json();
                
                // Simulate trace data
                const trace = generateTrace(endpoint, duration, response.ok);
                displayTrace(trace);
                
                // Update stats
                traceCount++;
                totalDuration += duration;
                if (duration > 500) slowCount++;
                if (!response.ok) errorCount++;
                updateStats();
                
            } catch (error) {
                console.error('Error:', error);
                errorCount++;
                updateStats();
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }

        async function createSensor() {
            document.getElementById('emptyState').style.display = 'none';
            document.getElementById('loading').style.display = 'block';

            const startTime = Date.now();
            
            try {
                const response = await fetch(API_BASE + '/api/sensors', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: 'Demo Sensor ' + Date.now(),
                        type: 'temperature',
                        value: Math.random() * 100,
                        unit: '°C'
                    })
                });
                
                const duration = Date.now() - startTime;
                const trace = generateTrace('/api/sensors [POST]', duration, response.ok);
                displayTrace(trace);
                
                traceCount++;
                totalDuration += duration;
                if (duration > 500) slowCount++;
                if (!response.ok) errorCount++;
                updateStats();
                
            } catch (error) {
                console.error('Error:', error);
                errorCount++;
                updateStats();
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }

        function generateTrace(endpoint, totalDuration, success) {
            const traceId = generateTraceId();
            const spans = [];

            if (endpoint.includes('slow')) {
                // Slow endpoint spans
                spans.push({
                    name: 'HTTP Request',
                    duration: totalDuration,
                    percentage: 100,
                    tags: ['http.method: GET', 'http.url: ' + endpoint]
                });
                spans.push({
                    name: '└─ Slow Database Query',
                    duration: Math.round(totalDuration * 0.5),
                    percentage: 50,
                    tags: ['db.system: postgresql', 'query.type: complex_join'],
                    slow: true
                });
                spans.push({
                    name: '└─ External API Call 1',
                    duration: Math.round(totalDuration * 0.2),
                    percentage: 20,
                    tags: ['http.method: GET', 'peer.service: analytics']
                });
                spans.push({
                    name: '└─ External API Call 2',
                    duration: Math.round(totalDuration * 0.2),
                    percentage: 20,
                    tags: ['http.method: GET', 'peer.service: reporting']
                });
                spans.push({
                    name: '└─ Heavy Computation',
                    duration: Math.round(totalDuration * 0.1),
                    percentage: 10,
                    tags: ['operation: data_processing']
                });
            } else if (endpoint.includes('aggregate')) {
                // Multi-service spans
                spans.push({
                    name: 'HTTP Request',
                    duration: totalDuration,
                    percentage: 100,
                    tags: ['http.method: GET', 'http.url: ' + endpoint]
                });
                spans.push({
                    name: '└─ Get Sensor Details',
                    duration: Math.round(totalDuration * 0.3),
                    percentage: 30,
                    tags: ['operation: get_sensor']
                });
                spans.push({
                    name: '  └─ Database Query',
                    duration: Math.round(totalDuration * 0.25),
                    percentage: 25,
                    tags: ['db.system: postgresql'],
                    fast: true
                });
                spans.push({
                    name: '└─ Analytics Service Call',
                    duration: Math.round(totalDuration * 0.35),
                    percentage: 35,
                    tags: ['http.method: GET', 'peer.service: analytics']
                });
                spans.push({
                    name: '└─ Reporting Service Call',
                    duration: Math.round(totalDuration * 0.35),
                    percentage: 35,
                    tags: ['http.method: GET', 'peer.service: reporting']
                });
            } else if (endpoint.includes('POST')) {
                // Create sensor spans
                spans.push({
                    name: 'HTTP Request',
                    duration: totalDuration,
                    percentage: 100,
                    tags: ['http.method: POST', 'http.url: /api/sensors']
                });
                spans.push({
                    name: '└─ Validation',
                    duration: Math.round(totalDuration * 0.1),
                    percentage: 10,
                    tags: ['operation: validate'],
                    fast: true
                });
                spans.push({
                    name: '└─ Process Data',
                    duration: Math.round(totalDuration * 0.2),
                    percentage: 20,
                    tags: ['operation: process']
                });
                spans.push({
                    name: '└─ Database Insert',
                    duration: Math.round(totalDuration * 0.4),
                    percentage: 40,
                    tags: ['db.system: postgresql', 'db.operation: INSERT']
                });
                spans.push({
                    name: '└─ Cache Invalidate',
                    duration: Math.round(totalDuration * 0.1),
                    percentage: 10,
                    tags: ['cache.system: redis'],
                    fast: true
                });
                spans.push({
                    name: '└─ Publish Event',
                    duration: Math.round(totalDuration * 0.2),
                    percentage: 20,
                    tags: ['event.type: sensor.created']
                });
            } else {
                // Normal request spans
                spans.push({
                    name: 'HTTP Request',
                    duration: totalDuration,
                    percentage: 100,
                    tags: ['http.method: GET', 'http.url: ' + endpoint]
                });
                spans.push({
                    name: '└─ Cache Lookup',
                    duration: Math.round(totalDuration * 0.1),
                    percentage: 10,
                    tags: ['cache.system: redis', 'cache.hit: false'],
                    fast: true
                });
                spans.push({
                    name: '└─ Database Query',
                    duration: Math.round(totalDuration * 0.7),
                    percentage: 70,
                    tags: ['db.system: postgresql', 'db.statement: SELECT * FROM sensors']
                });
                spans.push({
                    name: '└─ Response Serialization',
                    duration: Math.round(totalDuration * 0.2),
                    percentage: 20,
                    tags: ['operation: serialize'],
                    fast: true
                });
            }

            return {
                traceId,
                endpoint,
                totalDuration,
                success,
                spans,
                timestamp: new Date().toLocaleTimeString()
            };
        }

        function generateTraceId() {
            return Array.from({length: 16}, () => 
                Math.floor(Math.random() * 16).toString(16)
            ).join('');
        }

        function displayTrace(trace) {
            const container = document.getElementById('traceVisualization');
            
            const traceDiv = document.createElement('div');
            traceDiv.className = 'trace-item';
            
            const durationClass = trace.totalDuration > 500 ? 'slow' : '';
            
            traceDiv.innerHTML = `
                <div class="trace-header">
                    <div>
                        <strong style="color: #667eea; font-size: 1.1em;">${trace.endpoint}</strong>
                        <div style="font-size: 0.9em; color: #999; margin-top: 5px;">
                            ${trace.timestamp} | Trace ID: <span class="trace-id">${trace.traceId}</span>
                        </div>
                    </div>
                    <div class="trace-duration ${durationClass}">${trace.totalDuration}ms</div>
                </div>
                
                <div class="span-timeline">
                    ${trace.spans.map(span => `
                        <div class="span">
                            <div class="span-info">
                                <div class="span-name">${span.name}</div>
                                <div class="span-bar-container">
                                    <div class="span-bar ${span.slow ? 'slow' : span.fast ? 'fast' : ''}" 
                                         style="width: ${span.percentage}%">
                                        ${span.duration}ms
                                    </div>
                                </div>
                            </div>
                            <div class="span-details">
                                ${span.tags.map(tag => `<span class="span-tag">${tag}</span>`).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            
            container.insertBefore(traceDiv, container.firstChild);
            
            // Keep only last 5 traces
            while (container.children.length > 5) {
                container.removeChild(container.lastChild);
            }
        }

        // Auto-generate some initial traffic
        setTimeout(() => {
            makeRequest('/api/sensors');
        }, 1000);
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting OpenTelemetry + Jaeger Demo UI...")
    print("📊 Demo UI: http://localhost:8005")
    print("🔍 Jaeger UI: http://localhost:16686")
    print("🔌 Sensor API: http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8005)

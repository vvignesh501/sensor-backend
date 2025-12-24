"""
VISUAL RATE LIMITING DEMO - Interactive UI
Click buttons to send requests and watch the bucket fill/leak in real-time
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from leaky_bucket import LeakyBucket
import time

app = FastAPI()

# Single bucket for demo (in production, one per client)
demo_bucket = LeakyBucket(capacity=10, leak_rate=2.0)

@app.post("/api/request")
def make_request():
    """Simulate a request"""
    allowed = demo_bucket.allow_request()
    status = demo_bucket.get_status()
    
    return {
        "allowed": allowed,
        "status": status,
        "timestamp": time.time()
    }

@app.get("/api/bucket-status")
def get_bucket_status():
    """Get current bucket status"""
    return demo_bucket.get_status()

@app.post("/api/reset")
def reset_bucket():
    """Reset bucket for demo"""
    global demo_bucket
    demo_bucket = LeakyBucket(capacity=10, leak_rate=2.0)
    return {"message": "Bucket reset"}

@app.get("/", response_class=HTMLResponse)
def get_ui():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Leaky Bucket Rate Limiting Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #1a1a2e;
            color: #eee;
            padding: 20px;
            margin: 0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
        }
        .demo-area {
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 20px;
        }
        .controls {
            background: #16213e;
            padding: 30px;
            border-radius: 15px;
        }
        .bucket-visual {
            background: #16213e;
            padding: 30px;
            border-radius: 15px;
        }
        .bucket-container {
            position: relative;
            width: 200px;
            height: 400px;
            margin: 30px auto;
            border: 4px solid #667eea;
            border-radius: 10px;
            background: #0f3460;
            overflow: hidden;
        }
        .water {
            position: absolute;
            bottom: 0;
            width: 100%;
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            transition: height 0.5s ease;
        }
        .leak-hole {
            position: absolute;
            bottom: 10px;
            left: 50%;
            transform: translateX(-50%);
            width: 20px;
            height: 20px;
            background: #ff6b6b;
            border-radius: 50%;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .bucket-label {
            text-align: center;
            margin-top: 20px;
            font-size: 18px;
            font-weight: bold;
        }
        .stats {
            background: #0f3460;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #334155;
        }
        .stat-row:last-child {
            border-bottom: none;
        }
        .button {
            width: 100%;
            padding: 20px;
            font-size: 18px;
            font-weight: bold;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            margin-bottom: 15px;
            transition: all 0.3s;
        }
        .send-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .send-btn:hover {
            transform: scale(1.05);
        }
        .send-btn:active {
            transform: scale(0.95);
        }
        .burst-btn {
            background: #ff6b6b;
            color: white;
        }
        .reset-btn {
            background: #48bb78;
            color: white;
        }
        .log {
            background: #0f3460;
            padding: 20px;
            border-radius: 8px;
            height: 300px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 13px;
        }
        .log-entry {
            padding: 8px;
            margin-bottom: 5px;
            border-radius: 5px;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateX(-10px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .log-allowed {
            background: #48bb7833;
            border-left: 3px solid #48bb78;
        }
        .log-rejected {
            background: #ff6b6b33;
            border-left: 3px solid #ff6b6b;
        }
        .explanation {
            background: #0f3460;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .explanation h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💧 Leaky Bucket Rate Limiting</h1>
            <p>Click buttons to send requests and watch the bucket fill/leak</p>
        </div>

        <div class="demo-area">
            <div class="controls">
                <h2 style="color: #667eea; margin-bottom: 20px;">🎮 Controls</h2>
                
                <button class="button send-btn" onclick="sendRequest()">
                    📤 Send 1 Request
                </button>
                
                <button class="button burst-btn" onclick="sendBurst()">
                    💥 Send 15 Requests (Burst)
                </button>
                
                <button class="button reset-btn" onclick="resetBucket()">
                    🔄 Reset Bucket
                </button>

                <div class="explanation">
                    <h3>⚙️ Configuration</h3>
                    <div class="stat-row">
                        <span>Capacity:</span>
                        <strong>10 requests</strong>
                    </div>
                    <div class="stat-row">
                        <span>Leak Rate:</span>
                        <strong>2 req/sec</strong>
                    </div>
                </div>

                <div class="explanation">
                    <h3>📖 How It Works</h3>
                    <ol style="line-height: 1.8; margin-left: 20px; font-size: 14px;">
                        <li>Each request adds 1 drop to bucket</li>
                        <li>Bucket leaks at 2 drops/second</li>
                        <li>Max capacity: 10 drops</li>
                        <li>If full → Request rejected</li>
                        <li>Wait for leak → Space available</li>
                    </ol>
                </div>

                <h3 style="color: #667eea; margin: 20px 0 10px;">📋 Request Log</h3>
                <div class="log" id="requestLog"></div>
            </div>

            <div class="bucket-visual">
                <h2 style="color: #667eea; margin-bottom: 20px; text-align: center;">
                    🪣 Bucket Visualization
                </h2>
                
                <div class="bucket-container">
                    <div class="water" id="waterLevel"></div>
                    <div class="leak-hole" title="Leak: 2 req/sec"></div>
                </div>
                
                <div class="bucket-label">
                    <span id="bucketLevel">0</span> / 10 requests
                </div>

                <div class="stats">
                    <h3 style="color: #667eea; margin-bottom: 15px;">📊 Live Stats</h3>
                    <div class="stat-row">
                        <span>Water Level:</span>
                        <strong id="statWater">0</strong>
                    </div>
                    <div class="stat-row">
                        <span>Available Space:</span>
                        <strong id="statSpace">10</strong>
                    </div>
                    <div class="stat-row">
                        <span>Bucket Fullness:</span>
                        <strong id="statPercent">0%</strong>
                    </div>
                    <div class="stat-row">
                        <span>Leak Rate:</span>
                        <strong>2 req/sec</strong>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let requestCount = 0;

        async function sendRequest() {
            requestCount++;
            
            const response = await fetch('/api/request', { method: 'POST' });
            const data = await response.json();
            
            updateBucket(data.status);
            logRequest(requestCount, data.allowed, data.status);
        }

        async function sendBurst() {
            for (let i = 0; i < 15; i++) {
                await sendRequest();
                await sleep(100);  // Small delay for visual effect
            }
        }

        async function resetBucket() {
            await fetch('/api/reset', { method: 'POST' });
            requestCount = 0;
            document.getElementById('requestLog').innerHTML = '';
            updateBucket({ water_level: 0, capacity: 10, available_space: 10, percentage_full: 0 });
        }

        function updateBucket(status) {
            const waterLevel = document.getElementById('waterLevel');
            const percentage = (status.water_level / status.capacity) * 100;
            waterLevel.style.height = percentage + '%';
            
            document.getElementById('bucketLevel').textContent = status.water_level.toFixed(1);
            document.getElementById('statWater').textContent = status.water_level.toFixed(2);
            document.getElementById('statSpace').textContent = status.available_space.toFixed(2);
            document.getElementById('statPercent').textContent = status.percentage_full + '%';
        }

        function logRequest(num, allowed, status) {
            const log = document.getElementById('requestLog');
            const entry = document.createElement('div');
            entry.className = 'log-entry ' + (allowed ? 'log-allowed' : 'log-rejected');
            
            const time = new Date().toLocaleTimeString();
            const icon = allowed ? '✅' : '❌';
            const text = allowed ? 'ALLOWED' : 'REJECTED';
            
            entry.innerHTML = `
                ${icon} Request #${num}: ${text} | 
                Bucket: ${status.water_level.toFixed(1)}/${status.capacity}
            `;
            
            log.insertBefore(entry, log.firstChild);
            
            // Keep only last 20 entries
            while (log.children.length > 20) {
                log.removeChild(log.lastChild);
            }
        }

        function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        // Auto-update bucket status every second (shows leaking)
        setInterval(async () => {
            const response = await fetch('/api/bucket-status');
            const status = await response.json();
            updateBucket(status);
        }, 1000);
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    print("\n💧 Leaky Bucket Visual Demo")
    print("📍 http://localhost:8003")
    print("\n👆 Click buttons to see bucket fill and leak in real-time!\n")
    uvicorn.run(app, host="0.0.0.0", port=8003)

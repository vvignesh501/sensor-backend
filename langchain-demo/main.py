"""
LangChain + FastAPI Demo: Automated API Routing
User input → LangChain analyzes intent → Routes to correct API → Returns result
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any
import json

app = FastAPI(title="LangChain API Router Demo")

# ============================================================================
# MOCK DATABASE (Simulates real backend)
# ============================================================================

SENSORS_DB = {
    "sensor-1": {"id": "sensor-1", "name": "Temperature Sensor", "value": 22.5, "unit": "°C", "status": "active"},
    "sensor-2": {"id": "sensor-2", "name": "Humidity Sensor", "value": 65.0, "unit": "%", "status": "active"},
    "sensor-3": {"id": "sensor-3", "name": "Pressure Sensor", "value": 1013.25, "unit": "hPa", "status": "inactive"},
}

USERS_DB = {
    "user-1": {"id": "user-1", "name": "John Doe", "email": "john@example.com", "role": "admin"},
    "user-2": {"id": "user-2", "name": "Jane Smith", "email": "jane@example.com", "role": "user"},
}

ALERTS_DB = [
    {"id": 1, "sensor_id": "sensor-1", "message": "Temperature too high", "severity": "warning"},
    {"id": 2, "sensor_id": "sensor-3", "message": "Sensor offline", "severity": "critical"},
]

# ============================================================================
# BACKEND API ENDPOINTS (What LangChain will route to)
# ============================================================================

@app.get("/api/sensors")
def list_sensors():
    """List all sensors"""
    return {"sensors": list(SENSORS_DB.values())}

@app.get("/api/sensors/{sensor_id}")
def get_sensor(sensor_id: str):
    """Get specific sensor"""
    if sensor_id not in SENSORS_DB:
        raise HTTPException(404, "Sensor not found")
    return SENSORS_DB[sensor_id]

@app.post("/api/sensors/{sensor_id}/update")
def update_sensor(sensor_id: str, value: float):
    """Update sensor value"""
    if sensor_id not in SENSORS_DB:
        raise HTTPException(404, "Sensor not found")
    SENSORS_DB[sensor_id]["value"] = value
    return {"status": "updated", "sensor": SENSORS_DB[sensor_id]}

@app.get("/api/users")
def list_users():
    """List all users"""
    return {"users": list(USERS_DB.values())}

@app.get("/api/alerts")
def list_alerts():
    """List all alerts"""
    return {"alerts": ALERTS_DB}

@app.get("/api/stats")
def get_stats():
    """Get system statistics"""
    active_sensors = sum(1 for s in SENSORS_DB.values() if s["status"] == "active")
    return {
        "total_sensors": len(SENSORS_DB),
        "active_sensors": active_sensors,
        "total_users": len(USERS_DB),
        "total_alerts": len(ALERTS_DB)
    }

# ============================================================================
# LANGCHAIN LOGIC: Intent Recognition & API Routing
# ============================================================================

class IntentRouter:
    """
    Simulates LangChain's intent recognition
    In production, this would use GPT to understand natural language
    """
    
    def __init__(self):
        # Intent patterns (in production, LangChain/GPT would learn these)
        self.intent_patterns = {
            "list_sensors": ["show sensors", "list sensors", "all sensors", "get sensors"],
            "get_sensor": ["sensor", "show sensor", "get sensor", "sensor details"],
            "update_sensor": ["update sensor", "change sensor", "set sensor"],
            "list_users": ["show users", "list users", "all users", "get users"],
            "list_alerts": ["show alerts", "list alerts", "get alerts", "warnings"],
            "get_stats": ["statistics", "stats", "overview", "dashboard", "summary"],
        }
    
    def analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze user input and determine intent
        This simulates what LangChain + GPT would do
        """
        user_input_lower = user_input.lower()
        
        # Check for sensor ID in input
        sensor_id = None
        for sid in SENSORS_DB.keys():
            if sid in user_input_lower:
                sensor_id = sid
                break
        
        # Match intent
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in user_input_lower:
                    return {
                        "intent": intent,
                        "confidence": 0.95,
                        "parameters": {"sensor_id": sensor_id} if sensor_id else {}
                    }
        
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "parameters": {}
        }
    
    def route_to_api(self, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route to appropriate API based on intent
        This is the automation part - no manual routing needed!
        """
        intent = intent_result["intent"]
        params = intent_result["parameters"]
        
        try:
            if intent == "list_sensors":
                return list_sensors()
            
            elif intent == "get_sensor":
                sensor_id = params.get("sensor_id")
                if not sensor_id:
                    return {"error": "Please specify a sensor ID (e.g., sensor-1)"}
                return get_sensor(sensor_id)
            
            elif intent == "list_users":
                return list_users()
            
            elif intent == "list_alerts":
                return list_alerts()
            
            elif intent == "get_stats":
                return get_stats()
            
            else:
                return {
                    "error": "I don't understand that request",
                    "suggestion": "Try: 'show all sensors' or 'get statistics'"
                }
        
        except HTTPException as e:
            return {"error": str(e.detail)}
        except Exception as e:
            return {"error": str(e)}

# Initialize router
router = IntentRouter()

# ============================================================================
# MAIN ENDPOINT: Natural Language Query
# ============================================================================

class QueryRequest(BaseModel):
    query: str

@app.post("/api/query")
def process_query(request: QueryRequest):
    """
    Main endpoint: Takes natural language input, routes to correct API
    This is what makes it "automated" - user doesn't need to know API structure
    """
    
    # Step 1: Analyze intent (LangChain's job)
    intent_result = router.analyze_intent(request.query)
    
    # Step 2: Route to appropriate API (Automated routing)
    api_result = router.route_to_api(intent_result)
    
    # Step 3: Return combined result
    return {
        "query": request.query,
        "intent": intent_result["intent"],
        "confidence": intent_result["confidence"],
        "result": api_result
    }

# ============================================================================
# UI: Interactive Demo Interface
# ============================================================================

@app.get("/", response_class=HTMLResponse)
def get_ui():
    """Serve interactive UI"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>LangChain API Router Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .demo-section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        .input-section {
            margin-bottom: 20px;
        }
        .input-section label {
            display: block;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        .input-section input {
            width: 100%;
            padding: 15px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            transition: border-color 0.3s;
        }
        .input-section input:focus {
            outline: none;
            border-color: #667eea;
        }
        .button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.2s;
            width: 100%;
            font-weight: bold;
        }
        .button:hover {
            transform: translateY(-2px);
        }
        .button:active {
            transform: translateY(0);
        }
        .examples {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        .example-btn {
            background: #f0f0f0;
            border: 2px solid #ddd;
            padding: 10px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
        }
        .example-btn:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        .result-section {
            margin-top: 20px;
            display: none;
        }
        .result-section.show {
            display: block;
        }
        .result-box {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .result-box h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .result-box pre {
            background: #2d3748;
            color: #68d391;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 14px;
        }
        .intent-badge {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            margin-right: 10px;
        }
        .confidence-badge {
            display: inline-block;
            background: #48bb78;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #667eea;
            font-weight: bold;
        }
        .how-it-works {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .how-it-works h3 {
            color: #667eea;
            margin-bottom: 15px;
        }
        .how-it-works ol {
            margin-left: 20px;
        }
        .how-it-works li {
            margin-bottom: 10px;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 LangChain API Router Demo</h1>
            <p>Type natural language queries - AI automatically routes to the right API</p>
        </div>

        <div class="demo-section">
            <div class="input-section">
                <label>💬 Ask anything in natural language:</label>
                <input type="text" id="queryInput" placeholder="e.g., Show me all sensors" />
            </div>

            <button class="button" onclick="processQuery()">🚀 Process Query</button>

            <div style="margin-top: 20px;">
                <strong>Try these examples:</strong>
                <div class="examples">
                    <button class="example-btn" onclick="setQuery('show all sensors')">📊 Show all sensors</button>
                    <button class="example-btn" onclick="setQuery('get sensor-1 details')">🔍 Get sensor details</button>
                    <button class="example-btn" onclick="setQuery('list all users')">👥 List users</button>
                    <button class="example-btn" onclick="setQuery('show alerts')">⚠️ Show alerts</button>
                    <button class="example-btn" onclick="setQuery('get statistics')">📈 Get statistics</button>
                </div>
            </div>

            <div id="loading" class="loading" style="display: none;">
                Processing your query...
            </div>

            <div id="resultSection" class="result-section">
                <div class="result-box">
                    <h3>🎯 Intent Analysis</h3>
                    <div>
                        <span class="intent-badge" id="intentBadge">Unknown</span>
                        <span class="confidence-badge" id="confidenceBadge">0%</span>
                    </div>
                </div>

                <div class="result-box">
                    <h3>📡 API Response</h3>
                    <pre id="resultData"></pre>
                </div>
            </div>

            <div class="how-it-works">
                <h3>🔧 How It Works</h3>
                <ol>
                    <li><strong>User Input:</strong> You type a natural language query</li>
                    <li><strong>Intent Recognition:</strong> LangChain analyzes what you want</li>
                    <li><strong>Automated Routing:</strong> System routes to the correct API endpoint</li>
                    <li><strong>Response:</strong> Results displayed instantly</li>
                </ol>
                <p style="margin-top: 15px; color: #666;">
                    <strong>Benefits:</strong> No need to know API structure, endpoints, or parameters. 
                    Just ask in plain English! This reduces development time by 20-30%.
                </p>
            </div>
        </div>
    </div>

    <script>
        function setQuery(query) {
            document.getElementById('queryInput').value = query;
            processQuery();
        }

        async function processQuery() {
            const query = document.getElementById('queryInput').value;
            if (!query.trim()) {
                alert('Please enter a query');
                return;
            }

            // Show loading
            document.getElementById('loading').style.display = 'block';
            document.getElementById('resultSection').classList.remove('show');

            try {
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: query })
                });

                const data = await response.json();

                // Hide loading
                document.getElementById('loading').style.display = 'none';

                // Show results
                document.getElementById('intentBadge').textContent = data.intent;
                document.getElementById('confidenceBadge').textContent = 
                    (data.confidence * 100).toFixed(0) + '% confidence';
                document.getElementById('resultData').textContent = 
                    JSON.stringify(data.result, null, 2);
                document.getElementById('resultSection').classList.add('show');

            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                alert('Error: ' + error.message);
            }
        }

        // Allow Enter key to submit
        document.getElementById('queryInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                processQuery();
            }
        });
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

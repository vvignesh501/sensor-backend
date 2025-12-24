# -*- coding: utf-8 -*-
"""
LangChain LLM Demo - Visual Workflow UI
Shows step-by-step how LLMs process natural language and route to APIs
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, List
import time
import json

app = FastAPI(title="LangChain LLM Workflow Demo")

# Mock data
SENSORS = [
    {"id": "sensor-1", "name": "Temperature", "value": 22.5, "unit": "°C"},
    {"id": "sensor-2", "name": "Humidity", "value": 65.0, "unit": "%"},
    {"id": "sensor-3", "name": "Pressure", "value": 1013, "unit": "hPa"},
]

USERS = [
    {"id": 1, "name": "John Doe", "role": "Admin"},
    {"id": 2, "name": "Jane Smith", "role": "User"},
]

# ============================================================================
# LLM WORKFLOW SIMULATION
# ============================================================================

class LLMWorkflow:
    """Simulates how an LLM processes requests"""
    
    def process_step_by_step(self, query):
        """
        Returns step-by-step processing to show in UI
        This demonstrates what happens inside an LLM
        """
        steps = []
        
        # Step 1: Tokenization
        steps.append({
            "step": 1,
            "name": "Tokenization",
            "description": "Breaking input into tokens (words/subwords)",
            "input": query,
            "output": query.lower().split(),
            "time_ms": 10
        })
        
        # Step 2: Intent Recognition
        intent = self._recognize_intent(query)
        steps.append({
            "step": 2,
            "name": "Intent Recognition",
            "description": "Understanding what the user wants",
            "input": query.lower().split(),
            "output": {
                "intent": intent["intent"],
                "confidence": intent["confidence"],
                "reasoning": intent["reasoning"]
            },
            "time_ms": 50
        })
        
        # Step 3: Entity Extraction
        entities = self._extract_entities(query)
        steps.append({
            "step": 3,
            "name": "Entity Extraction",
            "description": "Identifying specific items (IDs, names, etc.)",
            "input": query,
            "output": entities,
            "time_ms": 30
        })
        
        # Step 4: API Mapping
        api_call = self._map_to_api(intent, entities)
        steps.append({
            "step": 4,
            "name": "API Mapping",
            "description": "Determining which API endpoint to call",
            "input": {"intent": intent["intent"], "entities": entities},
            "output": api_call,
            "time_ms": 20
        })
        
        # Step 5: Execute API
        result = self._execute_api(api_call)
        steps.append({
            "step": 5,
            "name": "API Execution",
            "description": "Calling the backend API",
            "input": api_call,
            "output": result,
            "time_ms": 100
        })
        
        # Step 6: Format Response
        formatted = self._format_response(result)
        steps.append({
            "step": 6,
            "name": "Response Formatting",
            "description": "Preparing user-friendly output",
            "input": result,
            "output": formatted,
            "time_ms": 15
        })
        
        return steps
    
    def _recognize_intent(self, query):
        """Recognize user intent"""
        q = query.lower()
        
        if "sensor" in q and ("all" in q or "list" in q or "show" in q):
            return {
                "intent": "list_sensors",
                "confidence": 0.95,
                "reasoning": "Keywords: 'sensor', 'list/show' → User wants to see all sensors"
            }
        elif "sensor" in q and any(f"sensor-{i}" in q for i in range(1, 10)):
            return {
                "intent": "get_sensor_details",
                "confidence": 0.92,
                "reasoning": "Keywords: 'sensor', specific ID → User wants details of one sensor"
            }
        elif "user" in q:
            return {
                "intent": "list_users",
                "confidence": 0.90,
                "reasoning": "Keyword: 'user' → User wants to see users"
            }
        elif "stat" in q or "overview" in q or "dashboard" in q:
            return {
                "intent": "get_statistics",
                "confidence": 0.88,
                "reasoning": "Keywords: 'statistics/overview' → User wants system stats"
            }
        else:
            return {
                "intent": "unknown",
                "confidence": 0.30,
                "reasoning": "No clear keywords matched"
            }
    
    def _extract_entities(self, query):
        """Extract entities from query"""
        entities = {}
        
        # Extract sensor IDs
        for i in range(1, 10):
            if f"sensor-{i}" in query.lower():
                entities["sensor_id"] = f"sensor-{i}"
                break
        
        # Extract numbers
        words = query.split()
        for word in words:
            if word.isdigit():
                entities["number"] = int(word)
        
        return entities if entities else {"none": "No entities found"}
    
    def _map_to_api(self, intent, entities):
        """Map intent to API call"""
        intent_name = intent["intent"]
        
        if intent_name == "list_sensors":
            return {
                "method": "GET",
                "endpoint": "/api/sensors",
                "params": {}
            }
        elif intent_name == "get_sensor_details":
            sensor_id = entities.get("sensor_id", "sensor-1")
            return {
                "method": "GET",
                "endpoint": f"/api/sensors/{sensor_id}",
                "params": {"sensor_id": sensor_id}
            }
        elif intent_name == "list_users":
            return {
                "method": "GET",
                "endpoint": "/api/users",
                "params": {}
            }
        elif intent_name == "get_statistics":
            return {
                "method": "GET",
                "endpoint": "/api/stats",
                "params": {}
            }
        else:
            return {
                "method": "ERROR",
                "endpoint": "unknown",
                "params": {}
            }
    
    def _execute_api(self, api_call):
        """Execute the API call"""
        endpoint = api_call["endpoint"]
        
        if endpoint == "/api/sensors":
            return {"sensors": SENSORS}
        elif "/api/sensors/" in endpoint:
            sensor_id = api_call["params"].get("sensor_id")
            sensor = next((s for s in SENSORS if s["id"] == sensor_id), None)
            return sensor if sensor else {"error": "Sensor not found"}
        elif endpoint == "/api/users":
            return {"users": USERS}
        elif endpoint == "/api/stats":
            return {
                "total_sensors": len(SENSORS),
                "total_users": len(USERS),
                "avg_temperature": 22.5
            }
        else:
            return {"error": "Unknown endpoint"}
    
    def _format_response(self, result):
        """Format response for user"""
        if isinstance(result, dict):
            if "sensors" in result:
                return f"Found {len(result['sensors'])} sensors"
            elif "users" in result:
                return f"Found {len(result['users'])} users"
            elif "total_sensors" in result:
                return f"System has {result['total_sensors']} sensors and {result['total_users']} users"
            elif "id" in result:
                return f"Sensor: {result['name']} = {result['value']}{result['unit']}"
        return str(result)

workflow = LLMWorkflow()

# ============================================================================
# API ENDPOINTS
# ============================================================================

class QueryRequest(BaseModel):
    query: str

@app.post("/api/process")
def process_query(request: QueryRequest):
    """Process query and return step-by-step workflow"""
    steps = workflow.process_step_by_step(request.query)
    return {"steps": steps}

# ============================================================================
# INTERACTIVE UI
# ============================================================================

@app.get("/", response_class=HTMLResponse)
def get_demo_ui():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>LangChain LLM Workflow Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .demo-grid {
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 20px;
        }
        .sidebar {
            background: #1e293b;
            border-radius: 15px;
            padding: 20px;
        }
        .sidebar h2 {
            color: #667eea;
            margin-bottom: 15px;
        }
        .query-btn {
            width: 100%;
            padding: 15px;
            margin-bottom: 10px;
            background: #334155;
            border: 2px solid #475569;
            border-radius: 8px;
            color: white;
            cursor: pointer;
            transition: all 0.3s;
            text-align: left;
            font-size: 14px;
        }
        .query-btn:hover {
            background: #667eea;
            border-color: #667eea;
            transform: translateX(5px);
        }
        .query-btn.active {
            background: #667eea;
            border-color: #667eea;
        }
        .workflow-area {
            background: #1e293b;
            border-radius: 15px;
            padding: 30px;
            min-height: 600px;
        }
        .workflow-step {
            background: #334155;
            border-left: 4px solid #667eea;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            opacity: 0;
            transform: translateY(20px);
            animation: slideIn 0.5s forwards;
        }
        @keyframes slideIn {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .step-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .step-number {
            background: #667eea;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 15px;
            font-size: 18px;
        }
        .step-title {
            flex: 1;
        }
        .step-title h3 {
            color: #667eea;
            margin-bottom: 5px;
        }
        .step-title p {
            color: #94a3b8;
            font-size: 14px;
        }
        .step-time {
            background: #48bb78;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
        }
        .step-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .step-box {
            background: #1e293b;
            padding: 15px;
            border-radius: 8px;
        }
        .step-box h4 {
            color: #94a3b8;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .step-box pre {
            background: #0f172a;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 13px;
            color: #68d391;
        }
        .loading {
            text-align: center;
            padding: 50px;
        }
        .loading-spinner {
            border: 4px solid #334155;
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
        .empty-state {
            text-align: center;
            padding: 100px 20px;
            color: #64748b;
        }
        .empty-state h2 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .summary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            text-align: center;
        }
        .summary h3 {
            margin-bottom: 10px;
        }
        .summary .total-time {
            font-size: 2em;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 LangChain LLM Workflow Demo</h1>
            <p>Click any query to see step-by-step how LLMs process natural language</p>
        </div>

        <div class="demo-grid">
            <div class="sidebar">
                <h2>📝 Sample Queries</h2>
                <button class="query-btn" onclick="processQuery('Show me all sensors')">
                    📊 Show me all sensors
                </button>
                <button class="query-btn" onclick="processQuery('Get sensor-1 details')">
                    🔍 Get sensor-1 details
                </button>
                <button class="query-btn" onclick="processQuery('List all users')">
                    👥 List all users
                </button>
                <button class="query-btn" onclick="processQuery('Show system statistics')">
                    📈 Show system statistics
                </button>
                <button class="query-btn" onclick="processQuery('What is sensor-2 reading?')">
                    🌡️ What is sensor-2 reading?
                </button>

                <div style="margin-top: 30px; padding: 15px; background: #334155; border-radius: 8px;">
                    <h3 style="color: #667eea; margin-bottom: 10px;">💡 What You'll See</h3>
                    <ul style="font-size: 14px; line-height: 1.8; color: #94a3b8;">
                        <li>Tokenization</li>
                        <li>Intent Recognition</li>
                        <li>Entity Extraction</li>
                        <li>API Mapping</li>
                        <li>Execution</li>
                        <li>Response Formatting</li>
                    </ul>
                </div>
            </div>

            <div class="workflow-area">
                <div id="emptyState" class="empty-state">
                    <h2>👈 Click a query to start</h2>
                    <p>Watch how LLMs process natural language step-by-step</p>
                </div>

                <div id="loading" class="loading" style="display: none;">
                    <div class="loading-spinner"></div>
                    <p>Processing query...</p>
                </div>

                <div id="workflowSteps"></div>
            </div>
        </div>
    </div>

    <script>
        let currentQuery = null;

        async function processQuery(query) {
            currentQuery = query;

            // Update button states
            document.querySelectorAll('.query-btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.textContent.includes(query.substring(0, 15))) {
                    btn.classList.add('active');
                }
            });

            // Show loading
            document.getElementById('emptyState').style.display = 'none';
            document.getElementById('loading').style.display = 'block';
            document.getElementById('workflowSteps').innerHTML = '';

            try {
                const response = await fetch('/api/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });

                const data = await response.json();

                // Hide loading
                document.getElementById('loading').style.display = 'none';

                // Display steps one by one
                displaySteps(data.steps);

            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                alert('Error: ' + error.message);
            }
        }

        function displaySteps(steps) {
            const container = document.getElementById('workflowSteps');
            let totalTime = 0;

            steps.forEach((step, index) => {
                setTimeout(() => {
                    totalTime += step.time_ms;

                    const stepDiv = document.createElement('div');
                    stepDiv.className = 'workflow-step';
                    stepDiv.style.animationDelay = '0s';

                    stepDiv.innerHTML = `
                        <div class="step-header">
                            <div class="step-number">${step.step}</div>
                            <div class="step-title">
                                <h3>${step.name}</h3>
                                <p>${step.description}</p>
                            </div>
                            <div class="step-time">${step.time_ms}ms</div>
                        </div>
                        <div class="step-content">
                            <div class="step-box">
                                <h4>Input</h4>
                                <pre>${JSON.stringify(step.input, null, 2)}</pre>
                            </div>
                            <div class="step-box">
                                <h4>Output</h4>
                                <pre>${JSON.stringify(step.output, null, 2)}</pre>
                            </div>
                        </div>
                    `;

                    container.appendChild(stepDiv);

                    // Add summary after last step
                    if (index === steps.length - 1) {
                        setTimeout(() => {
                            const summary = document.createElement('div');
                            summary.className = 'summary';
                            summary.innerHTML = `
                                <h3>✅ Processing Complete</h3>
                                <div class="total-time">${totalTime}ms</div>
                                <p>Total processing time</p>
                            `;
                            container.appendChild(summary);
                        }, 300);
                    }
                }, index * 400);
            });
        }
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting LangChain LLM Workflow Demo...")
    print("📱 Open: http://localhost:8001")
    print("👆 Click any query to see how LLMs work!\n")
    uvicorn.run(app, host="0.0.0.0", port=8001)

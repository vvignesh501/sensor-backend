# -*- coding: utf-8 -*-
"""
Simple API for tracing demo (without OpenTelemetry dependencies)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import time
import random

app = FastAPI(title="Sensor API", version="1.0.0")

# Add CORS middleware to allow requests from the demo UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock database
SENSORS_DB = [
    {"id": "sensor-1", "name": "Temperature Sensor", "type": "temperature", "value": 22.5, "unit": "°C"},
    {"id": "sensor-2", "name": "Humidity Sensor", "type": "humidity", "value": 65.0, "unit": "%"},
    {"id": "sensor-3", "name": "Pressure Sensor", "type": "pressure", "value": 1013, "unit": "hPa"},
]

class SensorCreate(BaseModel):
    name: str
    type: str
    value: float
    unit: str

@app.get("/")
def root():
    return {
        "service": "Sensor API",
        "version": "1.0.0",
        "endpoints": [
            "/api/sensors",
            "/api/sensors/{id}",
            "/api/sensors/{id}/aggregate",
            "/api/slow-endpoint",
            "/api/error-endpoint"
        ]
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/sensors")
def get_sensors():
    """Get all sensors"""
    time.sleep(random.uniform(0.05, 0.15))  # Simulate processing
    return SENSORS_DB

@app.get("/api/sensors/{sensor_id}")
def get_sensor(sensor_id: str):
    """Get sensor by ID"""
    time.sleep(random.uniform(0.03, 0.10))  # Simulate processing
    sensor = next((s for s in SENSORS_DB if s["id"] == sensor_id), None)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor

@app.get("/api/sensors/{sensor_id}/aggregate")
def aggregate_sensor_data(sensor_id: str):
    """Aggregate sensor data from multiple services"""
    time.sleep(random.uniform(0.2, 0.4))  # Simulate multiple service calls
    sensor = next((s for s in SENSORS_DB if s["id"] == sensor_id), None)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    return {
        "sensor": sensor,
        "analytics": {"avg": 25.5, "min": 20.0, "max": 30.0},
        "report": {"status": "normal", "alerts": []}
    }

@app.post("/api/sensors")
def create_sensor(sensor: SensorCreate):
    """Create new sensor"""
    time.sleep(random.uniform(0.1, 0.2))  # Simulate processing
    sensor_id = f"sensor-{len(SENSORS_DB) + 1}"
    new_sensor = {
        "id": sensor_id,
        **sensor.dict()
    }
    SENSORS_DB.append(new_sensor)
    return new_sensor

@app.get("/api/slow-endpoint")
def slow_endpoint():
    """Intentionally slow endpoint"""
    time.sleep(1.2)  # Simulate slow operation
    return {"message": "This endpoint is intentionally slow"}

@app.get("/api/error-endpoint")
def error_endpoint():
    """Endpoint that throws errors"""
    raise HTTPException(status_code=500, detail="Intentional error for demo")

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting Simple Sensor API...")
    print("📊 API: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)

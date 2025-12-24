# -*- coding: utf-8 -*-
"""
Example FastAPI application with OpenTelemetry tracing
Demonstrates distributed tracing across multiple services
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import httpx
import time
import random
from opentelemetry import trace
from tracing_config import (
    setup_tracing, 
    instrument_fastapi, 
    instrument_requests,
    add_span_attributes,
    add_span_event,
    record_exception
)

# Initialize tracing
tracer = setup_tracing(service_name="sensor-api")

# Create FastAPI app
app = FastAPI(title="Sensor API with Tracing", version="1.0.0")

# Instrument FastAPI
instrument_fastapi(app)
instrument_requests()

# Get tracer
tracer = trace.get_tracer(__name__)


# ============================================================================
# MODELS
# ============================================================================

class Sensor(BaseModel):
    id: str
    name: str
    type: str
    value: float
    unit: str


class SensorCreate(BaseModel):
    name: str
    type: str
    value: float
    unit: str


# Mock database
SENSORS_DB = [
    {"id": "sensor-1", "name": "Temperature Sensor", "type": "temperature", "value": 22.5, "unit": "°C"},
    {"id": "sensor-2", "name": "Humidity Sensor", "type": "humidity", "value": 65.0, "unit": "%"},
    {"id": "sensor-3", "name": "Pressure Sensor", "type": "pressure", "value": 1013, "unit": "hPa"},
]


# ============================================================================
# HELPER FUNCTIONS WITH MANUAL TRACING
# ============================================================================

def simulate_database_query(query: str, duration: float = 0.05):
    """Simulate database query with tracing"""
    with tracer.start_as_current_span("database.query") as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.statement", query)
        span.set_attribute("db.name", "sensordb")
        
        # Simulate query execution
        time.sleep(duration)
        
        add_span_event("query_executed", {"rows_affected": len(SENSORS_DB)})
        
        return SENSORS_DB


def simulate_cache_lookup(key: str):
    """Simulate cache lookup with tracing"""
    with tracer.start_as_current_span("cache.lookup") as span:
        span.set_attribute("cache.system", "redis")
        span.set_attribute("cache.key", key)
        
        # Simulate cache miss (80% of the time)
        cache_hit = random.random() > 0.8
        
        if cache_hit:
            span.set_attribute("cache.hit", True)
            add_span_event("cache_hit")
            time.sleep(0.001)  # Fast cache lookup
            return SENSORS_DB[0]
        else:
            span.set_attribute("cache.hit", False)
            add_span_event("cache_miss")
            time.sleep(0.002)
            return None


def simulate_external_api_call(service: str):
    """Simulate external API call with tracing"""
    with tracer.start_as_current_span(f"http.call.{service}") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.url", f"http://{service}:8000/api/data")
        span.set_attribute("peer.service", service)
        
        # Simulate API call
        duration = random.uniform(0.05, 0.2)
        time.sleep(duration)
        
        span.set_attribute("http.status_code", 200)
        span.set_attribute("http.response_time_ms", duration * 1000)
        
        return {"status": "success", "data": "mock_data"}


def process_sensor_data(sensor_data: dict):
    """Process sensor data with tracing"""
    with tracer.start_as_current_span("business_logic.process_sensor") as span:
        span.set_attribute("sensor.id", sensor_data.get("id"))
        span.set_attribute("sensor.type", sensor_data.get("type"))
        
        # Simulate validation
        with tracer.start_as_current_span("validation.check"):
            time.sleep(0.01)
            add_span_event("validation_passed")
        
        # Simulate transformation
        with tracer.start_as_current_span("transformation.apply"):
            time.sleep(0.02)
            add_span_event("data_transformed")
        
        # Simulate business rules
        with tracer.start_as_current_span("business_rules.apply"):
            time.sleep(0.015)
            add_span_event("rules_applied")
        
        return sensor_data


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Sensor API with OpenTelemetry",
        "version": "1.0.0",
        "tracing": "enabled",
        "jaeger_ui": "http://localhost:16686"
    }


@app.get("/api/sensors", response_model=List[Sensor])
def get_sensors():
    """
    Get all sensors - demonstrates database query tracing
    """
    with tracer.start_as_current_span("get_sensors") as span:
        span.set_attribute("endpoint", "/api/sensors")
        span.set_attribute("method", "GET")
        
        # Check cache first
        cached = simulate_cache_lookup("sensors:all")
        if cached:
            add_span_event("returning_cached_data")
            return [cached]
        
        # Query database
        sensors = simulate_database_query("SELECT * FROM sensors")
        
        add_span_attributes(
            sensor_count=len(sensors),
            cache_hit=False
        )
        
        return sensors


@app.get("/api/sensors/{sensor_id}", response_model=Sensor)
def get_sensor(sensor_id: str):
    """
    Get sensor by ID - demonstrates cache and database tracing
    """
    with tracer.start_as_current_span("get_sensor_by_id") as span:
        span.set_attribute("sensor.id", sensor_id)
        
        # Check cache
        cached = simulate_cache_lookup(f"sensor:{sensor_id}")
        if cached:
            return cached
        
        # Query database
        sensors = simulate_database_query(f"SELECT * FROM sensors WHERE id = '{sensor_id}'", 0.03)
        
        sensor = next((s for s in sensors if s["id"] == sensor_id), None)
        
        if not sensor:
            span.set_attribute("error", True)
            add_span_event("sensor_not_found")
            raise HTTPException(status_code=404, detail="Sensor not found")
        
        return sensor


@app.post("/api/sensors", response_model=Sensor)
def create_sensor(sensor: SensorCreate):
    """
    Create new sensor - demonstrates complex operation tracing
    """
    with tracer.start_as_current_span("create_sensor") as span:
        span.set_attribute("sensor.name", sensor.name)
        span.set_attribute("sensor.type", sensor.type)
        
        try:
            # Generate ID
            sensor_id = f"sensor-{len(SENSORS_DB) + 1}"
            
            # Process sensor data
            sensor_dict = sensor.dict()
            sensor_dict["id"] = sensor_id
            
            processed = process_sensor_data(sensor_dict)
            
            # Save to database
            with tracer.start_as_current_span("database.insert"):
                time.sleep(0.05)
                SENSORS_DB.append(processed)
                add_span_event("sensor_created", {"sensor_id": sensor_id})
            
            # Invalidate cache
            with tracer.start_as_current_span("cache.invalidate"):
                time.sleep(0.01)
                add_span_event("cache_invalidated")
            
            # Publish event (simulate)
            with tracer.start_as_current_span("event.publish"):
                span.set_attribute("event.type", "sensor.created")
                time.sleep(0.02)
                add_span_event("event_published")
            
            return processed
            
        except Exception as e:
            record_exception(e)
            raise


@app.get("/api/sensors/{sensor_id}/aggregate")
def aggregate_sensor_data(sensor_id: str):
    """
    Aggregate sensor data - demonstrates multiple service calls
    """
    with tracer.start_as_current_span("aggregate_sensor_data") as span:
        span.set_attribute("sensor.id", sensor_id)
        
        # Get sensor details
        sensor = get_sensor(sensor_id)
        
        # Call analytics service
        analytics = simulate_external_api_call("analytics-service")
        
        # Call reporting service
        report = simulate_external_api_call("reporting-service")
        
        # Aggregate results
        with tracer.start_as_current_span("aggregation.combine"):
            time.sleep(0.03)
            result = {
                "sensor": sensor,
                "analytics": analytics,
                "report": report
            }
            add_span_event("aggregation_complete")
        
        return result


@app.get("/api/slow-endpoint")
def slow_endpoint():
    """
    Intentionally slow endpoint to demonstrate performance profiling
    """
    with tracer.start_as_current_span("slow_endpoint") as span:
        span.set_attribute("endpoint.type", "slow")
        
        # Slow database query
        with tracer.start_as_current_span("slow_query"):
            span.set_attribute("query.type", "complex_join")
            time.sleep(0.5)  # Simulate slow query
            add_span_event("slow_query_completed")
        
        # Multiple external calls
        for i in range(3):
            with tracer.start_as_current_span(f"external_call_{i}"):
                time.sleep(0.2)
        
        # Heavy computation
        with tracer.start_as_current_span("heavy_computation"):
            time.sleep(0.3)
            add_span_event("computation_done")
        
        return {"message": "This endpoint is intentionally slow for profiling"}


@app.get("/api/error-endpoint")
def error_endpoint():
    """
    Endpoint that throws errors - demonstrates error tracing
    """
    with tracer.start_as_current_span("error_endpoint") as span:
        try:
            # Simulate some work
            time.sleep(0.05)
            
            # Throw error
            raise ValueError("Intentional error for tracing demonstration")
            
        except Exception as e:
            record_exception(e)
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    """Health check endpoint (not traced heavily)"""
    return {"status": "healthy", "tracing": "enabled"}


if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting Sensor API with OpenTelemetry Tracing...")
    print("📊 API: http://localhost:8000")
    print("🔍 Jaeger UI: http://localhost:16686")
    print("📖 API Docs: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)

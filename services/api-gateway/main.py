"""
API Gateway - Routes requests to microservices
Runs on port 8000 (main entry point)
"""
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from datetime import datetime
from contextlib import asynccontextmanager
import os

# Service URLs
AUTH_SERVICE = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
SENSOR_SERVICE = os.getenv("SENSOR_SERVICE_URL", "http://localhost:8002")
KAFKA_SERVICE = os.getenv("KAFKA_SERVICE_URL", "http://localhost:8003")

# Circuit breaker state
circuit_breakers = {
    "auth": {"open": False, "failures": 0, "max_failures": 5},
    "sensor": {"open": False, "failures": 0, "max_failures": 5},
    "kafka": {"open": False, "failures": 0, "max_failures": 5}
}

class ResilientHTTPClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def forward_request(self, service_name: str, url: str, method: str, **kwargs):
        """Forward request with circuit breaker pattern"""
        breaker = circuit_breakers[service_name]
        
        # Check if circuit is open
        if breaker["open"]:
            return JSONResponse(
                status_code=503,
                content={
                    "error": f"{service_name} service unavailable",
                    "circuit_breaker": "open",
                    "message": "Service is temporarily unavailable. Please try again later."
                }
            )
        
        try:
            # Forward request
            if method == "GET":
                response = await self.client.get(url, **kwargs)
            elif method == "POST":
                response = await self.client.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Reset failures on success
            breaker["failures"] = 0
            
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
            
        except Exception as e:
            # Increment failure count
            breaker["failures"] += 1
            
            # Open circuit breaker if threshold reached
            if breaker["failures"] >= breaker["max_failures"]:
                breaker["open"] = True
                print(f"⚠️ Circuit breaker OPENED for {service_name} service")
            
            return JSONResponse(
                status_code=503,
                content={
                    "error": f"{service_name} service error",
                    "message": str(e),
                    "failures": breaker["failures"]
                }
            )

http_client = ResilientHTTPClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 API Gateway started")
    yield
    await http_client.client.aclose()
    print("🛑 API Gateway stopped")

app = FastAPI(
    title="Sensor Backend API Gateway",
    version="1.0.0",
    description="Resilient API Gateway with circuit breaker pattern",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check aggregator
@app.get("/health")
async def health_check():
    """Aggregate health status from all services"""
    services_health = {}
    
    for service_name, service_url in [
        ("auth", AUTH_SERVICE),
        ("sensor", SENSOR_SERVICE),
        ("kafka", KAFKA_SERVICE)
    ]:
        try:
            response = await http_client.client.get(f"{service_url}/health", timeout=2.0)
            services_health[service_name] = response.json()
        except:
            services_health[service_name] = {
                "status": "unavailable",
                "circuit_breaker": "open" if circuit_breakers[service_name]["open"] else "closed"
            }
    
    # Gateway is healthy if at least one service is up
    overall_status = "healthy" if any(
        s.get("status") == "healthy" for s in services_health.values()
    ) else "degraded"
    
    return {
        "gateway": "healthy",
        "overall_status": overall_status,
        "services": services_health,
        "circuit_breakers": circuit_breakers,
        "timestamp": datetime.utcnow().isoformat()
    }

# Auth routes
@app.post("/auth/register")
async def register(request: Request):
    body = await request.json()
    return await http_client.forward_request(
        "auth",
        f"{AUTH_SERVICE}/register",
        "POST",
        json=body
    )

@app.post("/auth/token")
async def login(request: Request):
    form_data = await request.form()
    return await http_client.forward_request(
        "auth",
        f"{AUTH_SERVICE}/token",
        "POST",
        data=form_data
    )

# Sensor routes
@app.post("/test/sensor/{sensor_type}")
async def test_sensor(sensor_type: str, request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    return await http_client.forward_request(
        "sensor",
        f"{SENSOR_SERVICE}/test/{sensor_type}",
        "POST",
        headers=headers
    )

@app.get("/test/{test_id}")
async def get_test_result(test_id: str, request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    return await http_client.forward_request(
        "sensor",
        f"{SENSOR_SERVICE}/test/{test_id}",
        "GET",
        headers=headers
    )

# Kafka routes
@app.get("/kafka/stats")
async def kafka_stats(request: Request):
    return await http_client.forward_request(
        "kafka",
        f"{KAFKA_SERVICE}/stats",
        "GET"
    )

@app.get("/kafka/logs")
async def kafka_logs(request: Request, limit: int = 100):
    return await http_client.forward_request(
        "kafka",
        f"{KAFKA_SERVICE}/logs?limit={limit}",
        "GET"
    )

# Circuit breaker management
@app.post("/circuit-breaker/reset/{service_name}")
async def reset_circuit_breaker(service_name: str):
    """Manually reset circuit breaker for a service"""
    if service_name not in circuit_breakers:
        raise HTTPException(status_code=404, detail="Service not found")
    
    circuit_breakers[service_name]["open"] = False
    circuit_breakers[service_name]["failures"] = 0
    
    return {
        "message": f"Circuit breaker reset for {service_name}",
        "status": circuit_breakers[service_name]
    }

@app.get("/")
async def root():
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "services": {
            "auth": AUTH_SERVICE,
            "sensor": SENSOR_SERVICE,
            "kafka": KAFKA_SERVICE
        },
        "endpoints": {
            "health": "/health",
            "auth": "/auth/*",
            "sensor": "/test/*",
            "kafka": "/kafka/*"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
Sensor Service - Handles sensor testing and data processing
Runs independently on port 8002
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import asyncpg
import uuid
import numpy as np
import json
from datetime import datetime
from contextlib import asynccontextmanager
import os
from typing import Optional

# Configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
KAFKA_SERVICE_URL = os.getenv("KAFKA_SERVICE_URL", "http://localhost:8003")
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgresql%409891@localhost:5434/sensordb")

# Resilient HTTP client with timeout and retries
class ResilientHTTPClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=5.0)
        self.circuit_breaker = {}
    
    async def get(self, url: str, **kwargs):
        service = url.split('/')[2]  # Extract service name
        
        # Check circuit breaker
        if self.circuit_breaker.get(service, {}).get('open', False):
            raise HTTPException(status_code=503, detail=f"{service} unavailable")
        
        try:
            response = await self.client.get(url, **kwargs)
            # Reset circuit breaker on success
            self.circuit_breaker[service] = {'open': False, 'failures': 0}
            return response
        except Exception as e:
            # Increment failure count
            if service not in self.circuit_breaker:
                self.circuit_breaker[service] = {'open': False, 'failures': 0}
            
            self.circuit_breaker[service]['failures'] += 1
            
            # Open circuit after 3 failures
            if self.circuit_breaker[service]['failures'] >= 3:
                self.circuit_breaker[service]['open'] = True
                print(f"⚠️ Circuit breaker opened for {service}")
            
            raise HTTPException(status_code=503, detail=f"{service} unavailable: {str(e)}")
    
    async def post(self, url: str, **kwargs):
        service = url.split('/')[2]
        
        if self.circuit_breaker.get(service, {}).get('open', False):
            print(f"⚠️ Circuit breaker open for {service}, skipping request")
            return None  # Graceful degradation
        
        try:
            response = await self.client.post(url, **kwargs)
            self.circuit_breaker[service] = {'open': False, 'failures': 0}
            return response
        except Exception as e:
            if service not in self.circuit_breaker:
                self.circuit_breaker[service] = {'open': False, 'failures': 0}
            
            self.circuit_breaker[service]['failures'] += 1
            
            if self.circuit_breaker[service]['failures'] >= 3:
                self.circuit_breaker[service]['open'] = True
                print(f"⚠️ Circuit breaker opened for {service}")
            
            print(f"⚠️ Failed to call {service}: {str(e)}")
            return None  # Graceful degradation

http_client = ResilientHTTPClient()

# Database with fallback
class ResilientDatabase:
    def __init__(self):
        self.pool = None
        self.is_healthy = True
    
    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(DB_URL, min_size=2, max_size=10)
            self.is_healthy = True
            print("✅ Sensor Service DB connected")
        except Exception as e:
            self.is_healthy = False
            print(f"❌ Sensor Service DB connection failed: {e}")
    
    async def execute(self, query, *args):
        if not self.is_healthy:
            return False
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, *args)
            return True
        except Exception as e:
            print(f"⚠️ DB error: {e}")
            return False

db = ResilientDatabase()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    if db.pool:
        await db.pool.close()
    await http_client.client.aclose()

app = FastAPI(title="Sensor Service", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth dependency with fallback
async def get_current_user(authorization: Optional[str] = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Try to verify with auth service
        response = await http_client.get(
            f"{AUTH_SERVICE_URL}/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response and response.status_code == 200:
            return response.json()
    except:
        pass
    
    # Fallback: Basic JWT decode (degraded mode)
    try:
        import jwt
        payload = jwt.decode(token, options={"verify_signature": False})
        return {"username": payload.get("sub"), "email": "unknown"}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# Models
class TestResult(BaseModel):
    test_id: str
    sensor_type: str
    status: str
    timestamp: str

# Background task for async processing
async def process_sensor_data(test_id: str, sensor_type: str, user: dict):
    """Process sensor data asynchronously"""
    try:
        # Generate test data
        dynamic_data = np.random.normal(25.0, 2.5, (100, 16, 8)).astype(np.float32)
        
        test_metrics = {
            "temperature": "23.5°C",
            "humidity": "45%",
            "dynamic_range": "98.5%",
            "uniformity_score": "99.2%",
            "stability_drift": "0.02%/hr"
        }
        
        # Store in database (with fallback)
        db_success = await db.execute(
            "INSERT INTO sensor_tests (id, sensor_type, data_type, s3_status, s3_path, test_metrics) VALUES ($1, $2, $3, $4, $5, $6)",
            test_id, sensor_type, 'raw_data', 'success', f'local_storage/{test_id}', json.dumps(test_metrics)
        )
        
        if not db_success:
            print(f"⚠️ DB unavailable, test {test_id} not persisted")
        
        # Send to Kafka service (with fallback)
        kafka_event = {
            "test_id": test_id,
            "user_id": user.get('username', 'unknown'),
            "sensor_type": sensor_type,
            "test_metrics": test_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        kafka_response = await http_client.post(
            f"{KAFKA_SERVICE_URL}/send-event",
            json=kafka_event
        )
        
        if not kafka_response:
            print(f"⚠️ Kafka service unavailable, event {test_id} not sent")
        
        print(f"✅ Sensor test {test_id} processed successfully")
        
    except Exception as e:
        print(f"❌ Error processing sensor test {test_id}: {e}")

# Endpoints
@app.get("/health")
async def health():
    return {
        "service": "sensor-service",
        "status": "healthy",
        "database": "healthy" if db.is_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/test/{sensor_type}", response_model=TestResult)
async def test_sensor(
    sensor_type: str,
    background_tasks: BackgroundTasks,
    authorization: str = Depends(lambda r: r.headers.get("authorization"))
):
    # Verify user (with fallback)
    user = await get_current_user(authorization)
    
    test_id = str(uuid.uuid4())
    
    # Queue background processing
    background_tasks.add_task(process_sensor_data, test_id, sensor_type, user)
    
    # Return immediately
    return TestResult(
        test_id=test_id,
        sensor_type=sensor_type,
        status="processing",
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/test/{test_id}")
async def get_test_result(test_id: str):
    if not db.is_healthy:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    try:
        async with db.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM sensor_tests WHERE id = $1",
                test_id
            )
            if not result:
                raise HTTPException(status_code=404, detail="Test not found")
            return dict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

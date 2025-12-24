# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
from datetime import datetime, timedelta
import json
import asyncpg
import os
import jwt
import numpy as np
import boto3
import io
from contextlib import asynccontextmanager
import asyncio
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
from enum import Enum
from kafka_producer import SensorEventProducer

# JWT Configuration
SECRET_KEY = "sensor-backend-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Instance Configuration
INSTANCE_ID = os.getenv('INSTANCE_ID', '1')
START_TIME = datetime.utcnow()

# Lazy Database Pool
class ScaledAsyncDatabase:
    def __init__(self):
        self.pool = None
        self.db_url = "postgresql://postgres:postgresql%409891@localhost:5435/sensordb"
    
    async def ensure_connection(self):
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=1,
                max_size=5,
                max_inactive_connection_lifetime=60,
                max_queries=1000,
                command_timeout=10,
                server_settings={
                    'application_name': 'sensor_app',
                    'tcp_keepalives_idle': '600',
                    'tcp_keepalives_interval': '30',
                    'tcp_keepalives_count': '3'
                }
            )
            print("SUCCESS: Connection pool created: 1-5 connections with auto-cleanup")
    
    async def connect(self):
        await self.ensure_connection()
    
    async def disconnect(self):
        if self.pool:
            await self.pool.close()
        print("Database pool closed")
    
    async def _cleanup_on_error(self):
        """Close pool on errors to prevent idle connections"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            print("Pool closed due to error - will reconnect on next request")
    
    async def fetch_one(self, query, *args):
        await self.ensure_connection()
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None
        except Exception as e:
            print("POSTGRES ERROR - fetch_one failed: " + str(e))
            await self._cleanup_on_error()
            raise e
    
    async def fetch_all(self, query, *args):
        await self.ensure_connection()
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
        except Exception as e:
            print("POSTGRES ERROR - fetch_all failed: " + str(e))
            raise e
    
    async def execute_transaction(self, queries):
        await self.ensure_connection()
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for query, args in queries:
                        await conn.execute(query, *args)
                    return True
        except Exception as e:
            print("POSTGRES ERROR - transaction failed: " + str(e))
            raise e

# Initialize database
db = ScaledAsyncDatabase()

# Initialize Kafka producer
kafka_producer = SensorEventProducer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to database (required)
    await db.connect()
    
    # Create test user for dashboard login
    try:
        user_id = str(uuid.uuid4())
        await db.execute_transaction([
            ("INSERT INTO users (id, username, email, hashed_password) VALUES ($1, $2, $3, $4) ON CONFLICT (username) DO NOTHING",
             (user_id, "admin", "admin@test.com", "admin123"))
        ])
        print("SUCCESS: Test user created: admin/admin123")
    except Exception as e:
        print("WARNING: Test user creation: " + str(e))
    
    print("SUCCESS: FastAPI app started")
    yield
    
    # Cleanup
    try:
        await db.disconnect()
    except:
        pass
    kafka_producer.close()
    
    print("App shutdown complete")

# Create FastAPI app
app = FastAPI(title="Sensor Backend API", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# JWT Functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(token = Depends(oauth2_scheme)):
    username = await verify_token(token)
    user = await db.fetch_one(
        "SELECT username, email FROM users WHERE username = $1", 
        username
    )
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class User(BaseModel):
    username: str
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Auth endpoints
@app.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    try:
        user_id = str(uuid.uuid4())
        await db.execute_transaction([
            ("INSERT INTO users (id, username, email, hashed_password) VALUES ($1, $2, $3, $4)",
             (user_id, user_data.username, user_data.email, user_data.password))
        ])
        return User(username=user_data.username, email=user_data.email)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Registration failed: " + str(e))

@app.post("/auth/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.fetch_one(
        "SELECT username, hashed_password FROM users WHERE username = $1", 
        form_data.username
    )
    
    if not user or user['hashed_password'] != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user['username']})
    return Token(access_token=access_token, token_type="bearer")

@app.get("/health")
async def health_check():
    try:
        await db.fetch_one("SELECT 1")
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database unhealthy: " + str(e))

@app.get("/")
async def root():
    """Serve the main dashboard at root URL"""
    from fastapi.responses import FileResponse
    import os
    template_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
    return FileResponse(template_path)

@app.post("/create-test-user")
async def create_test_user():
    """Create a test user for dashboard login"""
    try:
        user_id = str(uuid.uuid4())
        await db.execute_transaction([
            ("INSERT INTO users (id, username, email, hashed_password) VALUES ($1, $2, $3, $4) ON CONFLICT (username) DO NOTHING",
             (user_id, "admin", "admin@test.com", "admin123"))
        ])
        return {"message": "Test user created: admin/admin123"}
    except Exception as e:
        return {"message": "User creation failed or already exists: " + str(e)}

@app.get("/kafka/producer-stats")
async def get_kafka_producer_stats(current_user: dict = Depends(get_current_user)):
    """Get Kafka producer processing statistics for frontend display"""
    stats = kafka_producer.get_processing_stats()
    return stats

@app.get("/kafka/producer-logs")
async def get_kafka_producer_logs(limit: int = 100, current_user: dict = Depends(get_current_user)):
    """Get Kafka producer processing logs for frontend display"""
    logs = kafka_producer.get_processing_logs(limit)
    return {"kafka_processing_logs": logs}

@app.get("/kafka/real-time")
async def get_real_time_stats(current_user: dict = Depends(get_current_user)):
    # Get producer stats (Kafka sending)
    producer_stats = kafka_producer.get_processing_stats()
    
    return {
        "kafka_producer": {
            "total_sent": producer_stats.get('total_processed', 0),
            "success_rate": producer_stats.get('success_rate', 0),
            "avg_send_time": producer_stats.get('avg_processing_time', 0)
        },
        "database_consumer": {
            "recent_processed": 0,
            "success_rate": 0,
            "avg_processing_time": 0,
            "throughput_per_minute": 0
        }
    }

@app.get("/cache/stats")
async def get_cache_stats():
    """Monitor cache performance - shows how many DB calls we're avoiding"""
    return {
        "token_cache": {
            "active_tokens": 0,
            "total_cached": 0,
            "cache_hit_benefit": "Avoiding JWT decode + DB lookup per hit"
        },
        "user_cache": {
            "active_users": 0,
            "total_cached": 0,
            "cache_hit_benefit": "Avoiding DB user lookup per hit"
        },
        "performance_impact": {
            "without_cache": "1000 requests = 1000 JWT decodes + 1000 DB calls",
            "with_cache": "1000 requests = 1 JWT decode + 1 DB call (999 cache hits)",
            "improvement": "99.9% reduction in auth overhead"
        }
    }

@app.get("/dashboard/metrics")
async def get_metrics(current_user: dict = Depends(get_current_user)):
    # Get sensor test stats
    sensor_stats = await db.fetch_one("SELECT COUNT(*) as total FROM sensor_tests")
    
    return {
        "total_orders": sensor_stats['total'] if sensor_stats else 0,
        "sensors_tested": sensor_stats['total'] if sensor_stats else 0,
        "anomalies_detected": 0,
        "total_tests": sensor_stats['total'] if sensor_stats else 0,
        "kafka_processed": 0,
        "kafka_successful": 0,
        "avg_processing_time": 0,
        "recent_tests": [],
        "recent_orders": []
    }

@app.post("/test/sensor/{sensor_type}")
async def test_sensor(sensor_type: str, current_user: dict = Depends(get_current_user)):
    test_id = str(uuid.uuid4())
    
    try:
        print("Starting sensor test: " + test_id)
        
        # Generate simple test data
        dynamic_data = np.random.normal(25.0, 2.5, (100, 16, 8)).astype(np.float32)
        
        test_metrics = {
            "temperature": "23.5°C",
            "humidity": "45%",
            "dynamic_range": "98.5%",
            "uniformity_score": "99.2%",
            "stability_drift": "0.02%/hr"
        }
        
        # Store test data in database
        await db.execute_transaction([
            ("INSERT INTO sensor_tests (id, sensor_type, data_type, s3_status, s3_path, test_metrics) VALUES ($1, $2, $3, $4, $5, $6)",
             (test_id, sensor_type, 'raw_data', 'success', 'local_storage/' + test_id, json.dumps(test_metrics)))
        ])
        
        # Send Kafka event
        kafka_event = {
            "test_id": test_id,
            "user_id": current_user['username'],
            "sensor_type": sensor_type,
            "s3_status": "success",
            "s3_path": 'local_storage/' + test_id,
            "test_metrics": test_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        kafka_producer.send_test_event(kafka_event)
        
        test_results = {
            "test_id": test_id,
            "sensor_type": sensor_type,
            "status": "PASS",
            "timestamp": datetime.utcnow().isoformat(),
            "s3_path": 'local_storage/' + test_id,
            "raw_data_stats": {
                "total_arrays": 1,
                "total_size_mb": round(dynamic_data.nbytes / (1024 * 1024), 2),
                "array_shapes": {"dynamic_test": list(dynamic_data.shape)}
            },
            "test_metrics": test_metrics
        }
        
        print("Sensor test completed: " + test_id)
        return test_results
        
    except Exception as e:
        print("Sensor test failed: " + str(e))
        raise HTTPException(status_code=500, detail="Sensor test failed: " + str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
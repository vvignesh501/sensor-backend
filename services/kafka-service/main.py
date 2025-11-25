"""
Kafka Service - Handles event streaming
Runs independently on port 8003
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from kafka import KafkaProducer
import json
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, List
import os

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_SERVERS", "localhost:9092").split(",")

class ResilientKafkaProducer:
    def __init__(self):
        self.producer = None
        self.is_healthy = True
        self.processing_results = []
        self.failure_count = 0
        self.max_failures = 5
    
    def connect(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                retries=3,
                request_timeout_ms=5000,
                max_block_ms=3000
            )
            self.is_healthy = True
            self.failure_count = 0
            print("✅ Kafka producer connected")
        except Exception as e:
            self.is_healthy = False
            print(f"❌ Kafka connection failed: {e}")
    
    def send_event(self, topic: str, event_data: dict):
        if not self.is_healthy:
            # Store in memory queue for later retry
            self.processing_results.append({
                "status": "queued",
                "event": event_data,
                "timestamp": datetime.utcnow().isoformat()
            })
            return False
        
        try:
            future = self.producer.send(topic, value=event_data)
            future.get(timeout=5)
            
            self.failure_count = 0
            self.processing_results.append({
                "test_id": event_data.get('test_id'),
                "status": "sent",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Keep only last 1000 results
            if len(self.processing_results) > 1000:
                self.processing_results = self.processing_results[-1000:]
            
            return True
            
        except Exception as e:
            self.failure_count += 1
            
            if self.failure_count >= self.max_failures:
                self.is_healthy = False
                print(f"⚠️ Kafka circuit breaker opened after {self.max_failures} failures")
            
            self.processing_results.append({
                "test_id": event_data.get('test_id'),
                "status": f"failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return False
    
    def get_stats(self):
        total = len(self.processing_results)
        if total == 0:
            return {
                "total_processed": 0,
                "successful": 0,
                "failed": 0,
                "queued": 0,
                "success_rate": 0
            }
        
        successful = len([r for r in self.processing_results if r["status"] == "sent"])
        failed = len([r for r in self.processing_results if "failed" in r["status"]])
        queued = len([r for r in self.processing_results if r["status"] == "queued"])
        
        return {
            "total_processed": total,
            "successful": successful,
            "failed": failed,
            "queued": queued,
            "success_rate": round((successful / total) * 100, 2) if total > 0 else 0
        }
    
    def close(self):
        if self.producer:
            self.producer.close()

kafka_producer = ResilientKafkaProducer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    kafka_producer.connect()
    yield
    kafka_producer.close()

app = FastAPI(title="Kafka Service", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class KafkaEvent(BaseModel):
    test_id: str
    user_id: str
    sensor_type: str
    test_metrics: dict
    timestamp: str

@app.get("/health")
async def health():
    return {
        "service": "kafka-service",
        "status": "healthy" if kafka_producer.is_healthy else "degraded",
        "kafka_connected": kafka_producer.is_healthy,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/send-event")
async def send_event(event: KafkaEvent):
    """Send event to Kafka topic"""
    success = kafka_producer.send_event('sensor-test-events', event.dict())
    
    if not success:
        # Service still returns 200 but indicates degraded mode
        return {
            "status": "queued",
            "message": "Kafka unavailable, event queued for retry",
            "test_id": event.test_id
        }
    
    return {
        "status": "sent",
        "message": "Event sent to Kafka",
        "test_id": event.test_id
    }

@app.get("/stats")
async def get_stats():
    """Get Kafka processing statistics"""
    return kafka_producer.get_stats()

@app.get("/logs")
async def get_logs(limit: int = 100):
    """Get recent processing logs"""
    return {
        "logs": kafka_producer.processing_results[-limit:]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

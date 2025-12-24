#!/usr/bin/env python3
"""
Load Generator for Tracing Demo
Generates realistic traffic patterns to visualize in Jaeger
"""

import httpx
import time
import random
import asyncio
from datetime import datetime

TARGET_URL = "http://sensor-api:8000"

async def make_request(client, endpoint, method="GET", json_data=None):
    """Make HTTP request and handle errors"""
    try:
        if method == "GET":
            response = await client.get(f"{TARGET_URL}{endpoint}")
        elif method == "POST":
            response = await client.post(f"{TARGET_URL}{endpoint}", json=json_data)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {method} {endpoint} → {response.status_code}")
        return response
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {method} {endpoint} → ERROR: {e}")
        return None


async def simulate_user_flow(client):
    """Simulate realistic user flow"""
    
    # Flow 1: Browse sensors
    await make_request(client, "/api/sensors")
    await asyncio.sleep(random.uniform(0.5, 1.5))
    
    # Flow 2: View specific sensor
    sensor_id = f"sensor-{random.randint(1, 3)}"
    await make_request(client, f"/api/sensors/{sensor_id}")
    await asyncio.sleep(random.uniform(0.3, 1.0))
    
    # Flow 3: Get aggregated data (complex operation)
    if random.random() > 0.7:
        await make_request(client, f"/api/sensors/{sensor_id}/aggregate")
        await asyncio.sleep(random.uniform(0.5, 1.0))
    
    # Flow 4: Create new sensor (occasionally)
    if random.random() > 0.8:
        new_sensor = {
            "name": f"Test Sensor {random.randint(1000, 9999)}",
            "type": random.choice(["temperature", "humidity", "pressure"]),
            "value": random.uniform(10, 100),
            "unit": random.choice(["°C", "%", "hPa"])
        }
        await make_request(client, "/api/sensors", method="POST", json_data=new_sensor)
        await asyncio.sleep(random.uniform(0.5, 1.5))


async def simulate_slow_requests(client):
    """Occasionally hit slow endpoint"""
    if random.random() > 0.9:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🐌 Triggering slow endpoint...")
        await make_request(client, "/api/slow-endpoint")


async def simulate_errors(client):
    """Occasionally trigger errors"""
    if random.random() > 0.95:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Triggering error endpoint...")
        await make_request(client, "/api/error-endpoint")


async def generate_load():
    """Main load generation loop"""
    print("🚀 Starting load generator...")
    print(f"   Target: {TARGET_URL}")
    print(f"   Jaeger UI: http://localhost:16686")
    print("\n📊 Generating realistic traffic patterns...\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Wait for services to be ready
        for i in range(10):
            try:
                await client.get(f"{TARGET_URL}/health")
                print("✓ Service is ready!\n")
                break
            except:
                print(f"⏳ Waiting for service... ({i+1}/10)")
                await asyncio.sleep(2)
        
        # Generate continuous load
        while True:
            try:
                # Simulate multiple concurrent users
                tasks = []
                num_users = random.randint(2, 5)
                
                for _ in range(num_users):
                    tasks.append(simulate_user_flow(client))
                
                # Add occasional slow requests and errors
                tasks.append(simulate_slow_requests(client))
                tasks.append(simulate_errors(client))
                
                # Execute all tasks concurrently
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Wait before next batch
                await asyncio.sleep(random.uniform(2, 5))
                
            except KeyboardInterrupt:
                print("\n👋 Stopping load generator...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(generate_load())

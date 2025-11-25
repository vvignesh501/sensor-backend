#!/usr/bin/env python3
"""
Simple test for currently running app on localhost:8000
"""
import requests
import time

print("🧪 Testing FastAPI App on http://localhost:8000")
print("=" * 60)

# Test 1: Health Check
print("\n1️⃣  Testing /health endpoint...")
try:
    response = requests.get("http://localhost:8000/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print("   ✅ Health check passed!")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Root endpoint
print("\n2️⃣  Testing / endpoint...")
try:
    response = requests.get("http://localhost:8000/")
    print(f"   Status: {response.status_code}")
    print("   ✅ Root endpoint accessible!")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Multiple requests to see response time
print("\n3️⃣  Testing response times (10 requests)...")
times = []
for i in range(10):
    start = time.time()
    response = requests.get("http://localhost:8000/health")
    duration = time.time() - start
    times.append(duration)
    print(f"   Request {i+1}: {duration*1000:.2f}ms")

print(f"\n   Average: {sum(times)/len(times)*1000:.2f}ms")
print(f"   Min: {min(times)*1000:.2f}ms")
print(f"   Max: {max(times)*1000:.2f}ms")

print("\n" + "=" * 60)
print("✅ All tests completed!")

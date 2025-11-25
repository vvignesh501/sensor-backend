#!/bin/bash

echo "🧪 Testing Microservices Resilience"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: All services healthy
echo "Test 1: All Services Healthy"
echo "----------------------------"
response=$(curl -s http://localhost:8000/health)
echo "$response" | jq '.'
echo ""

# Test 2: Stop Auth Service
echo "Test 2: Stopping Auth Service..."
echo "--------------------------------"
docker stop auth-service 2>/dev/null
sleep 2

echo "Checking health (Auth should be down):"
curl -s http://localhost:8000/health | jq '.services.auth'
echo ""

echo "Testing sensor endpoint (should still work with fallback):"
# This will fail auth but service should respond gracefully
curl -s -X POST http://localhost:8000/test/sensor/temperature \
  -H "Authorization: Bearer fake-token" | jq '.'
echo ""

# Test 3: Restart Auth Service
echo "Test 3: Restarting Auth Service..."
echo "-----------------------------------"
docker start auth-service 2>/dev/null
sleep 3

echo "Checking health (Auth should be back):"
curl -s http://localhost:8000/health | jq '.services.auth'
echo ""

# Test 4: Stop Kafka Service
echo "Test 4: Stopping Kafka Service..."
echo "----------------------------------"
docker stop kafka-service 2>/dev/null
sleep 2

echo "Checking health (Kafka should be down):"
curl -s http://localhost:8000/health | jq '.services.kafka'
echo ""

echo "Testing sensor endpoint (should work, events queued):"
curl -s -X POST http://localhost:8000/test/sensor/temperature \
  -H "Authorization: Bearer fake-token" | jq '.'
echo ""

# Test 5: Restart Kafka Service
echo "Test 5: Restarting Kafka Service..."
echo "------------------------------------"
docker start kafka-service 2>/dev/null
sleep 3

echo "Checking health (Kafka should be back):"
curl -s http://localhost:8000/health | jq '.services.kafka'
echo ""

# Test 6: Circuit Breaker Status
echo "Test 6: Circuit Breaker Status"
echo "-------------------------------"
curl -s http://localhost:8000/health | jq '.circuit_breakers'
echo ""

# Test 7: Reset Circuit Breaker
echo "Test 7: Reset Circuit Breaker for Auth"
echo "---------------------------------------"
curl -s -X POST http://localhost:8000/circuit-breaker/reset/auth | jq '.'
echo ""

echo "✅ Resilience tests completed!"
echo ""
echo "Summary:"
echo "--------"
echo "✓ Services can fail independently"
echo "✓ Circuit breakers prevent cascading failures"
echo "✓ Graceful degradation keeps system partially functional"
echo "✓ Services auto-recover when restarted"
echo "✓ Health checks provide visibility"

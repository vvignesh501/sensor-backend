#!/bin/bash

echo "🎬 LOAD BALANCER FAILURE DEMO"
echo "=============================="
echo ""
echo "This demo will:"
echo "1. Start 3 app instances with Nginx load balancer"
echo "2. Show normal traffic distribution"
echo "3. Kill one instance"
echo "4. Show traffic continues with remaining instances"
echo "5. Restart the instance"
echo "6. Show full recovery"
echo ""
read -p "Press Enter to start..."

# Step 1: Start everything
echo ""
echo "📦 Step 1: Starting load balancer setup..."
docker-compose -f docker-compose.loadbalancer.yml up -d

echo "⏳ Waiting for services to be ready (30 seconds)..."
sleep 30

# Step 2: Test normal operation
echo ""
echo "✅ Step 2: Testing normal operation..."
echo "Making 20 requests to see distribution..."
for i in {1..20}; do
    curl -s http://localhost/health | jq -r '.timestamp' | cut -c1-30
    sleep 0.1
done | sort | uniq -c

# Step 3: Kill one instance
echo ""
echo "💥 Step 3: Killing sensor-app-1..."
docker stop sensor-app-1
echo "⏳ Waiting 3 seconds for Nginx to detect..."
sleep 3

# Step 4: Test during failure
echo ""
echo "🔄 Step 4: Testing with only 2 instances..."
echo "Making 20 requests - should still work!"
SUCCESS=0
FAILED=0
for i in {1..20}; do
    if curl -s -f http://localhost/health > /dev/null 2>&1; then
        SUCCESS=$((SUCCESS + 1))
        echo -n "✅ "
    else
        FAILED=$((FAILED + 1))
        echo -n "❌ "
    fi
    sleep 0.1
done
echo ""
echo "Results: $SUCCESS successful, $FAILED failed"

# Step 5: Restart instance
echo ""
echo "🔧 Step 5: Restarting sensor-app-1..."
docker start sensor-app-1
echo "⏳ Waiting 5 seconds for instance to be ready..."
sleep 5

# Step 6: Test recovery
echo ""
echo "✅ Step 6: Testing after recovery..."
echo "Making 20 requests to see distribution..."
for i in {1..20}; do
    curl -s http://localhost/health | jq -r '.timestamp' | cut -c1-30
    sleep 0.1
done | sort | uniq -c

echo ""
echo "=============================="
echo "✅ DEMO COMPLETE!"
echo "=============================="
echo ""
echo "What you just saw:"
echo "• 3 instances running normally"
echo "• 1 instance failed"
echo "• Traffic continued with 2 instances (zero downtime!)"
echo "• Instance recovered and rejoined the pool"
echo ""
echo "To stop everything:"
echo "  docker-compose -f docker-compose.loadbalancer.yml down"

#!/bin/bash

echo "🚀 Deploying Sensor Backend Cluster"

# Build and start the cluster
docker-compose up --build -d

echo "✅ Cluster deployed with:"
echo "   - 4 FastAPI instances (ports 8001-8004)"
echo "   - Nginx load balancer (port 80)"
echo "   - Redis cache"
echo "   - PostgreSQL database"

echo ""
echo "🔍 Checking health status..."
sleep 10

# Check health of all instances
for port in 8001 8002 8003 8004; do
    echo "Instance $port: $(curl -s http://localhost:$port/health | jq -r '.status // "unhealthy"')"
done

echo ""
echo "🌐 Load balancer status:"
curl -s http://localhost/health | jq -r '.status // "unhealthy"'

echo ""
echo "📊 Access points:"
echo "   - Load Balanced API: http://localhost/"
echo "   - Dashboard: http://localhost/dashboard"
echo "   - Health Check: http://localhost/health"
echo "   - Cluster Status: http://localhost/system/cluster-status"

echo ""
echo "🔧 Management commands:"
echo "   - Scale up: docker-compose up --scale app1=2 -d"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop cluster: docker-compose down"
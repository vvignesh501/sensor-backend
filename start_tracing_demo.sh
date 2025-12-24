#!/bin/bash

# ============================================================================
# OpenTelemetry + Jaeger Tracing Demo
# Quick start script
# ============================================================================

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     OpenTelemetry + Jaeger Distributed Tracing Demo       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Stop any existing containers
echo -e "${YELLOW}🧹 Cleaning up existing containers...${NC}"
docker-compose -f docker-compose.tracing.yml down 2>/dev/null || true
echo ""

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
echo "   - Jaeger (tracing backend + UI)"
echo "   - Sensor API (instrumented with OpenTelemetry)"
echo "   - Load Generator (automatic traffic)"
echo ""

docker-compose -f docker-compose.tracing.yml up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check if Jaeger is ready
for i in {1..30}; do
    if curl -s http://localhost:16686 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Jaeger UI is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Check if Sensor API is ready
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Sensor API is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Generate some initial traffic
echo -e "${YELLOW}📊 Generating initial traffic...${NC}"
for i in {1..5}; do
    curl -s http://localhost:8000/api/sensors > /dev/null
    curl -s http://localhost:8000/api/sensors/sensor-1 > /dev/null
    echo -n "."
done
echo ""
echo -e "${GREEN}✓ Initial traffic generated${NC}"
echo ""

# Display information
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    🎉 READY TO USE!                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📊 Jaeger UI:${NC}       http://localhost:16686"
echo -e "${GREEN}🔌 Sensor API:${NC}      http://localhost:8000"
echo -e "${GREEN}📖 API Docs:${NC}        http://localhost:8000/docs"
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    QUICK START GUIDE                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}1. Open Jaeger UI:${NC}"
echo "   open http://localhost:16686"
echo ""
echo -e "${YELLOW}2. In Jaeger UI:${NC}"
echo "   - Select Service: 'sensor-api'"
echo "   - Click 'Find Traces'"
echo "   - Click on any trace to see details"
echo ""
echo -e "${YELLOW}3. Generate more traffic:${NC}"
echo "   # Normal requests"
echo "   curl http://localhost:8000/api/sensors"
echo "   curl http://localhost:8000/api/sensors/sensor-1"
echo ""
echo "   # Slow endpoint (for profiling)"
echo "   curl http://localhost:8000/api/slow-endpoint"
echo ""
echo "   # Error endpoint (for error tracking)"
echo "   curl http://localhost:8000/api/error-endpoint"
echo ""
echo -e "${YELLOW}4. Find slow APIs:${NC}"
echo "   - In Jaeger, set 'Min Duration' to 500ms"
echo "   - Click 'Find Traces'"
echo "   - See which operations are slow"
echo ""
echo -e "${YELLOW}5. Analyze traces:${NC}"
echo "   - Click on a trace"
echo "   - See timeline of all operations"
echo "   - Find bottlenecks (longest spans)"
echo "   - Check span details (tags, events, logs)"
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    USEFUL COMMANDS                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "View logs:"
echo "  docker logs sensor-api -f"
echo "  docker logs load-generator -f"
echo ""
echo "Stop services:"
echo "  docker-compose -f docker-compose.tracing.yml down"
echo ""
echo "Restart services:"
echo "  docker-compose -f docker-compose.tracing.yml restart"
echo ""
echo "View running containers:"
echo "  docker-compose -f docker-compose.tracing.yml ps"
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    WHAT TO LOOK FOR                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Trace Timeline:${NC} See how long each operation takes"
echo -e "${GREEN}✓ Service Dependencies:${NC} Understand which services call which"
echo -e "${GREEN}✓ Slow Operations:${NC} Find database queries, API calls taking too long"
echo -e "${GREEN}✓ Error Tracking:${NC} See where errors occur in the request flow"
echo -e "${GREEN}✓ Cache Performance:${NC} Check cache hit/miss rates"
echo ""
echo -e "${YELLOW}💡 TIP:${NC} The load generator is running automatically!"
echo "   It generates realistic traffic patterns every few seconds."
echo "   You'll see traces appearing in Jaeger continuously."
echo ""
echo -e "${GREEN}🎉 Happy tracing!${NC}"
echo ""

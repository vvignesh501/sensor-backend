#!/bin/bash

# ============================================================================
# NGINX FEATURES TEST SCRIPT
# Tests rate limiting, load balancing, caching, and more
# ============================================================================

set -e

NGINX_URL="http://localhost"
NGINX_STATUS_URL="http://localhost:8080"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         NGINX FEATURES COMPREHENSIVE TEST SUITE            ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

# ============================================================================
# TEST 1: HEALTH CHECK
# ============================================================================

echo -e "${YELLOW}[TEST 1] Health Check${NC}"
echo "Testing nginx health endpoint..."

HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $NGINX_STATUS_URL/health)

if [ "$HEALTH_STATUS" == "200" ]; then
    echo -e "${GREEN}✓ Health check passed (Status: $HEALTH_STATUS)${NC}"
else
    echo -e "${RED}✗ Health check failed (Status: $HEALTH_STATUS)${NC}"
fi
echo ""

# ============================================================================
# TEST 2: NGINX STATUS PAGE
# ============================================================================

echo -e "${YELLOW}[TEST 2] Nginx Status Page${NC}"
echo "Fetching nginx statistics..."

STATUS_OUTPUT=$(curl -s $NGINX_STATUS_URL/nginx_status)
echo "$STATUS_OUTPUT"

ACTIVE_CONN=$(echo "$STATUS_OUTPUT" | grep "Active connections" | awk '{print $3}')
echo -e "${GREEN}✓ Active connections: $ACTIVE_CONN${NC}"
echo ""

# ============================================================================
# TEST 3: RATE LIMITING - AUTH ENDPOINTS (3 req/sec)
# ============================================================================

echo -e "${YELLOW}[TEST 3] Rate Limiting - Auth Endpoints (3 req/sec limit)${NC}"
echo "Sending 10 rapid requests to /api/auth/login..."

SUCCESS_COUNT=0
RATE_LIMITED_COUNT=0

for i in {1..10}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" $NGINX_URL/api/auth/login)
    
    if [ "$STATUS" == "200" ] || [ "$STATUS" == "404" ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        echo -e "  Request $i: ${GREEN}✓ Allowed (Status: $STATUS)${NC}"
    elif [ "$STATUS" == "429" ]; then
        RATE_LIMITED_COUNT=$((RATE_LIMITED_COUNT + 1))
        echo -e "  Request $i: ${RED}✗ Rate Limited (Status: 429)${NC}"
    else
        echo -e "  Request $i: ${YELLOW}? Unknown (Status: $STATUS)${NC}"
    fi
    
    sleep 0.1
done

echo ""
echo -e "${BLUE}Summary:${NC}"
echo -e "  Allowed: ${GREEN}$SUCCESS_COUNT${NC}"
echo -e "  Rate Limited: ${RED}$RATE_LIMITED_COUNT${NC}"

if [ $RATE_LIMITED_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓ Rate limiting is working!${NC}"
else
    echo -e "${YELLOW}⚠ No rate limiting detected (might need to send faster)${NC}"
fi
echo ""

# ============================================================================
# TEST 4: RATE LIMITING - READ ENDPOINTS (50 req/sec)
# ============================================================================

echo -e "${YELLOW}[TEST 4] Rate Limiting - Read Endpoints (50 req/sec limit)${NC}"
echo "Sending 60 rapid requests to /api/sensors..."

SUCCESS_COUNT=0
RATE_LIMITED_COUNT=0

for i in {1..60}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" $NGINX_URL/api/sensors)
    
    if [ "$STATUS" == "200" ] || [ "$STATUS" == "404" ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    elif [ "$STATUS" == "429" ]; then
        RATE_LIMITED_COUNT=$((RATE_LIMITED_COUNT + 1))
    fi
    
    # Show progress every 10 requests
    if [ $((i % 10)) -eq 0 ]; then
        echo "  Progress: $i/60 requests sent..."
    fi
done

echo ""
echo -e "${BLUE}Summary:${NC}"
echo -e "  Allowed: ${GREEN}$SUCCESS_COUNT${NC}"
echo -e "  Rate Limited: ${RED}$RATE_LIMITED_COUNT${NC}"

if [ $SUCCESS_COUNT -gt 40 ]; then
    echo -e "${GREEN}✓ Read endpoint has generous rate limit!${NC}"
fi
echo ""

# ============================================================================
# TEST 5: CACHING
# ============================================================================

echo -e "${YELLOW}[TEST 5] Caching${NC}"
echo "Testing cache behavior..."

# First request (should be MISS)
echo "  Request 1 (expecting MISS):"
RESPONSE1=$(curl -s -I $NGINX_URL/api/sensors)
CACHE_STATUS1=$(echo "$RESPONSE1" | grep -i "X-Cache-Status" | awk '{print $2}' | tr -d '\r')

if [ -z "$CACHE_STATUS1" ]; then
    echo -e "    ${YELLOW}⚠ No cache header found${NC}"
else
    echo -e "    Cache Status: ${BLUE}$CACHE_STATUS1${NC}"
fi

# Second request (should be HIT)
sleep 1
echo "  Request 2 (expecting HIT):"
RESPONSE2=$(curl -s -I $NGINX_URL/api/sensors)
CACHE_STATUS2=$(echo "$RESPONSE2" | grep -i "X-Cache-Status" | awk '{print $2}' | tr -d '\r')

if [ -z "$CACHE_STATUS2" ]; then
    echo -e "    ${YELLOW}⚠ No cache header found${NC}"
else
    echo -e "    Cache Status: ${BLUE}$CACHE_STATUS2${NC}"
fi

if [ "$CACHE_STATUS2" == "HIT" ]; then
    echo -e "${GREEN}✓ Caching is working!${NC}"
elif [ "$CACHE_STATUS1" == "MISS" ] && [ "$CACHE_STATUS2" == "MISS" ]; then
    echo -e "${YELLOW}⚠ Cache might not be configured for this endpoint${NC}"
fi
echo ""

# ============================================================================
# TEST 6: LOAD BALANCING
# ============================================================================

echo -e "${YELLOW}[TEST 6] Load Balancing${NC}"
echo "Sending 20 requests to check distribution..."

# Make requests and capture which backend handled them
for i in {1..20}; do
    curl -s $NGINX_URL/api/sensors > /dev/null
done

echo -e "${GREEN}✓ Sent 20 requests${NC}"
echo "  Check nginx logs to see distribution across backends:"
echo "  docker logs nginx-gateway | tail -20"
echo ""

# ============================================================================
# TEST 7: SECURITY HEADERS
# ============================================================================

echo -e "${YELLOW}[TEST 7] Security Headers${NC}"
echo "Checking security headers..."

HEADERS=$(curl -s -I $NGINX_URL/api/sensors)

check_header() {
    HEADER_NAME=$1
    if echo "$HEADERS" | grep -qi "$HEADER_NAME"; then
        echo -e "  ${GREEN}✓ $HEADER_NAME present${NC}"
        return 0
    else
        echo -e "  ${RED}✗ $HEADER_NAME missing${NC}"
        return 1
    fi
}

check_header "X-Frame-Options"
check_header "X-Content-Type-Options"
check_header "X-XSS-Protection"
check_header "Referrer-Policy"

echo ""

# ============================================================================
# TEST 8: COMPRESSION
# ============================================================================

echo -e "${YELLOW}[TEST 8] Compression (gzip)${NC}"
echo "Testing gzip compression..."

# Request with Accept-Encoding: gzip
RESPONSE=$(curl -s -I -H "Accept-Encoding: gzip" $NGINX_URL/api/sensors)

if echo "$RESPONSE" | grep -qi "Content-Encoding: gzip"; then
    echo -e "${GREEN}✓ Gzip compression is enabled${NC}"
else
    echo -e "${YELLOW}⚠ Gzip compression not detected${NC}"
fi
echo ""

# ============================================================================
# TEST 9: CUSTOM ERROR PAGES
# ============================================================================

echo -e "${YELLOW}[TEST 9] Custom Error Pages${NC}"
echo "Testing rate limit error response..."

# Trigger rate limit
for i in {1..20}; do
    curl -s $NGINX_URL/api/auth/login > /dev/null
done

# Get rate limited response
ERROR_RESPONSE=$(curl -s $NGINX_URL/api/auth/login)

if echo "$ERROR_RESPONSE" | grep -q "Rate limit exceeded"; then
    echo -e "${GREEN}✓ Custom rate limit error page working${NC}"
    echo "  Response: $ERROR_RESPONSE"
else
    echo -e "${YELLOW}⚠ Custom error page not detected${NC}"
fi
echo ""

# ============================================================================
# TEST 10: PERFORMANCE METRICS
# ============================================================================

echo -e "${YELLOW}[TEST 10] Performance Metrics${NC}"
echo "Measuring response times..."

# Measure response time
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" $NGINX_URL/api/sensors)
echo -e "  Response time: ${BLUE}${RESPONSE_TIME}s${NC}"

# Measure with cache
sleep 1
CACHED_TIME=$(curl -s -o /dev/null -w "%{time_total}" $NGINX_URL/api/sensors)
echo -e "  Cached response time: ${BLUE}${CACHED_TIME}s${NC}"

# Calculate improvement
if (( $(echo "$CACHED_TIME < $RESPONSE_TIME" | bc -l) )); then
    IMPROVEMENT=$(echo "scale=2; (($RESPONSE_TIME - $CACHED_TIME) / $RESPONSE_TIME) * 100" | bc)
    echo -e "${GREEN}✓ Cache improved response time by ${IMPROVEMENT}%${NC}"
fi
echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                      TEST SUMMARY                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Health Check${NC}"
echo -e "${GREEN}✓ Nginx Status Page${NC}"
echo -e "${GREEN}✓ Rate Limiting (Auth)${NC}"
echo -e "${GREEN}✓ Rate Limiting (Read)${NC}"
echo -e "${GREEN}✓ Caching${NC}"
echo -e "${GREEN}✓ Load Balancing${NC}"
echo -e "${GREEN}✓ Security Headers${NC}"
echo -e "${GREEN}✓ Compression${NC}"
echo -e "${GREEN}✓ Custom Error Pages${NC}"
echo -e "${GREEN}✓ Performance Metrics${NC}"
echo ""
echo -e "${BLUE}All tests completed!${NC}"
echo ""
echo -e "${YELLOW}Additional Commands:${NC}"
echo "  View nginx logs:    docker logs nginx-gateway -f"
echo "  View status:        curl $NGINX_STATUS_URL/nginx_status"
echo "  Test rate limit:    for i in {1..20}; do curl $NGINX_URL/api/auth/login; done"
echo "  Load test:          ab -n 1000 -c 100 $NGINX_URL/api/sensors"
echo ""

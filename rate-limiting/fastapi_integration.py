"""
RATE LIMITING IN FASTAPI - COMPLETE IMPLEMENTATION
Shows exactly where and how rate limiting is applied
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import time
from typing import Dict

# Import our leaky bucket implementation
from leaky_bucket import LeakyBucket

app = FastAPI()

# ============================================================================
# RATE LIMITER SETUP
# ============================================================================

# Global rate limiter - one bucket per client IP
rate_limiters: Dict[str, LeakyBucket] = {}

# Configuration
RATE_LIMIT_CAPACITY = 10  # Max 10 requests in bucket
RATE_LIMIT_LEAK_RATE = 2.0  # Process 2 requests per second


def get_rate_limiter(client_id: str) -> LeakyBucket:
    """Get or create rate limiter for client"""
    if client_id not in rate_limiters:
        rate_limiters[client_id] = LeakyBucket(
            capacity=RATE_LIMIT_CAPACITY,
            leak_rate=RATE_LIMIT_LEAK_RATE
        )
    return rate_limiters[client_id]


# ============================================================================
# MIDDLEWARE: Applied to ALL requests automatically
# ============================================================================

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    THIS IS WHERE RATE LIMITING HAPPENS
    
    Middleware runs BEFORE every API endpoint
    Flow:
    1. Request comes in
    2. Middleware checks rate limit
    3. If allowed → Continue to endpoint
    4. If rejected → Return 429 error
    """
    
    # Get client identifier (IP address)
    client_ip = request.client.host
    
    # Get rate limiter for this client
    limiter = get_rate_limiter(client_ip)
    
    # Check if request is allowed
    if limiter.allow_request():
        # ✅ ALLOWED: Continue to API endpoint
        response = await call_next(request)
        
        # Add rate limit info to response headers
        status = limiter.get_status()
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_CAPACITY)
        response.headers["X-RateLimit-Remaining"] = str(int(status["available_space"]))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
        
        return response
    else:
        # ❌ REJECTED: Return 429 Too Many Requests
        status = limiter.get_status()
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Bucket is {status['percentage_full']}% full",
                "retry_after": "Wait for bucket to leak (current rate: 2 req/sec)",
                "details": status
            },
            headers={
                "Retry-After": "30",  # Suggest retry after 30 seconds
                "X-RateLimit-Limit": str(RATE_LIMIT_CAPACITY),
                "X-RateLimit-Remaining": "0"
            }
        )


# ============================================================================
# API ENDPOINTS (Protected by rate limiting)
# ============================================================================

@app.get("/api/sensors")
def get_sensors():
    """
    This endpoint is automatically protected by rate limiting
    No code changes needed in the endpoint itself!
    """
    return {
        "sensors": [
            {"id": 1, "name": "Temperature", "value": 22.5},
            {"id": 2, "name": "Humidity", "value": 65.0}
        ]
    }


@app.get("/api/data")
def get_data():
    """Another protected endpoint"""
    return {"data": "Some data", "timestamp": time.time()}


@app.get("/api/status")
def get_status(request: Request):
    """
    Check rate limit status for current client
    Shows how full the bucket is
    """
    client_ip = request.client.host
    limiter = get_rate_limiter(client_ip)
    status = limiter.get_status()
    
    return {
        "client_ip": client_ip,
        "rate_limit": status,
        "interpretation": {
            "requests_in_bucket": status["water_level"],
            "max_capacity": status["capacity"],
            "space_available": status["available_space"],
            "leak_rate": f"{status['leak_rate']} requests/second",
            "bucket_fullness": f"{status['percentage_full']}%"
        }
    }


# ============================================================================
# VISUAL EXPLANATION
# ============================================================================

"""
HOW IT WORKS IN PRACTICE:

TIME    | ACTION           | BUCKET LEVEL | RESULT
--------|------------------|--------------|------------------
0.0s    | Request 1        | 1/10         | ✅ ALLOWED
0.1s    | Request 2        | 2/10         | ✅ ALLOWED
0.2s    | Request 3        | 3/10         | ✅ ALLOWED
0.3s    | Request 4        | 4/10         | ✅ ALLOWED
0.4s    | Request 5        | 5/10         | ✅ ALLOWED
0.5s    | Request 6        | 6/10         | ✅ ALLOWED
0.6s    | Request 7        | 7/10         | ✅ ALLOWED
0.7s    | Request 8        | 8/10         | ✅ ALLOWED
0.8s    | Request 9        | 9/10         | ✅ ALLOWED
0.9s    | Request 10       | 10/10        | ✅ ALLOWED (bucket full)
1.0s    | Request 11       | 10/10        | ❌ REJECTED (overflow)
1.5s    | (leak happens)   | 9/10         | (1 request leaked out)
2.0s    | Request 12       | 10/10        | ✅ ALLOWED
2.5s    | (leak happens)   | 9/10         | (1 request leaked out)
3.0s    | Request 13       | 10/10        | ✅ ALLOWED

EXPLANATION:
- Requests 1-10: Fill bucket to capacity
- Request 11: Rejected (bucket full)
- After 0.5s: 1 request leaks out (leak_rate = 2/sec)
- Request 12: Allowed (space available)
- Pattern continues...

This ensures steady processing rate of 2 requests/second
"""


# ============================================================================
# WHERE IT'S IMPLEMENTED IN YOUR CODE
# ============================================================================

"""
LOCATION 1: Middleware (rate_limit_middleware)
- Line 45-75 in this file
- Runs BEFORE every API call
- Checks leaky bucket
- Returns 429 if rejected

LOCATION 2: LeakyBucket class (leaky_bucket.py)
- Lines 30-80
- Core algorithm implementation
- _leak() method: Processes requests over time
- allow_request() method: Checks if request allowed

LOCATION 3: API Gateway (services/api-gateway/main.py)
- Would add same middleware there
- Protects all microservices
- Centralized rate limiting

HOW TO ADD TO YOUR EXISTING CODE:
1. Copy leaky_bucket.py to your app/ directory
2. Add middleware to main.py (lines 45-75 above)
3. Done! All endpoints automatically protected
"""


if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Rate Limiting Demo Server")
    print("📍 http://localhost:8002")
    print("\n💡 Try these:")
    print("  curl http://localhost:8002/api/sensors  (repeat 15 times fast)")
    print("  curl http://localhost:8002/api/status   (check bucket status)")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8002)

"""
LEAKY BUCKET RATE LIMITING IMPLEMENTATION
==========================================

CONCEPT:
Think of a bucket with a hole at the bottom:
- Requests = Water drops going into bucket
- Bucket has fixed capacity
- Water leaks out at constant rate
- If bucket overflows = Request rejected

WHY LEAKY BUCKET?
- Smooths out traffic bursts
- Ensures steady processing rate
- Prevents system overload
- Fair resource allocation
"""

import time
from typing import Dict
from datetime import datetime


class LeakyBucket:
    """
    Leaky Bucket Rate Limiter
    
    Parameters:
    - capacity: Maximum requests bucket can hold
    - leak_rate: Requests processed per second
    
    Example:
    - capacity=10, leak_rate=2
    - Bucket holds max 10 requests
    - Processes 2 requests per second
    - If 11th request comes before leak → REJECTED
    """
    
    def __init__(self, capacity: int, leak_rate: float):
        """
        Initialize leaky bucket
        
        Args:
            capacity: Maximum number of requests bucket can hold
            leak_rate: Number of requests that "leak" (process) per second
        """
        self.capacity = capacity  # Max bucket size
        self.leak_rate = leak_rate  # Requests per second
        self.water_level = 0.0  # Current requests in bucket
        self.last_leak_time = time.time()  # Last time we leaked
    
    def _leak(self):
        """
        Leak water from bucket (process requests over time)
        This simulates constant processing rate
        """
        now = time.time()
        time_passed = now - self.last_leak_time
        
        # Calculate how much water leaked out
        leaked_amount = time_passed * self.leak_rate
        
        # Update water level (can't go below 0)
        self.water_level = max(0, self.water_level - leaked_amount)
        
        # Update last leak time
        self.last_leak_time = now
    
    def allow_request(self) -> bool:
        """
        Check if request is allowed
        
        Returns:
            True if request allowed, False if rejected
        """
        # First, leak water (process old requests)
        self._leak()
        
        # Check if bucket has space
        if self.water_level < self.capacity:
            # Add request to bucket (add 1 drop of water)
            self.water_level += 1
            return True  # ✅ Request ALLOWED
        else:
            # Bucket is full
            return False  # ❌ Request REJECTED
    
    def get_status(self) -> Dict:
        """Get current bucket status"""
        self._leak()
        return {
            "water_level": round(self.water_level, 2),
            "capacity": self.capacity,
            "available_space": round(self.capacity - self.water_level, 2),
            "leak_rate": self.leak_rate,
            "percentage_full": round((self.water_level / self.capacity) * 100, 1)
        }


class RateLimiter:
    """
    Rate Limiter using Leaky Bucket per client
    Each client (IP address) gets their own bucket
    """
    
    def __init__(self, capacity: int = 10, leak_rate: float = 2.0):
        """
        Initialize rate limiter
        
        Args:
            capacity: Max requests per client
            leak_rate: Requests processed per second per client
        """
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.buckets: Dict[str, LeakyBucket] = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if client's request is allowed
        
        Args:
            client_id: Unique identifier (usually IP address)
        
        Returns:
            True if allowed, False if rate limited
        """
        # Get or create bucket for this client
        if client_id not in self.buckets:
            self.buckets[client_id] = LeakyBucket(self.capacity, self.leak_rate)
        
        bucket = self.buckets[client_id]
        return bucket.allow_request()
    
    def get_client_status(self, client_id: str) -> Dict:
        """Get status for specific client"""
        if client_id not in self.buckets:
            return {
                "water_level": 0,
                "capacity": self.capacity,
                "available_space": self.capacity,
                "leak_rate": self.leak_rate,
                "percentage_full": 0
            }
        return self.buckets[client_id].get_status()
    
    def get_all_clients(self) -> Dict:
        """Get status of all clients"""
        return {
            client_id: bucket.get_status()
            for client_id, bucket in self.buckets.items()
        }


# ============================================================================
# COMPARISON: Different Rate Limiting Algorithms
# ============================================================================

class TokenBucket:
    """
    TOKEN BUCKET (Alternative algorithm)
    
    Difference from Leaky Bucket:
    - Leaky Bucket: Constant output rate (smooth)
    - Token Bucket: Allows bursts up to capacity
    
    Use Token Bucket when:
    - You want to allow occasional bursts
    - Example: User can make 10 requests instantly, then wait
    
    Use Leaky Bucket when:
    - You want steady, smooth rate
    - Example: Process exactly 2 requests/second, no bursts
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def _refill(self):
        """Add tokens over time"""
        now = time.time()
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def allow_request(self) -> bool:
        """Check if request allowed"""
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("LEAKY BUCKET RATE LIMITING DEMO")
    print("="*70)
    
    # Create rate limiter: 5 requests max, 1 request/second leak rate
    limiter = RateLimiter(capacity=5, leak_rate=1.0)
    
    client = "user-123"
    
    print(f"\nConfiguration:")
    print(f"  Capacity: 5 requests")
    print(f"  Leak Rate: 1 request/second")
    print(f"  Client: {client}")
    print()
    
    # Simulate 10 rapid requests
    print("Sending 10 rapid requests:")
    for i in range(1, 11):
        allowed = limiter.is_allowed(client)
        status = limiter.get_client_status(client)
        
        if allowed:
            print(f"  Request {i}: ✅ ALLOWED  | Bucket: {status['water_level']}/{status['capacity']}")
        else:
            print(f"  Request {i}: ❌ REJECTED | Bucket: {status['water_level']}/{status['capacity']} (FULL)")
    
    print("\nWaiting 3 seconds for bucket to leak...")
    time.sleep(3)
    
    status = limiter.get_client_status(client)
    print(f"After 3 seconds: Bucket level = {status['water_level']}/{status['capacity']}")
    print("(3 requests leaked out at 1 req/sec)")
    
    print("\nSending 3 more requests:")
    for i in range(11, 14):
        allowed = limiter.is_allowed(client)
        status = limiter.get_client_status(client)
        
        if allowed:
            print(f"  Request {i}: ✅ ALLOWED  | Bucket: {status['water_level']}/{status['capacity']}")
        else:
            print(f"  Request {i}: ❌ REJECTED | Bucket: {status['water_level']}/{status['capacity']}")
    
    print("\n" + "="*70)
    print("KEY TAKEAWAY:")
    print("- First 5 requests: ALLOWED (bucket has space)")
    print("- Next 5 requests: REJECTED (bucket full)")
    print("- After 3 seconds: 3 requests leaked out")
    print("- Next 3 requests: ALLOWED (space available)")
    print("="*70)

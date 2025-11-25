#!/usr/bin/env python3
"""
Load Test: 1000 Concurrent Requests
Tests horizontal and vertical scaling under high load
"""

import asyncio
import aiohttp
import time
from datetime import datetime

# Configuration
TARGET_URL = "http://localhost:8000"  # Change to ALB URL in production
CONCURRENT_REQUESTS = 1000
TOTAL_REQUESTS = 10000

async def send_request(session, request_id):
    """Send a single sensor data request"""
    payload = {
        "sensor_id": f"sensor-{request_id % 100}",
        "value": 25.5,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        start = time.time()
        async with session.post(f"{TARGET_URL}/sensors/ingest", json=payload) as response:
            duration = time.time() - start
            status = response.status
            return {
                'success': status == 200,
                'duration': duration,
                'status': status
            }
    except Exception as e:
        return {
            'success': False,
            'duration': 0,
            'error': str(e)
        }

async def run_load_test():
    """Run load test with 1000 concurrent requests"""
    
    print(f"🚀 Starting load test: {CONCURRENT_REQUESTS} concurrent requests")
    print(f"📊 Total requests: {TOTAL_REQUESTS}")
    print(f"🎯 Target: {TARGET_URL}\n")
    
    results = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'durations': []
    }
    
    connector = aiohttp.TCPConnector(limit=CONCURRENT_REQUESTS)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        start_time = time.time()
        
        # Send requests in batches
        for batch_start in range(0, TOTAL_REQUESTS, CONCURRENT_REQUESTS):
            batch_end = min(batch_start + CONCURRENT_REQUESTS, TOTAL_REQUESTS)
            batch_size = batch_end - batch_start
            
            print(f"📤 Sending batch {batch_start}-{batch_end} ({batch_size} requests)...")
            
            # Create concurrent tasks
            tasks = [
                send_request(session, i)
                for i in range(batch_start, batch_end)
            ]
            
            # Execute concurrently
            batch_results = await asyncio.gather(*tasks)
            
            # Aggregate results
            for result in batch_results:
                results['total'] += 1
                if result['success']:
                    results['success'] += 1
                    results['durations'].append(result['duration'])
                else:
                    results['failed'] += 1
            
            # Progress update
            elapsed = time.time() - start_time
            rate = results['total'] / elapsed
            print(f"   ✅ Success: {results['success']}, ❌ Failed: {results['failed']}, "
                  f"⚡ Rate: {rate:.0f} req/s\n")
    
    # Final statistics
    total_time = time.time() - start_time
    
    print("\n" + "="*70)
    print("📊 LOAD TEST RESULTS")
    print("="*70)
    print(f"Total Requests:     {results['total']}")
    print(f"Successful:         {results['success']} ({results['success']/results['total']*100:.1f}%)")
    print(f"Failed:             {results['failed']} ({results['failed']/results['total']*100:.1f}%)")
    print(f"Total Time:         {total_time:.2f}s")
    print(f"Requests/Second:    {results['total']/total_time:.0f}")
    
    if results['durations']:
        durations = sorted(results['durations'])
        print(f"\nLatency Statistics:")
        print(f"  Min:     {min(durations)*1000:.0f}ms")
        print(f"  Max:     {max(durations)*1000:.0f}ms")
        print(f"  Avg:     {sum(durations)/len(durations)*1000:.0f}ms")
        print(f"  p50:     {durations[len(durations)//2]*1000:.0f}ms")
        print(f"  p95:     {durations[int(len(durations)*0.95)]*1000:.0f}ms")
        print(f"  p99:     {durations[int(len(durations)*0.99)]*1000:.0f}ms")
    
    print("="*70)
    
    # Scaling observations
    print("\n🔍 EXPECTED SCALING BEHAVIOR:")
    print("1. Initial: 3 tasks running (min capacity)")
    print("2. At ~60% CPU: Auto-scaling triggers, adds more tasks")
    print("3. At 500 req/min per task: Request-based scaling kicks in")
    print("4. Max: 20 tasks (can handle ~20,000 concurrent requests)")
    print("\n💡 Monitor with: python3 scripts/monitor_dashboard.py")

if __name__ == '__main__':
    asyncio.run(run_load_test())

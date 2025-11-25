#!/usr/bin/env python3
"""
Load Balancer Testing Script
Tests Nginx load balancer distributing traffic across multiple FastAPI instances
"""
import asyncio
import aiohttp
import time
from collections import Counter
from datetime import datetime

# Configuration
BASE_URL = "http://localhost"
TOTAL_REQUESTS = 100
CONCURRENT_REQUESTS = 10

async def make_request(session, request_id):
    """Make a single request and return which instance handled it"""
    try:
        start_time = time.time()
        async with session.get(f"{BASE_URL}/health") as response:
            duration = time.time() - start_time
            data = await response.json()
            
            return {
                'request_id': request_id,
                'status': response.status,
                'instance': data.get('timestamp', 'unknown'),  # Each instance returns different timestamp
                'duration': duration,
                'success': True
            }
    except Exception as e:
        return {
            'request_id': request_id,
            'status': 0,
            'instance': 'error',
            'duration': 0,
            'success': False,
            'error': str(e)
        }

async def load_test():
    """Run load test with concurrent requests"""
    print("🚀 Starting Load Balancer Test")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Total Requests: {TOTAL_REQUESTS}")
    print(f"Concurrent Requests: {CONCURRENT_REQUESTS}")
    print("=" * 60)
    print()
    
    results = []
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        # Create batches of concurrent requests
        for batch_start in range(0, TOTAL_REQUESTS, CONCURRENT_REQUESTS):
            batch_end = min(batch_start + CONCURRENT_REQUESTS, TOTAL_REQUESTS)
            batch_size = batch_end - batch_start
            
            print(f"📊 Sending batch {batch_start//CONCURRENT_REQUESTS + 1} ({batch_size} requests)...", end=" ")
            
            # Create concurrent tasks
            tasks = [
                make_request(session, i) 
                for i in range(batch_start, batch_end)
            ]
            
            # Execute concurrently
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            print("✅ Done")
            
            # Small delay between batches
            await asyncio.sleep(0.1)
    
    total_time = time.time() - start_time
    
    # Analyze results
    print()
    print("=" * 60)
    print("📈 RESULTS")
    print("=" * 60)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\n✅ Successful Requests: {len(successful)}/{TOTAL_REQUESTS}")
    print(f"❌ Failed Requests: {len(failed)}/{TOTAL_REQUESTS}")
    print(f"⏱️  Total Time: {total_time:.2f}s")
    print(f"🚀 Requests/Second: {TOTAL_REQUESTS/total_time:.2f}")
    
    if successful:
        durations = [r['duration'] for r in successful]
        print(f"\n⏱️  Response Times:")
        print(f"   Average: {sum(durations)/len(durations)*1000:.2f}ms")
        print(f"   Min: {min(durations)*1000:.2f}ms")
        print(f"   Max: {max(durations)*1000:.2f}ms")
    
    # Show load distribution
    print(f"\n🔄 Load Distribution:")
    instance_counter = Counter([r['instance'] for r in successful])
    
    if len(instance_counter) > 1:
        print("   Load balancer is distributing traffic! ✅")
        for instance, count in instance_counter.most_common():
            percentage = (count / len(successful)) * 100
            bar = "█" * int(percentage / 2)
            print(f"   Instance {instance[:20]}: {count:3d} requests ({percentage:5.1f}%) {bar}")
    else:
        print("   ⚠️  All requests went to same instance (load balancer may not be running)")
    
    # Show errors if any
    if failed:
        print(f"\n❌ Errors:")
        error_counter = Counter([r.get('error', 'Unknown') for r in failed])
        for error, count in error_counter.most_common():
            print(f"   {error}: {count} times")
    
    print()
    print("=" * 60)

async def test_instance_failure():
    """Test what happens when one instance fails"""
    print("\n🧪 Testing Instance Failure Scenario")
    print("=" * 60)
    print("This test simulates what happens when one backend instance fails")
    print("Nginx should automatically route traffic to healthy instances")
    print()
    print("To test manually:")
    print("1. Run: docker stop sensor-app-1")
    print("2. Watch traffic go to app-2 and app-3 only")
    print("3. Run: docker start sensor-app-1")
    print("4. Watch traffic redistribute to all three")
    print("=" * 60)

async def quick_test():
    """Quick test to verify load balancer is working"""
    print("\n⚡ Quick Load Balancer Test")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        print("Making 10 requests to see distribution...")
        tasks = [make_request(session, i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        successful = [r for r in results if r['success']]
        instances = set([r['instance'] for r in successful])
        
        print(f"\n✅ {len(successful)}/10 requests successful")
        print(f"🔄 Requests distributed across {len(instances)} instance(s)")
        
        if len(instances) > 1:
            print("✅ Load balancer is working!")
        else:
            print("⚠️  All requests went to same instance")
            print("   Make sure docker-compose.loadbalancer.yml is running")

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        asyncio.run(quick_test())
    elif len(sys.argv) > 1 and sys.argv[1] == "failure":
        asyncio.run(test_instance_failure())
    else:
        asyncio.run(load_test())

if __name__ == "__main__":
    main()

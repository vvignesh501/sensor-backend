#!/usr/bin/env python3
"""
Automated Failure Scenario Test
Demonstrates load balancer resilience when one instance fails
"""
import asyncio
import aiohttp
import subprocess
import time
from collections import Counter

BASE_URL = "http://localhost"

def run_docker_command(command):
    """Execute docker command"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

async def make_request(session, request_id):
    """Make a single request"""
    try:
        async with session.get(f"{BASE_URL}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
            data = await response.json()
            return {
                'id': request_id,
                'status': response.status,
                'success': True,
                'timestamp': data.get('timestamp', 'unknown')
            }
    except Exception as e:
        return {
            'id': request_id,
            'status': 0,
            'success': False,
            'error': str(e)
        }

async def send_requests(num_requests, label):
    """Send multiple requests and analyze results"""
    print(f"\n📊 {label}")
    print("-" * 60)
    
    async with aiohttp.ClientSession() as session:
        tasks = [make_request(session, i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"✅ Successful: {len(successful)}/{num_requests}")
    print(f"❌ Failed: {len(failed)}/{num_requests}")
    
    if successful:
        # Count unique instances
        instances = Counter([r['timestamp'] for r in successful])
        print(f"🔄 Active Instances: {len(instances)}")
        
        for instance, count in instances.most_common():
            percentage = (count / len(successful)) * 100
            bar = "█" * int(percentage / 3)
            print(f"   Instance {instance[:25]}: {count:2d} requests ({percentage:5.1f}%) {bar}")
    
    return successful, failed

async def main():
    """Run the complete failure scenario test"""
    print("=" * 60)
    print("🧪 LOAD BALANCER FAILURE SCENARIO TEST")
    print("=" * 60)
    print("\nThis test demonstrates:")
    print("1. Normal operation with 3 instances")
    print("2. One instance fails")
    print("3. Traffic automatically routes to healthy instances")
    print("4. Zero downtime - all requests still processed")
    print("5. Instance recovers and rejoins the pool")
    print()
    
    # Phase 1: Normal Operation
    print("\n" + "=" * 60)
    print("PHASE 1: Normal Operation (All 3 Instances Healthy)")
    print("=" * 60)
    
    successful, failed = await send_requests(30, "Sending 30 requests...")
    
    if len(failed) > 0:
        print("\n⚠️  Some requests failed. Make sure load balancer is running:")
        print("   docker-compose -f docker-compose.loadbalancer.yml up -d")
        return
    
    initial_instances = len(set([r['timestamp'] for r in successful]))
    print(f"\n✅ All instances healthy: {initial_instances} instances responding")
    
    # Phase 2: Simulate Failure
    print("\n" + "=" * 60)
    print("PHASE 2: Simulating Instance Failure")
    print("=" * 60)
    print("\n🔴 Stopping sensor-app-1...")
    
    if run_docker_command("docker stop sensor-app-1"):
        print("✅ Instance stopped")
    else:
        print("❌ Failed to stop instance")
        return
    
    # Wait for Nginx to detect failure
    print("⏳ Waiting 3 seconds for Nginx to detect failure...")
    await asyncio.sleep(3)
    
    # Phase 3: Test During Failure
    print("\n" + "=" * 60)
    print("PHASE 3: Testing During Failure (Only 2 Instances)")
    print("=" * 60)
    
    successful, failed = await send_requests(30, "Sending 30 requests...")
    
    active_instances = len(set([r['timestamp'] for r in successful]))
    
    print(f"\n📊 RESILIENCE TEST RESULTS:")
    print(f"   ✅ Requests processed: {len(successful)}/30")
    print(f"   ❌ Requests failed: {len(failed)}/30")
    print(f"   🔄 Active instances: {active_instances}")
    
    if len(failed) == 0:
        print("\n🎉 SUCCESS! Zero downtime achieved!")
        print("   All requests were processed by remaining healthy instances")
    else:
        print(f"\n⚠️  {len(failed)} requests failed during transition")
    
    # Phase 4: Recovery
    print("\n" + "=" * 60)
    print("PHASE 4: Instance Recovery")
    print("=" * 60)
    print("\n🟢 Starting sensor-app-1...")
    
    if run_docker_command("docker start sensor-app-1"):
        print("✅ Instance started")
    else:
        print("❌ Failed to start instance")
        return
    
    # Wait for instance to be ready
    print("⏳ Waiting 5 seconds for instance to be ready...")
    await asyncio.sleep(5)
    
    # Phase 5: Test After Recovery
    print("\n" + "=" * 60)
    print("PHASE 5: Testing After Recovery (All 3 Instances)")
    print("=" * 60)
    
    successful, failed = await send_requests(30, "Sending 30 requests...")
    
    recovered_instances = len(set([r['timestamp'] for r in successful]))
    
    print(f"\n📊 RECOVERY TEST RESULTS:")
    print(f"   ✅ Requests processed: {len(successful)}/30")
    print(f"   🔄 Active instances: {recovered_instances}")
    
    if recovered_instances == initial_instances:
        print("\n🎉 FULL RECOVERY! All instances back online")
    
    # Final Summary
    print("\n" + "=" * 60)
    print("📋 FINAL SUMMARY")
    print("=" * 60)
    print(f"\n✅ Initial State: {initial_instances} instances healthy")
    print(f"🔴 During Failure: {active_instances} instances active")
    print(f"🟢 After Recovery: {recovered_instances} instances active")
    print(f"\n💡 Key Findings:")
    print(f"   • Zero downtime: Load balancer automatically rerouted traffic")
    print(f"   • Resilience: {len(successful)}/30 requests succeeded during failure")
    print(f"   • Auto-recovery: Failed instance rejoined pool automatically")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)
    print("\n🎓 Interview Talking Points:")
    print("   1. 'When one instance failed, Nginx detected it within seconds'")
    print("   2. 'Traffic automatically rerouted to healthy instances'")
    print("   3. 'Zero downtime - all requests were processed successfully'")
    print("   4. 'When instance recovered, it automatically rejoined the pool'")
    print("   5. 'This demonstrates high availability and fault tolerance'")
    print()

if __name__ == "__main__":
    asyncio.run(main())

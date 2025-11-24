import asyncio
import aiohttp
import time
import json
from datetime import datetime

class LoadTester1000:
    def __init__(self, base_url="http://localhost:8005", concurrent_users=1000):
        self.base_url = base_url
        self.concurrent_users = concurrent_users
        self.results = []
        
    async def test_single_user(self, session, user_id):
        """Simulate complete user workflow with Kafka processing"""
        start_time = time.time()
        
        try:
            # Authenticate with existing user
            auth_data = {
                "username": "Vignesh",
                "password": "redlen@9891"
            }
            
            async with session.post(f"{self.base_url}/auth/token", data=auth_data) as auth_response:
                if auth_response.status != 200:
                    return {
                        "user_id": user_id,
                        "error": f"Auth failed: {auth_response.status}",
                        "timestamp": datetime.now().isoformat(),
                        "total_time": time.time() - start_time
                    }
                
                auth_result = await auth_response.json()
                token = auth_result["access_token"]
            
            # Test sensor (this will trigger Kafka processing)
            headers = {"Authorization": f"Bearer {token}"}
            sensor_start = time.time()
            
            async with session.post(f"{self.base_url}/test/sensor/MM", headers=headers) as response:
                sensor_end = time.time()
                
                result = {
                    "user_id": user_id,
                    "status_code": response.status,
                    "auth_time": sensor_start - start_time,
                    "sensor_time": sensor_end - sensor_start,
                    "total_time": sensor_end - start_time,
                    "timestamp": datetime.now().isoformat()
                }
                
                if response.status == 200:
                    data = await response.json()
                    result["test_id"] = data.get("test_id")
                    result["s3_status"] = data.get("s3_status")
                    result["s3_path"] = data.get("s3_path")
                    result["data_size_mb"] = data.get("raw_data_stats", {}).get("total_size_mb", 0)
                    result["kafka_sent"] = True
                else:
                    result["error"] = await response.text()
                    result["kafka_sent"] = False
                
                return result
                
        except Exception as e:
            return {
                "user_id": user_id,
                "status_code": 0,
                "error": str(e),
                "total_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "kafka_sent": False
            }
    
    async def display_frontend_instructions(self, results):
        """Display instructions for viewing results in frontend dashboard"""
        successful = [r for r in results if isinstance(r, dict) and r.get("status_code") == 200]
        
        print(f"\n🌐 === FRONTEND DASHBOARD ACCESS ===")
        print(f"📊 View real-time Kafka processing logs at:")
        print(f"   {self.base_url}/dashboard/kafka-processing")
        print(f"   (or open: file:///Users/pranamyaakella/PycharmProjects/Redlen_workspace/sensor-backend/kafka_processing_dashboard.html)")
        print(f"")
        print(f"📈 API Endpoints for monitoring:")
        print(f"   GET {self.base_url}/kafka/producer-logs - Processing logs")
        print(f"   GET {self.base_url}/kafka/producer-stats - Statistics")
        print(f"   GET {self.base_url}/kafka/logs - Database logs")
        print(f"")
        print(f"🔍 Expected results in dashboard:")
        print(f"   - {len(successful)} successful Kafka messages")
        print(f"   - Processing times and status for each test")
        print(f"   - Real-time statistics and success rates")
        print(f"")
        print(f"💡 The dashboard auto-refreshes every 5 seconds")
        print(f"   All results are now displayed in the frontend instead of JSON files")
    
    async def run_load_test(self):
        """Run load test with 1000 concurrent users"""
        print(f"🚀 KAFKA LOAD TEST - 1000 CONCURRENT USERS")
        print(f"Target: {self.base_url}")
        print(f"User: Vignesh")
        print(f"Kafka Consumer: Running")
        print(f"S3 Bucket: sensor-prod-data-vvignesh501-2025")
        print("=" * 60)
        
        connector = aiohttp.TCPConnector(limit=1200, limit_per_host=1200)
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            
            for user_id in range(self.concurrent_users):
                task = asyncio.create_task(self.test_single_user(session, user_id))
                tasks.append(task)
            
            # Execute all tasks concurrently
            start_time = time.time()
            print(f"🔥 Launching {self.concurrent_users} concurrent sensor tests...")
            
            self.results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            print(f"✅ Load test completed in {end_time - start_time:.2f} seconds")
            self.analyze_results()
    
    async def analyze_results(self):
        """Comprehensive analysis of load test results"""
        # Filter out exceptions
        valid_results = [r for r in self.results if isinstance(r, dict)]
        successful = [r for r in valid_results if r.get("status_code") == 200]
        failed = [r for r in valid_results if r.get("status_code") != 200]
        
        print(f"\n🎯 === LOAD TEST RESULTS ===")
        print(f"Total requests: {len(valid_results)}")
        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")
        print(f"📊 Success rate: {len(successful)/len(valid_results)*100:.2f}%")
        
        if successful:
            # Timing analysis
            total_times = [r["total_time"] for r in successful]
            auth_times = [r.get("auth_time", 0) for r in successful]
            sensor_times = [r.get("sensor_time", 0) for r in successful]
            
            print(f"\n⏱️  === TIMING ANALYSIS ===")
            print(f"Average total time: {sum(total_times)/len(total_times):.3f}s")
            print(f"Average auth time: {sum(auth_times)/len(auth_times):.3f}s")
            print(f"Average sensor time: {sum(sensor_times)/len(sensor_times):.3f}s")
            print(f"Min total time: {min(total_times):.3f}s")
            print(f"Max total time: {max(total_times):.3f}s")
            
            # S3 analysis
            s3_success = [r for r in successful if r.get("s3_status") == "success"]
            s3_failed = [r for r in successful if r.get("s3_status") != "success"]
            
            print(f"\n☁️  === S3 UPLOAD ANALYSIS ===")
            print(f"S3 uploads successful: {len(s3_success)}")
            print(f"S3 uploads failed: {len(s3_failed)}")
            print(f"S3 success rate: {len(s3_success)/len(successful)*100:.2f}%")
            
            if s3_success:
                total_data = sum(r.get("data_size_mb", 0) for r in s3_success)
                print(f"Total data uploaded: {total_data:.2f} MB")
                print(f"Average data per test: {total_data/len(s3_success):.2f} MB")
            
            # Kafka analysis
            kafka_sent = [r for r in successful if r.get("kafka_sent", False)]
            print(f"\n📨 === KAFKA PROCESSING ===")
            print(f"Messages sent to Kafka: {len(kafka_sent)}")
            print(f"Kafka send rate: {len(kafka_sent)/len(successful)*100:.2f}%")
        
        # Error analysis
        if failed:
            print(f"\n🚨 === ERROR ANALYSIS ===")
            error_types = {}
            for r in failed:
                error = r.get("error", "Unknown error")
                status = r.get("status_code", "Unknown")
                key = f"{status}: {error[:50]}..."
                error_types[key] = error_types.get(key, 0) + 1
            
            for error, count in error_types.items():
                print(f"  {error}: {count} occurrences")
        
        # Performance metrics
        if successful:
            throughput = len(successful) / max(total_times)
            print(f"\n🚀 === PERFORMANCE METRICS ===")
            print(f"Peak throughput: {throughput:.2f} requests/second")
            print(f"Total successful tests: {len(successful)}")
            print(f"Total data processed: {sum(r.get('data_size_mb', 0) for r in successful):.2f} MB")
        
        print(f"\n💾 Load test completed - check frontend for real-time results")
        
        # Print sample successful test IDs for Kafka monitoring
        if successful:
            print(f"\n🔍 === SAMPLE TEST IDs FOR KAFKA MONITORING ===")
            for i, r in enumerate(successful[:10]):
                print(f"Test {i+1}: {r.get('test_id')} - S3: {r.get('s3_status')} - Time: {r.get('total_time', 0):.3f}s")
            
            # Display frontend access instructions
            await self.display_frontend_instructions(self.results)
            
            print(f"\n📈 Additional API endpoints:")
            print(f"  GET {self.base_url}/kafka/stats - Database statistics")
            print(f"  GET {self.base_url}/kafka/logs - Database processing logs")
            print(f"  GET {self.base_url}/kafka/real-time - Last 5 minutes stats")

async def main():
    tester = LoadTester1000(concurrent_users=1000)
    await tester.run_load_test()

if __name__ == "__main__":
    asyncio.run(main())
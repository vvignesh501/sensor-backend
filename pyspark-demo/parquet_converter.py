"""
Parquet Conversion Demo - Compare JSON vs Parquet storage
"""
import json
import os
import time
from datetime import datetime, timedelta
import random
import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from typing import Dict, List

class ParquetDemo:
    def __init__(self, bucket_name: str, region: str = 'us-east-1'):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', region_name=region)
        self.results = {}
        
    def generate_sensor_data(self, num_records: int = 100) -> List[Dict]:
        """Generate realistic sensor data"""
        data = []
        base_time = datetime.now() - timedelta(hours=1)
        
        for i in range(num_records):
            record = {
                'sensor_id': f'SENSOR_{random.randint(1000, 9999)}',
                'timestamp': (base_time + timedelta(seconds=i*36)).isoformat(),
                'temperature': round(random.uniform(15.0, 35.0), 2),
                'humidity': round(random.uniform(30.0, 80.0), 2),
                'pressure': round(random.uniform(980.0, 1020.0), 2),
                'location': random.choice(['Building_A', 'Building_B', 'Building_C']),
                'status': random.choice(['active', 'active', 'active', 'warning']),
                'battery_level': round(random.uniform(20.0, 100.0), 1),
                'signal_strength': random.randint(-90, -30),
                'firmware_version': f'v{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,20)}',
                'metadata': {
                    'device_type': 'IoT_Sensor_Pro',
                    'manufacturer': 'SensorCorp',
                    'installation_date': '2024-01-15',
                    'calibration_date': '2024-11-01'
                }
            }
            data.append(record)
        
        return data
    
    def save_as_json(self, data: List[Dict], filename: str) -> int:
        """Save data as JSON and upload to S3"""
        json_path = f'/app/data/{filename}.json'
        
        # Write JSON file
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Get file size
        json_size = os.path.getsize(json_path)
        
        # Upload to S3
        s3_key = f'json/{filename}.json'
        self.s3_client.upload_file(json_path, self.bucket_name, s3_key)
        
        print(f"✓ JSON uploaded: s3://{self.bucket_name}/{s3_key}")
        print(f"  Size: {json_size:,} bytes ({json_size/1024:.2f} KB)")
        
        return json_size
    
    def save_as_parquet(self, data: List[Dict], filename: str) -> int:
        """Save data as Parquet and upload to S3"""
        parquet_path = f'/app/data/{filename}.parquet'
        
        # Flatten metadata for Parquet
        flattened_data = []
        for record in data:
            flat_record = {k: v for k, v in record.items() if k != 'metadata'}
            if 'metadata' in record:
                for mk, mv in record['metadata'].items():
                    flat_record[f'metadata_{mk}'] = mv
            flattened_data.append(flat_record)
        
        # Convert to DataFrame
        df = pd.DataFrame(flattened_data)
        
        # Write Parquet with compression
        df.to_parquet(
            parquet_path,
            engine='pyarrow',
            compression='snappy',
            index=False
        )
        
        # Get file size
        parquet_size = os.path.getsize(parquet_path)
        
        # Upload to S3
        s3_key = f'parquet/{filename}.parquet'
        self.s3_client.upload_file(parquet_path, self.bucket_name, s3_key)
        
        print(f"✓ Parquet uploaded: s3://{self.bucket_name}/{s3_key}")
        print(f"  Size: {parquet_size:,} bytes ({parquet_size/1024:.2f} KB)")
        
        return parquet_size
    
    def benchmark_read_performance(self, filename: str) -> Dict:
        """Compare read performance between JSON and Parquet"""
        results = {}
        
        # Benchmark JSON read from S3
        print("\n📊 Benchmarking JSON read...")
        json_key = f'json/{filename}.json'
        start = time.time()
        json_obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=json_key)
        json_data = json.loads(json_obj['Body'].read())
        json_df = pd.DataFrame(json_data)
        json_time = time.time() - start
        results['json_read_time'] = json_time
        print(f"  JSON read time: {json_time*1000:.2f}ms")
        
        # Benchmark Parquet read from S3
        print("\n📊 Benchmarking Parquet read...")
        parquet_key = f'parquet/{filename}.parquet'
        parquet_s3_path = f's3://{self.bucket_name}/{parquet_key}'
        start = time.time()
        parquet_df = pd.read_parquet(parquet_s3_path)
        parquet_time = time.time() - start
        results['parquet_read_time'] = parquet_time
        print(f"  Parquet read time: {parquet_time*1000:.2f}ms")
        
        # Calculate speedup
        speedup = json_time / parquet_time
        results['speedup'] = speedup
        print(f"\n⚡ Parquet is {speedup:.2f}x faster for reading!")
        
        return results
    
    def run_demo(self, num_records: int = 100):
        """Run complete demo"""
        print("=" * 70)
        print("🚀 PARQUET VS JSON STORAGE DEMO")
        print("=" * 70)
        
        # Generate data
        print(f"\n📝 Generating {num_records} sensor records...")
        data = self.generate_sensor_data(num_records)
        print(f"✓ Generated {len(data)} records")
        
        # Save as JSON
        print("\n" + "=" * 70)
        print("💾 SAVING AS JSON")
        print("=" * 70)
        json_size = self.save_as_json(data, 'sensor_data')
        
        # Save as Parquet
        print("\n" + "=" * 70)
        print("💾 SAVING AS PARQUET")
        print("=" * 70)
        parquet_size = self.save_as_parquet(data, 'sensor_data')
        
        # Calculate savings
        print("\n" + "=" * 70)
        print("📊 STORAGE COMPARISON")
        print("=" * 70)
        savings_bytes = json_size - parquet_size
        savings_percent = (savings_bytes / json_size) * 100
        compression_ratio = json_size / parquet_size
        
        print(f"\nJSON Size:     {json_size:,} bytes ({json_size/1024:.2f} KB)")
        print(f"Parquet Size:  {parquet_size:,} bytes ({parquet_size/1024:.2f} KB)")
        print(f"\n💰 Storage Saved: {savings_bytes:,} bytes ({savings_bytes/1024:.2f} KB)")
        print(f"📉 Reduction: {savings_percent:.1f}%")
        print(f"🗜️  Compression Ratio: {compression_ratio:.2f}x")
        
        # Benchmark performance
        print("\n" + "=" * 70)
        print("⚡ PERFORMANCE COMPARISON")
        print("=" * 70)
        perf_results = self.benchmark_read_performance('sensor_data')
        
        # Store results
        self.results = {
            'num_records': num_records,
            'json_size': json_size,
            'parquet_size': parquet_size,
            'savings_bytes': savings_bytes,
            'savings_percent': savings_percent,
            'compression_ratio': compression_ratio,
            **perf_results
        }
        
        print("\n" + "=" * 70)
        print("✅ DEMO COMPLETE")
        print("=" * 70)
        
        return self.results

if __name__ == '__main__':
    # Configuration
    BUCKET_NAME = os.getenv('S3_BUCKET', 'sensor-data-demo')
    REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # Run demo
    demo = ParquetDemo(BUCKET_NAME, REGION)
    results = demo.run_demo(num_records=100)
    
    # Save results
    with open('/app/data/comparison_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to /app/data/comparison_results.json")

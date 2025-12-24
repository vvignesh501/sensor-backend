"""
Local Parquet Demo - No S3 required
"""
import json
import os
import time
from datetime import datetime, timedelta
import random
import pandas as pd
from typing import Dict, List

class LocalParquetDemo:
    def __init__(self):
        self.data_dir = '/app/data' if os.path.exists('/app') else './data'
        os.makedirs(self.data_dir, exist_ok=True)
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
                'device_type': 'IoT_Sensor_Pro',
                'manufacturer': 'SensorCorp',
            }
            data.append(record)
        
        return data
    
    def save_as_json(self, data: List[Dict], filename: str) -> int:
        """Save data as JSON"""
        json_path = f'{self.data_dir}/{filename}.json'
        
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        json_size = os.path.getsize(json_path)
        print(f"✓ JSON saved: {json_path}")
        print(f"  Size: {json_size:,} bytes ({json_size/1024:.2f} KB)")
        
        return json_size
    
    def save_as_parquet(self, data: List[Dict], filename: str) -> int:
        """Save data as Parquet"""
        parquet_path = f'{self.data_dir}/{filename}.parquet'
        
        df = pd.DataFrame(data)
        df.to_parquet(
            parquet_path,
            engine='pyarrow',
            compression='snappy',
            index=False
        )
        
        parquet_size = os.path.getsize(parquet_path)
        print(f"✓ Parquet saved: {parquet_path}")
        print(f"  Size: {parquet_size:,} bytes ({parquet_size/1024:.2f} KB)")
        
        return parquet_size
    
    def benchmark_read_performance(self, filename: str) -> Dict:
        """Compare read performance"""
        results = {}
        
        # JSON read
        print("\n📊 Benchmarking JSON read...")
        json_path = f'{self.data_dir}/{filename}.json'
        start = time.time()
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        json_df = pd.DataFrame(json_data)
        json_time = time.time() - start
        results['json_read_time'] = json_time
        print(f"  JSON read time: {json_time*1000:.2f}ms")
        
        # Parquet read
        print("\n📊 Benchmarking Parquet read...")
        parquet_path = f'{self.data_dir}/{filename}.parquet'
        start = time.time()
        parquet_df = pd.read_parquet(parquet_path)
        parquet_time = time.time() - start
        results['parquet_read_time'] = parquet_time
        print(f"  Parquet read time: {parquet_time*1000:.2f}ms")
        
        speedup = json_time / parquet_time if parquet_time > 0 else 0
        results['speedup'] = speedup
        print(f"\n⚡ Parquet is {speedup:.2f}x faster for reading!")
        
        return results
    
    def run_demo(self, num_records: int = 100):
        """Run complete demo"""
        print("=" * 70)
        print("🚀 PARQUET VS JSON STORAGE DEMO (LOCAL)")
        print("=" * 70)
        
        print(f"\n📝 Generating {num_records} sensor records...")
        data = self.generate_sensor_data(num_records)
        print(f"✓ Generated {len(data)} records")
        
        print("\n" + "=" * 70)
        print("💾 SAVING AS JSON")
        print("=" * 70)
        json_size = self.save_as_json(data, 'sensor_data')
        
        print("\n" + "=" * 70)
        print("💾 SAVING AS PARQUET")
        print("=" * 70)
        parquet_size = self.save_as_parquet(data, 'sensor_data')
        
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
        
        print("\n" + "=" * 70)
        print("⚡ PERFORMANCE COMPARISON")
        print("=" * 70)
        perf_results = self.benchmark_read_performance('sensor_data')
        
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
        
        # Save results
        results_path = f'{self.data_dir}/comparison_results.json'
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Results saved to {results_path}")
        
        return self.results

if __name__ == '__main__':
    demo = LocalParquetDemo()
    results = demo.run_demo(num_records=100)

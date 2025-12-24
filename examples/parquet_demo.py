#!/usr/bin/env python3
"""
Parquet Format Demo
Shows JSON vs Parquet comparison with real sensor data
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
import random

# Create sample sensor data
def generate_sensor_data(num_records=10000):
    """Generate sample IoT sensor data"""
    data = []
    start_date = datetime(2024, 1, 1)
    
    sensor_types = ['temperature', 'humidity', 'pressure', 'motion', 'light']
    locations = ['warehouse-1', 'warehouse-2', 'factory-floor', 'office-a', 'office-b']
    
    for i in range(num_records):
        timestamp = start_date + timedelta(minutes=i)
        data.append({
            'sensor_id': f'sensor-{random.randint(1, 100):03d}',
            'sensor_type': random.choice(sensor_types),
            'location': random.choice(locations),
            'timestamp': timestamp.isoformat(),
            'value': round(random.uniform(15.0, 35.0), 2),
            'unit': '°C' if random.choice(sensor_types) == 'temperature' else '%',
            'battery_level': random.randint(20, 100),
            'signal_strength': random.randint(-90, -30),
            'firmware_version': f'v{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}',
            'status': random.choice(['active', 'active', 'active', 'warning', 'error']),
            'metadata': {
                'device_model': f'IoT-{random.randint(100, 999)}',
                'manufacturer': random.choice(['Acme', 'TechCorp', 'SensorPro']),
                'installation_date': '2023-06-15'
            }
        })
    
    return data


def main():
    print("=" * 70)
    print("📊 Parquet Format Demo - JSON vs Parquet Comparison")
    print("=" * 70)
    print()
    
    # Generate data
    print("🔄 Generating 10,000 sensor records...")
    sensor_data = generate_sensor_data(10000)
    df = pd.DataFrame(sensor_data)
    
    # Flatten nested metadata for better Parquet performance
    df['device_model'] = df['metadata'].apply(lambda x: x['device_model'])
    df['manufacturer'] = df['metadata'].apply(lambda x: x['manufacturer'])
    df['installation_date'] = df['metadata'].apply(lambda x: x['installation_date'])
    df = df.drop('metadata', axis=1)
    
    print(f"✓ Generated {len(df)} records")
    print()
    
    # Create output directory
    os.makedirs('data', exist_ok=True)
    
    # Save as JSON
    print("💾 Saving as JSON...")
    json_file = 'data/sensor_data.json'
    df.to_json(json_file, orient='records', indent=2)
    json_size = os.path.getsize(json_file)
    print(f"✓ JSON file: {json_file}")
    print(f"  Size: {json_size:,} bytes ({json_size / 1024 / 1024:.2f} MB)")
    print()
    
    # Save as Parquet (Snappy compression)
    print("💾 Saving as Parquet (Snappy compression)...")
    parquet_file = 'data/sensor_data.parquet'
    df.to_parquet(
        parquet_file,
        engine='pyarrow',
        compression='snappy',
        index=False
    )
    parquet_size = os.path.getsize(parquet_file)
    print(f"✓ Parquet file: {parquet_file}")
    print(f"  Size: {parquet_size:,} bytes ({parquet_size / 1024 / 1024:.2f} MB)")
    print()
    
    # Save as Parquet (GZIP compression - better compression, slower)
    print("💾 Saving as Parquet (GZIP compression)...")
    parquet_gzip_file = 'data/sensor_data_gzip.parquet'
    df.to_parquet(
        parquet_gzip_file,
        engine='pyarrow',
        compression='gzip',
        index=False
    )
    parquet_gzip_size = os.path.getsize(parquet_gzip_file)
    print(f"✓ Parquet file (GZIP): {parquet_gzip_file}")
    print(f"  Size: {parquet_gzip_size:,} bytes ({parquet_gzip_size / 1024 / 1024:.2f} MB)")
    print()
    
    # Comparison
    print("=" * 70)
    print("📈 COMPARISON RESULTS")
    print("=" * 70)
    print()
    
    compression_ratio_snappy = ((json_size - parquet_size) / json_size) * 100
    compression_ratio_gzip = ((json_size - parquet_gzip_size) / json_size) * 100
    
    print(f"Format              Size (MB)    Compression    Read Speed    Use Case")
    print("-" * 70)
    print(f"JSON                {json_size/1024/1024:>8.2f}    Baseline       Slow          Human-readable")
    print(f"Parquet (Snappy)    {parquet_size/1024/1024:>8.2f}    {compression_ratio_snappy:>5.1f}%         Fast          Production")
    print(f"Parquet (GZIP)      {parquet_gzip_size/1024/1024:>8.2f}    {compression_ratio_gzip:>5.1f}%         Medium        Archival")
    print()
    
    # Cost savings
    print("💰 COST SAVINGS (AWS S3 Standard - $0.023/GB/month)")
    print("-" * 70)
    monthly_json_cost = (json_size / 1024 / 1024 / 1024) * 0.023 * 30  # 30 days
    monthly_parquet_cost = (parquet_size / 1024 / 1024 / 1024) * 0.023 * 30
    savings = monthly_json_cost - monthly_parquet_cost
    
    print(f"JSON storage cost:     ${monthly_json_cost:.4f}/month")
    print(f"Parquet storage cost:  ${monthly_parquet_cost:.4f}/month")
    print(f"Savings:               ${savings:.4f}/month ({compression_ratio_snappy:.1f}%)")
    print()
    
    # Query performance demo
    print("=" * 70)
    print("⚡ QUERY PERFORMANCE DEMO")
    print("=" * 70)
    print()
    
    import time
    
    # Query 1: Read all data
    print("Query 1: Read all data")
    print("-" * 70)
    
    start = time.time()
    df_json = pd.read_json(json_file)
    json_time = time.time() - start
    print(f"JSON:    {json_time:.4f} seconds")
    
    start = time.time()
    df_parquet = pd.read_parquet(parquet_file)
    parquet_time = time.time() - start
    print(f"Parquet: {parquet_time:.4f} seconds ({json_time/parquet_time:.1f}x faster)")
    print()
    
    # Query 2: Read specific columns only
    print("Query 2: Read only 2 columns (sensor_id, value)")
    print("-" * 70)
    
    start = time.time()
    df_json = pd.read_json(json_file)[['sensor_id', 'value']]
    json_time = time.time() - start
    print(f"JSON:    {json_time:.4f} seconds (must read entire file)")
    
    start = time.time()
    df_parquet = pd.read_parquet(parquet_file, columns=['sensor_id', 'value'])
    parquet_time = time.time() - start
    print(f"Parquet: {parquet_time:.4f} seconds ({json_time/parquet_time:.1f}x faster)")
    print(f"         ✓ Columnar format reads only needed columns!")
    print()
    
    # Query 3: Filter data
    print("Query 3: Filter data (temperature > 25)")
    print("-" * 70)
    
    start = time.time()
    df_json = pd.read_json(json_file)
    df_filtered = df_json[df_json['value'] > 25]
    json_time = time.time() - start
    print(f"JSON:    {json_time:.4f} seconds")
    
    start = time.time()
    df_parquet = pd.read_parquet(
        parquet_file,
        filters=[('value', '>', 25)]
    )
    parquet_time = time.time() - start
    print(f"Parquet: {parquet_time:.4f} seconds ({json_time/parquet_time:.1f}x faster)")
    print(f"         ✓ Predicate pushdown skips irrelevant data!")
    print()
    
    # Show sample data
    print("=" * 70)
    print("📋 SAMPLE DATA (First 5 records)")
    print("=" * 70)
    print()
    print(df.head())
    print()
    
    # Show schema
    print("=" * 70)
    print("📐 PARQUET SCHEMA")
    print("=" * 70)
    print()
    
    import pyarrow.parquet as pq
    parquet_file_obj = pq.ParquetFile(parquet_file)
    print(parquet_file_obj.schema)
    print()
    
    # Show metadata
    print("=" * 70)
    print("📊 PARQUET METADATA")
    print("=" * 70)
    print()
    print(f"Number of row groups: {parquet_file_obj.num_row_groups}")
    print(f"Number of columns:    {len(parquet_file_obj.schema)}")
    print(f"Total rows:           {parquet_file_obj.metadata.num_rows:,}")
    print()
    
    # Show statistics
    print("Column Statistics (for predicate pushdown):")
    print("-" * 70)
    for i in range(min(3, len(parquet_file_obj.schema))):
        col_name = parquet_file_obj.schema[i].name
        row_group = parquet_file_obj.metadata.row_group(0)
        col_meta = row_group.column(i)
        if col_meta.statistics:
            print(f"{col_name}:")
            print(f"  Min: {col_meta.statistics.min}")
            print(f"  Max: {col_meta.statistics.max}")
            print(f"  Null count: {col_meta.statistics.null_count}")
    print()
    
    print("=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70)
    print()
    print("📁 Files created:")
    print(f"  - {json_file}")
    print(f"  - {parquet_file}")
    print(f"  - {parquet_gzip_file}")
    print()
    print("💡 Key Takeaways:")
    print(f"  ✓ {compression_ratio_snappy:.0f}% smaller file size")
    print(f"  ✓ {json_time/parquet_time:.0f}x faster queries")
    print("  ✓ Columnar format reads only needed columns")
    print("  ✓ Predicate pushdown skips irrelevant data")
    print("  ✓ Built-in compression (Snappy/GZIP)")
    print("  ✓ Schema evolution support")
    print()


if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print("❌ Missing dependencies!")
        print()
        print("Install required packages:")
        print("  pip install pandas pyarrow")
        print()
        print(f"Error: {e}")

"""
PySpark Data Processor - Real-time analytics on Parquet data
"""
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, avg, max, min, count, window, 
    current_timestamp, to_timestamp, desc
)
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
import time

class PySparkProcessor:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.spark = self._create_spark_session()
        
    def _create_spark_session(self) -> SparkSession:
        """Create Spark session with S3 support"""
        spark = SparkSession.builder \
            .appName("SensorDataAnalytics") \
            .config("spark.jars.packages", 
                   "org.apache.hadoop:hadoop-aws:3.3.4,"
                   "com.amazonaws:aws-java-sdk-bundle:1.12.262") \
            .config("spark.hadoop.fs.s3a.impl", 
                   "org.apache.hadoop.fs.s3a.S3AFileSystem") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("WARN")
        return spark
    
    def load_parquet_data(self):
        """Load Parquet data from S3"""
        s3_path = f"s3a://{self.bucket_name}/parquet/sensor_data.parquet"
        print(f"📂 Loading data from {s3_path}")
        
        start = time.time()
        df = self.spark.read.parquet(s3_path)
        load_time = time.time() - start
        
        print(f"✓ Loaded {df.count()} records in {load_time*1000:.2f}ms")
        return df, load_time
    
    def analyze_sensor_metrics(self, df):
        """Perform real-time analytics"""
        print("\n📊 Computing analytics...")
        
        start = time.time()
        
        # Overall statistics
        stats = df.select(
            avg('temperature').alias('avg_temp'),
            max('temperature').alias('max_temp'),
            min('temperature').alias('min_temp'),
            avg('humidity').alias('avg_humidity'),
            avg('pressure').alias('avg_pressure'),
            avg('battery_level').alias('avg_battery')
        ).collect()[0]
        
        # Location-based aggregation
        location_stats = df.groupBy('location').agg(
            count('*').alias('sensor_count'),
            avg('temperature').alias('avg_temp'),
            avg('humidity').alias('avg_humidity')
        ).orderBy(desc('sensor_count')).collect()
        
        # Status distribution
        status_dist = df.groupBy('status').agg(
            count('*').alias('count')
        ).collect()
        
        # Low battery sensors
        low_battery = df.filter(col('battery_level') < 30).select(
            'sensor_id', 'battery_level', 'location'
        ).orderBy('battery_level').collect()
        
        analysis_time = time.time() - start
        
        results = {
            'overall_stats': stats.asDict(),
            'location_stats': [row.asDict() for row in location_stats],
            'status_distribution': [row.asDict() for row in status_dist],
            'low_battery_sensors': [row.asDict() for row in low_battery],
            'analysis_time': analysis_time
        }
        
        print(f"✓ Analysis completed in {analysis_time*1000:.2f}ms")
        
        return results
    
    def get_realtime_dashboard_data(self):
        """Get all data needed for dashboard"""
        print("\n" + "="*70)
        print("⚡ PYSPARK REAL-TIME ANALYTICS")
        print("="*70)
        
        # Load data
        df, load_time = self.load_parquet_data()
        
        # Analyze
        analysis = self.analyze_sensor_metrics(df)
        
        # Total time
        total_time = load_time + analysis['analysis_time']
        
        print("\n" + "="*70)
        print("📈 DASHBOARD DATA READY")
        print("="*70)
        print(f"Total processing time: {total_time*1000:.2f}ms")
        print(f"Records processed: {df.count()}")
        
        return {
            'dataframe': df,
            'analysis': analysis,
            'performance': {
                'load_time': load_time,
                'analysis_time': analysis['analysis_time'],
                'total_time': total_time
            }
        }
    
    def stop(self):
        """Stop Spark session"""
        self.spark.stop()

if __name__ == '__main__':
    BUCKET_NAME = os.getenv('S3_BUCKET', 'sensor-data-demo')
    
    processor = PySparkProcessor(BUCKET_NAME)
    try:
        results = processor.get_realtime_dashboard_data()
        
        # Print summary
        print("\n📊 ANALYSIS SUMMARY:")
        stats = results['analysis']['overall_stats']
        print(f"  Average Temperature: {stats['avg_temp']:.2f}°C")
        print(f"  Average Humidity: {stats['avg_humidity']:.2f}%")
        print(f"  Average Battery: {stats['avg_battery']:.1f}%")
        
        print("\n📍 BY LOCATION:")
        for loc in results['analysis']['location_stats']:
            print(f"  {loc['location']}: {loc['sensor_count']} sensors, "
                  f"Temp: {loc['avg_temp']:.2f}°C")
        
    finally:
        processor.stop()

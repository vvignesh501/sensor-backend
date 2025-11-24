#!/usr/bin/env python3
"""
Complete Data Flow Example: N-Dimensional Sensor Data → Redshift Analytics

Shows how raw sensor arrays are transformed into structured analytics data
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json

class SensorDataFlowExample:
    """Demonstrates the complete data transformation pipeline"""
    
    def __init__(self):
        self.test_id = f"demo_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.sensor_type = "MM"
    
    def generate_sample_sensor_data(self):
        """Generate realistic 3D sensor data with patterns and anomalies"""
        
        print("🔬 Generating Sample Sensor Data")
        print("=" * 50)
        
        # Create 3D sensor data: (100 time points, 16x8 spatial grid)
        base_data = np.random.normal(25.0, 2.5, (100, 16, 8)).astype(np.float32)
        
        # Add realistic patterns
        for t in range(100):
            # Temporal drift
            drift = t * 0.02
            base_data[t, :, :] += drift
            
            # Spatial gradient (temperature gradient across sensor)
            for x in range(16):
                for y in range(8):
                    spatial_effect = (x - 8) * 0.1 + (y - 4) * 0.05
                    base_data[t, x, y] += spatial_effect
        
        # Inject some anomalies
        base_data[50, 8, 4] = 100.0  # Point anomaly
        base_data[75, :, :] = -10.0  # Temporal anomaly
        base_data[:, 12, 6] = 50.0   # Spatial anomaly
        
        print(f"✅ Generated data shape: {base_data.shape}")
        print(f"   Data range: [{np.min(base_data):.2f}, {np.max(base_data):.2f}]")
        print(f"   Mean: {np.mean(base_data):.2f}, Std: {np.std(base_data):.2f}")
        
        return base_data
    
    def transform_to_redshift_tables(self, sensor_data):
        """Transform N-dimensional data into Redshift-ready tables"""
        
        print(f"\n📊 Transforming to Redshift Tables")
        print("=" * 50)
        
        tables = {}
        
        # 1. RAW DATA TABLE - Every data point becomes a row
        print("1️⃣ Creating Raw Data Table...")
        raw_rows = []
        
        for t in range(sensor_data.shape[0]):
            for x in range(sensor_data.shape[1]):
                for y in range(sensor_data.shape[2]):
                    raw_rows.append({
                        'test_id': self.test_id,
                        'sensor_type': self.sensor_type,
                        'timestamp_idx': t,
                        'x_coordinate': x,
                        'y_coordinate': y,
                        'sensor_value': float(sensor_data[t, x, y]),
                        'processing_timestamp': datetime.utcnow(),
                        'data_quality_score': self._calculate_quality_score(sensor_data, t, x, y)
                    })
        
        tables['sensor_raw_data'] = pd.DataFrame(raw_rows)
        print(f"   ✅ Raw data: {len(raw_rows):,} rows")
        
        # 2. TIME SERIES TABLE - Aggregated by time
        print("2️⃣ Creating Time Series Table...")
        time_series_rows = []
        
        for t in range(sensor_data.shape[0]):
            time_slice = sensor_data[t, :, :]
            
            time_series_rows.append({
                'test_id': self.test_id,
                'sensor_type': self.sensor_type,
                'time_index': t,
                'avg_value': float(np.mean(time_slice)),
                'max_value': float(np.max(time_slice)),
                'min_value': float(np.min(time_slice)),
                'std_value': float(np.std(time_slice)),
                'anomaly_count': int(self._count_anomalies(time_slice)),
                'uniformity_score': float(1.0 / (1.0 + np.std(time_slice))),
                'processing_timestamp': datetime.utcnow(),
                'data_points_count': int(time_slice.size)
            })
        
        tables['sensor_time_series'] = pd.DataFrame(time_series_rows)
        print(f"   ✅ Time series: {len(time_series_rows)} rows")
        
        # 3. SPATIAL TABLE - Aggregated by location
        print("3️⃣ Creating Spatial Analytics Table...")
        spatial_rows = []
        
        # Average over time for each spatial location
        spatial_avg = np.mean(sensor_data, axis=0)
        
        for x in range(spatial_avg.shape[0]):
            for y in range(spatial_avg.shape[1]):
                gradient = self._calculate_gradient(spatial_avg, x, y)
                local_mean = self._calculate_local_mean(spatial_avg, x, y)
                
                spatial_rows.append({
                    'test_id': self.test_id,
                    'sensor_type': self.sensor_type,
                    'x_coordinate': x,
                    'y_coordinate': y,
                    'avg_temporal_value': float(spatial_avg[x, y]),
                    'local_mean_3x3': float(local_mean),
                    'gradient_magnitude': float(gradient),
                    'is_edge_point': bool(gradient > np.std(spatial_avg)),
                    'processing_timestamp': datetime.utcnow(),
                    'spatial_zone': f"zone_{x//4}_{y//2}"
                })
        
        tables['sensor_spatial_data'] = pd.DataFrame(spatial_rows)
        print(f"   ✅ Spatial data: {len(spatial_rows)} rows")
        
        # 4. METADATA TABLE - High-level test summary
        print("4️⃣ Creating Metadata Table...")
        metadata = {
            'test_id': self.test_id,
            'sensor_type': self.sensor_type,
            'test_timestamp': datetime.utcnow() - timedelta(minutes=5),
            'processing_timestamp': datetime.utcnow(),
            'data_shape': str(sensor_data.shape),
            'total_data_points': int(sensor_data.size),
            'avg_sensor_value': float(np.mean(sensor_data)),
            'anomaly_percentage': float(self._calculate_anomaly_percentage(sensor_data)),
            'quality_score': float(self._calculate_overall_quality(sensor_data)),
            'processing_duration_ms': 1500,
            's3_raw_path': f's3://sensor-prod-data/{self.test_id}.npy',
            's3_processed_path': f's3://sensor-analytics-processed-data/{self.test_id}_analytics.json'
        }
        
        tables['sensor_test_metadata'] = pd.DataFrame([metadata])
        print(f"   ✅ Metadata: 1 row")
        
        return tables
    
    def show_analytics_examples(self, tables):
        """Show example analytics queries you can run on Redshift"""
        
        print(f"\n📈 Analytics Examples")
        print("=" * 50)
        
        # Example 1: Time series trend
        print("1️⃣ Time Series Trend Analysis:")
        time_series = tables['sensor_time_series']
        trend_data = time_series[['time_index', 'avg_value', 'std_value']].head(10)
        print(trend_data.to_string(index=False))
        
        # Example 2: Spatial hotspots
        print(f"\n2️⃣ Spatial Hotspots (Top 5 by gradient):")
        spatial_data = tables['sensor_spatial_data']
        hotspots = spatial_data.nlargest(5, 'gradient_magnitude')[
            ['x_coordinate', 'y_coordinate', 'avg_temporal_value', 'gradient_magnitude', 'spatial_zone']
        ]
        print(hotspots.to_string(index=False))
        
        # Example 3: Anomaly summary
        print(f"\n3️⃣ Anomaly Summary:")
        metadata = tables['sensor_test_metadata'].iloc[0]
        print(f"   Total anomaly percentage: {metadata['anomaly_percentage']:.2f}%")
        print(f"   Overall quality score: {metadata['quality_score']:.2f}")
        
        anomaly_times = time_series[time_series['anomaly_count'] > 0]
        print(f"   Time points with anomalies: {len(anomaly_times)}")
        
        edge_points = spatial_data[spatial_data['is_edge_point'] == True]
        print(f"   Spatial edge points detected: {len(edge_points)}")
    
    def generate_redshift_sql_examples(self):
        """Generate example SQL queries for Redshift analytics"""
        
        print(f"\n💾 Redshift SQL Query Examples")
        print("=" * 50)
        
        queries = {
            "Daily Sensor Performance": f"""
            SELECT 
                sensor_type,
                DATE_TRUNC('day', processing_timestamp) as test_date,
                COUNT(*) as tests_count,
                AVG(avg_sensor_value) as daily_avg,
                AVG(anomaly_percentage) as avg_anomaly_rate,
                AVG(quality_score) as avg_quality
            FROM sensor_test_metadata
            WHERE processing_timestamp >= DATEADD(day, -30, GETDATE())
            GROUP BY sensor_type, DATE_TRUNC('day', processing_timestamp)
            ORDER BY test_date DESC;
            """,
            
            "Anomaly Detection": f"""
            SELECT 
                t.test_id,
                t.sensor_type,
                t.anomaly_percentage,
                COUNT(ts.time_index) as anomalous_time_points,
                AVG(ts.avg_value) as avg_value_during_anomalies
            FROM sensor_test_metadata t
            JOIN sensor_time_series ts ON t.test_id = ts.test_id
            WHERE t.anomaly_percentage > 5.0
              AND ts.anomaly_count > 0
            GROUP BY t.test_id, t.sensor_type, t.anomaly_percentage
            ORDER BY t.anomaly_percentage DESC;
            """,
            
            "Spatial Pattern Analysis": f"""
            SELECT 
                spatial_zone,
                sensor_type,
                COUNT(*) as measurements,
                AVG(avg_temporal_value) as zone_avg,
                AVG(gradient_magnitude) as avg_gradient,
                COUNT(CASE WHEN is_edge_point THEN 1 END) as edge_count
            FROM sensor_spatial_data
            WHERE processing_timestamp >= DATEADD(day, -7, GETDATE())
            GROUP BY spatial_zone, sensor_type
            ORDER BY avg_gradient DESC;
            """,
            
            "Real-time Dashboard Query": f"""
            SELECT 
                m.test_id,
                m.sensor_type,
                m.test_timestamp,
                m.quality_score,
                ts.time_index,
                ts.avg_value,
                ts.uniformity_score
            FROM sensor_test_metadata m
            JOIN sensor_time_series ts ON m.test_id = ts.test_id
            WHERE m.processing_timestamp >= DATEADD(hour, -1, GETDATE())
            ORDER BY m.test_timestamp DESC, ts.time_index;
            """
        }
        
        for query_name, sql in queries.items():
            print(f"\n🔍 {query_name}:")
            print(sql.strip())
    
    def _calculate_quality_score(self, data, t, x, y):
        """Calculate quality score for a data point"""
        value = data[t, x, y]
        global_mean = np.mean(data)
        global_std = np.std(data)
        
        if global_std == 0:
            return 1.0
        
        z_score = abs((value - global_mean) / global_std)
        return max(0.0, 1.0 - z_score / 5.0)
    
    def _count_anomalies(self, time_slice):
        """Count anomalies in a time slice using z-score"""
        mean_val = np.mean(time_slice)
        std_val = np.std(time_slice)
        
        if std_val == 0:
            return 0
        
        z_scores = np.abs((time_slice - mean_val) / std_val)
        return np.sum(z_scores > 3)
    
    def _calculate_gradient(self, spatial_data, x, y):
        """Calculate gradient magnitude at a point"""
        if x == 0 or x == spatial_data.shape[0]-1 or y == 0 or y == spatial_data.shape[1]-1:
            return 0.0
        
        grad_x = spatial_data[x+1, y] - spatial_data[x-1, y]
        grad_y = spatial_data[x, y+1] - spatial_data[x, y-1]
        
        return np.sqrt(grad_x**2 + grad_y**2)
    
    def _calculate_local_mean(self, spatial_data, x, y, window=3):
        """Calculate local mean around a point"""
        half_window = window // 2
        x_start = max(0, x - half_window)
        x_end = min(spatial_data.shape[0], x + half_window + 1)
        y_start = max(0, y - half_window)
        y_end = min(spatial_data.shape[1], y + half_window + 1)
        
        return np.mean(spatial_data[x_start:x_end, y_start:y_end])
    
    def _calculate_anomaly_percentage(self, data):
        """Calculate overall anomaly percentage"""
        mean_val = np.mean(data)
        std_val = np.std(data)
        
        if std_val == 0:
            return 0.0
        
        z_scores = np.abs((data - mean_val) / std_val)
        anomalies = np.sum(z_scores > 3)
        
        return (anomalies / data.size) * 100
    
    def _calculate_overall_quality(self, data):
        """Calculate overall data quality score"""
        # Based on signal-to-noise ratio and anomaly rate
        signal_power = np.mean(data ** 2)
        noise_power = np.var(data)
        
        if noise_power == 0:
            snr = 100
        else:
            snr = 10 * np.log10(signal_power / noise_power)
        
        anomaly_rate = self._calculate_anomaly_percentage(data)
        
        # Quality score: high SNR and low anomaly rate = high quality
        quality = min(100, max(0, snr * 10 - anomaly_rate * 5))
        return quality / 100


def main():
    """Run the complete data flow demonstration"""
    
    print("🚀 Sensor Data → Redshift Analytics Pipeline Demo")
    print("=" * 60)
    
    demo = SensorDataFlowExample()
    
    # 1. Generate sample sensor data
    sensor_data = demo.generate_sample_sensor_data()
    
    # 2. Transform to Redshift tables
    tables = demo.transform_to_redshift_tables(sensor_data)
    
    # 3. Show analytics examples
    demo.show_analytics_examples(tables)
    
    # 4. Generate SQL examples
    demo.generate_redshift_sql_examples()
    
    print(f"\n✅ Demo Complete!")
    print(f"📊 Data Transformation Summary:")
    print(f"   Original: {sensor_data.shape} N-dimensional array")
    print(f"   Transformed to: {len(tables)} Redshift tables")
    print(f"   Total rows: {sum(len(df) for df in tables.values()):,}")
    print(f"   Ready for: Time-series analysis, spatial analytics, anomaly detection")


if __name__ == "__main__":
    main()
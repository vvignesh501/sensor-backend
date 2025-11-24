import json
import boto3
import numpy as np
import pandas as pd
from datetime import datetime
import io

class OptimizedRedshiftProcessor:
    """Optimized processor for transforming N-dimensional data to Redshift analytics"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.redshift_client = boto3.client('redshift-data')
        
    def process_sensor_data(self, data: np.ndarray, test_id: str, sensor_type: str):
        """Transform raw data into 4 analytics formats for Redshift"""
        
        results = {}
        
        # 1. TIME-SERIES DATA (trending, forecasting)
        results['time_series'] = self._create_time_series_data(data, test_id, sensor_type)
        
        # 2. SPATIAL DATA (heatmaps, pattern analysis)
        results['spatial'] = self._create_spatial_data(data, test_id, sensor_type)
        
        # 3. AGGREGATED METRICS (dashboards, KPIs)
        results['metrics'] = self._create_aggregated_metrics(data, test_id, sensor_type)
        
        # 4. EVENT DATA (anomaly detection, alerts)
        results['events'] = self._create_event_data(data, test_id, sensor_type)
        
        return results
    
    def _create_time_series_data(self, data: np.ndarray, test_id: str, sensor_type: str):
        """Create time-series data for trending and forecasting"""
        
        if data.ndim < 3:
            return pd.DataFrame()  # Need temporal dimension
        
        time_series = []
        
        for t in range(data.shape[0]):
            time_slice = data[t, :, :]
            
            time_series.append({
                'test_id': test_id,
                'sensor_type': sensor_type,
                'time_index': t,
                'timestamp': datetime.utcnow(),
                'avg_value': float(np.mean(time_slice)),
                'max_value': float(np.max(time_slice)),
                'min_value': float(np.min(time_slice)),
                'std_value': float(np.std(time_slice)),
                'trend_slope': self._calculate_trend(data[:t+1, :, :]) if t > 5 else 0.0,
                'volatility': float(np.std(time_slice) / np.mean(time_slice)) if np.mean(time_slice) != 0 else 0.0
            })
        
        return pd.DataFrame(time_series)
    
    def _create_spatial_data(self, data: np.ndarray, test_id: str, sensor_type: str):
        """Create spatial data for heatmaps and pattern analysis"""
        
        if data.ndim < 2:
            return pd.DataFrame()
        
        # Average over time if 3D
        spatial_avg = np.mean(data, axis=0) if data.ndim == 3 else data
        
        spatial_data = []
        
        for x in range(spatial_avg.shape[0]):
            for y in range(spatial_avg.shape[1]):
                
                spatial_data.append({
                    'test_id': test_id,
                    'sensor_type': sensor_type,
                    'x_coord': x,
                    'y_coord': y,
                    'avg_value': float(spatial_avg[x, y]),
                    'local_variance': self._get_local_variance(spatial_avg, x, y),
                    'gradient_magnitude': self._get_gradient(spatial_avg, x, y),
                    'spatial_zone': f"zone_{x//4}_{y//2}",
                    'is_hotspot': bool(spatial_avg[x, y] > np.mean(spatial_avg) + 2*np.std(spatial_avg)),
                    'is_coldspot': bool(spatial_avg[x, y] < np.mean(spatial_avg) - 2*np.std(spatial_avg))
                })
        
        return pd.DataFrame(spatial_data)
    
    def _create_aggregated_metrics(self, data: np.ndarray, test_id: str, sensor_type: str):
        """Create aggregated metrics for dashboards and KPIs"""
        
        metrics = {
            'test_id': test_id,
            'sensor_type': sensor_type,
            'processing_time': datetime.utcnow(),
            
            # Basic statistics
            'global_mean': float(np.mean(data)),
            'global_std': float(np.std(data)),
            'global_min': float(np.min(data)),
            'global_max': float(np.max(data)),
            'dynamic_range': float(np.max(data) - np.min(data)),
            
            # Quality metrics
            'signal_to_noise_ratio': self._calculate_snr(data),
            'uniformity_score': float(1.0 / (1.0 + np.std(data))),
            'stability_index': self._calculate_stability(data),
            
            # Performance KPIs
            'anomaly_percentage': self._calculate_anomaly_rate(data),
            'quality_grade': self._assign_quality_grade(data),
            'pass_fail_status': 'PASS' if self._calculate_anomaly_rate(data) < 5.0 else 'FAIL'
        }
        
        return pd.DataFrame([metrics])
    
    def _create_event_data(self, data: np.ndarray, test_id: str, sensor_type: str):
        """Create event data for anomaly detection and alerts"""
        
        events = []
        
        # Detect anomalies using z-score
        mean_val = np.mean(data)
        std_val = np.std(data)
        
        if std_val > 0:
            z_scores = np.abs((data - mean_val) / std_val)
            anomaly_threshold = 3.0
            
            # Find anomaly locations
            anomaly_coords = np.where(z_scores > anomaly_threshold)
            
            for i in range(len(anomaly_coords[0])):
                coords = tuple(anomaly_coords[j][i] for j in range(len(anomaly_coords)))
                
                events.append({
                    'test_id': test_id,
                    'sensor_type': sensor_type,
                    'event_type': 'ANOMALY',
                    'event_time': datetime.utcnow(),
                    'coordinates': str(coords),
                    'anomaly_value': float(data[coords]),
                    'z_score': float(z_scores[coords]),
                    'severity': 'HIGH' if z_scores[coords] > 5 else 'MEDIUM',
                    'description': f'Anomaly detected at {coords} with z-score {z_scores[coords]:.2f}'
                })
        
        # Add quality events
        quality_score = self._calculate_snr(data)
        if quality_score < 10:  # Low quality threshold
            events.append({
                'test_id': test_id,
                'sensor_type': sensor_type,
                'event_type': 'QUALITY_ALERT',
                'event_time': datetime.utcnow(),
                'coordinates': 'GLOBAL',
                'anomaly_value': quality_score,
                'z_score': 0.0,
                'severity': 'LOW',
                'description': f'Low signal quality detected: SNR = {quality_score:.2f} dB'
            })
        
        return pd.DataFrame(events)
    
    def upload_to_redshift(self, dataframes: dict, test_id: str):
        """Upload all analytics data to Redshift tables"""
        
        table_mapping = {
            'time_series': 'sensor_time_series_analytics',
            'spatial': 'sensor_spatial_analytics', 
            'metrics': 'sensor_aggregated_metrics',
            'events': 'sensor_event_data'
        }
        
        results = {}
        
        for data_type, df in dataframes.items():
            if len(df) > 0:
                table_name = table_mapping[data_type]
                result = self._upload_dataframe_to_redshift(df, table_name, test_id)
                results[data_type] = result
        
        return results
    
    def _upload_dataframe_to_redshift(self, df: pd.DataFrame, table_name: str, test_id: str):
        """Upload DataFrame to Redshift via S3 COPY"""
        
        try:
            # Upload CSV to S3
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, header=False)
            
            s3_key = f"redshift_staging/{table_name}/{datetime.utcnow().strftime('%Y/%m/%d')}/{test_id}_{datetime.utcnow().isoformat()}.csv"
            
            self.s3_client.put_object(
                Bucket='sensor-analytics-processed-data',
                Key=s3_key,
                Body=csv_buffer.getvalue(),
                ContentType='text/csv'
            )
            
            # Execute COPY command
            copy_sql = f"""
            COPY {table_name}
            FROM 's3://sensor-analytics-processed-data/{s3_key}'
            IAM_ROLE 'arn:aws:iam::123456789012:role/redshift-s3-access-role'
            CSV
            TIMEFORMAT 'YYYY-MM-DD HH:MI:SS'
            """
            
            response = self.redshift_client.execute_statement(
                ClusterIdentifier='sensor-analytics-cluster',
                Database='sensor_analytics',
                DbUser='admin',
                Sql=copy_sql
            )
            
            return {
                'status': 'success',
                'rows_loaded': len(df),
                'table': table_name,
                'query_id': response['Id']
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'table': table_name
            }
    
    # Helper methods
    def _calculate_trend(self, time_data):
        """Calculate trend slope over time"""
        if time_data.shape[0] < 2:
            return 0.0
        
        time_means = [np.mean(time_data[t]) for t in range(time_data.shape[0])]
        x = np.arange(len(time_means))
        
        if len(time_means) > 1:
            slope = np.polyfit(x, time_means, 1)[0]
            return float(slope)
        return 0.0
    
    def _get_local_variance(self, spatial_data, x, y, window=3):
        """Calculate local variance around a point"""
        half_window = window // 2
        x_start = max(0, x - half_window)
        x_end = min(spatial_data.shape[0], x + half_window + 1)
        y_start = max(0, y - half_window)
        y_end = min(spatial_data.shape[1], y + half_window + 1)
        
        local_region = spatial_data[x_start:x_end, y_start:y_end]
        return float(np.var(local_region))
    
    def _get_gradient(self, spatial_data, x, y):
        """Calculate gradient magnitude"""
        if x == 0 or x == spatial_data.shape[0]-1 or y == 0 or y == spatial_data.shape[1]-1:
            return 0.0
        
        grad_x = spatial_data[x+1, y] - spatial_data[x-1, y]
        grad_y = spatial_data[x, y+1] - spatial_data[x, y-1]
        
        return float(np.sqrt(grad_x**2 + grad_y**2))
    
    def _calculate_snr(self, data):
        """Calculate Signal-to-Noise Ratio"""
        signal_power = np.mean(data ** 2)
        noise_power = np.var(data)
        
        if noise_power == 0:
            return 100.0
        
        snr_db = 10 * np.log10(signal_power / noise_power)
        return float(snr_db)
    
    def _calculate_stability(self, data):
        """Calculate stability index"""
        if data.ndim == 3:
            # Temporal stability
            time_means = [np.mean(data[t]) for t in range(data.shape[0])]
            return float(1.0 / (1.0 + np.std(time_means)))
        else:
            return float(1.0 / (1.0 + np.std(data)))
    
    def _calculate_anomaly_rate(self, data):
        """Calculate percentage of anomalous points"""
        mean_val = np.mean(data)
        std_val = np.std(data)
        
        if std_val == 0:
            return 0.0
        
        z_scores = np.abs((data - mean_val) / std_val)
        anomalies = np.sum(z_scores > 3)
        
        return float((anomalies / data.size) * 100)
    
    def _assign_quality_grade(self, data):
        """Assign quality grade A-F"""
        anomaly_rate = self._calculate_anomaly_rate(data)
        snr = self._calculate_snr(data)
        
        if anomaly_rate < 1 and snr > 20:
            return 'A'
        elif anomaly_rate < 3 and snr > 15:
            return 'B'
        elif anomaly_rate < 5 and snr > 10:
            return 'C'
        elif anomaly_rate < 10 and snr > 5:
            return 'D'
        else:
            return 'F'


def lambda_handler(event, context):
    """Lambda handler for processing sensor data to Redshift analytics"""
    
    processor = OptimizedRedshiftProcessor()
    
    try:
        for record in event['Records']:
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']
            
            # Extract metadata
            test_id = object_key.split('/')[-1].split('.')[0]
            sensor_type = object_key.split('/')[-2] if len(object_key.split('/')) > 1 else 'MM'
            
            # Download data
            response = processor.s3_client.get_object(Bucket=bucket_name, Key=object_key)
            data = np.load(io.BytesIO(response['Body'].read()))
            
            # Process into 4 analytics formats
            analytics_data = processor.process_sensor_data(data, test_id, sensor_type)
            
            # Upload to Redshift
            upload_results = processor.upload_to_redshift(analytics_data, test_id)
            
            print(f"Successfully processed {test_id} to Redshift analytics tables")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully processed {len(event["Records"])} files',
                'analytics_tables': ['time_series', 'spatial', 'metrics', 'events']
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
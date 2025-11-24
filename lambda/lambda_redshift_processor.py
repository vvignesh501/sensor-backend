import json
import boto3
import numpy as np
import pandas as pd
from datetime import datetime
import io
import psycopg2
from typing import Dict, List, Any

class RedshiftDataProcessor:
    """Lambda processor that transforms N-dimensional data for Redshift analytics"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.redshift_client = boto3.client('redshift-data')
        
        # Redshift connection details
        self.cluster_id = 'sensor-analytics-cluster'
        self.database = 'sensor_analytics'
        self.db_user = 'admin'
        
    def transform_ndarray_to_tabular(self, data: np.ndarray, test_id: str, sensor_type: str) -> pd.DataFrame:
        """
        Transform N-dimensional sensor data into tabular format for Redshift
        
        Example: (100, 16, 8) array becomes 12,800 rows with columns:
        - test_id, sensor_type, timestamp_idx, x_coord, y_coord, value, processing_time
        """
        
        rows = []
        processing_time = datetime.utcnow()
        
        # Flatten N-dimensional array into rows
        if data.ndim == 3:  # (time, x, y)
            for t in range(data.shape[0]):
                for x in range(data.shape[1]):
                    for y in range(data.shape[2]):
                        rows.append({
                            'test_id': test_id,
                            'sensor_type': sensor_type,
                            'timestamp_idx': t,
                            'x_coordinate': x,
                            'y_coordinate': y,
                            'sensor_value': float(data[t, x, y]),
                            'processing_timestamp': processing_time,
                            'data_quality_score': self._calculate_local_quality(data, t, x, y)
                        })
        
        elif data.ndim == 2:  # (x, y)
            for x in range(data.shape[0]):
                for y in range(data.shape[1]):
                    rows.append({
                        'test_id': test_id,
                        'sensor_type': sensor_type,
                        'timestamp_idx': 0,
                        'x_coordinate': x,
                        'y_coordinate': y,
                        'sensor_value': float(data[x, y]),
                        'processing_timestamp': processing_time,
                        'data_quality_score': self._calculate_local_quality(data, x, y)
                    })
        
        return pd.DataFrame(rows)
    
    def create_analytics_summary(self, data: np.ndarray, test_id: str, sensor_type: str) -> pd.DataFrame:
        """
        Create aggregated analytics data for Redshift
        Perfect for time-series analysis and dashboards
        """
        
        summary_rows = []
        processing_time = datetime.utcnow()
        
        if data.ndim >= 3:  # Time-series data
            for t in range(data.shape[0]):
                time_slice = data[t, :, :]
                
                summary_rows.append({
                    'test_id': test_id,
                    'sensor_type': sensor_type,
                    'time_index': t,
                    'avg_value': float(np.mean(time_slice)),
                    'max_value': float(np.max(time_slice)),
                    'min_value': float(np.min(time_slice)),
                    'std_value': float(np.std(time_slice)),
                    'anomaly_count': int(np.sum(np.abs(time_slice - np.mean(time_slice)) > 3 * np.std(time_slice))),
                    'uniformity_score': float(1.0 / (1.0 + np.std(time_slice))),
                    'processing_timestamp': processing_time,
                    'data_points_count': int(time_slice.size)
                })
        
        return pd.DataFrame(summary_rows)
    
    def create_spatial_analytics(self, data: np.ndarray, test_id: str, sensor_type: str) -> pd.DataFrame:
        """
        Create spatial analytics data for Redshift
        Useful for heatmaps and spatial pattern analysis
        """
        
        spatial_rows = []
        processing_time = datetime.utcnow()
        
        if data.ndim >= 2:
            # Average over time dimension if present
            if data.ndim == 3:
                spatial_data = np.mean(data, axis=0)  # Average over time
            else:
                spatial_data = data
            
            for x in range(spatial_data.shape[0]):
                for y in range(spatial_data.shape[1]):
                    # Calculate local features
                    local_mean = self._get_local_mean(spatial_data, x, y, window=3)
                    gradient = self._get_local_gradient(spatial_data, x, y)
                    
                    spatial_rows.append({
                        'test_id': test_id,
                        'sensor_type': sensor_type,
                        'x_coordinate': x,
                        'y_coordinate': y,
                        'avg_temporal_value': float(spatial_data[x, y]),
                        'local_mean_3x3': float(local_mean),
                        'gradient_magnitude': float(gradient),
                        'is_edge_point': bool(gradient > np.std(spatial_data)),
                        'processing_timestamp': processing_time,
                        'spatial_zone': f"zone_{x//4}_{y//4}"  # Group into zones
                    })
        
        return pd.DataFrame(spatial_rows)
    
    def upload_to_redshift(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """
        Upload DataFrame to Redshift via S3 COPY command
        Most efficient method for bulk data loading
        """
        
        try:
            # 1. Upload CSV to S3
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, header=False)
            
            s3_key = f"redshift_staging/{table_name}/{datetime.utcnow().strftime('%Y/%m/%d')}/{datetime.utcnow().isoformat()}.csv"
            
            self.s3_client.put_object(
                Bucket='sensor-analytics-processed-data',
                Key=s3_key,
                Body=csv_buffer.getvalue(),
                ContentType='text/csv'
            )
            
            # 2. Execute COPY command in Redshift
            copy_sql = f"""
            COPY {table_name}
            FROM 's3://sensor-analytics-processed-data/{s3_key}'
            IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftS3AccessRole'
            CSV
            TIMEFORMAT 'YYYY-MM-DD HH:MI:SS'
            """
            
            response = self.redshift_client.execute_statement(
                ClusterIdentifier=self.cluster_id,
                Database=self.database,
                DbUser=self.db_user,
                Sql=copy_sql
            )
            
            return {
                'status': 'success',
                'rows_loaded': len(df),
                's3_path': s3_key,
                'query_id': response['Id']
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _calculate_local_quality(self, data: np.ndarray, *coords) -> float:
        """Calculate local data quality score"""
        try:
            value = data[coords]
            local_std = np.std(data)
            if local_std == 0:
                return 1.0
            z_score = abs((value - np.mean(data)) / local_std)
            return max(0.0, 1.0 - z_score / 5.0)  # Quality decreases with z-score
        except:
            return 0.5
    
    def _get_local_mean(self, data: np.ndarray, x: int, y: int, window: int = 3) -> float:
        """Get mean of local window around point"""
        half_window = window // 2
        x_start = max(0, x - half_window)
        x_end = min(data.shape[0], x + half_window + 1)
        y_start = max(0, y - half_window)
        y_end = min(data.shape[1], y + half_window + 1)
        
        return np.mean(data[x_start:x_end, y_start:y_end])
    
    def _get_local_gradient(self, data: np.ndarray, x: int, y: int) -> float:
        """Calculate gradient magnitude at point"""
        if x == 0 or x == data.shape[0]-1 or y == 0 or y == data.shape[1]-1:
            return 0.0
        
        grad_x = data[x+1, y] - data[x-1, y]
        grad_y = data[x, y+1] - data[x, y-1]
        
        return np.sqrt(grad_x**2 + grad_y**2)


def lambda_handler(event, context):
    """
    Lambda handler for processing sensor data and loading to Redshift
    """
    
    processor = RedshiftDataProcessor()
    
    try:
        for record in event['Records']:
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']
            
            # Extract metadata
            test_id = object_key.split('/')[-1].split('.')[0]
            sensor_type = object_key.split('/')[-2] if len(object_key.split('/')) > 1 else 'unknown'
            
            # Download and load data
            response = processor.s3_client.get_object(Bucket=bucket_name, Key=object_key)
            data = np.load(io.BytesIO(response['Body'].read()))
            
            # Transform data for different analytics use cases
            
            # 1. Raw data table (for detailed analysis)
            raw_df = processor.transform_ndarray_to_tabular(data, test_id, sensor_type)
            raw_result = processor.upload_to_redshift(raw_df, 'sensor_raw_data')
            
            # 2. Time-series summary (for trending)
            if data.ndim >= 3:
                summary_df = processor.create_analytics_summary(data, test_id, sensor_type)
                summary_result = processor.upload_to_redshift(summary_df, 'sensor_time_series')
            
            # 3. Spatial analytics (for heatmaps)
            if data.ndim >= 2:
                spatial_df = processor.create_spatial_analytics(data, test_id, sensor_type)
                spatial_result = processor.upload_to_redshift(spatial_df, 'sensor_spatial_data')
            
            print(f"Successfully processed {test_id} to Redshift")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully processed {len(event["Records"])} files to Redshift',
                'tables_updated': ['sensor_raw_data', 'sensor_time_series', 'sensor_spatial_data']
            })
        }
        
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
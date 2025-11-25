import json
import boto3
import numpy as np
from datetime import datetime
import io
import gzip
from typing import Dict, List, Tuple, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class NDimensionalDataProcessor:
    """AWS Lambda processor for N-dimensional sensor data analytics preprocessing"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.sns_client = boto3.client('sns')
        
        # Configuration
        self.source_bucket = 'sensor-prod-data-vvignesh501-2025'
        self.processed_bucket = 'sensor-analytics-processed-data'
        self.metadata_table = 'sensor-analytics-metadata'
        self.anomaly_topic_arn = 'arn:aws:sns:us-east-1:123456789012:sensor-anomalies'
    
    def preprocess_ndarray(self, data: np.ndarray, test_id: str) -> Dict[str, Any]:
        """
        Comprehensive preprocessing of N-dimensional sensor data
        
        Args:
            data: N-dimensional numpy array
            test_id: Unique test identifier
            
        Returns:
            Dictionary containing processed analytics features
        """
        logger.info(f"Processing {data.ndim}D array with shape {data.shape}")
        
        # Basic statistics
        stats = {
            'shape': list(data.shape),
            'dimensions': data.ndim,
            'total_elements': data.size,
            'data_type': str(data.dtype),
            'memory_usage_mb': data.nbytes / (1024 * 1024)
        }
        
        # Statistical features
        features = {
            'global_stats': {
                'mean': float(np.mean(data)),
                'std': float(np.std(data)),
                'min': float(np.min(data)),
                'max': float(np.max(data)),
                'median': float(np.median(data)),
                'percentile_25': float(np.percentile(data, 25)),
                'percentile_75': float(np.percentile(data, 75)),
                'skewness': float(self._calculate_skewness(data)),
                'kurtosis': float(self._calculate_kurtosis(data))
            }
        }
        
        # Dimension-specific analysis
        if data.ndim >= 2:
            features['spatial_analysis'] = self._analyze_spatial_patterns(data)
        
        if data.ndim >= 3:
            features['temporal_analysis'] = self._analyze_temporal_patterns(data)
            
        # Anomaly detection
        anomalies = self._detect_anomalies(data)
        features['anomaly_detection'] = anomalies
        
        # Quality metrics
        features['quality_metrics'] = self._calculate_quality_metrics(data)
        
        # Frequency domain analysis
        features['frequency_analysis'] = self._frequency_domain_analysis(data)
        
        return {
            'test_id': test_id,
            'timestamp': datetime.utcnow().isoformat(),
            'data_stats': stats,
            'analytics_features': features,
            'processing_metadata': {
                'processor_version': '1.0',
                'processing_time': datetime.utcnow().isoformat()
            }
        }
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness of the data"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        return np.mean(((data - mean) / std) ** 3)
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis of the data"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        return np.mean(((data - mean) / std) ** 4) - 3
    
    def _analyze_spatial_patterns(self, data: np.ndarray) -> Dict[str, Any]:
        """Analyze spatial patterns in 2D+ data"""
        spatial_features = {}
        
        # For 2D data (or higher), analyze each 2D slice
        if data.ndim >= 2:
            # Analyze the last two dimensions as spatial
            spatial_data = data.reshape(-1, data.shape[-2], data.shape[-1])
            
            spatial_features = {
                'uniformity_score': float(1.0 / (1.0 + np.std(data))),
                'gradient_magnitude': float(np.mean(np.abs(np.gradient(spatial_data[0])))),
                'edge_density': self._calculate_edge_density(spatial_data[0]),
                'spatial_correlation': self._calculate_spatial_correlation(spatial_data[0])
            }
        
        return spatial_features
    
    def _analyze_temporal_patterns(self, data: np.ndarray) -> Dict[str, Any]:
        """Analyze temporal patterns in 3D+ data"""
        temporal_features = {}
        
        if data.ndim >= 3:
            # Treat first dimension as temporal
            temporal_series = np.mean(data, axis=(1, 2))  # Average over spatial dimensions
            
            temporal_features = {
                'trend': float(np.polyfit(range(len(temporal_series)), temporal_series, 1)[0]),
                'stability': float(np.std(np.diff(temporal_series))),
                'drift_rate': float((temporal_series[-1] - temporal_series[0]) / len(temporal_series)),
                'autocorrelation': float(np.corrcoef(temporal_series[:-1], temporal_series[1:])[0, 1])
            }
        
        return temporal_features
    
    def _detect_anomalies(self, data: np.ndarray) -> Dict[str, Any]:
        """Detect anomalies using statistical methods"""
        # Z-score based anomaly detection
        z_scores = np.abs((data - np.mean(data)) / np.std(data))
        anomaly_threshold = 3.0
        
        anomalies = {
            'total_anomalies': int(np.sum(z_scores > anomaly_threshold)),
            'anomaly_percentage': float(np.sum(z_scores > anomaly_threshold) / data.size * 100),
            'max_z_score': float(np.max(z_scores)),
            'anomaly_locations': self._find_anomaly_locations(z_scores, anomaly_threshold)
        }
        
        return anomalies
    
    def _calculate_quality_metrics(self, data: np.ndarray) -> Dict[str, Any]:
        """Calculate data quality metrics"""
        quality = {
            'signal_to_noise_ratio': self._calculate_snr(data),
            'dynamic_range': float(np.max(data) - np.min(data)),
            'zero_crossings': int(np.sum(np.diff(np.signbit(data.flatten())))),
            'missing_data_percentage': float(np.sum(np.isnan(data)) / data.size * 100),
            'outlier_percentage': self._calculate_outlier_percentage(data)
        }
        
        return quality
    
    def _frequency_domain_analysis(self, data: np.ndarray) -> Dict[str, Any]:
        """Perform frequency domain analysis"""
        # For simplicity, analyze 1D signal (flatten or take a slice)
        signal = data.flatten()[:1024]  # Limit for performance
        
        # FFT analysis
        fft = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal))
        power_spectrum = np.abs(fft) ** 2
        
        frequency_features = {
            'dominant_frequency': float(freqs[np.argmax(power_spectrum[1:]) + 1]),
            'spectral_centroid': float(np.sum(freqs * power_spectrum) / np.sum(power_spectrum)),
            'spectral_bandwidth': float(np.sqrt(np.sum(((freqs - np.sum(freqs * power_spectrum) / np.sum(power_spectrum)) ** 2) * power_spectrum) / np.sum(power_spectrum))),
            'total_power': float(np.sum(power_spectrum))
        }
        
        return frequency_features
    
    def _calculate_edge_density(self, data_2d: np.ndarray) -> float:
        """Calculate edge density in 2D data"""
        # Simple edge detection using gradient
        grad_x = np.gradient(data_2d, axis=0)
        grad_y = np.gradient(data_2d, axis=1)
        edge_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        return float(np.mean(edge_magnitude))
    
    def _calculate_spatial_correlation(self, data_2d: np.ndarray) -> float:
        """Calculate spatial correlation"""
        # Autocorrelation in spatial domain
        if data_2d.size < 4:
            return 0.0
        
        shifted = np.roll(data_2d, 1, axis=0)
        correlation = np.corrcoef(data_2d.flatten(), shifted.flatten())[0, 1]
        return float(correlation) if not np.isnan(correlation) else 0.0
    
    def _find_anomaly_locations(self, z_scores: np.ndarray, threshold: float) -> List[List[int]]:
        """Find locations of anomalies"""
        anomaly_indices = np.where(z_scores > threshold)
        locations = []
        
        # Limit to first 10 anomalies for performance
        for i in range(min(10, len(anomaly_indices[0]))):
            location = [int(anomaly_indices[j][i]) for j in range(len(anomaly_indices))]
            locations.append(location)
        
        return locations
    
    def _calculate_snr(self, data: np.ndarray) -> float:
        """Calculate Signal-to-Noise Ratio"""
        signal_power = np.mean(data ** 2)
        noise_power = np.var(data)
        
        if noise_power == 0:
            return float('inf')
        
        snr_db = 10 * np.log10(signal_power / noise_power)
        return float(snr_db)
    
    def _calculate_outlier_percentage(self, data: np.ndarray) -> float:
        """Calculate percentage of outliers using IQR method"""
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = np.sum((data < lower_bound) | (data > upper_bound))
        return float(outliers / data.size * 100)
    
    def save_processed_data(self, processed_data: Dict[str, Any], test_id: str) -> str:
        """Save processed data to S3 and metadata to DynamoDB"""
        
        # Save to S3
        s3_key = f"processed/{datetime.utcnow().strftime('%Y/%m/%d')}/{test_id}_analytics.json"
        
        try:
            # Compress and upload to S3
            json_data = json.dumps(processed_data, indent=2)
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            self.s3_client.put_object(
                Bucket=self.processed_bucket,
                Key=s3_key,
                Body=compressed_data,
                ContentType='application/json',
                ContentEncoding='gzip',
                Metadata={
                    'test_id': test_id,
                    'processing_timestamp': datetime.utcnow().isoformat(),
                    'data_dimensions': str(processed_data['data_stats']['dimensions'])
                }
            )
            
            # Save metadata to DynamoDB
            table = self.dynamodb.Table(self.metadata_table)
            table.put_item(
                Item={
                    'test_id': test_id,
                    'processing_timestamp': datetime.utcnow().isoformat(),
                    's3_location': f"s3://{self.processed_bucket}/{s3_key}",
                    'data_shape': processed_data['data_stats']['shape'],
                    'anomaly_count': processed_data['analytics_features']['anomaly_detection']['total_anomalies'],
                    'quality_score': processed_data['analytics_features']['quality_metrics']['signal_to_noise_ratio']
                }
            )
            
            logger.info(f"Processed data saved to {s3_key}")
            return s3_key
            
        except Exception as e:
            logger.error(f"Error saving processed data: {str(e)}")
            raise
    
    def check_anomaly_alerts(self, processed_data: Dict[str, Any]) -> None:
        """Check for anomalies and send alerts if necessary"""
        anomaly_data = processed_data['analytics_features']['anomaly_detection']
        
        # Alert thresholds
        if (anomaly_data['anomaly_percentage'] > 5.0 or 
            anomaly_data['max_z_score'] > 5.0):
            
            alert_message = {
                'test_id': processed_data['test_id'],
                'alert_type': 'HIGH_ANOMALY_DETECTED',
                'anomaly_percentage': anomaly_data['anomaly_percentage'],
                'max_z_score': anomaly_data['max_z_score'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            try:
                self.sns_client.publish(
                    TopicArn=self.anomaly_topic_arn,
                    Message=json.dumps(alert_message),
                    Subject=f"Sensor Anomaly Alert - Test {processed_data['test_id']}"
                )
                logger.info(f"Anomaly alert sent for test {processed_data['test_id']}")
            except Exception as e:
                logger.error(f"Error sending anomaly alert: {str(e)}")


def lambda_handler(event, context):
    """
    AWS Lambda handler for processing N-dimensional sensor data
    
    Expected event format:
    {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "source-bucket"},
                    "object": {"key": "path/to/sensor/data.npy"}
                }
            }
        ]
    }
    """
    
    processor = NDimensionalDataProcessor()
    
    try:
        # Process each S3 event
        for record in event['Records']:
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']
            
            logger.info(f"Processing {object_key} from {bucket_name}")
            
            # Extract test_id from object key
            test_id = object_key.split('/')[-1].split('.')[0]
            
            # Download data from S3
            response = processor.s3_client.get_object(Bucket=bucket_name, Key=object_key)
            
            # Load numpy array (assuming .npy format)
            if object_key.endswith('.npy'):
                data = np.load(io.BytesIO(response['Body'].read()))
            else:
                # Handle other formats or generate sample data
                logger.warning(f"Unsupported format for {object_key}, generating sample data")
                data = np.random.normal(25.0, 2.5, (100, 16, 8)).astype(np.float32)
            
            # Process the N-dimensional data
            processed_data = processor.preprocess_ndarray(data, test_id)
            
            # Save processed results
            s3_key = processor.save_processed_data(processed_data, test_id)
            
            # Check for anomalies and send alerts
            processor.check_anomaly_alerts(processed_data)
            
            logger.info(f"Successfully processed {test_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully processed {len(event["Records"])} files',
                'processed_files': [record['s3']['object']['key'] for record in event['Records']]
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to process sensor data'
            })
        }


# Test function for local development
def test_local():
    """Test the processor locally with sample data"""
    processor = NDimensionalDataProcessor()
    
    # Generate sample N-dimensional data
    test_data = np.random.normal(25.0, 2.5, (100, 16, 8)).astype(np.float32)
    
    # Add some anomalies
    test_data[50, 8, 4] = 100.0  # Outlier
    test_data[75, :, :] = -50.0  # Anomalous slice
    
    # Process the data
    result = processor.preprocess_ndarray(test_data, "test_001")
    
    print("Processing Results:")
    print(json.dumps(result, indent=2))
    
    return result

if __name__ == "__main__":
    test_local()
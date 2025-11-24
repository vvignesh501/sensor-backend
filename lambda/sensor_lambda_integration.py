#!/usr/bin/env python3
"""
Integration module to connect sensor backend with AWS Lambda data processor
Handles uploading sensor data to S3 and triggering Lambda processing
"""

import boto3
import numpy as np
import json
import io
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class SensorLambdaIntegration:
    """Integration class for sensor backend and Lambda data processor"""
    
    def __init__(self, 
                 aws_region: str = "us-east-1",
                 source_bucket: str = "sensor-prod-data-vvignesh501-2025",
                 processed_bucket: str = "sensor-analytics-processed-data"):
        
        self.aws_region = aws_region
        self.source_bucket = source_bucket
        self.processed_bucket = processed_bucket
        
        # Initialize AWS clients
        self.s3_client = boto3.client('s3', region_name=aws_region)
        self.lambda_client = boto3.client('lambda', region_name=aws_region)
        self.dynamodb = boto3.resource('dynamodb', region_name=aws_region)
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def upload_sensor_data_async(self, 
                                     sensor_data: np.ndarray, 
                                     test_id: str, 
                                     sensor_type: str,
                                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Asynchronously upload sensor data to S3 and trigger Lambda processing
        
        Args:
            sensor_data: N-dimensional numpy array
            test_id: Unique test identifier
            sensor_type: Type of sensor (MM, etc.)
            metadata: Additional metadata
            
        Returns:
            Dictionary with upload status and processing info
        """
        
        loop = asyncio.get_event_loop()
        
        try:
            # Upload to S3 in background thread
            upload_result = await loop.run_in_executor(
                self.executor,
                self._upload_to_s3,
                sensor_data, test_id, sensor_type, metadata
            )
            
            if upload_result['status'] == 'success':
                # Trigger Lambda processing
                lambda_result = await loop.run_in_executor(
                    self.executor,
                    self._trigger_lambda_processing,
                    upload_result['s3_key'], test_id
                )
                
                return {
                    'test_id': test_id,
                    'upload_status': 'success',
                    's3_path': upload_result['s3_key'],
                    'lambda_triggered': lambda_result['triggered'],
                    'processing_status': 'initiated',
                    'timestamp': datetime.utcnow().isoformat(),
                    'data_stats': {
                        'shape': list(sensor_data.shape),
                        'size_mb': round(sensor_data.nbytes / (1024 * 1024), 2),
                        'dtype': str(sensor_data.dtype)
                    }
                }
            else:
                return {
                    'test_id': test_id,
                    'upload_status': 'failed',
                    'error': upload_result.get('error', 'Unknown error'),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in async upload for test {test_id}: {str(e)}")
            return {
                'test_id': test_id,
                'upload_status': 'failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _upload_to_s3(self, 
                     sensor_data: np.ndarray, 
                     test_id: str, 
                     sensor_type: str,
                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Upload sensor data to S3"""
        
        try:
            # Create S3 key with date partitioning
            date_prefix = datetime.utcnow().strftime('%Y/%m/%d')
            s3_key = f"raw_data/{date_prefix}/{sensor_type}/{test_id}.npy"
            
            # Convert numpy array to bytes
            buffer = io.BytesIO()
            np.save(buffer, sensor_data)
            buffer.seek(0)
            
            # Prepare metadata
            s3_metadata = {
                'test_id': test_id,
                'sensor_type': sensor_type,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'data_shape': json.dumps(list(sensor_data.shape)),
                'data_dtype': str(sensor_data.dtype),
                'data_size_bytes': str(sensor_data.nbytes)
            }
            
            if metadata:
                s3_metadata.update({k: str(v) for k, v in metadata.items()})
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.source_bucket,
                Key=s3_key,
                Body=buffer.getvalue(),
                ContentType='application/octet-stream',
                Metadata=s3_metadata,
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Successfully uploaded {test_id} to s3://{self.source_bucket}/{s3_key}")
            
            return {
                'status': 'success',
                's3_key': s3_key,
                'bucket': self.source_bucket,
                'size_bytes': sensor_data.nbytes
            }
            
        except Exception as e:
            logger.error(f"S3 upload failed for {test_id}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _trigger_lambda_processing(self, s3_key: str, test_id: str) -> Dict[str, Any]:
        """Trigger Lambda function for data processing"""
        
        try:
            # Create Lambda event payload
            event_payload = {
                "Records": [
                    {
                        "s3": {
                            "bucket": {"name": self.source_bucket},
                            "object": {"key": s3_key}
                        }
                    }
                ]
            }
            
            # Invoke Lambda function asynchronously
            response = self.lambda_client.invoke(
                FunctionName='sensor-data-processor',
                InvocationType='Event',  # Asynchronous invocation
                Payload=json.dumps(event_payload)
            )
            
            logger.info(f"Lambda triggered for {test_id}, Status: {response['StatusCode']}")
            
            return {
                'triggered': True,
                'status_code': response['StatusCode'],
                'request_id': response['ResponseMetadata']['RequestId']
            }
            
        except Exception as e:
            logger.error(f"Lambda trigger failed for {test_id}: {str(e)}")
            return {
                'triggered': False,
                'error': str(e)
            }
    
    async def get_processing_results(self, test_id: str, timeout: int = 60) -> Optional[Dict[str, Any]]:
        """
        Poll for processing results from Lambda
        
        Args:
            test_id: Test identifier
            timeout: Maximum wait time in seconds
            
        Returns:
            Processing results or None if not ready
        """
        
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            try:
                # Check processed data bucket
                processed_key = f"processed/{datetime.utcnow().strftime('%Y/%m/%d')}/{test_id}_analytics.json"
                
                response = self.s3_client.get_object(
                    Bucket=self.processed_bucket,
                    Key=processed_key
                )
                
                # Decompress and parse results
                import gzip
                compressed_data = response['Body'].read()
                json_data = gzip.decompress(compressed_data).decode('utf-8')
                results = json.loads(json_data)
                
                logger.info(f"Processing results retrieved for {test_id}")
                return results
                
            except self.s3_client.exceptions.NoSuchKey:
                # Results not ready yet, wait and retry
                await asyncio.sleep(2)
                continue
            except Exception as e:
                logger.error(f"Error retrieving results for {test_id}: {str(e)}")
                break
        
        logger.warning(f"Processing results not available for {test_id} within timeout")
        return None
    
    async def get_analytics_summary(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics summary from DynamoDB metadata table"""
        
        try:
            table = self.dynamodb.Table('sensor-analytics-metadata')
            
            response = table.get_item(Key={'test_id': test_id})
            
            if 'Item' in response:
                return dict(response['Item'])
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving analytics summary for {test_id}: {str(e)}")
            return None
    
    def create_enhanced_sensor_response(self, 
                                      original_response: Dict[str, Any],
                                      lambda_integration_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance the original sensor response with Lambda processing information
        
        Args:
            original_response: Original sensor test response
            lambda_integration_result: Result from Lambda integration
            
        Returns:
            Enhanced response with analytics information
        """
        
        enhanced_response = original_response.copy()
        
        # Add Lambda processing information
        enhanced_response['analytics_processing'] = {
            'lambda_triggered': lambda_integration_result.get('lambda_triggered', False),
            'processing_status': lambda_integration_result.get('processing_status', 'unknown'),
            's3_analytics_path': lambda_integration_result.get('s3_path', ''),
            'data_uploaded': lambda_integration_result.get('upload_status') == 'success'
        }
        
        # Add data statistics
        if 'data_stats' in lambda_integration_result:
            enhanced_response['raw_data_stats'].update({
                'analytics_ready': True,
                'processing_initiated': True,
                **lambda_integration_result['data_stats']
            })
        
        return enhanced_response


# Integration function for the FastAPI app
async def integrate_with_lambda(sensor_data: np.ndarray, 
                              test_id: str, 
                              sensor_type: str,
                              test_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Integration function to be called from the FastAPI sensor test endpoint
    
    Args:
        sensor_data: N-dimensional sensor data
        test_id: Test identifier
        sensor_type: Sensor type
        test_metrics: Test metrics from sensor
        
    Returns:
        Integration result
    """
    
    integration = SensorLambdaIntegration()
    
    # Upload data and trigger processing
    result = await integration.upload_sensor_data_async(
        sensor_data=sensor_data,
        test_id=test_id,
        sensor_type=sensor_type,
        metadata=test_metrics
    )
    
    return result


# Example usage in FastAPI endpoint
def enhanced_sensor_test_example():
    """
    Example of how to modify the existing sensor test endpoint
    to integrate with Lambda processing
    """
    
    example_code = '''
    @app.post("/test/sensor/{sensor_type}")
    async def test_sensor(sensor_type: str, current_user: dict = Depends(get_current_user)):
        test_id = str(uuid.uuid4())
        
        try:
            print("Starting sensor test: " + test_id)
            
            # Generate sensor data (your existing code)
            dynamic_data = np.random.normal(25.0, 2.5, (100, 16, 8)).astype(np.float32)
            
            test_metrics = {
                "temperature": "23.5°C",
                "humidity": "45%",
                "dynamic_range": "98.5%",
                "uniformity_score": "99.2%",
                "stability_drift": "0.02%/hr"
            }
            
            # Store test data in database (your existing code)
            await db.execute_transaction([
                ("INSERT INTO sensor_tests (id, sensor_type, data_type, s3_status, s3_path, test_metrics) VALUES ($1, $2, $3, $4, $5, $6)",
                 (test_id, sensor_type, 'raw_data', 'success', 'local_storage/' + test_id, json.dumps(test_metrics)))
            ])
            
            # NEW: Integrate with Lambda processing
            lambda_result = await integrate_with_lambda(
                sensor_data=dynamic_data,
                test_id=test_id,
                sensor_type=sensor_type,
                test_metrics=test_metrics
            )
            
            # Send Kafka event (your existing code)
            kafka_event = {
                "test_id": test_id,
                "user_id": current_user['username'],
                "sensor_type": sensor_type,
                "s3_status": lambda_result.get('upload_status', 'unknown'),
                "s3_path": lambda_result.get('s3_path', 'local_storage/' + test_id),
                "test_metrics": test_metrics,
                "analytics_processing": lambda_result.get('processing_status', 'unknown'),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            kafka_producer.send_test_event(kafka_event)
            
            # Enhanced response with Lambda integration
            test_results = {
                "test_id": test_id,
                "sensor_type": sensor_type,
                "status": "PASS",
                "timestamp": datetime.utcnow().isoformat(),
                "s3_path": lambda_result.get('s3_path', 'local_storage/' + test_id),
                "raw_data_stats": {
                    "total_arrays": 1,
                    "total_size_mb": round(dynamic_data.nbytes / (1024 * 1024), 2),
                    "array_shapes": {"dynamic_test": list(dynamic_data.shape)},
                    "analytics_processing": lambda_result.get('processing_status', 'unknown'),
                    "lambda_triggered": lambda_result.get('lambda_triggered', False)
                },
                "test_metrics": test_metrics,
                "analytics_info": {
                    "processing_initiated": lambda_result.get('upload_status') == 'success',
                    "expected_results_in": "30-60 seconds",
                    "analytics_endpoint": f"/analytics/results/{test_id}"
                }
            }
            
            print("Sensor test completed with Lambda integration: " + test_id)
            return test_results
            
        except Exception as e:
            print("Sensor test failed: " + str(e))
            raise HTTPException(status_code=500, detail="Sensor test failed: " + str(e))
    '''
    
    return example_code


if __name__ == "__main__":
    # Test the integration locally
    import asyncio
    
    async def test_integration():
        integration = SensorLambdaIntegration()
        
        # Generate test data
        test_data = np.random.normal(25.0, 2.5, (100, 16, 8)).astype(np.float32)
        test_id = f"integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"Testing Lambda integration with test_id: {test_id}")
        
        # Test upload and processing
        result = await integration.upload_sensor_data_async(
            sensor_data=test_data,
            test_id=test_id,
            sensor_type="MM",
            metadata={"test_type": "integration_test"}
        )
        
        print("Integration result:")
        print(json.dumps(result, indent=2))
    
    # Run test
    asyncio.run(test_integration())
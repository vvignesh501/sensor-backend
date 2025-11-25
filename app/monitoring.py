"""
Data Pipeline Monitoring Module
Tracks sensor data ingestion, processing, and failures across PostgreSQL, Kafka, and S3
"""

import boto3
import time
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from functools import wraps

# CloudWatch client
cloudwatch = boto3.client('cloudwatch', region_name='us-east-2')

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Data pipeline stages"""
    INGESTION = "ingestion"
    POSTGRES_WRITE = "postgres_write"
    KAFKA_PUBLISH = "kafka_publish"
    S3_UPLOAD = "s3_upload"
    PROCESSING = "processing"


class FailureType(Enum):
    """Types of failures"""
    CONNECTION_ERROR = "connection_error"
    TIMEOUT = "timeout"
    VALIDATION_ERROR = "validation_error"
    DUPLICATE = "duplicate"
    STORAGE_FULL = "storage_full"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


class DataPipelineMetrics:
    """Publish custom metrics to CloudWatch"""
    
    NAMESPACE = "SensorBackend/DataPipeline"
    
    @staticmethod
    def publish_metric(metric_name: str, value: float, unit: str = "Count", 
                      dimensions: Optional[Dict[str, str]] = None):
        """Publish a single metric to CloudWatch"""
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            cloudwatch.put_metric_data(
                Namespace=DataPipelineMetrics.NAMESPACE,
                MetricData=[metric_data]
            )
        except Exception as e:
            logger.error(f"Failed to publish metric {metric_name}: {e}")
    
    @staticmethod
    def record_success(stage: PipelineStage, sensor_id: str = None):
        """Record successful operation"""
        dimensions = {'Stage': stage.value}
        if sensor_id:
            dimensions['SensorId'] = sensor_id
        
        DataPipelineMetrics.publish_metric(
            'SuccessCount',
            1.0,
            'Count',
            dimensions
        )
    
    @staticmethod
    def record_failure(stage: PipelineStage, failure_type: FailureType, 
                      sensor_id: str = None, error_message: str = None):
        """Record failed operation"""
        dimensions = {
            'Stage': stage.value,
            'FailureType': failure_type.value
        }
        if sensor_id:
            dimensions['SensorId'] = sensor_id
        
        DataPipelineMetrics.publish_metric(
            'FailureCount',
            1.0,
            'Count',
            dimensions
        )
        
        # Log detailed error
        logger.error(
            f"Pipeline failure - Stage: {stage.value}, "
            f"Type: {failure_type.value}, "
            f"Sensor: {sensor_id}, "
            f"Error: {error_message}"
        )
    
    @staticmethod
    def record_latency(stage: PipelineStage, duration_ms: float, sensor_id: str = None):
        """Record operation latency"""
        dimensions = {'Stage': stage.value}
        if sensor_id:
            dimensions['SensorId'] = sensor_id
        
        DataPipelineMetrics.publish_metric(
            'ProcessingLatency',
            duration_ms,
            'Milliseconds',
            dimensions
        )
    
    @staticmethod
    def record_data_size(stage: PipelineStage, size_bytes: int):
        """Record data size processed"""
        DataPipelineMetrics.publish_metric(
            'DataSize',
            float(size_bytes),
            'Bytes',
            {'Stage': stage.value}
        )
    
    @staticmethod
    def record_queue_depth(queue_name: str, depth: int):
        """Record queue depth for Kafka/message queues"""
        DataPipelineMetrics.publish_metric(
            'QueueDepth',
            float(depth),
            'Count',
            {'Queue': queue_name}
        )
    
    @staticmethod
    def record_retry_attempt(stage: PipelineStage, attempt_number: int):
        """Record retry attempts"""
        DataPipelineMetrics.publish_metric(
            'RetryAttempts',
            float(attempt_number),
            'Count',
            {'Stage': stage.value}
        )


def monitor_pipeline_operation(stage: PipelineStage):
    """Decorator to monitor pipeline operations"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            sensor_id = kwargs.get('sensor_id') or (args[0] if args else None)
            
            try:
                result = await func(*args, **kwargs)
                
                # Record success
                duration_ms = (time.time() - start_time) * 1000
                DataPipelineMetrics.record_success(stage, str(sensor_id))
                DataPipelineMetrics.record_latency(stage, duration_ms, str(sensor_id))
                
                return result
                
            except ConnectionError as e:
                DataPipelineMetrics.record_failure(
                    stage, FailureType.CONNECTION_ERROR, str(sensor_id), str(e)
                )
                raise
            except TimeoutError as e:
                DataPipelineMetrics.record_failure(
                    stage, FailureType.TIMEOUT, str(sensor_id), str(e)
                )
                raise
            except ValueError as e:
                DataPipelineMetrics.record_failure(
                    stage, FailureType.VALIDATION_ERROR, str(sensor_id), str(e)
                )
                raise
            except Exception as e:
                DataPipelineMetrics.record_failure(
                    stage, FailureType.UNKNOWN, str(sensor_id), str(e)
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            sensor_id = kwargs.get('sensor_id') or (args[0] if args else None)
            
            try:
                result = func(*args, **kwargs)
                
                # Record success
                duration_ms = (time.time() - start_time) * 1000
                DataPipelineMetrics.record_success(stage, str(sensor_id))
                DataPipelineMetrics.record_latency(stage, duration_ms, str(sensor_id))
                
                return result
                
            except ConnectionError as e:
                DataPipelineMetrics.record_failure(
                    stage, FailureType.CONNECTION_ERROR, str(sensor_id), str(e)
                )
                raise
            except TimeoutError as e:
                DataPipelineMetrics.record_failure(
                    stage, FailureType.TIMEOUT, str(sensor_id), str(e)
                )
                raise
            except ValueError as e:
                DataPipelineMetrics.record_failure(
                    stage, FailureType.VALIDATION_ERROR, str(sensor_id), str(e)
                )
                raise
            except Exception as e:
                DataPipelineMetrics.record_failure(
                    stage, FailureType.UNKNOWN, str(sensor_id), str(e)
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class FailureTracker:
    """Track and aggregate failures for analysis"""
    
    def __init__(self):
        self.failures = []
    
    def log_failure(self, stage: PipelineStage, failure_type: FailureType,
                   sensor_id: str, error_message: str, metadata: Dict[str, Any] = None):
        """Log a failure with full context"""
        failure_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'stage': stage.value,
            'failure_type': failure_type.value,
            'sensor_id': sensor_id,
            'error_message': error_message,
            'metadata': metadata or {}
        }
        
        self.failures.append(failure_record)
        
        # Also send to CloudWatch
        DataPipelineMetrics.record_failure(stage, failure_type, sensor_id, error_message)
        
        # Log to application logs
        logger.error(
            f"FAILURE_TRACKED: {failure_record}",
            extra={'failure_data': failure_record}
        )
    
    def get_failure_summary(self) -> Dict[str, Any]:
        """Get summary of failures"""
        if not self.failures:
            return {'total': 0, 'by_stage': {}, 'by_type': {}}
        
        summary = {
            'total': len(self.failures),
            'by_stage': {},
            'by_type': {},
            'recent_failures': self.failures[-10:]
        }
        
        for failure in self.failures:
            stage = failure['stage']
            ftype = failure['failure_type']
            
            summary['by_stage'][stage] = summary['by_stage'].get(stage, 0) + 1
            summary['by_type'][ftype] = summary['by_type'].get(ftype, 0) + 1
        
        return summary


# Global failure tracker instance
failure_tracker = FailureTracker()

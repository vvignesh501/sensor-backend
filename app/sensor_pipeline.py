"""
Example: Sensor Data Pipeline with Monitoring
Shows how to integrate monitoring into your data pipeline
"""

import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

import boto3
from sqlalchemy.ext.asyncio import AsyncSession
from kafka import KafkaProducer

from .monitoring import (
    monitor_pipeline_operation,
    PipelineStage,
    FailureType,
    DataPipelineMetrics,
    failure_tracker
)

logger = logging.getLogger(__name__)

# AWS S3 client
s3_client = boto3.client('s3', region_name='us-east-2')


class SensorDataPipeline:
    """
    Sensor data pipeline with comprehensive monitoring
    Handles: Ingestion -> PostgreSQL -> Kafka -> S3
    """
    
    def __init__(self, db_session: AsyncSession, kafka_producer: KafkaProducer,
                 s3_bucket: str):
        self.db = db_session
        self.kafka = kafka_producer
        self.s3_bucket = s3_bucket
    
    @monitor_pipeline_operation(PipelineStage.INGESTION)
    async def ingest_sensor_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest and validate sensor data
        Automatically tracked by @monitor_pipeline_operation decorator
        """
        sensor_id = sensor_data.get('sensor_id')
        
        # Validate data
        if not sensor_id:
            raise ValueError("Missing sensor_id")
        
        if 'value' not in sensor_data:
            raise ValueError("Missing sensor value")
        
        # Add timestamp
        sensor_data['ingested_at'] = datetime.utcnow().isoformat()
        
        # Track data size
        data_size = len(json.dumps(sensor_data).encode('utf-8'))
        DataPipelineMetrics.record_data_size(PipelineStage.INGESTION, data_size)
        
        logger.info(f"Ingested sensor data: {sensor_id}")
        return sensor_data
    
    @monitor_pipeline_operation(PipelineStage.POSTGRES_WRITE)
    async def write_to_postgres(self, sensor_data: Dict[str, Any]) -> int:
        """
        Write sensor data to PostgreSQL
        Failures are automatically tracked and logged
        """
        sensor_id = sensor_data['sensor_id']
        
        try:
            # Example: Insert into database
            query = """
                INSERT INTO sensor_readings (sensor_id, value, timestamp, metadata)
                VALUES (:sensor_id, :value, :timestamp, :metadata)
                RETURNING id
            """
            
            result = await self.db.execute(
                query,
                {
                    'sensor_id': sensor_id,
                    'value': sensor_data['value'],
                    'timestamp': sensor_data.get('timestamp', datetime.utcnow()),
                    'metadata': json.dumps(sensor_data.get('metadata', {}))
                }
            )
            
            await self.db.commit()
            record_id = result.scalar()
            
            logger.info(f"Wrote sensor data to PostgreSQL: {sensor_id}, record_id: {record_id}")
            return record_id
            
        except Exception as e:
            await self.db.rollback()
            
            # Manual failure tracking with additional context
            failure_tracker.log_failure(
                PipelineStage.POSTGRES_WRITE,
                FailureType.CONNECTION_ERROR if 'connection' in str(e).lower() else FailureType.UNKNOWN,
                sensor_id,
                str(e),
                metadata={'table': 'sensor_readings', 'operation': 'INSERT'}
            )
            raise
    
    @monitor_pipeline_operation(PipelineStage.KAFKA_PUBLISH)
    async def publish_to_kafka(self, sensor_data: Dict[str, Any], topic: str = 'sensor-data'):
        """
        Publish sensor data to Kafka
        Includes retry logic with monitoring
        """
        sensor_id = sensor_data['sensor_id']
        max_retries = 3
        
        for attempt in range(1, max_retries + 1):
            try:
                # Serialize data
                message = json.dumps(sensor_data).encode('utf-8')
                
                # Track data size
                DataPipelineMetrics.record_data_size(PipelineStage.KAFKA_PUBLISH, len(message))
                
                # Publish to Kafka
                future = self.kafka.send(topic, value=message, key=sensor_id.encode('utf-8'))
                
                # Wait for confirmation
                record_metadata = future.get(timeout=10)
                
                logger.info(
                    f"Published to Kafka: {sensor_id}, "
                    f"topic: {record_metadata.topic}, "
                    f"partition: {record_metadata.partition}, "
                    f"offset: {record_metadata.offset}"
                )
                return record_metadata
                
            except Exception as e:
                if attempt < max_retries:
                    # Record retry attempt
                    DataPipelineMetrics.record_retry_attempt(PipelineStage.KAFKA_PUBLISH, attempt)
                    logger.warning(f"Kafka publish failed, retrying ({attempt}/{max_retries}): {e}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    # Final failure
                    failure_tracker.log_failure(
                        PipelineStage.KAFKA_PUBLISH,
                        FailureType.TIMEOUT if 'timeout' in str(e).lower() else FailureType.NETWORK_ERROR,
                        sensor_id,
                        str(e),
                        metadata={'topic': topic, 'attempts': attempt}
                    )
                    raise
    
    @monitor_pipeline_operation(PipelineStage.S3_UPLOAD)
    async def upload_to_s3(self, sensor_data: Dict[str, Any], prefix: str = 'sensor-data'):
        """
        Upload sensor data to S3 for long-term storage
        """
        sensor_id = sensor_data['sensor_id']
        timestamp = datetime.utcnow()
        
        # Create S3 key with partitioning
        s3_key = (
            f"{prefix}/"
            f"year={timestamp.year}/"
            f"month={timestamp.month:02d}/"
            f"day={timestamp.day:02d}/"
            f"{sensor_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        try:
            # Serialize data
            data_bytes = json.dumps(sensor_data, indent=2).encode('utf-8')
            
            # Track data size
            DataPipelineMetrics.record_data_size(PipelineStage.S3_UPLOAD, len(data_bytes))
            
            # Upload to S3
            s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=data_bytes,
                ContentType='application/json',
                Metadata={
                    'sensor_id': sensor_id,
                    'ingested_at': sensor_data.get('ingested_at', '')
                }
            )
            
            logger.info(f"Uploaded to S3: {sensor_id}, key: {s3_key}")
            return s3_key
            
        except Exception as e:
            failure_tracker.log_failure(
                PipelineStage.S3_UPLOAD,
                FailureType.NETWORK_ERROR if 'network' in str(e).lower() else FailureType.UNKNOWN,
                sensor_id,
                str(e),
                metadata={'bucket': self.s3_bucket, 's3_key': s3_key}
            )
            raise
    
    async def process_sensor_batch(self, sensor_batch: List[Dict[str, Any]]):
        """
        Process a batch of sensor data through the entire pipeline
        """
        results = {
            'total': len(sensor_batch),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for sensor_data in sensor_batch:
            sensor_id = sensor_data.get('sensor_id', 'unknown')
            
            try:
                # Step 1: Ingest and validate
                validated_data = await self.ingest_sensor_data(sensor_data)
                
                # Step 2: Write to PostgreSQL
                record_id = await self.write_to_postgres(validated_data)
                validated_data['record_id'] = record_id
                
                # Step 3: Publish to Kafka (async, non-blocking)
                await self.publish_to_kafka(validated_data)
                
                # Step 4: Upload to S3 (for archival)
                s3_key = await self.upload_to_s3(validated_data)
                
                results['successful'] += 1
                logger.info(f"Successfully processed sensor: {sensor_id}")
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'sensor_id': sensor_id,
                    'error': str(e)
                })
                logger.error(f"Failed to process sensor {sensor_id}: {e}")
        
        # Log batch summary
        logger.info(
            f"Batch processing complete: "
            f"{results['successful']}/{results['total']} successful, "
            f"{results['failed']} failed"
        )
        
        return results


# Example usage in FastAPI endpoint
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/sensors/ingest")
async def ingest_sensors(
    sensor_data: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db)
):
    pipeline = SensorDataPipeline(
        db_session=db,
        kafka_producer=get_kafka_producer(),
        s3_bucket='my-sensor-data-bucket'
    )
    
    results = await pipeline.process_sensor_batch(sensor_data)
    
    return {
        'status': 'completed',
        'results': results,
        'failure_summary': failure_tracker.get_failure_summary()
    }
"""

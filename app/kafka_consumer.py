from kafka import KafkaConsumer
import json
import asyncpg
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, Dict, List

class AsyncDatabase:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = "postgresql://postgres:postgresql%409891@localhost:5432/sensordb"
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        print("✅ Kafka Consumer DB pool created: 5-20 connections")
    
    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            print("🔌 Kafka Consumer DB pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute_transaction(self, queries: List[tuple]) -> bool:
        async with self.get_connection() as conn:
            async with conn.transaction():
                for query, args in queries:
                    await conn.execute(query, *args)
                return True

class SensorEventConsumer:
    def __init__(self, bootstrap_servers=['localhost:9092']):
        self.consumer = KafkaConsumer(
            'sensor-test-events',
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='sensor-db-writer',
            client_id='consumer-node-1'
        )
        self.db = AsyncDatabase()
    

    
    async def init_sensor_table(self):
        async with self.db.get_connection() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sensor_tests (
                    id VARCHAR PRIMARY KEY,
                    sensor_type VARCHAR NOT NULL,
                    data_type VARCHAR DEFAULT 'raw_data',
                    s3_status VARCHAR NOT NULL,
                    s3_path VARCHAR,
                    test_metrics JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS kafka_logs (
                    id SERIAL PRIMARY KEY,
                    test_id VARCHAR NOT NULL,
                    user_id VARCHAR NOT NULL,
                    sensor_type VARCHAR NOT NULL,
                    kafka_start_time TIMESTAMP NOT NULL,
                    kafka_end_time TIMESTAMP NOT NULL,
                    processing_time_seconds DECIMAL(10,6) NOT NULL,
                    status VARCHAR NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    async def process_event(self, event_data):
        kafka_start = datetime.fromisoformat(event_data['kafka_start_time'])
        kafka_end = datetime.utcnow()
        processing_time = (kafka_end - kafka_start).total_seconds()
        
        try:
            # Store only Kafka processing log (sensor_tests already stored by FastAPI)
            queries = [
                ("INSERT INTO kafka_logs (test_id, user_id, sensor_type, kafka_start_time, kafka_end_time, processing_time_seconds, status) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                 (event_data['test_id'], event_data['user_id'], event_data['sensor_type'], kafka_start, kafka_end, processing_time, 'processed'))
            ]
            H
            await self.db.execute_transaction(queries)
            print(f"NODE1: Processed {event_data['test_id']} in {processing_time:.6f}s")
            
        except Exception as e:
            await self._log_processing_failure(event_data, kafka_start, kafka_end, processing_time, str(e))
            print(f"Error processing {event_data['test_id']}: {e}")
    
    async def _log_processing_failure(self, event_data, kafka_start, kafka_end, processing_time, error_msg):
        """Log processing failure to kafka_logs table"""
        try:
            queries = [
                ("INSERT INTO kafka_logs (test_id, user_id, sensor_type, kafka_start_time, kafka_end_time, processing_time_seconds, status) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                 (event_data.get('test_id', 'unknown'), event_data.get('user_id', 'unknown'), event_data.get('sensor_type', 'unknown'), kafka_start, kafka_end, processing_time, f'failed: {error_msg}'))
            ]
            await self.db.execute_transaction(queries)
        except Exception as log_error:
            print(f"Failed to log processing failure: {log_error}")
    
    async def start_consuming(self):
        await self.db.connect()
        await self.init_sensor_table()
        print("Starting Async Kafka Consumer Node 1...")
        
        try:
            for message in self.consumer:
                try:
                    print(f"NODE1: Processing partition {message.partition}, offset {message.offset}")
                    await self.process_event(message.value)
                except Exception as e:
                    print(f"NODE1: Error processing message: {e}")
        finally:
            await self.db.disconnect()

async def main():
    consumer = SensorEventConsumer()
    await consumer.start_consuming()

if __name__ == "__main__":
    asyncio.run(main())
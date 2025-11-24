from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter(prefix="/kafka", tags=["kafka-monitoring"])

class KafkaLogResponse(BaseModel):
    id: int
    test_id: str
    user_id: str
    sensor_type: str
    kafka_start_time: datetime
    kafka_end_time: datetime
    processing_time_seconds: float
    status: str
    created_at: datetime

class KafkaStatsResponse(BaseModel):
    total_processed: int
    successful: int
    failed: int
    average_processing_time: float
    min_processing_time: float
    max_processing_time: float
    throughput_per_second: float

def get_db_connection():
    return psycopg2.connect(
        "host=localhost port=5434 dbname=sensordb user=postgres password=postgresql@9891",
        cursor_factory=RealDictCursor
    )

@router.get("/logs", response_model=List[KafkaLogResponse])
async def get_kafka_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    test_id: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None)
):
    """Get Kafka processing logs with filtering"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Build dynamic query
        where_conditions = []
        params = []
        
        if status:
            where_conditions.append("status = %s")
            params.append(status)
        
        if user_id:
            where_conditions.append("user_id = %s")
            params.append(user_id)
            
        if test_id:
            where_conditions.append("test_id = %s")
            params.append(test_id)
            
        if start_time:
            where_conditions.append("created_at >= %s")
            params.append(start_time)
            
        if end_time:
            where_conditions.append("created_at <= %s")
            params.append(end_time)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
            SELECT * FROM kafka_logs 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
        """
        
        params.extend([limit, offset])
        cur.execute(query, params)
        
        logs = cur.fetchall()
        return [KafkaLogResponse(**log) for log in logs]
        
    finally:
        cur.close()
        conn.close()

@router.get("/stats", response_model=KafkaStatsResponse)
async def get_kafka_stats(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None)
):
    """Get Kafka processing statistics"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Default to last 24 hours if no time range specified
        if not start_time:
            start_time = datetime.now() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now()
        
        cur.execute("""
            SELECT 
                COUNT(*) as total_processed,
                COUNT(CASE WHEN status = 'processed' THEN 1 END) as successful,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                AVG(processing_time_seconds) as avg_processing_time,
                MIN(processing_time_seconds) as min_processing_time,
                MAX(processing_time_seconds) as max_processing_time,
                EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))) as time_span_seconds
            FROM kafka_logs 
            WHERE created_at BETWEEN %s AND %s
        """, (start_time, end_time))
        
        stats = cur.fetchone()
        
        # Calculate throughput
        time_span = stats['time_span_seconds'] or 1
        throughput = stats['total_processed'] / time_span if time_span > 0 else 0
        
        return KafkaStatsResponse(
            total_processed=stats['total_processed'],
            successful=stats['successful'],
            failed=stats['failed'],
            average_processing_time=float(stats['avg_processing_time'] or 0),
            min_processing_time=float(stats['min_processing_time'] or 0),
            max_processing_time=float(stats['max_processing_time'] or 0),
            throughput_per_second=throughput
        )
        
    finally:
        cur.close()
        conn.close()

@router.get("/real-time")
async def get_real_time_stats():
    """Get real-time processing statistics (last 5 minutes)"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        
        cur.execute("""
            SELECT 
                COUNT(*) as recent_processed,
                AVG(processing_time_seconds) as avg_processing_time,
                COUNT(CASE WHEN status = 'processed' THEN 1 END) as successful,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
            FROM kafka_logs 
            WHERE created_at >= %s
        """, (five_minutes_ago,))
        
        stats = cur.fetchone()
        
        return {
            "recent_processed": stats['recent_processed'],
            "success_rate": (stats['successful'] / stats['recent_processed'] * 100) if stats['recent_processed'] > 0 else 0,
            "average_processing_time": float(stats['avg_processing_time'] or 0),
            "throughput_per_minute": stats['recent_processed'] / 5
        }
        
    finally:
        cur.close()
        conn.close()

@router.get("/test/{test_id}")
async def get_test_processing_status(test_id: str):
    """Get processing status for specific test ID"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check sensor_tests table
        cur.execute("SELECT * FROM sensor_tests WHERE id = %s", (test_id,))
        sensor_test = cur.fetchone()
        
        # Check kafka_logs table
        cur.execute("SELECT * FROM kafka_logs WHERE test_id = %s", (test_id,))
        kafka_log = cur.fetchone()
        
        if not sensor_test and not kafka_log:
            raise HTTPException(status_code=404, detail="Test ID not found")
        
        return {
            "test_id": test_id,
            "sensor_data_stored": sensor_test is not None,
            "kafka_processed": kafka_log is not None,
            "s3_status": sensor_test.get('s3_status') if sensor_test else None,
            "processing_time": float(kafka_log.get('processing_time_seconds', 0)) if kafka_log else None,
            "kafka_status": kafka_log.get('status') if kafka_log else None,
            "created_at": kafka_log.get('created_at') if kafka_log else None
        }
        
    finally:
        cur.close()
        conn.close()
from kafka import KafkaProducer
import json
import logging
from datetime import datetime
from typing import Dict, List

class SensorEventProducer:
    def __init__(self, bootstrap_servers=['localhost:9092']):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            retries=5,
            retry_backoff_ms=300,
            request_timeout_ms=30000,
            max_block_ms=10000,
            batch_size=16384,
            linger_ms=10,
            acks='all'
        )
        self.topic = 'sensor-test-events'
        self.processing_results = []
    
    def send_test_event(self, event_data):
        start_time = datetime.utcnow()
        for attempt in range(3):
            try:
                future = self.producer.send(
                    self.topic,
                    key=event_data['test_id'],
                    value=event_data
                )
                record_metadata = future.get(timeout=10)
                
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                self._record_result(event_data, processing_time, "Success - Sent to Kafka")
                return True
                
            except Exception as e:
                if attempt == 2:  # Last attempt
                    processing_time = (datetime.utcnow() - start_time).total_seconds()
                    self._record_result(event_data, processing_time, f"Failed - {str(e)}")
                    logging.error(f"Failed to send Kafka event after 3 attempts: {e}")
                    return False
        return False
    
    def _record_result(self, event_data: Dict, processing_time: float, status: str):
        """Record processing result for frontend display"""
        result = {
            "test_id": event_data.get('test_id', 'unknown'),
            "user": event_data.get('user_id', 'unknown'),
            "sensor_type": event_data.get('sensor_type', 'unknown'),
            "processing_time": round(processing_time, 6),
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Keep only last 1000 results to prevent memory issues
        self.processing_results.append(result)
        if len(self.processing_results) > 1000:
            self.processing_results = self.processing_results[-1000:]
    
    def get_processing_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent processing logs for frontend display"""
        return self.processing_results[-limit:] if self.processing_results else []
    
    def get_processing_stats(self) -> Dict:
        """Get processing statistics for frontend display"""
        if not self.processing_results:
            return {
                "total_processed": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0,
                "avg_processing_time": 0
            }
        
        total = len(self.processing_results)
        successful = len([r for r in self.processing_results if "Success" in r["status"]])
        failed = total - successful
        avg_time = sum(r["processing_time"] for r in self.processing_results) / total
        
        return {
            "total_processed": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round((successful / total) * 100, 2) if total > 0 else 0,
            "avg_processing_time": round(avg_time, 6)
        }
    
    def clear_results(self):
        """Clear processing results"""
        self.processing_results = []
    
    def clear_old_results(self, keep_recent: int = 50):
        """Clear old results, keep only recent ones"""
        if len(self.processing_results) > keep_recent:
            self.processing_results = self.processing_results[-keep_recent:]
            return len(self.processing_results)
        return 0
    
    def close(self):
        self.producer.close()
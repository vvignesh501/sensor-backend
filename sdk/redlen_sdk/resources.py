"""
API Resource Classes
Organized endpoints by resource type
"""
from typing import List, Optional, Dict
from datetime import datetime

from .models import Sensor, SensorReading, SensorStatistics, PaginatedResponse


class BaseResource:
    """Base class for API resources"""
    
    def __init__(self, client):
        self.client = client


class SensorResource(BaseResource):
    """Sensor API endpoints"""
    
    def list(
        self,
        page: int = 1,
        page_size: int = 100,
        location: Optional[str] = None
    ) -> List[Sensor]:
        """
        List all sensors
        
        Args:
            page: Page number
            page_size: Items per page
            location: Filter by location
        
        Returns:
            List of Sensor objects
        """
        params = {
            "page": page,
            "page_size": page_size
        }
        if location:
            params["location"] = location
        
        response = self.client.request("GET", "/api/v1/sensors", params=params)
        return [Sensor(**sensor) for sensor in response.get("items", response)]
    
    def get(self, sensor_id: str) -> Sensor:
        """
        Get specific sensor
        
        Args:
            sensor_id: Sensor ID
        
        Returns:
            Sensor object
        """
        response = self.client.request("GET", f"/api/v1/sensors/{sensor_id}")
        return Sensor(**response)
    
    def create(
        self,
        sensor_id: str,
        sensor_type: str,
        location: str
    ) -> Sensor:
        """
        Create new sensor
        
        Args:
            sensor_id: Unique sensor ID
            sensor_type: Type of sensor
            location: Sensor location
        
        Returns:
            Created Sensor object
        """
        data = {
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "location": location
        }
        response = self.client.request("POST", "/api/v1/sensors", json=data)
        return Sensor(**response)
    
    def update(
        self,
        sensor_id: str,
        status: Optional[str] = None,
        location: Optional[str] = None
    ) -> Sensor:
        """
        Update sensor
        
        Args:
            sensor_id: Sensor ID
            status: New status
            location: New location
        
        Returns:
            Updated Sensor object
        """
        data = {}
        if status:
            data["status"] = status
        if location:
            data["location"] = location
        
        response = self.client.request("PUT", f"/api/v1/sensors/{sensor_id}", json=data)
        return Sensor(**response)
    
    def delete(self, sensor_id: str) -> bool:
        """
        Delete sensor
        
        Args:
            sensor_id: Sensor ID
        
        Returns:
            True if deleted successfully
        """
        self.client.request("DELETE", f"/api/v1/sensors/{sensor_id}")
        return True


class ReadingResource(BaseResource):
    """Sensor reading API endpoints"""
    
    def create(
        self,
        sensor_id: str,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        pressure: Optional[float] = None,
        battery_level: float = 100.0,
        signal_strength: int = -50,
        timestamp: Optional[datetime] = None
    ) -> SensorReading:
        """
        Create sensor reading
        
        Args:
            sensor_id: Sensor ID
            temperature: Temperature in Celsius
            humidity: Humidity percentage
            pressure: Pressure in hPa
            battery_level: Battery level percentage
            signal_strength: Signal strength in dBm
            timestamp: Reading timestamp
        
        Returns:
            Created SensorReading object
        """
        data = {
            "sensor_id": sensor_id,
            "temperature": temperature,
            "humidity": humidity,
            "pressure": pressure,
            "battery_level": battery_level,
            "signal_strength": signal_strength,
            "timestamp": (timestamp or datetime.now()).isoformat()
        }
        
        # Validate with Pydantic model
        reading = SensorReading(**data)
        
        response = self.client.request(
            "POST",
            f"/api/v1/sensors/{sensor_id}/readings",
            json=reading.dict()
        )
        return SensorReading(**response)
    
    def list(
        self,
        sensor_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SensorReading]:
        """
        List sensor readings
        
        Args:
            sensor_id: Sensor ID
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of readings
        
        Returns:
            List of SensorReading objects
        """
        params = {"limit": limit}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        
        response = self.client.request(
            "GET",
            f"/api/v1/sensors/{sensor_id}/readings",
            params=params
        )
        return [SensorReading(**reading) for reading in response]
    
    def get_latest(self, sensor_id: str) -> Optional[SensorReading]:
        """
        Get latest reading for sensor
        
        Args:
            sensor_id: Sensor ID
        
        Returns:
            Latest SensorReading or None
        """
        response = self.client.request(
            "GET",
            f"/api/v1/sensors/{sensor_id}/readings/latest"
        )
        return SensorReading(**response) if response else None


class AnalyticsResource(BaseResource):
    """Analytics API endpoints"""
    
    def get_statistics(
        self,
        sensor_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> SensorStatistics:
        """
        Get sensor statistics
        
        Args:
            sensor_id: Sensor ID
            start_date: Start date
            end_date: End date
        
        Returns:
            SensorStatistics object
        """
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        
        response = self.client.request(
            "GET",
            f"/api/v1/analytics/sensors/{sensor_id}/statistics",
            params=params
        )
        return SensorStatistics(**response)
    
    def get_health_report(self) -> Dict:
        """
        Get overall system health report
        
        Returns:
            Health report dictionary
        """
        return self.client.request("GET", "/api/v1/analytics/health")
    
    def get_building_summary(self, building: str) -> Dict:
        """
        Get building summary
        
        Args:
            building: Building name
        
        Returns:
            Building summary dictionary
        """
        return self.client.request(
            "GET",
            f"/api/v1/analytics/buildings/{building}/summary"
        )

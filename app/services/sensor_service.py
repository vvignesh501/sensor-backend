"""
Service Layer - Business Logic
Interview Topics: Service Layer Pattern, Single Responsibility, Dependency Injection
"""
from typing import List, Optional, Dict
from datetime import datetime
from ..domain.entities import (
    Sensor, SensorReading, SensorStatus, SensorType, Location,
    SensorValidator, TemperatureValidator, HumidityValidator, CompositeValidator
)
from ..domain.repositories import ISensorRepository, ISensorReadingRepository


class SensorService:
    """
    Service class encapsulating business logic
    Interview: Explain Service Layer, why separate from controllers
    """
    
    def __init__(
        self,
        sensor_repo: ISensorRepository,
        reading_repo: ISensorReadingRepository
    ):
        """
        Dependency Injection via constructor
        Interview: Explain DI benefits, testability
        """
        self._sensor_repo = sensor_repo
        self._reading_repo = reading_repo
        self._validator = CompositeValidator([
            TemperatureValidator(),
            HumidityValidator()
        ])
    
    async def create_sensor(
        self,
        sensor_id: str,
        sensor_type: SensorType,
        location: Location
    ) -> Sensor:
        """
        Create new sensor with validation
        Interview: Business rule enforcement
        """
        # Check if sensor already exists
        if await self._sensor_repo.exists(sensor_id):
            raise ValueError(f"Sensor {sensor_id} already exists")
        
        # Create sensor entity
        sensor = Sensor(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            location=location
        )
        
        # Persist
        return await self._sensor_repo.save(sensor)
    
    async def get_sensor(self, sensor_id: str) -> Optional[Sensor]:
        """Get sensor by ID"""
        return await self._sensor_repo.get_by_id(sensor_id)
    
    async def get_all_sensors(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Sensor]:
        """Get all sensors with pagination"""
        return await self._sensor_repo.get_all(skip, limit)
    
    async def get_sensors_by_building(self, building: str) -> List[Sensor]:
        """Get sensors in specific building"""
        return await self._sensor_repo.get_by_location(building)
    
    async def add_reading(
        self,
        sensor_id: str,
        reading: SensorReading
    ) -> SensorReading:
        """
        Add reading to sensor with validation
        Interview: Transaction management, validation
        """
        # Get sensor
        sensor = await self._sensor_repo.get_by_id(sensor_id)
        if not sensor:
            raise ValueError(f"Sensor {sensor_id} not found")
        
        # Validate reading
        if not self._validator.validate(reading):
            raise ValueError(self._validator.get_error_message())
        
        # Add reading to sensor (business logic)
        sensor.add_reading(reading)
        
        # Persist both
        await self._reading_repo.save(reading)
        await self._sensor_repo.save(sensor)
        
        return reading
    
    async def get_sensor_statistics(self, sensor_id: str) -> Dict:
        """
        Get aggregated statistics for sensor
        Interview: Aggregation, data transformation
        """
        sensor = await self._sensor_repo.get_by_id(sensor_id)
        if not sensor:
            raise ValueError(f"Sensor {sensor_id} not found")
        
        stats = await self._reading_repo.get_statistics(sensor_id)
        
        return {
            "sensor_id": sensor_id,
            "sensor_type": sensor.sensor_type.value,
            "location": str(sensor.location),
            "status": sensor.status.value,
            "statistics": stats
        }
    
    async def activate_sensor(self, sensor_id: str) -> Sensor:
        """
        Activate sensor
        Interview: State management
        """
        sensor = await self._sensor_repo.get_by_id(sensor_id)
        if not sensor:
            raise ValueError(f"Sensor {sensor_id} not found")
        
        sensor.activate()
        return await self._sensor_repo.save(sensor)
    
    async def deactivate_sensor(self, sensor_id: str) -> Sensor:
        """Deactivate sensor"""
        sensor = await self._sensor_repo.get_by_id(sensor_id)
        if not sensor:
            raise ValueError(f"Sensor {sensor_id} not found")
        
        sensor.deactivate()
        return await self._sensor_repo.save(sensor)
    
    async def get_sensors_needing_maintenance(self) -> List[Sensor]:
        """
        Get all sensors that need maintenance
        Interview: Business logic, filtering
        """
        all_sensors = await self._sensor_repo.get_all()
        
        maintenance_sensors = []
        for sensor in all_sensors:
            latest_reading = sensor.get_latest_reading()
            if latest_reading and latest_reading.needs_maintenance():
                maintenance_sensors.append(sensor)
        
        return maintenance_sensors
    
    async def delete_sensor(self, sensor_id: str) -> bool:
        """
        Delete sensor
        Interview: Cascade deletion, cleanup
        """
        sensor = await self._sensor_repo.get_by_id(sensor_id)
        if not sensor:
            return False
        
        # In production: Also delete associated readings
        return await self._sensor_repo.delete(sensor_id)


class SensorAnalyticsService:
    """
    Separate service for analytics
    Interview: Single Responsibility Principle
    """
    
    def __init__(
        self,
        sensor_repo: ISensorRepository,
        reading_repo: ISensorReadingRepository
    ):
        self._sensor_repo = sensor_repo
        self._reading_repo = reading_repo
    
    async def get_building_summary(self, building: str) -> Dict:
        """
        Get summary statistics for a building
        Interview: Aggregation, complex queries
        """
        sensors = await self._sensor_repo.get_by_location(building)
        
        total_sensors = len(sensors)
        active_sensors = sum(1 for s in sensors if s.status == SensorStatus.ACTIVE)
        warning_sensors = sum(1 for s in sensors if s.status == SensorStatus.WARNING)
        
        # Get average temperature across all sensors
        all_temps = []
        for sensor in sensors:
            avg_temp = sensor.get_average_temperature()
            if avg_temp:
                all_temps.append(avg_temp)
        
        return {
            "building": building,
            "total_sensors": total_sensors,
            "active_sensors": active_sensors,
            "warning_sensors": warning_sensors,
            "average_temperature": sum(all_temps) / len(all_temps) if all_temps else None
        }
    
    async def get_sensor_health_report(self) -> Dict:
        """
        Generate health report for all sensors
        Interview: Reporting, data aggregation
        """
        all_sensors = await self._sensor_repo.get_all()
        
        status_counts = {status: 0 for status in SensorStatus}
        for sensor in all_sensors:
            status_counts[sensor.status] += 1
        
        return {
            "total_sensors": len(all_sensors),
            "status_breakdown": {
                status.value: count 
                for status, count in status_counts.items()
            },
            "health_percentage": (
                status_counts[SensorStatus.ACTIVE] / len(all_sensors) * 100
                if all_sensors else 0
            )
        }
    
    async def get_trending_data(
        self,
        sensor_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Get trending data for time period
        Interview: Time-series analysis
        """
        readings = await self._reading_repo.get_by_sensor(
            sensor_id, start_date, end_date
        )
        
        if not readings:
            return {"sensor_id": sensor_id, "data_points": 0, "trend": []}
        
        # Calculate trend
        trend_data = [
            {
                "timestamp": r.timestamp.isoformat(),
                "temperature": r.temperature,
                "humidity": r.humidity,
                "battery_level": r.battery_level
            }
            for r in readings
        ]
        
        return {
            "sensor_id": sensor_id,
            "data_points": len(readings),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "trend": trend_data
        }

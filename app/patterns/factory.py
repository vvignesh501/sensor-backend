"""
Factory and Builder Patterns
Interview Topics: Creational Patterns, Object Creation
"""
from typing import Dict, Optional
from datetime import datetime
from ..domain.entities import (
    Sensor, SensorReading, SensorType, SensorStatus, Location, User
)


class SensorFactory:
    """
    Factory Pattern - Centralized object creation
    Interview: When to use Factory, benefits
    """
    
    @staticmethod
    def create_temperature_sensor(
        sensor_id: str,
        location: Location
    ) -> Sensor:
        """Create temperature-specific sensor"""
        return Sensor(
            sensor_id=sensor_id,
            sensor_type=SensorType.TEMPERATURE,
            location=location,
            status=SensorStatus.ACTIVE
        )
    
    @staticmethod
    def create_humidity_sensor(
        sensor_id: str,
        location: Location
    ) -> Sensor:
        """Create humidity-specific sensor"""
        return Sensor(
            sensor_id=sensor_id,
            sensor_type=SensorType.HUMIDITY,
            location=location,
            status=SensorStatus.ACTIVE
        )
    
    @staticmethod
    def create_multi_sensor(
        sensor_id: str,
        location: Location
    ) -> Sensor:
        """Create multi-purpose sensor"""
        return Sensor(
            sensor_id=sensor_id,
            sensor_type=SensorType.MULTI_SENSOR,
            location=location,
            status=SensorStatus.ACTIVE
        )
    
    @staticmethod
    def create_from_type(
        sensor_id: str,
        sensor_type: str,
        location: Location
    ) -> Sensor:
        """
        Factory method with type parameter
        Interview: Explain polymorphic creation
        """
        type_map = {
            "temperature": SensorFactory.create_temperature_sensor,
            "humidity": SensorFactory.create_humidity_sensor,
            "multi": SensorFactory.create_multi_sensor
        }
        
        factory_method = type_map.get(sensor_type.lower())
        if not factory_method:
            raise ValueError(f"Unknown sensor type: {sensor_type}")
        
        return factory_method(sensor_id, location)


class SensorReadingBuilder:
    """
    Builder Pattern - Complex object construction
    Interview: When to use Builder vs Constructor
    """
    
    def __init__(self, sensor_id: str):
        self._sensor_id = sensor_id
        self._timestamp = datetime.now()
        self._temperature: Optional[float] = None
        self._humidity: Optional[float] = None
        self._pressure: Optional[float] = None
        self._battery_level: float = 100.0
        self._signal_strength: int = -50
    
    def with_temperature(self, temperature: float) -> 'SensorReadingBuilder':
        """Fluent interface for temperature"""
        self._temperature = temperature
        return self
    
    def with_humidity(self, humidity: float) -> 'SensorReadingBuilder':
        """Fluent interface for humidity"""
        self._humidity = humidity
        return self
    
    def with_pressure(self, pressure: float) -> 'SensorReadingBuilder':
        """Fluent interface for pressure"""
        self._pressure = pressure
        return self
    
    def with_battery_level(self, battery_level: float) -> 'SensorReadingBuilder':
        """Fluent interface for battery"""
        self._battery_level = battery_level
        return self
    
    def with_signal_strength(self, signal_strength: int) -> 'SensorReadingBuilder':
        """Fluent interface for signal"""
        self._signal_strength = signal_strength
        return self
    
    def with_timestamp(self, timestamp: datetime) -> 'SensorReadingBuilder':
        """Fluent interface for timestamp"""
        self._timestamp = timestamp
        return self
    
    def build(self) -> SensorReading:
        """
        Build final object
        Interview: Explain validation in builder
        """
        return SensorReading(
            sensor_id=self._sensor_id,
            timestamp=self._timestamp,
            temperature=self._temperature,
            humidity=self._humidity,
            pressure=self._pressure,
            battery_level=self._battery_level,
            signal_strength=self._signal_strength
        )


class UserFactory:
    """
    Factory for creating users with different roles
    Interview: Role-based object creation
    """
    
    @staticmethod
    def create_admin_user(
        user_id: str,
        username: str,
        email: str,
        hashed_password: str
    ) -> User:
        """Create admin user with full permissions"""
        return User(
            user_id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
            roles=['admin', 'writer', 'reader']
        )
    
    @staticmethod
    def create_writer_user(
        user_id: str,
        username: str,
        email: str,
        hashed_password: str
    ) -> User:
        """Create writer user"""
        return User(
            user_id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
            roles=['writer', 'reader']
        )
    
    @staticmethod
    def create_reader_user(
        user_id: str,
        username: str,
        email: str,
        hashed_password: str
    ) -> User:
        """Create read-only user"""
        return User(
            user_id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
            roles=['reader']
        )


class LocationBuilder:
    """
    Builder for Location value object
    Interview: Builder for immutable objects
    """
    
    def __init__(self):
        self._building: Optional[str] = None
        self._floor: Optional[int] = None
        self._room: Optional[str] = None
    
    def in_building(self, building: str) -> 'LocationBuilder':
        """Set building"""
        self._building = building
        return self
    
    def on_floor(self, floor: int) -> 'LocationBuilder':
        """Set floor"""
        self._floor = floor
        return self
    
    def in_room(self, room: str) -> 'LocationBuilder':
        """Set room"""
        self._room = room
        return self
    
    def build(self) -> Location:
        """Build immutable location"""
        if not all([self._building, self._floor is not None, self._room]):
            raise ValueError("All location fields are required")
        
        return Location(
            building=self._building,
            floor=self._floor,
            room=self._room
        )


# Example usage demonstrating patterns
def demo_patterns():
    """
    Demonstrate factory and builder patterns
    Interview: Show practical usage
    """
    print("=== Factory Pattern Demo ===")
    
    # Using factory
    location = Location("Building_A", 1, "Room_101")
    sensor = SensorFactory.create_temperature_sensor("TEMP_001", location)
    print(f"Created sensor: {sensor.sensor_id}, Type: {sensor.sensor_type.value}")
    
    print("\n=== Builder Pattern Demo ===")
    
    # Using builder for complex object
    reading = (SensorReadingBuilder("TEMP_001")
               .with_temperature(22.5)
               .with_humidity(45.0)
               .with_battery_level(85.0)
               .with_signal_strength(-65)
               .build())
    
    print(f"Created reading: Temp={reading.temperature}°C, Humidity={reading.humidity}%")
    
    print("\n=== Location Builder Demo ===")
    
    # Using builder for value object
    location2 = (LocationBuilder()
                 .in_building("Building_B")
                 .on_floor(2)
                 .in_room("Room_202")
                 .build())
    
    print(f"Created location: {location2}")


if __name__ == "__main__":
    demo_patterns()

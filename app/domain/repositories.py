"""
Repository Pattern - Abstract data access
Interview Topics: Repository Pattern, Dependency Inversion, Interface Segregation
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from .entities import Sensor, SensorReading, User


class ISensorRepository(ABC):
    """
    Repository Interface - Dependency Inversion Principle
    Interview: Explain why we use interfaces, benefits of abstraction
    """
    
    @abstractmethod
    async def get_by_id(self, sensor_id: str) -> Optional[Sensor]:
        """Get sensor by ID"""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Sensor]:
        """Get all sensors with pagination"""
        pass
    
    @abstractmethod
    async def get_by_location(self, building: str) -> List[Sensor]:
        """Get sensors by location"""
        pass
    
    @abstractmethod
    async def save(self, sensor: Sensor) -> Sensor:
        """Save or update sensor"""
        pass
    
    @abstractmethod
    async def delete(self, sensor_id: str) -> bool:
        """Delete sensor"""
        pass
    
    @abstractmethod
    async def exists(self, sensor_id: str) -> bool:
        """Check if sensor exists"""
        pass


class IUserRepository(ABC):
    """
    User Repository Interface
    Interview: Interface Segregation Principle
    """
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """Save or update user"""
        pass
    
    @abstractmethod
    async def exists(self, username: str) -> bool:
        """Check if user exists"""
        pass


class ISensorReadingRepository(ABC):
    """
    Sensor Reading Repository Interface
    Interview: Separation of Concerns
    """
    
    @abstractmethod
    async def save(self, reading: SensorReading) -> SensorReading:
        """Save sensor reading"""
        pass
    
    @abstractmethod
    async def get_by_sensor(
        self, 
        sensor_id: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[SensorReading]:
        """Get readings for a sensor"""
        pass
    
    @abstractmethod
    async def get_latest(self, sensor_id: str) -> Optional[SensorReading]:
        """Get latest reading for sensor"""
        pass
    
    @abstractmethod
    async def get_statistics(self, sensor_id: str) -> Dict:
        """Get aggregated statistics"""
        pass


# Concrete Implementation - In-Memory (for demo)
class InMemorySensorRepository(ISensorRepository):
    """
    Concrete implementation using in-memory storage
    Interview: Explain how this enables testing, flexibility
    """
    
    def __init__(self):
        self._sensors: Dict[str, Sensor] = {}
    
    async def get_by_id(self, sensor_id: str) -> Optional[Sensor]:
        return self._sensors.get(sensor_id)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Sensor]:
        sensors = list(self._sensors.values())
        return sensors[skip:skip + limit]
    
    async def get_by_location(self, building: str) -> List[Sensor]:
        return [
            sensor for sensor in self._sensors.values()
            if sensor.location.building == building
        ]
    
    async def save(self, sensor: Sensor) -> Sensor:
        self._sensors[sensor.sensor_id] = sensor
        return sensor
    
    async def delete(self, sensor_id: str) -> bool:
        if sensor_id in self._sensors:
            del self._sensors[sensor_id]
            return True
        return False
    
    async def exists(self, sensor_id: str) -> bool:
        return sensor_id in self._sensors


class InMemoryUserRepository(IUserRepository):
    """Concrete user repository implementation"""
    
    def __init__(self):
        self._users: Dict[str, User] = {}
    
    async def get_by_username(self, username: str) -> Optional[User]:
        return self._users.get(username)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        for user in self._users.values():
            if user.email == email:
                return user
        return None
    
    async def save(self, user: User) -> User:
        self._users[user.username] = user
        return user
    
    async def exists(self, username: str) -> bool:
        return username in self._users


class InMemorySensorReadingRepository(ISensorReadingRepository):
    """Concrete sensor reading repository"""
    
    def __init__(self):
        self._readings: List[SensorReading] = []
    
    async def save(self, reading: SensorReading) -> SensorReading:
        self._readings.append(reading)
        return reading
    
    async def get_by_sensor(
        self,
        sensor_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[SensorReading]:
        readings = [r for r in self._readings if r.sensor_id == sensor_id]
        
        if start_date:
            readings = [r for r in readings if r.timestamp >= start_date]
        if end_date:
            readings = [r for r in readings if r.timestamp <= end_date]
        
        return sorted(readings, key=lambda r: r.timestamp)
    
    async def get_latest(self, sensor_id: str) -> Optional[SensorReading]:
        sensor_readings = [r for r in self._readings if r.sensor_id == sensor_id]
        if not sensor_readings:
            return None
        return max(sensor_readings, key=lambda r: r.timestamp)
    
    async def get_statistics(self, sensor_id: str) -> Dict:
        readings = [r for r in self._readings if r.sensor_id == sensor_id]
        
        if not readings:
            return {}
        
        temps = [r.temperature for r in readings if r.temperature is not None]
        humidities = [r.humidity for r in readings if r.humidity is not None]
        
        return {
            "count": len(readings),
            "avg_temperature": sum(temps) / len(temps) if temps else None,
            "avg_humidity": sum(humidities) / len(humidities) if humidities else None,
            "min_temperature": min(temps) if temps else None,
            "max_temperature": max(temps) if temps else None,
        }

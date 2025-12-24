"""
Domain Entities - Core Business Objects
Demonstrates: Encapsulation, Data Classes, Value Objects
Interview Topics: Domain-Driven Design, Entity vs Value Object
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from abc import ABC, abstractmethod


class SensorStatus(Enum):
    """Enum for sensor status - Type Safety"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    WARNING = "warning"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class SensorType(Enum):
    """Enum for sensor types"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    MULTI_SENSOR = "multi_sensor"


@dataclass(frozen=True)
class Location:
    """
    Value Object - Immutable location
    Interview: Explain difference between Entity and Value Object
    """
    building: str
    floor: int
    room: str
    
    def __str__(self) -> str:
        return f"{self.building}-Floor{self.floor}-{self.room}"
    
    def is_same_building(self, other: 'Location') -> bool:
        """Business logic in value object"""
        return self.building == other.building


@dataclass
class SensorReading:
    """
    Entity - Has identity and lifecycle
    Interview: Explain Entity characteristics
    """
    sensor_id: str
    timestamp: datetime
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    battery_level: float = 100.0
    signal_strength: int = -50
    
    def __post_init__(self):
        """Validation in constructor"""
        if self.battery_level < 0 or self.battery_level > 100:
            raise ValueError("Battery level must be between 0 and 100")
        if self.signal_strength > 0:
            raise ValueError("Signal strength must be negative (dBm)")
    
    def is_battery_low(self, threshold: float = 20.0) -> bool:
        """Business rule encapsulation"""
        return self.battery_level < threshold
    
    def is_signal_weak(self, threshold: int = -80) -> bool:
        """Business rule encapsulation"""
        return self.signal_strength < threshold
    
    def needs_maintenance(self) -> bool:
        """Complex business logic"""
        return self.is_battery_low() or self.is_signal_weak()


@dataclass
class Sensor:
    """
    Aggregate Root - Main entity with business logic
    Interview: Explain Aggregate pattern, Encapsulation
    """
    sensor_id: str
    sensor_type: SensorType
    location: Location
    status: SensorStatus = SensorStatus.ACTIVE
    readings: List[SensorReading] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_reading(self, reading: SensorReading) -> None:
        """
        Encapsulation - Control how readings are added
        Interview: Explain why not direct list access
        """
        if reading.sensor_id != self.sensor_id:
            raise ValueError("Reading sensor_id must match sensor")
        
        self.readings.append(reading)
        self.updated_at = datetime.now()
        
        # Auto-update status based on reading
        if reading.needs_maintenance():
            self.status = SensorStatus.WARNING
    
    def get_latest_reading(self) -> Optional[SensorReading]:
        """Business logic method"""
        if not self.readings:
            return None
        return max(self.readings, key=lambda r: r.timestamp)
    
    def get_average_temperature(self) -> Optional[float]:
        """Aggregate calculation"""
        temps = [r.temperature for r in self.readings if r.temperature is not None]
        return sum(temps) / len(temps) if temps else None
    
    def activate(self) -> None:
        """State transition with validation"""
        if self.status == SensorStatus.ERROR:
            raise ValueError("Cannot activate sensor in ERROR state")
        self.status = SensorStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """State transition"""
        self.status = SensorStatus.INACTIVE
        self.updated_at = datetime.now()
    
    def mark_for_maintenance(self) -> None:
        """State transition"""
        self.status = SensorStatus.MAINTENANCE
        self.updated_at = datetime.now()


@dataclass
class User:
    """
    User Entity with role-based permissions
    Interview: Explain authentication vs authorization
    """
    user_id: str
    username: str
    email: str
    hashed_password: str
    roles: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    
    def has_role(self, role: str) -> bool:
        """Authorization check"""
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Multiple role check"""
        return any(role in self.roles for role in roles)
    
    def can_write(self) -> bool:
        """Permission check"""
        return self.has_any_role(['admin', 'writer'])
    
    def can_delete(self) -> bool:
        """Permission check"""
        return self.has_role('admin')
    
    def update_last_login(self) -> None:
        """Track user activity"""
        self.last_login = datetime.now()


# Abstract Base Class for demonstrating polymorphism
class SensorValidator(ABC):
    """
    Abstract base class for validation strategies
    Interview: Explain Strategy Pattern, Polymorphism
    """
    
    @abstractmethod
    def validate(self, reading: SensorReading) -> bool:
        """Validate sensor reading"""
        pass
    
    @abstractmethod
    def get_error_message(self) -> str:
        """Get validation error message"""
        pass


class TemperatureValidator(SensorValidator):
    """Concrete validator for temperature"""
    
    def __init__(self, min_temp: float = -40.0, max_temp: float = 85.0):
        self.min_temp = min_temp
        self.max_temp = max_temp
    
    def validate(self, reading: SensorReading) -> bool:
        if reading.temperature is None:
            return True
        return self.min_temp <= reading.temperature <= self.max_temp
    
    def get_error_message(self) -> str:
        return f"Temperature must be between {self.min_temp}°C and {self.max_temp}°C"


class HumidityValidator(SensorValidator):
    """Concrete validator for humidity"""
    
    def __init__(self, min_humidity: float = 0.0, max_humidity: float = 100.0):
        self.min_humidity = min_humidity
        self.max_humidity = max_humidity
    
    def validate(self, reading: SensorReading) -> bool:
        if reading.humidity is None:
            return True
        return self.min_humidity <= reading.humidity <= self.max_humidity
    
    def get_error_message(self) -> str:
        return f"Humidity must be between {self.min_humidity}% and {self.max_humidity}%"


class CompositeValidator(SensorValidator):
    """
    Composite Pattern - Combine multiple validators
    Interview: Explain Composite Pattern
    """
    
    def __init__(self, validators: List[SensorValidator]):
        self.validators = validators
    
    def validate(self, reading: SensorReading) -> bool:
        return all(v.validate(reading) for v in self.validators)
    
    def get_error_message(self) -> str:
        return " AND ".join(v.get_error_message() for v in self.validators)

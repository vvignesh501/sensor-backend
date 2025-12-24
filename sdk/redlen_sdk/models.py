"""
Data Models
Pydantic models for type safety and validation
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class SensorReading(BaseModel):
    """Sensor reading data model"""
    sensor_id: str
    timestamp: datetime
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    battery_level: float = Field(ge=0, le=100)
    signal_strength: int = Field(le=0)
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if v is not None and not -40 <= v <= 85:
            raise ValueError('Temperature must be between -40 and 85°C')
        return v
    
    @validator('humidity')
    def validate_humidity(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError('Humidity must be between 0 and 100%')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Sensor(BaseModel):
    """Sensor data model"""
    sensor_id: str
    sensor_type: str
    location: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SensorStatistics(BaseModel):
    """Sensor statistics model"""
    sensor_id: str
    count: int
    avg_temperature: Optional[float] = None
    avg_humidity: Optional[float] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: List[dict]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool

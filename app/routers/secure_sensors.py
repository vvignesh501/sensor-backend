"""
Secure Sensor API Endpoints
Demonstrates JWT authentication on sensor data endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.security import get_current_active_user, User
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/v1/sensors", tags=["sensors"])


class SensorData(BaseModel):
    sensor_id: str
    temperature: float
    humidity: float
    timestamp: datetime
    location: str


class SensorResponse(BaseModel):
    sensor_id: str
    status: str
    data: SensorData


# Mock sensor database
fake_sensor_db = [
    {
        "sensor_id": "SENSOR_001",
        "temperature": 22.5,
        "humidity": 45.2,
        "timestamp": datetime.now(),
        "location": "Building_A"
    },
    {
        "sensor_id": "SENSOR_002",
        "temperature": 23.1,
        "humidity": 48.7,
        "timestamp": datetime.now(),
        "location": "Building_B"
    }
]


@router.get("/", response_model=List[SensorData])
async def get_all_sensors(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all sensor data
    
    Requires: Valid JWT token with 'read' scope
    """
    # Check if user has read permission
    if "read" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return fake_sensor_db


@router.get("/{sensor_id}", response_model=SensorData)
async def get_sensor(
    sensor_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get specific sensor data by ID
    
    Requires: Valid JWT token with 'read' scope
    """
    if "read" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    sensor = next((s for s in fake_sensor_db if s["sensor_id"] == sensor_id), None)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor {sensor_id} not found"
        )
    
    return sensor


@router.post("/", response_model=SensorResponse)
async def create_sensor_data(
    sensor_data: SensorData,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new sensor data entry
    
    Requires: Valid JWT token with 'write' scope
    """
    if "write" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to write data"
        )
    
    # Add to database (mock)
    fake_sensor_db.append(sensor_data.dict())
    
    return {
        "sensor_id": sensor_data.sensor_id,
        "status": "created",
        "data": sensor_data
    }


@router.delete("/{sensor_id}")
async def delete_sensor(
    sensor_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete sensor data
    
    Requires: Valid JWT token with 'admin' scope
    """
    if "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    global fake_sensor_db
    fake_sensor_db = [s for s in fake_sensor_db if s["sensor_id"] != sensor_id]
    
    return {"message": f"Sensor {sensor_id} deleted successfully"}

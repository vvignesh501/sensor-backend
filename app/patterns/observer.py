"""
Observer Pattern - Event-driven architecture
Interview Topics: Observer Pattern, Event-driven design, Pub-Sub
"""
from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime
from ..domain.entities import SensorReading, Sensor


class ISensorObserver(ABC):
    """
    Observer interface
    Interview: Explain Observer pattern, when to use
    """
    
    @abstractmethod
    async def on_reading_received(self, reading: SensorReading) -> None:
        """Called when new reading is received"""
        pass
    
    @abstractmethod
    async def on_sensor_status_changed(self, sensor: Sensor, old_status: str, new_status: str) -> None:
        """Called when sensor status changes"""
        pass


class SensorSubject:
    """
    Subject (Observable) - Manages observers
    Interview: Explain loose coupling, notification mechanism
    """
    
    def __init__(self):
        self._observers: List[ISensorObserver] = []
    
    def attach(self, observer: ISensorObserver) -> None:
        """
        Attach observer
        Interview: Explain registration mechanism
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer: ISensorObserver) -> None:
        """Detach observer"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    async def notify_reading(self, reading: SensorReading) -> None:
        """
        Notify all observers of new reading
        Interview: Explain notification pattern
        """
        for observer in self._observers:
            await observer.on_reading_received(reading)
    
    async def notify_status_change(
        self,
        sensor: Sensor,
        old_status: str,
        new_status: str
    ) -> None:
        """Notify observers of status change"""
        for observer in self._observers:
            await observer.on_sensor_status_changed(sensor, old_status, new_status)


class AlertObserver(ISensorObserver):
    """
    Concrete observer - Sends alerts
    Interview: Concrete implementation example
    """
    
    def __init__(self):
        self.alerts: List[Dict] = []
    
    async def on_reading_received(self, reading: SensorReading) -> None:
        """Check reading and create alerts"""
        if reading.is_battery_low():
            alert = {
                "type": "LOW_BATTERY",
                "sensor_id": reading.sensor_id,
                "battery_level": reading.battery_level,
                "timestamp": datetime.now()
            }
            self.alerts.append(alert)
            print(f"🔔 ALERT: Low battery on {reading.sensor_id}: {reading.battery_level}%")
        
        if reading.is_signal_weak():
            alert = {
                "type": "WEAK_SIGNAL",
                "sensor_id": reading.sensor_id,
                "signal_strength": reading.signal_strength,
                "timestamp": datetime.now()
            }
            self.alerts.append(alert)
            print(f"🔔 ALERT: Weak signal on {reading.sensor_id}: {reading.signal_strength}dBm")
    
    async def on_sensor_status_changed(
        self,
        sensor: Sensor,
        old_status: str,
        new_status: str
    ) -> None:
        """Alert on status change"""
        alert = {
            "type": "STATUS_CHANGE",
            "sensor_id": sensor.sensor_id,
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": datetime.now()
        }
        self.alerts.append(alert)
        print(f"🔔 ALERT: Sensor {sensor.sensor_id} status changed: {old_status} → {new_status}")


class LoggingObserver(ISensorObserver):
    """
    Concrete observer - Logs events
    Interview: Multiple observers example
    """
    
    def __init__(self):
        self.logs: List[str] = []
    
    async def on_reading_received(self, reading: SensorReading) -> None:
        """Log reading"""
        log_entry = (
            f"[{datetime.now()}] Reading received: "
            f"Sensor={reading.sensor_id}, "
            f"Temp={reading.temperature}°C, "
            f"Humidity={reading.humidity}%"
        )
        self.logs.append(log_entry)
        print(f"📝 LOG: {log_entry}")
    
    async def on_sensor_status_changed(
        self,
        sensor: Sensor,
        old_status: str,
        new_status: str
    ) -> None:
        """Log status change"""
        log_entry = (
            f"[{datetime.now()}] Status change: "
            f"Sensor={sensor.sensor_id}, "
            f"{old_status} → {new_status}"
        )
        self.logs.append(log_entry)
        print(f"📝 LOG: {log_entry}")


class MetricsObserver(ISensorObserver):
    """
    Concrete observer - Collects metrics
    Interview: Real-world use case
    """
    
    def __init__(self):
        self.metrics = {
            "total_readings": 0,
            "low_battery_count": 0,
            "weak_signal_count": 0,
            "status_changes": 0
        }
    
    async def on_reading_received(self, reading: SensorReading) -> None:
        """Update metrics"""
        self.metrics["total_readings"] += 1
        
        if reading.is_battery_low():
            self.metrics["low_battery_count"] += 1
        
        if reading.is_signal_weak():
            self.metrics["weak_signal_count"] += 1
    
    async def on_sensor_status_changed(
        self,
        sensor: Sensor,
        old_status: str,
        new_status: str
    ) -> None:
        """Track status changes"""
        self.metrics["status_changes"] += 1
    
    def get_metrics(self) -> Dict:
        """Get collected metrics"""
        return self.metrics.copy()


class DatabaseObserver(ISensorObserver):
    """
    Concrete observer - Persists to database
    Interview: Separation of concerns
    """
    
    def __init__(self):
        self.persisted_readings: List[SensorReading] = []
        self.persisted_events: List[Dict] = []
    
    async def on_reading_received(self, reading: SensorReading) -> None:
        """Persist reading to database"""
        # In production: Save to actual database
        self.persisted_readings.append(reading)
        print(f"💾 DB: Persisted reading for {reading.sensor_id}")
    
    async def on_sensor_status_changed(
        self,
        sensor: Sensor,
        old_status: str,
        new_status: str
    ) -> None:
        """Persist status change event"""
        event = {
            "sensor_id": sensor.sensor_id,
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": datetime.now()
        }
        self.persisted_events.append(event)
        print(f"💾 DB: Persisted status change for {sensor.sensor_id}")


# Demo usage
async def demo_observer_pattern():
    """
    Demonstrate observer pattern
    Interview: Show practical implementation
    """
    from ..domain.entities import Location, SensorType
    from ..patterns.factory import SensorFactory, SensorReadingBuilder
    
    print("=== Observer Pattern Demo ===\n")
    
    # Create subject
    subject = SensorSubject()
    
    # Create and attach observers
    alert_observer = AlertObserver()
    logging_observer = LoggingObserver()
    metrics_observer = MetricsObserver()
    db_observer = DatabaseObserver()
    
    subject.attach(alert_observer)
    subject.attach(logging_observer)
    subject.attach(metrics_observer)
    subject.attach(db_observer)
    
    print("✓ Attached 4 observers\n")
    
    # Create sensor
    location = Location("Building_A", 1, "Room_101")
    sensor = SensorFactory.create_temperature_sensor("TEMP_001", location)
    
    # Simulate readings
    print("--- Simulating normal reading ---")
    reading1 = (SensorReadingBuilder("TEMP_001")
                .with_temperature(22.5)
                .with_humidity(45.0)
                .with_battery_level(85.0)
                .with_signal_strength(-65)
                .build())
    
    await subject.notify_reading(reading1)
    
    print("\n--- Simulating low battery reading ---")
    reading2 = (SensorReadingBuilder("TEMP_001")
                .with_temperature(23.0)
                .with_humidity(46.0)
                .with_battery_level(15.0)  # Low battery!
                .with_signal_strength(-65)
                .build())
    
    await subject.notify_reading(reading2)
    
    print("\n--- Simulating weak signal reading ---")
    reading3 = (SensorReadingBuilder("TEMP_001")
                .with_temperature(23.5)
                .with_humidity(47.0)
                .with_battery_level(85.0)
                .with_signal_strength(-85)  # Weak signal!
                .build())
    
    await subject.notify_reading(reading3)
    
    print("\n--- Simulating status change ---")
    await subject.notify_status_change(sensor, "ACTIVE", "WARNING")
    
    # Show metrics
    print("\n=== Metrics Summary ===")
    metrics = metrics_observer.get_metrics()
    for key, value in metrics.items():
        print(f"{key}: {value}")
    
    print(f"\nTotal alerts: {len(alert_observer.alerts)}")
    print(f"Total logs: {len(logging_observer.logs)}")
    print(f"Persisted readings: {len(db_observer.persisted_readings)}")
    print(f"Persisted events: {len(db_observer.persisted_events)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_observer_pattern())

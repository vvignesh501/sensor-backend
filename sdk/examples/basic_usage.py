"""
Basic SDK Usage Examples
"""
from redlen_sdk import SensorClient
from redlen_sdk.exceptions import NotFoundError, RateLimitError
from datetime import datetime, timedelta


def main():
    # Initialize client
    client = SensorClient(
        api_key="your-api-key-here",
        base_url="http://localhost:8000"
    )
    
    print("=== Redlen Sensor SDK Examples ===\n")
    
    # Example 1: List all sensors
    print("1. Listing all sensors...")
    try:
        sensors = client.sensors.list()
        print(f"   Found {len(sensors)} sensors")
        for sensor in sensors[:3]:  # Show first 3
            print(f"   - {sensor.sensor_id}: {sensor.status}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 2: Get specific sensor
    print("\n2. Getting specific sensor...")
    try:
        sensor = client.sensors.get("SENSOR_001")
        print(f"   Sensor: {sensor.sensor_id}")
        print(f"   Type: {sensor.sensor_type}")
        print(f"   Location: {sensor.location}")
        print(f"   Status: {sensor.status}")
    except NotFoundError:
        print("   Sensor not found")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 3: Create new sensor
    print("\n3. Creating new sensor...")
    try:
        new_sensor = client.sensors.create(
            sensor_id="SDK_TEST_001",
            sensor_type="temperature",
            location="Building_A-Floor1-Room101"
        )
        print(f"   Created: {new_sensor.sensor_id}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 4: Add sensor reading
    print("\n4. Adding sensor reading...")
    try:
        reading = client.readings.create(
            sensor_id="SDK_TEST_001",
            temperature=22.5,
            humidity=45.0,
            battery_level=85.0,
            signal_strength=-65
        )
        print(f"   Reading added at {reading.timestamp}")
        print(f"   Temperature: {reading.temperature}°C")
        print(f"   Humidity: {reading.humidity}%")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 5: Get sensor statistics
    print("\n5. Getting sensor statistics...")
    try:
        stats = client.analytics.get_statistics("SDK_TEST_001")
        print(f"   Total readings: {stats.count}")
        print(f"   Avg temperature: {stats.avg_temperature}°C")
        print(f"   Avg humidity: {stats.avg_humidity}%")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 6: Get readings with date range
    print("\n6. Getting readings for last 24 hours...")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        readings = client.readings.list(
            sensor_id="SDK_TEST_001",
            start_date=start_date,
            end_date=end_date,
            limit=10
        )
        print(f"   Found {len(readings)} readings")
        for reading in readings[:3]:
            print(f"   - {reading.timestamp}: {reading.temperature}°C")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 7: Get latest reading
    print("\n7. Getting latest reading...")
    try:
        latest = client.readings.get_latest("SDK_TEST_001")
        if latest:
            print(f"   Latest reading: {latest.timestamp}")
            print(f"   Temperature: {latest.temperature}°C")
            print(f"   Battery: {latest.battery_level}%")
        else:
            print("   No readings found")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 8: Update sensor
    print("\n8. Updating sensor status...")
    try:
        updated = client.sensors.update(
            sensor_id="SDK_TEST_001",
            status="maintenance"
        )
        print(f"   Status updated to: {updated.status}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 9: Get health report
    print("\n9. Getting system health report...")
    try:
        health = client.analytics.get_health_report()
        print(f"   Total sensors: {health.get('total_sensors', 0)}")
        print(f"   Active sensors: {health.get('active_sensors', 0)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 10: Error handling
    print("\n10. Demonstrating error handling...")
    try:
        # Try to get non-existent sensor
        client.sensors.get("NONEXISTENT")
    except NotFoundError as e:
        print(f"   Caught NotFoundError: {e.message}")
    except RateLimitError as e:
        print(f"   Caught RateLimitError: Retry after {e.retry_after}s")
    except Exception as e:
        print(f"   Caught generic error: {e}")
    
    # Close client
    client.close()
    print("\n=== Examples Complete ===")


# Context manager usage
def context_manager_example():
    """Example using context manager"""
    print("\n=== Context Manager Example ===")
    
    with SensorClient(api_key="your-key", base_url="http://localhost:8000") as client:
        sensors = client.sensors.list()
        print(f"Found {len(sensors)} sensors")
    # Client automatically closed


if __name__ == "__main__":
    main()
    context_manager_example()

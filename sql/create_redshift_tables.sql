-- Auto-create Redshift tables for sensor analytics
-- Run this once after Terraform creates the cluster

-- 1. TIME-SERIES ANALYTICS (trending, forecasting)
CREATE TABLE IF NOT EXISTS sensor_time_series_analytics (
    test_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(20) NOT NULL,
    time_index INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    avg_value DECIMAL(10,4),
    max_value DECIMAL(10,4),
    min_value DECIMAL(10,4),
    std_value DECIMAL(10,4),
    trend_slope DECIMAL(10,6),
    volatility DECIMAL(8,4),
    PRIMARY KEY (test_id, time_index)
)
DISTSTYLE KEY
DISTKEY (test_id)
SORTKEY (timestamp, test_id);

-- 2. SPATIAL ANALYTICS (heatmaps, pattern analysis)
CREATE TABLE IF NOT EXISTS sensor_spatial_analytics (
    test_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(20) NOT NULL,
    x_coord INTEGER NOT NULL,
    y_coord INTEGER NOT NULL,
    avg_value DECIMAL(10,4),
    local_variance DECIMAL(10,4),
    gradient_magnitude DECIMAL(10,4),
    spatial_zone VARCHAR(20),
    is_hotspot BOOLEAN DEFAULT FALSE,
    is_coldspot BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (test_id, x_coord, y_coord)
)
DISTSTYLE KEY
DISTKEY (test_id)
SORTKEY (test_id, spatial_zone);

-- 3. AGGREGATED METRICS (dashboards, KPIs)
CREATE TABLE IF NOT EXISTS sensor_aggregated_metrics (
    test_id VARCHAR(50) PRIMARY KEY,
    sensor_type VARCHAR(20) NOT NULL,
    processing_time TIMESTAMP NOT NULL,
    global_mean DECIMAL(10,4),
    global_std DECIMAL(10,4),
    global_min DECIMAL(10,4),
    global_max DECIMAL(10,4),
    dynamic_range DECIMAL(10,4),
    signal_to_noise_ratio DECIMAL(8,2),
    uniformity_score DECIMAL(5,4),
    stability_index DECIMAL(5,4),
    anomaly_percentage DECIMAL(5,2),
    quality_grade CHAR(1),
    pass_fail_status VARCHAR(10)
)
DISTSTYLE ALL
SORTKEY (processing_time);

-- 4. EVENT DATA (anomaly detection, alerts)
CREATE TABLE IF NOT EXISTS sensor_event_data (
    test_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(20) NOT NULL,
    event_type VARCHAR(30) NOT NULL,
    event_time TIMESTAMP NOT NULL,
    coordinates VARCHAR(50),
    anomaly_value DECIMAL(10,4),
    z_score DECIMAL(8,4),
    severity VARCHAR(10),
    description VARCHAR(500)
)
DISTSTYLE KEY
DISTKEY (test_id)
SORTKEY (event_time, severity);

-- Analytics Views for Quick Queries

-- Real-time Dashboard View
CREATE OR REPLACE VIEW dashboard_metrics AS
SELECT 
    m.test_id,
    m.sensor_type,
    m.processing_time,
    m.quality_grade,
    m.pass_fail_status,
    m.anomaly_percentage,
    COUNT(e.event_type) as alert_count,
    AVG(t.avg_value) as avg_sensor_reading
FROM sensor_aggregated_metrics m
LEFT JOIN sensor_event_data e ON m.test_id = e.test_id
LEFT JOIN sensor_time_series_analytics t ON m.test_id = t.test_id
WHERE m.processing_time >= DATEADD(hour, -24, GETDATE())
GROUP BY m.test_id, m.sensor_type, m.processing_time, 
         m.quality_grade, m.pass_fail_status, m.anomaly_percentage
ORDER BY m.processing_time DESC;

-- Trending Analysis View
CREATE OR REPLACE VIEW sensor_trends AS
SELECT 
    sensor_type,
    DATE_TRUNC('hour', timestamp) as hour_bucket,
    AVG(avg_value) as hourly_avg,
    AVG(trend_slope) as avg_trend,
    AVG(volatility) as avg_volatility,
    COUNT(*) as data_points
FROM sensor_time_series_analytics
WHERE timestamp >= DATEADD(day, -7, GETDATE())
GROUP BY sensor_type, DATE_TRUNC('hour', timestamp)
ORDER BY hour_bucket DESC;

-- Spatial Heatmap View
CREATE OR REPLACE VIEW spatial_heatmap AS
SELECT 
    spatial_zone,
    sensor_type,
    AVG(avg_value) as zone_avg,
    COUNT(CASE WHEN is_hotspot THEN 1 END) as hotspot_count,
    COUNT(CASE WHEN is_coldspot THEN 1 END) as coldspot_count,
    AVG(gradient_magnitude) as avg_gradient
FROM sensor_spatial_analytics
GROUP BY spatial_zone, sensor_type
ORDER BY zone_avg DESC;
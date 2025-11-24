-- Redshift Table Schemas for Sensor Analytics

-- 1. Raw Sensor Data Table (Detailed point-by-point data)
CREATE TABLE IF NOT EXISTS sensor_raw_data (
    test_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(20) NOT NULL,
    timestamp_idx INTEGER NOT NULL,
    x_coordinate INTEGER NOT NULL,
    y_coordinate INTEGER NOT NULL,
    sensor_value DECIMAL(10,4) NOT NULL,
    processing_timestamp TIMESTAMP NOT NULL,
    data_quality_score DECIMAL(3,2),
    PRIMARY KEY (test_id, timestamp_idx, x_coordinate, y_coordinate)
)
DISTSTYLE KEY
DISTKEY (test_id)
SORTKEY (processing_timestamp, test_id);

-- 2. Time Series Summary Table (Aggregated by time)
CREATE TABLE IF NOT EXISTS sensor_time_series (
    test_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(20) NOT NULL,
    time_index INTEGER NOT NULL,
    avg_value DECIMAL(10,4) NOT NULL,
    max_value DECIMAL(10,4) NOT NULL,
    min_value DECIMAL(10,4) NOT NULL,
    std_value DECIMAL(10,4) NOT NULL,
    anomaly_count INTEGER DEFAULT 0,
    uniformity_score DECIMAL(5,4),
    processing_timestamp TIMESTAMP NOT NULL,
    data_points_count INTEGER,
    PRIMARY KEY (test_id, time_index)
)
DISTSTYLE KEY
DISTKEY (test_id)
SORTKEY (processing_timestamp, test_id, time_index);

-- 3. Spatial Analytics Table (For heatmaps and spatial patterns)
CREATE TABLE IF NOT EXISTS sensor_spatial_data (
    test_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(20) NOT NULL,
    x_coordinate INTEGER NOT NULL,
    y_coordinate INTEGER NOT NULL,
    avg_temporal_value DECIMAL(10,4) NOT NULL,
    local_mean_3x3 DECIMAL(10,4),
    gradient_magnitude DECIMAL(10,4),
    is_edge_point BOOLEAN DEFAULT FALSE,
    processing_timestamp TIMESTAMP NOT NULL,
    spatial_zone VARCHAR(20),
    PRIMARY KEY (test_id, x_coordinate, y_coordinate)
)
DISTSTYLE KEY
DISTKEY (test_id)
SORTKEY (processing_timestamp, test_id, spatial_zone);

-- 4. Test Metadata Table (High-level test information)
CREATE TABLE IF NOT EXISTS sensor_test_metadata (
    test_id VARCHAR(50) PRIMARY KEY,
    sensor_type VARCHAR(20) NOT NULL,
    test_timestamp TIMESTAMP NOT NULL,
    processing_timestamp TIMESTAMP NOT NULL,
    data_shape VARCHAR(50),
    total_data_points INTEGER,
    avg_sensor_value DECIMAL(10,4),
    anomaly_percentage DECIMAL(5,2),
    quality_score DECIMAL(5,2),
    processing_duration_ms INTEGER,
    s3_raw_path VARCHAR(500),
    s3_processed_path VARCHAR(500)
)
DISTSTYLE ALL
SORTKEY (test_timestamp);

-- Analytics Views for Common Queries

-- View 1: Latest Test Results
CREATE OR REPLACE VIEW latest_test_results AS
SELECT 
    t.test_id,
    t.sensor_type,
    t.test_timestamp,
    t.avg_sensor_value,
    t.anomaly_percentage,
    t.quality_score,
    COUNT(ts.time_index) as time_points,
    AVG(ts.uniformity_score) as avg_uniformity
FROM sensor_test_metadata t
LEFT JOIN sensor_time_series ts ON t.test_id = ts.test_id
WHERE t.test_timestamp >= DATEADD(day, -7, GETDATE())
GROUP BY t.test_id, t.sensor_type, t.test_timestamp, 
         t.avg_sensor_value, t.anomaly_percentage, t.quality_score
ORDER BY t.test_timestamp DESC;

-- View 2: Sensor Performance Trends
CREATE OR REPLACE VIEW sensor_performance_trends AS
SELECT 
    sensor_type,
    DATE_TRUNC('hour', processing_timestamp) as hour_bucket,
    COUNT(*) as tests_count,
    AVG(avg_value) as avg_sensor_reading,
    AVG(uniformity_score) as avg_uniformity,
    SUM(anomaly_count) as total_anomalies,
    AVG(std_value) as avg_variability
FROM sensor_time_series
WHERE processing_timestamp >= DATEADD(day, -30, GETDATE())
GROUP BY sensor_type, DATE_TRUNC('hour', processing_timestamp)
ORDER BY hour_bucket DESC, sensor_type;

-- View 3: Spatial Hotspots
CREATE OR REPLACE VIEW spatial_hotspots AS
SELECT 
    sensor_type,
    spatial_zone,
    COUNT(*) as test_count,
    AVG(avg_temporal_value) as avg_value,
    AVG(gradient_magnitude) as avg_gradient,
    COUNT(CASE WHEN is_edge_point THEN 1 END) as edge_points,
    DATE_TRUNC('day', processing_timestamp) as test_date
FROM sensor_spatial_data
WHERE processing_timestamp >= DATEADD(day, -7, GETDATE())
GROUP BY sensor_type, spatial_zone, DATE_TRUNC('day', processing_timestamp)
ORDER BY avg_gradient DESC;

-- Indexes for Performance
CREATE INDEX idx_sensor_raw_data_timestamp ON sensor_raw_data(processing_timestamp);
CREATE INDEX idx_sensor_raw_data_sensor_type ON sensor_raw_data(sensor_type);
CREATE INDEX idx_time_series_sensor_type ON sensor_time_series(sensor_type);
CREATE INDEX idx_spatial_data_zone ON sensor_spatial_data(spatial_zone);

-- Sample Analytics Queries

-- Query 1: Find anomalous tests in last 24 hours
/*
SELECT 
    test_id,
    sensor_type,
    processing_timestamp,
    anomaly_percentage,
    quality_score
FROM sensor_test_metadata
WHERE processing_timestamp >= DATEADD(hour, -24, GETDATE())
  AND anomaly_percentage > 5.0
ORDER BY anomaly_percentage DESC;
*/

-- Query 2: Sensor value distribution by spatial zone
/*
SELECT 
    spatial_zone,
    sensor_type,
    AVG(avg_temporal_value) as mean_value,
    STDDEV(avg_temporal_value) as std_value,
    COUNT(*) as data_points
FROM sensor_spatial_data
WHERE processing_timestamp >= DATEADD(day, -7, GETDATE())
GROUP BY spatial_zone, sensor_type
ORDER BY mean_value DESC;
*/

-- Query 3: Time series trend analysis
/*
SELECT 
    test_id,
    time_index,
    avg_value,
    LAG(avg_value) OVER (PARTITION BY test_id ORDER BY time_index) as prev_value,
    avg_value - LAG(avg_value) OVER (PARTITION BY test_id ORDER BY time_index) as value_change
FROM sensor_time_series
WHERE test_id = 'your_test_id'
ORDER BY time_index;
*/
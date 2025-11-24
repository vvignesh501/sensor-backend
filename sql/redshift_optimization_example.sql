-- Redshift Optimization Examples for Sensor Data

-- 1. DISTKEY Example - Distribute by test_id
CREATE TABLE sensor_time_series_analytics (
    test_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(20) NOT NULL,
    time_index INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    avg_value DECIMAL(10,4)
)
DISTSTYLE KEY
DISTKEY (test_id)           -- ← Spreads data across nodes by test_id
SORTKEY (timestamp, test_id); -- ← Physically sorts by timestamp first

-- Query Performance Examples:

-- FAST: Uses DISTKEY (goes to specific node)
SELECT * FROM sensor_time_series_analytics 
WHERE test_id = 'test_12345';
-- → Only 1 node processes this

-- FAST: Uses SORTKEY (zone maps skip irrelevant data)
SELECT AVG(avg_value) FROM sensor_time_series_analytics 
WHERE timestamp >= '2024-01-01' AND timestamp < '2024-01-02';
-- → Skips all data outside date range

-- SUPER FAST: Uses both DISTKEY + SORTKEY
SELECT * FROM sensor_time_series_analytics 
WHERE test_id = 'test_12345' 
  AND timestamp >= '2024-01-01';
-- → Single node + zone map optimization

-- 2. Compound SORTKEY for Multi-Column Queries
CREATE TABLE sensor_spatial_analytics (
    test_id VARCHAR(50),
    x_coord INTEGER,
    y_coord INTEGER,
    avg_value DECIMAL(10,4)
)
DISTSTYLE KEY
DISTKEY (test_id)
COMPOUND SORTKEY (test_id, x_coord, y_coord); -- ← Multi-column sort

-- This query is optimized:
SELECT * FROM sensor_spatial_analytics 
WHERE test_id = 'test_001' 
  AND x_coord BETWEEN 5 AND 10 
  AND y_coord BETWEEN 2 AND 6;

-- 3. DISTSTYLE ALL for Small Lookup Tables
CREATE TABLE sensor_types_lookup (
    sensor_type VARCHAR(20),
    description VARCHAR(100),
    calibration_factor DECIMAL(8,4)
)
DISTSTYLE ALL;  -- ← Copy entire table to every node

-- JOINs with this table are instant (no network traffic)
SELECT t.test_id, t.avg_value * l.calibration_factor as calibrated_value
FROM sensor_time_series_analytics t
JOIN sensor_types_lookup l ON t.sensor_type = l.sensor_type;

-- 4. Interleaved SORTKEY for Multiple Query Patterns
CREATE TABLE sensor_events (
    test_id VARCHAR(50),
    event_time TIMESTAMP,
    sensor_type VARCHAR(20),
    severity VARCHAR(10)
)
DISTSTYLE KEY
DISTKEY (test_id)
INTERLEAVED SORTKEY (event_time, sensor_type, severity);

-- All these queries are fast:
-- Query by time:
SELECT * FROM sensor_events WHERE event_time >= '2024-01-01';

-- Query by sensor type:
SELECT * FROM sensor_events WHERE sensor_type = 'MM';

-- Query by severity:
SELECT * FROM sensor_events WHERE severity = 'HIGH';

-- 5. Performance Monitoring Queries

-- Check table distribution
SELECT 
    slice,
    COUNT(*) as rows_per_slice
FROM stv_tbl_perm 
WHERE name = 'sensor_time_series_analytics'
GROUP BY slice
ORDER BY slice;

-- Check sort key effectiveness
SELECT 
    table_name,
    sortkey1,
    max_varchar,
    sortkey1_enc,
    sortkey_num
FROM svv_table_info 
WHERE table_name = 'sensor_time_series_analytics';

-- Check query performance
SELECT 
    query,
    starttime,
    endtime,
    DATEDIFF(seconds, starttime, endtime) as duration_seconds,
    rows
FROM stl_query 
WHERE querytxt LIKE '%sensor_%'
ORDER BY starttime DESC
LIMIT 10;
-- Redshift Spectrum Setup for Sensor Data

-- 1. Create External Schema (points to S3)
CREATE EXTERNAL SCHEMA sensor_s3_data
FROM DATA CATALOG
DATABASE 'sensor_data_catalog'
IAM_ROLE 'arn:aws:iam::123456789012:role/redshift-s3-access-role'
CREATE EXTERNAL DATABASE IF NOT EXISTS;

-- 2. Create External Table for Raw Sensor Arrays
CREATE EXTERNAL TABLE sensor_s3_data.raw_sensor_files (
    test_id VARCHAR(50),
    sensor_type VARCHAR(20),
    upload_date DATE,
    file_size_mb DECIMAL(10,2),
    data_shape VARCHAR(50),
    s3_path VARCHAR(500)
)
STORED AS PARQUET
LOCATION 's3://sensor-prod-data-vvignesh501-2025/raw_data/'
TABLE PROPERTIES ('has_encrypted_data'='false');

-- 3. Create External Table for Processed Analytics
CREATE EXTERNAL TABLE sensor_s3_data.processed_analytics (
    test_id VARCHAR(50),
    sensor_type VARCHAR(20),
    processing_date DATE,
    global_mean DECIMAL(10,4),
    global_std DECIMAL(10,4),
    anomaly_percentage DECIMAL(5,2),
    quality_score DECIMAL(5,2),
    s3_path VARCHAR(500)
)
STORED AS PARQUET
LOCATION 's3://sensor-analytics-processed-data/analytics/'
TABLE PROPERTIES ('has_encrypted_data'='false');

-- 4. Hybrid Queries: Redshift Tables + S3 Data
-- Fast summary from Redshift + detailed analysis from S3

-- Example 1: Join Redshift metrics with S3 raw data
SELECT 
    r.test_id,
    r.sensor_type,
    r.quality_grade,           -- From Redshift (fast)
    s.file_size_mb,           -- From S3 (via Spectrum)
    s.data_shape              -- From S3 (via Spectrum)
FROM sensor_aggregated_metrics r
JOIN sensor_s3_data.raw_sensor_files s ON r.test_id = s.test_id
WHERE r.quality_grade = 'F'   -- Failed tests
  AND s.file_size_mb > 100;   -- Large files

-- Example 2: Historical analysis without loading TBs into Redshift
SELECT 
    sensor_type,
    DATE_TRUNC('month', processing_date) as month,
    AVG(global_mean) as monthly_avg,
    COUNT(*) as tests_per_month,
    SUM(file_size_mb) as total_data_gb
FROM sensor_s3_data.processed_analytics
WHERE processing_date >= '2023-01-01'
GROUP BY sensor_type, DATE_TRUNC('month', processing_date)
ORDER BY month DESC;

-- Example 3: Cost-effective archival queries
-- Query 5 years of data without storing in expensive Redshift
SELECT 
    test_id,
    anomaly_percentage,
    quality_score
FROM sensor_s3_data.processed_analytics
WHERE processing_date BETWEEN '2019-01-01' AND '2024-01-01'
  AND anomaly_percentage > 10
ORDER BY anomaly_percentage DESC
LIMIT 100;
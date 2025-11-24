# 🚀 Complete Hands-On Integration Guide
## Terraform + S3 + Lambda + Redshift + Spectrum

### 📋 **Step 1: Deploy Infrastructure with Terraform**

```bash
# 1. Initialize Terraform
cd /Users/pranamyaakella/PycharmProjects/Redlen_workspace/sensor-backend
terraform init

# 2. Plan deployment (see what will be created)
terraform plan

# 3. Deploy everything
terraform apply
# Type 'yes' when prompted

# 4. Note the outputs (save these!)
terraform output
```

**What gets created:**
- ✅ Redshift cluster
- ✅ S3 buckets (source + processed)
- ✅ Lambda function
- ✅ VPC, subnets, security groups
- ✅ IAM roles and permissions

### 📋 **Step 2: Set Up Redshift Tables**

```bash
# 1. Get Redshift endpoint from terraform output
REDSHIFT_ENDPOINT=$(terraform output -raw redshift_cluster_endpoint)

# 2. Connect to Redshift (use password from terraform: TempPassword123!)
psql -h $REDSHIFT_ENDPOINT -d sensor_analytics -U admin -p 5439

# 3. Create tables
\i create_redshift_tables.sql

# 4. Create Spectrum external schema
CREATE EXTERNAL SCHEMA sensor_s3_data
FROM DATA CATALOG
DATABASE 'sensor_data_catalog'
IAM_ROLE 'arn:aws:iam::YOUR_ACCOUNT:role/redshift-s3-access-role'
CREATE EXTERNAL DATABASE IF NOT EXISTS;
```

### 📋 **Step 3: Deploy Lambda Function**

```bash
# 1. Package Lambda function
mkdir lambda_package
cp optimized_redshift_processor.py lambda_package/lambda_function.py
cd lambda_package

# 2. Install dependencies
pip install numpy pandas boto3 -t .

# 3. Create deployment package
zip -r ../sensor_processor.zip .
cd ..

# 4. Update Lambda function
aws lambda update-function-code \
    --function-name sensor-data-processor \
    --zip-file fileb://sensor_processor.zip
```

### 📋 **Step 4: Test the Complete Pipeline**

```bash
# 1. Start your FastAPI application
python3 simple_app.py

# 2. In another terminal, run load test
python3 load_test_1000_kafka.py
```

### 📋 **Step 5: Verify Data Flow**

**Check S3 uploads:**
```bash
aws s3 ls s3://sensor-prod-data-vvignesh501-2025/raw_data/ --recursive
```

**Check Lambda processing:**
```bash
aws logs tail /aws/lambda/sensor-data-processor --follow
```

**Check Redshift data:**
```sql
-- Connect to Redshift and run:
SELECT COUNT(*) FROM sensor_time_series_analytics;
SELECT COUNT(*) FROM sensor_spatial_analytics;
SELECT COUNT(*) FROM sensor_aggregated_metrics;
```

### 📋 **Step 6: Set Up Historical Data for Spectrum**

**Create sample historical data:**
```sql
-- In Redshift, create historical data
INSERT INTO sensor_s3_data.historical_analytics
SELECT 
    test_id,
    sensor_type,
    processing_time::DATE - INTERVAL '1 year' as processing_date,
    global_mean,
    global_std,
    anomaly_percentage,
    quality_score
FROM sensor_aggregated_metrics;
```

### 📋 **Step 7: Test Hybrid Queries (Redshift + Spectrum)**

```sql
-- Query combining recent (Redshift) + historical (Spectrum) data
SELECT 
    'Recent' as data_source,
    sensor_type,
    AVG(quality_score) as avg_quality,
    COUNT(*) as test_count
FROM sensor_aggregated_metrics
WHERE processing_time >= CURRENT_DATE - 30
GROUP BY sensor_type

UNION ALL

SELECT 
    'Historical' as data_source,
    sensor_type,
    AVG(quality_score) as avg_quality,
    COUNT(*) as test_count
FROM sensor_s3_data.historical_analytics
WHERE processing_date >= CURRENT_DATE - 365
GROUP BY sensor_type

ORDER BY data_source, sensor_type;
```

### 📋 **Step 8: Monitor and Verify Integration**

**Check CloudWatch Logs:**
```bash
# Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/sensor"

# Redshift query logs
aws logs describe-log-groups --log-group-name-prefix "/aws/redshift"
```

**Verify S3 Integration:**
```bash
# Check processed data
aws s3 ls s3://sensor-analytics-processed-data/redshift_staging/ --recursive

# Check file sizes and counts
aws s3api list-objects-v2 \
    --bucket sensor-prod-data-vvignesh501-2025 \
    --query 'Contents[].{Key:Key,Size:Size}' \
    --output table
```

**Test Redshift Performance:**
```sql
-- Performance test query
SELECT 
    sensor_type,
    DATE_TRUNC('hour', processing_time) as hour,
    COUNT(*) as tests_per_hour,
    AVG(quality_score) as avg_quality
FROM sensor_aggregated_metrics
WHERE processing_time >= CURRENT_DATE - 7
GROUP BY sensor_type, DATE_TRUNC('hour', processing_time)
ORDER BY hour DESC;
```

### 📋 **Step 9: Create Analytics Dashboard Queries**

**Real-time Dashboard:**
```sql
-- Current system health
SELECT 
    COUNT(*) as total_tests_today,
    AVG(quality_score) as avg_quality,
    COUNT(CASE WHEN quality_grade = 'F' THEN 1 END) as failed_tests,
    MAX(processing_time) as last_test_time
FROM sensor_aggregated_metrics
WHERE processing_time >= CURRENT_DATE;
```

**Trend Analysis:**
```sql
-- 30-day trend
SELECT 
    DATE_TRUNC('day', processing_time) as day,
    sensor_type,
    COUNT(*) as daily_tests,
    AVG(anomaly_percentage) as avg_anomaly_rate
FROM sensor_aggregated_metrics
WHERE processing_time >= CURRENT_DATE - 30
GROUP BY DATE_TRUNC('day', processing_time), sensor_type
ORDER BY day DESC;
```

**Spectrum Historical Analysis:**
```sql
-- Year-over-year comparison
SELECT 
    EXTRACT(year FROM processing_date) as year,
    sensor_type,
    AVG(quality_score) as yearly_avg_quality,
    COUNT(*) as yearly_tests
FROM sensor_s3_data.historical_analytics
GROUP BY EXTRACT(year FROM processing_date), sensor_type
ORDER BY year DESC, sensor_type;
```

### 📋 **Step 10: Verify Cost Optimization**

**Check storage costs:**
```bash
# S3 storage usage
aws s3api list-objects-v2 \
    --bucket sensor-analytics-processed-data \
    --query 'sum(Contents[].Size)' \
    --output text

# Redshift storage usage
aws redshift describe-clusters \
    --cluster-identifier sensor-analytics-cluster \
    --query 'Clusters[0].TotalStorageCapacityInMegaBytes'
```

**Monitor query costs:**
```sql
-- Check Spectrum query costs in Redshift
SELECT 
    query,
    starttime,
    endtime,
    bytes_scanned_from_s3,
    bytes_returned_from_s3
FROM svl_s3query_summary
WHERE starttime >= CURRENT_DATE - 1
ORDER BY starttime DESC;
```

### 🎯 **Success Verification Checklist**

- [ ] Terraform deployed all resources
- [ ] FastAPI app uploads data to S3
- [ ] Lambda processes data automatically
- [ ] Redshift tables populated with analytics
- [ ] Spectrum queries work on S3 data
- [ ] Hybrid queries combine Redshift + S3
- [ ] CloudWatch shows successful processing
- [ ] Cost monitoring shows S3 savings

### 🚨 **Troubleshooting Common Issues**

**Lambda timeout:**
```bash
aws lambda update-function-configuration \
    --function-name sensor-data-processor \
    --timeout 900
```

**Redshift connection issues:**
```bash
# Check security group allows your IP
aws ec2 describe-security-groups \
    --group-ids sg-your-redshift-sg
```

**S3 permissions:**
```bash
# Verify IAM role has S3 access
aws iam get-role-policy \
    --role-name redshift-s3-access-role \
    --policy-name redshift-s3-policy
```

This hands-on guide gives you a complete working system with real data flowing through the entire pipeline!
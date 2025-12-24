# 🚀 PySpark + Parquet Real-Time Analytics Demo

## Overview
This demo showcases the power of Parquet format and PySpark for real-time analytics:

1. **Storage Optimization**: Compare JSON vs Parquet storage (typically 70-95% savings)
2. **Performance**: Demonstrate PySpark's speed for analytics
3. **Real-Time Dashboard**: Interactive Streamlit dashboard with live metrics
4. **AWS Integration**: Seamless S3 integration with shared credentials

## Architecture

```
┌─────────────────┐
│  Docker         │
│  Container      │
│  ┌───────────┐  │      ┌──────────────┐
│  │ PySpark   │◄─┼──────┤  S3 Bucket   │
│  │ Processor │  │      │              │
│  └─────┬─────┘  │      │ JSON: 45KB   │
│        │        │      │ Parquet: 3KB │
│  ┌─────▼─────┐  │      └──────────────┘
│  │ Streamlit │  │
│  │ Dashboard │  │
│  └───────────┘  │
└────────┬────────┘
         │
    http://localhost:8501
```

## Features

### 1. Parquet Conversion
- Generates 100 realistic sensor records
- Saves as both JSON and Parquet
- Uploads to S3
- Compares file sizes and compression ratios

### 2. PySpark Analytics
- Real-time data processing
- Aggregations by location
- Status monitoring
- Low battery alerts
- Performance metrics

### 3. Interactive Dashboard
- Live metrics visualization
- Storage comparison charts
- Location-based analytics
- Sensor status distribution
- Performance benchmarks

## Quick Start

### Prerequisites
```bash
# AWS credentials configured
aws configure

# Docker installed
docker --version
```

### Run Demo
```bash
cd sensor-backend/pyspark-demo

# Set your S3 bucket name
export S3_BUCKET=your-bucket-name
export AWS_REGION=us-east-1

# Run complete demo
chmod +x run_demo.sh
./run_demo.sh
```

### Manual Steps
```bash
# Build image
docker-compose build

# Step 1: Convert data to Parquet
docker-compose run --rm pyspark-processor python parquet_converter.py

# Step 2: Start dashboard
docker-compose up
```

## Expected Results

### Storage Savings
```
JSON Size:     45,234 bytes (44.17 KB)
Parquet Size:  3,891 bytes (3.80 KB)

💰 Storage Saved: 41,343 bytes (40.37 KB)
📉 Reduction: 91.4%
🗜️  Compression Ratio: 11.6x
```

### Performance Improvement
```
JSON read time: 125.43ms
Parquet read time: 8.76ms

⚡ Parquet is 14.3x faster for reading!
```

### PySpark Processing
```
Data Load Time: 45.23ms
Analysis Time: 12.87ms
Total Processing: 58.10ms
```

## Dashboard Access

- **Streamlit Dashboard**: http://localhost:8501
- **Spark UI**: http://localhost:4040

## AWS Credentials Sharing

The Docker container shares AWS credentials via volume mount:
```yaml
volumes:
  - ~/.aws:/root/.aws:ro
```

This allows all microservices in the container to access S3 without hardcoding credentials.

## What You'll Learn

1. **Parquet Benefits**:
   - 70-95% storage reduction
   - 10-20x faster read performance
   - Columnar format advantages
   - Built-in compression

2. **PySpark Power**:
   - Distributed processing
   - Real-time analytics
   - S3 integration
   - Scalable architecture

3. **Production Patterns**:
   - Docker containerization
   - AWS credential management
   - Real-time dashboards
   - Performance monitoring

## Troubleshooting

### AWS Credentials Not Found
```bash
aws configure
# Enter your AWS Access Key ID and Secret
```

### S3 Bucket Access Denied
```bash
# Create bucket
aws s3 mb s3://your-bucket-name

# Or use existing bucket
export S3_BUCKET=existing-bucket-name
```

### Port Already in Use
```bash
# Change ports in docker-compose.yml
ports:
  - "8502:8501"  # Use different port
```

## Clean Up

```bash
# Stop containers
docker-compose down

# Remove S3 data
aws s3 rm s3://$S3_BUCKET/json/ --recursive
aws s3 rm s3://$S3_BUCKET/parquet/ --recursive
```

## Next Steps

- Scale to millions of records
- Add real-time streaming with Kafka
- Implement partitioning strategies
- Deploy to EMR or Databricks
- Add machine learning models

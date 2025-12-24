#!/bin/bash

echo "🚀 Starting Sensor Backend Locally"
echo "==================================="
echo ""

# Start services
echo "1. Starting PostgreSQL and Kafka..."
docker-compose -f docker-compose.local.yml up -d

# Wait for services
echo ""
echo "2. Waiting for services to be ready..."
sleep 15

# Create database tables
echo ""
echo "3. Creating database tables..."
docker exec -i sensor-postgres-local psql -U postgres -d sensordb << EOF
CREATE TABLE IF NOT EXISTS users (
  id VARCHAR PRIMARY KEY,
  username VARCHAR UNIQUE NOT NULL,
  email VARCHAR NOT NULL,
  hashed_password VARCHAR NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sensor_tests (
  id VARCHAR PRIMARY KEY,
  sensor_type VARCHAR NOT NULL,
  data_type VARCHAR DEFAULT 'raw_data',
  s3_status VARCHAR NOT NULL,
  s3_path VARCHAR,
  test_metrics JSONB,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kafka_logs (
  id SERIAL PRIMARY KEY,
  test_id VARCHAR NOT NULL,
  user_id VARCHAR NOT NULL,
  sensor_type VARCHAR NOT NULL,
  kafka_start_time TIMESTAMP NOT NULL,
  kafka_end_time TIMESTAMP NOT NULL,
  processing_time_seconds DECIMAL(10,6) NOT NULL,
  status VARCHAR NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF

echo "✅ Database tables created"
echo ""

# Start FastAPI app
echo "4. Starting FastAPI app..."
echo ""
cd app
python3 main.py

echo ""
echo "✅ App is running at http://localhost:8000"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose.local.yml down"

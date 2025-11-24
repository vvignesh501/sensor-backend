#!/bin/bash

# Start Kafka and Zookeeper locally

echo "Starting Zookeeper..."
./kafka/bin/zookeeper-server-start.sh ./kafka/config/zookeeper.properties &
ZOOKEEPER_PID=$!

sleep 5

echo "Starting Kafka..."
./kafka/bin/kafka-server-start.sh ./kafka/config/server.properties &
KAFKA_PID=$!

sleep 5

echo "Creating topic..."
./kafka/bin/kafka-topics.sh --create --topic sensor-test-events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

echo "Kafka started successfully!"
echo "Zookeeper PID: $ZOOKEEPER_PID"
echo "Kafka PID: $KAFKA_PID"

# Keep script running
wait
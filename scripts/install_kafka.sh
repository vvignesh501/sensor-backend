#!/bin/bash

# Install Kafka locally without Docker

echo "Installing Kafka locally..."

# Download Kafka
wget https://downloads.apache.org/kafka/2.13-3.6.0/kafka_2.13-3.6.0.tgz
tar -xzf kafka_2.13-3.6.0.tgz
mv kafka_2.13-3.6.0 kafka

echo "Kafka installed in ./kafka directory"
echo "To start:"
echo "1. ./start_kafka.sh"
echo "2. python3 kafka_consumer.py"
echo "3. python3 simple_app.py"
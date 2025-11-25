#!/bin/bash

# Real-Time AWS Monitoring Script
# Monitors ECS, ALB, and RDS metrics in real-time

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION="${AWS_REGION:-us-east-2}"
CLUSTER_NAME="sensor-app-cluster"
SERVICE_NAME="sensor-app-service"
ALB_NAME="sensor-app-alb"
DB_INSTANCE="sensor-postgres-v2"
REFRESH_INTERVAL=5

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Sensor Backend Real-Time Monitor${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to get ECS metrics
get_ecs_metrics() {
    local end_time=$(date -u +"%Y-%m-%dT%H:%M:%S")
    local start_time=$(date -u -v-5M +"%Y-%m-%dT%H:%M:%S" 2>/dev/null || date -u -d '5 minutes ago' +"%Y-%m-%dT%H:%M:%S")
    
    # CPU Utilization
    cpu=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/ECS \
        --metric-name CPUUtilization \
        --dimensions Name=ClusterName,Value=$CLUSTER_NAME Name=ServiceName,Value=$SERVICE_NAME \
        --start-time $start_time \
        --end-time $end_time \
        --period 60 \
        --statistics Average \
        --region $REGION \
        --query 'Datapoints[0].Average' \
        --output text 2>/dev/null || echo "N/A")
    
    # Memory Utilization
    memory=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/ECS \
        --metric-name MemoryUtilization \
        --dimensions Name=ClusterName,Value=$CLUSTER_NAME Name=ServiceName,Value=$SERVICE_NAME \
        --start-time $start_time \
        --end-time $end_time \
        --period 60 \
        --statistics Average \
        --region $REGION \
        --query 'Datapoints[0].Average' \
        --output text 2>/dev/null || echo "N/A")
    
    # Task Count
    task_count=$(aws ecs describe-services \
        --cluster $CLUSTER_NAME \
        --services $SERVICE_NAME \
        --region $REGION \
        --query 'services[0].runningCount' \
        --output text 2>/dev/null || echo "N/A")
    
    echo -e "${GREEN}ECS Metrics:${NC}"
    echo -e "  CPU Usage:    ${YELLOW}${cpu}%${NC}"
    echo -e "  Memory Usage: ${YELLOW}${memory}%${NC}"
    echo -e "  Running Tasks: ${YELLOW}${task_count}${NC}"
}

# Function to get ALB metrics
get_alb_metrics() {
    local end_time=$(date -u +"%Y-%m-%dT%H:%M:%S")
    local start_time=$(date -u -v-5M +"%Y-%m-%dT%H:%M:%S" 2>/dev/null || date -u -d '5 minutes ago' +"%Y-%m-%dT%H:%M:%S")
    
    # Get ALB ARN suffix
    alb_arn=$(aws elbv2 describe-load-balancers \
        --names $ALB_NAME \
        --region $REGION \
        --query 'LoadBalancers[0].LoadBalancerArn' \
        --output text 2>/dev/null)
    
    if [ "$alb_arn" != "None" ] && [ -n "$alb_arn" ]; then
        alb_suffix=$(echo $alb_arn | cut -d':' -f6 | cut -d'/' -f2-)
        
        # Request Count
        requests=$(aws cloudwatch get-metric-statistics \
            --namespace AWS/ApplicationELB \
            --metric-name RequestCount \
            --dimensions Name=LoadBalancer,Value=$alb_suffix \
            --start-time $start_time \
            --end-time $end_time \
            --period 300 \
            --statistics Sum \
            --region $REGION \
            --query 'Datapoints[0].Sum' \
            --output text 2>/dev/null || echo "N/A")
        
        # Response Time
        response_time=$(aws cloudwatch get-metric-statistics \
            --namespace AWS/ApplicationELB \
            --metric-name TargetResponseTime \
            --dimensions Name=LoadBalancer,Value=$alb_suffix \
            --start-time $start_time \
            --end-time $end_time \
            --period 60 \
            --statistics Average \
            --region $REGION \
            --query 'Datapoints[0].Average' \
            --output text 2>/dev/null || echo "N/A")
        
        # Healthy Hosts
        healthy=$(aws cloudwatch get-metric-statistics \
            --namespace AWS/ApplicationELB \
            --metric-name HealthyHostCount \
            --dimensions Name=LoadBalancer,Value=$alb_suffix \
            --start-time $start_time \
            --end-time $end_time \
            --period 60 \
            --statistics Average \
            --region $REGION \
            --query 'Datapoints[0].Average' \
            --output text 2>/dev/null || echo "N/A")
        
        echo -e "${GREEN}ALB Metrics:${NC}"
        echo -e "  Request Count: ${YELLOW}${requests}${NC}"
        echo -e "  Response Time: ${YELLOW}${response_time}s${NC}"
        echo -e "  Healthy Hosts: ${YELLOW}${healthy}${NC}"
    else
        echo -e "${RED}ALB not found or not accessible${NC}"
    fi
}

# Function to get RDS metrics
get_rds_metrics() {
    local end_time=$(date -u +"%Y-%m-%dT%H:%M:%S")
    local start_time=$(date -u -v-5M +"%Y-%m-%dT%H:%M:%S" 2>/dev/null || date -u -d '5 minutes ago' +"%Y-%m-%dT%H:%M:%S")
    
    # CPU Utilization
    rds_cpu=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/RDS \
        --metric-name CPUUtilization \
        --dimensions Name=DBInstanceIdentifier,Value=$DB_INSTANCE \
        --start-time $start_time \
        --end-time $end_time \
        --period 60 \
        --statistics Average \
        --region $REGION \
        --query 'Datapoints[0].Average' \
        --output text 2>/dev/null || echo "N/A")
    
    # Database Connections
    connections=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/RDS \
        --metric-name DatabaseConnections \
        --dimensions Name=DBInstanceIdentifier,Value=$DB_INSTANCE \
        --start-time $start_time \
        --end-time $end_time \
        --period 60 \
        --statistics Average \
        --region $REGION \
        --query 'Datapoints[0].Average' \
        --output text 2>/dev/null || echo "N/A")
    
    echo -e "${GREEN}RDS Metrics:${NC}"
    echo -e "  CPU Usage:    ${YELLOW}${rds_cpu}%${NC}"
    echo -e "  Connections:  ${YELLOW}${connections}${NC}"
}

# Function to get recent logs
get_recent_logs() {
    echo -e "${GREEN}Recent Logs (last 5):${NC}"
    aws logs tail /ecs/sensor-app \
        --since 1m \
        --format short \
        --region $REGION \
        2>/dev/null | tail -5 || echo "  No recent logs"
}

# Function to check alarms
check_alarms() {
    alarms=$(aws cloudwatch describe-alarms \
        --alarm-name-prefix "sensor-app" \
        --state-value ALARM \
        --region $REGION \
        --query 'MetricAlarms[*].[AlarmName,StateReason]' \
        --output text 2>/dev/null)
    
    if [ -n "$alarms" ]; then
        echo -e "${RED}Active Alarms:${NC}"
        echo "$alarms" | while read line; do
            echo -e "  ${RED}⚠ $line${NC}"
        done
    else
        echo -e "${GREEN}✓ No active alarms${NC}"
    fi
}

# Main monitoring loop
echo "Starting real-time monitoring (Ctrl+C to stop)..."
echo "Refresh interval: ${REFRESH_INTERVAL}s"
echo ""

while true; do
    clear
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Sensor Backend - $(date)${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    get_ecs_metrics
    echo ""
    
    get_alb_metrics
    echo ""
    
    get_rds_metrics
    echo ""
    
    check_alarms
    echo ""
    
    get_recent_logs
    echo ""
    
    echo -e "${BLUE}Refreshing in ${REFRESH_INTERVAL}s... (Ctrl+C to stop)${NC}"
    sleep $REFRESH_INTERVAL
done

#!/bin/bash

# Stream CloudWatch Logs in Real-Time
# Shows live application logs from ECS containers

set -e

# Configuration
REGION="${AWS_REGION:-us-east-2}"
LOG_GROUP="/ecs/sensor-app"
FILTER_PATTERN="${1:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  CloudWatch Logs - Live Stream${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${CYAN}Log Group: ${LOG_GROUP}${NC}"
echo -e "${CYAN}Region: ${REGION}${NC}"

if [ -n "$FILTER_PATTERN" ]; then
    echo -e "${CYAN}Filter: ${FILTER_PATTERN}${NC}"
fi

echo -e "${BLUE}========================================${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check if log group exists
if ! aws logs describe-log-groups \
    --log-group-name-prefix "$LOG_GROUP" \
    --region "$REGION" \
    --query 'logGroups[0]' \
    --output text &> /dev/null; then
    echo -e "${RED}Error: Log group '$LOG_GROUP' not found${NC}"
    echo -e "${YELLOW}Make sure your ECS service is deployed and running${NC}"
    exit 1
fi

echo -e "${GREEN}Streaming logs... (Ctrl+C to stop)${NC}"
echo ""

# Stream logs with color coding
if [ -n "$FILTER_PATTERN" ]; then
    aws logs tail "$LOG_GROUP" \
        --follow \
        --format short \
        --filter-pattern "$FILTER_PATTERN" \
        --region "$REGION" | while read line; do
        
        # Color code based on content
        if echo "$line" | grep -qi "error\|exception\|failed"; then
            echo -e "${RED}$line${NC}"
        elif echo "$line" | grep -qi "warning\|warn"; then
            echo -e "${YELLOW}$line${NC}"
        elif echo "$line" | grep -qi "info"; then
            echo -e "${GREEN}$line${NC}"
        else
            echo "$line"
        fi
    done
else
    aws logs tail "$LOG_GROUP" \
        --follow \
        --format short \
        --region "$REGION" | while read line; do
        
        # Color code based on content
        if echo "$line" | grep -qi "error\|exception\|failed"; then
            echo -e "${RED}$line${NC}"
        elif echo "$line" | grep -qi "warning\|warn"; then
            echo -e "${YELLOW}$line${NC}"
        elif echo "$line" | grep -qi "info"; then
            echo -e "${GREEN}$line${NC}"
        else
            echo "$line"
        fi
    done
fi

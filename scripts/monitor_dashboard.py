#!/usr/bin/env python3
"""
Real-Time AWS Monitoring Dashboard
Displays live metrics for ECS, ALB, RDS, and CloudWatch Logs
"""

import boto3
import time
import os
from datetime import datetime, timedelta
from collections import deque

# Configuration
REGION = os.getenv('AWS_REGION', 'us-east-2')
CLUSTER_NAME = 'sensor-app-cluster'
SERVICE_NAME = 'sensor-app-service'
ALB_NAME = 'sensor-app-alb'
DB_INSTANCE = 'sensor-postgres-v2'
LOG_GROUP = '/ecs/sensor-app'
REFRESH_INTERVAL = 5

# AWS Clients
cloudwatch = boto3.client('cloudwatch', region_name=REGION)
ecs = boto3.client('ecs', region_name=REGION)
elbv2 = boto3.client('elbv2', region_name=REGION)
logs = boto3.client('logs', region_name=REGION)

# Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def get_metric(namespace, metric_name, dimensions, statistic='Average', period=60):
    """Get CloudWatch metric value"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        response = cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=[statistic]
        )
        
        if response['Datapoints']:
            return round(response['Datapoints'][0][statistic], 2)
        return None
    except Exception as e:
        return None

def get_ecs_metrics():
    """Get ECS service metrics"""
    metrics = {}
    
    # CPU and Memory
    dimensions = [
        {'Name': 'ClusterName', 'Value': CLUSTER_NAME},
        {'Name': 'ServiceName', 'Value': SERVICE_NAME}
    ]
    
    metrics['cpu'] = get_metric('AWS/ECS', 'CPUUtilization', dimensions)
    metrics['memory'] = get_metric('AWS/ECS', 'MemoryUtilization', dimensions)
    
    # Task count
    try:
        response = ecs.describe_services(
            cluster=CLUSTER_NAME,
            services=[SERVICE_NAME]
        )
        if response['services']:
            service = response['services'][0]
            metrics['running_tasks'] = service['runningCount']
            metrics['desired_tasks'] = service['desiredCount']
            metrics['pending_tasks'] = service['pendingCount']
    except Exception:
        metrics['running_tasks'] = None
        metrics['desired_tasks'] = None
        metrics['pending_tasks'] = None
    
    return metrics

def get_alb_metrics():
    """Get ALB metrics"""
    metrics = {}
    
    try:
        # Get ALB ARN
        response = elbv2.describe_load_balancers(Names=[ALB_NAME])
        if response['LoadBalancers']:
            alb_arn = response['LoadBalancers'][0]['LoadBalancerArn']
            alb_suffix = '/'.join(alb_arn.split(':')[-1].split('/')[1:])
            
            dimensions = [{'Name': 'LoadBalancer', 'Value': alb_suffix}]
            
            # Request count
            metrics['requests'] = get_metric(
                'AWS/ApplicationELB', 
                'RequestCount', 
                dimensions, 
                'Sum', 
                300
            )
            
            # Response time
            metrics['response_time'] = get_metric(
                'AWS/ApplicationELB',
                'TargetResponseTime',
                dimensions
            )
            
            # Healthy hosts
            metrics['healthy_hosts'] = get_metric(
                'AWS/ApplicationELB',
                'HealthyHostCount',
                dimensions
            )
            
            # HTTP codes
            metrics['http_2xx'] = get_metric(
                'AWS/ApplicationELB',
                'HTTPCode_Target_2XX_Count',
                dimensions,
                'Sum',
                300
            )
            metrics['http_4xx'] = get_metric(
                'AWS/ApplicationELB',
                'HTTPCode_Target_4XX_Count',
                dimensions,
                'Sum',
                300
            )
            metrics['http_5xx'] = get_metric(
                'AWS/ApplicationELB',
                'HTTPCode_Target_5XX_Count',
                dimensions,
                'Sum',
                300
            )
    except Exception as e:
        pass
    
    return metrics

def get_rds_metrics():
    """Get RDS metrics"""
    metrics = {}
    
    dimensions = [{'Name': 'DBInstanceIdentifier', 'Value': DB_INSTANCE}]
    
    metrics['cpu'] = get_metric('AWS/RDS', 'CPUUtilization', dimensions)
    metrics['connections'] = get_metric('AWS/RDS', 'DatabaseConnections', dimensions)
    metrics['read_iops'] = get_metric('AWS/RDS', 'ReadIOPS', dimensions)
    metrics['write_iops'] = get_metric('AWS/RDS', 'WriteIOPS', dimensions)
    
    return metrics

def get_recent_logs(limit=5):
    """Get recent CloudWatch logs"""
    try:
        # Get log streams
        streams_response = logs.describe_log_streams(
            logGroupName=LOG_GROUP,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        if not streams_response['logStreams']:
            return []
        
        # Get events from most recent stream
        stream_name = streams_response['logStreams'][0]['logStreamName']
        
        events_response = logs.get_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=stream_name,
            limit=limit,
            startFromHead=False
        )
        
        return events_response['events']
    except Exception:
        return []

def get_active_alarms():
    """Get active CloudWatch alarms"""
    try:
        response = cloudwatch.describe_alarms(
            AlarmNamePrefix='sensor-app',
            StateValue='ALARM'
        )
        return response['MetricAlarms']
    except Exception:
        return []

def format_value(value, unit='', color=Colors.YELLOW):
    """Format metric value with color"""
    if value is None:
        return f"{Colors.RED}N/A{Colors.ENDC}"
    return f"{color}{value}{unit}{Colors.ENDC}"

def get_status_color(value, warning_threshold, critical_threshold):
    """Get color based on threshold"""
    if value is None:
        return Colors.RED
    if value >= critical_threshold:
        return Colors.RED
    if value >= warning_threshold:
        return Colors.YELLOW
    return Colors.GREEN

def print_header():
    """Print dashboard header"""
    print(f"{Colors.BLUE}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}   SENSOR BACKEND - REAL-TIME MONITORING DASHBOARD{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*80}{Colors.ENDC}")
    print(f"{Colors.CYAN}   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}   Region: {REGION}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*80}{Colors.ENDC}\n")

def print_ecs_metrics(metrics):
    """Print ECS metrics"""
    print(f"{Colors.GREEN}{Colors.BOLD}📦 ECS SERVICE METRICS{Colors.ENDC}")
    print(f"{Colors.BLUE}{'─'*80}{Colors.ENDC}")
    
    cpu_color = get_status_color(metrics.get('cpu'), 70, 85)
    mem_color = get_status_color(metrics.get('memory'), 70, 85)
    
    print(f"  CPU Utilization:     {format_value(metrics.get('cpu'), '%', cpu_color)}")
    print(f"  Memory Utilization:  {format_value(metrics.get('memory'), '%', mem_color)}")
    print(f"  Running Tasks:       {format_value(metrics.get('running_tasks'))}")
    print(f"  Desired Tasks:       {format_value(metrics.get('desired_tasks'))}")
    print(f"  Pending Tasks:       {format_value(metrics.get('pending_tasks'))}")
    print()

def print_alb_metrics(metrics):
    """Print ALB metrics"""
    print(f"{Colors.GREEN}{Colors.BOLD}⚖️  APPLICATION LOAD BALANCER{Colors.ENDC}")
    print(f"{Colors.BLUE}{'─'*80}{Colors.ENDC}")
    
    response_color = get_status_color(metrics.get('response_time'), 1.0, 2.0)
    
    print(f"  Request Count (5m):  {format_value(metrics.get('requests'))}")
    print(f"  Response Time:       {format_value(metrics.get('response_time'), 's', response_color)}")
    print(f"  Healthy Hosts:       {format_value(metrics.get('healthy_hosts'))}")
    print(f"  HTTP 2XX:            {format_value(metrics.get('http_2xx'), '', Colors.GREEN)}")
    print(f"  HTTP 4XX:            {format_value(metrics.get('http_4xx'), '', Colors.YELLOW)}")
    print(f"  HTTP 5XX:            {format_value(metrics.get('http_5xx'), '', Colors.RED)}")
    print()

def print_rds_metrics(metrics):
    """Print RDS metrics"""
    print(f"{Colors.GREEN}{Colors.BOLD}🗄️  RDS DATABASE{Colors.ENDC}")
    print(f"{Colors.BLUE}{'─'*80}{Colors.ENDC}")
    
    cpu_color = get_status_color(metrics.get('cpu'), 70, 85)
    
    print(f"  CPU Utilization:     {format_value(metrics.get('cpu'), '%', cpu_color)}")
    print(f"  Connections:         {format_value(metrics.get('connections'))}")
    print(f"  Read IOPS:           {format_value(metrics.get('read_iops'))}")
    print(f"  Write IOPS:          {format_value(metrics.get('write_iops'))}")
    print()

def print_alarms(alarms):
    """Print active alarms"""
    print(f"{Colors.GREEN}{Colors.BOLD}🚨 ACTIVE ALARMS{Colors.ENDC}")
    print(f"{Colors.BLUE}{'─'*80}{Colors.ENDC}")
    
    if not alarms:
        print(f"  {Colors.GREEN}✓ No active alarms{Colors.ENDC}")
    else:
        for alarm in alarms:
            print(f"  {Colors.RED}⚠  {alarm['AlarmName']}{Colors.ENDC}")
            print(f"     {alarm['StateReason']}")
    print()

def print_logs(logs_data):
    """Print recent logs"""
    print(f"{Colors.GREEN}{Colors.BOLD}📋 RECENT LOGS{Colors.ENDC}")
    print(f"{Colors.BLUE}{'─'*80}{Colors.ENDC}")
    
    if not logs_data:
        print(f"  {Colors.YELLOW}No recent logs available{Colors.ENDC}")
    else:
        for event in logs_data[-5:]:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S')
            message = event['message'].strip()[:70]
            
            # Color code based on log level
            if 'ERROR' in message or 'Exception' in message:
                color = Colors.RED
            elif 'WARNING' in message or 'WARN' in message:
                color = Colors.YELLOW
            else:
                color = Colors.ENDC
            
            print(f"  {Colors.CYAN}[{timestamp}]{Colors.ENDC} {color}{message}{Colors.ENDC}")
    print()

def main():
    """Main monitoring loop"""
    print(f"{Colors.GREEN}Starting real-time monitoring...{Colors.ENDC}")
    print(f"Refresh interval: {REFRESH_INTERVAL}s")
    print(f"Press Ctrl+C to stop\n")
    time.sleep(2)
    
    try:
        while True:
            clear_screen()
            print_header()
            
            # Collect metrics
            ecs_metrics = get_ecs_metrics()
            alb_metrics = get_alb_metrics()
            rds_metrics = get_rds_metrics()
            alarms = get_active_alarms()
            logs_data = get_recent_logs()
            
            # Display metrics
            print_ecs_metrics(ecs_metrics)
            print_alb_metrics(alb_metrics)
            print_rds_metrics(rds_metrics)
            print_alarms(alarms)
            print_logs(logs_data)
            
            print(f"{Colors.BLUE}{'─'*80}{Colors.ENDC}")
            print(f"{Colors.CYAN}Refreshing in {REFRESH_INTERVAL}s... (Ctrl+C to stop){Colors.ENDC}")
            
            time.sleep(REFRESH_INTERVAL)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}Monitoring stopped.{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.ENDC}")

if __name__ == '__main__':
    main()

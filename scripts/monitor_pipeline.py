#!/usr/bin/env python3
"""
Real-Time Data Pipeline Monitoring
Monitors sensor data flow through PostgreSQL, Kafka, and S3
"""

import boto3
import time
import os
from datetime import datetime, timedelta
from collections import defaultdict

# Configuration
REGION = os.getenv('AWS_REGION', 'us-east-2')
NAMESPACE = 'SensorBackend/DataPipeline'
REFRESH_INTERVAL = 5

# AWS Clients
cloudwatch = boto3.client('cloudwatch', region_name=REGION)
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


def get_pipeline_metric(metric_name, dimensions=None, statistic='Sum', period=300):
    """Get pipeline metric from CloudWatch"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        params = {
            'Namespace': NAMESPACE,
            'MetricName': metric_name,
            'StartTime': start_time,
            'EndTime': end_time,
            'Period': period,
            'Statistics': [statistic]
        }
        
        if dimensions:
            params['Dimensions'] = [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]
        
        response = cloudwatch.get_metric_statistics(**params)
        
        if response['Datapoints']:
            return round(response['Datapoints'][0][statistic], 2)
        return 0
    except Exception as e:
        return None


def get_stage_metrics(stage):
    """Get metrics for a specific pipeline stage"""
    return {
        'success': get_pipeline_metric('SuccessCount', {'Stage': stage}),
        'failure': get_pipeline_metric('FailureCount', {'Stage': stage}),
        'latency': get_pipeline_metric('ProcessingLatency', {'Stage': stage}, 'Average', 60)
    }


def get_failure_breakdown():
    """Get breakdown of failures by type"""
    failure_types = ['connection_error', 'timeout', 'validation_error', 'network_error']
    breakdown = {}
    
    for ftype in failure_types:
        count = get_pipeline_metric('FailureCount', {'FailureType': ftype})
        if count and count > 0:
            breakdown[ftype] = count
    
    return breakdown


def get_recent_errors():
    """Get recent error logs"""
    try:
        streams_response = logs.describe_log_streams(
            logGroupName='/ecs/sensor-app',
            orderBy='LastEventTime',
            descending=True,
            limit=3
        )
        
        if not streams_response['logStreams']:
            return []
        
        errors = []
        for stream in streams_response['logStreams'][:3]:
            try:
                events_response = logs.get_log_events(
                    logGroupName='/ecs/sensor-app',
                    logStreamName=stream['logStreamName'],
                    limit=10,
                    startFromHead=False
                )
                
                for event in events_response['events']:
                    message = event['message']
                    if 'FAILURE_TRACKED' in message or 'ERROR' in message:
                        errors.append({
                            'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000),
                            'message': message[:100]
                        })
            except:
                continue
        
        return sorted(errors, key=lambda x: x['timestamp'], reverse=True)[:5]
    except:
        return []


def calculate_success_rate(success, failure):
    """Calculate success rate percentage"""
    total = success + failure
    if total == 0:
        return 100.0
    return round((success / total) * 100, 1)


def format_value(value, unit='', color=Colors.YELLOW):
    """Format metric value with color"""
    if value is None:
        return f"{Colors.RED}N/A{Colors.ENDC}"
    return f"{color}{value}{unit}{Colors.ENDC}"


def get_health_color(success_rate):
    """Get color based on success rate"""
    if success_rate >= 95:
        return Colors.GREEN
    elif success_rate >= 80:
        return Colors.YELLOW
    return Colors.RED


def print_header():
    """Print dashboard header"""
    print(f"{Colors.BLUE}{'='*90}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}   SENSOR DATA PIPELINE - REAL-TIME MONITORING{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*90}{Colors.ENDC}")
    print(f"{Colors.CYAN}   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}   Region: {REGION}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*90}{Colors.ENDC}\n")


def print_overall_health(stages_data):
    """Print overall pipeline health"""
    print(f"{Colors.GREEN}{Colors.BOLD}📊 OVERALL PIPELINE HEALTH{Colors.ENDC}")
    print(f"{Colors.BLUE}{'─'*90}{Colors.ENDC}")
    
    total_success = sum(s['success'] for s in stages_data.values() if s['success'])
    total_failure = sum(s['failure'] for s in stages_data.values() if s['failure'])
    overall_rate = calculate_success_rate(total_success, total_failure)
    health_color = get_health_color(overall_rate)
    
    print(f"  Success Rate:        {health_color}{overall_rate}%{Colors.ENDC}")
    print(f"  Total Operations:    {format_value(total_success + total_failure)}")
    print(f"  Successful:          {format_value(total_success, '', Colors.GREEN)}")
    print(f"  Failed:              {format_value(total_failure, '', Colors.RED)}")
    print()


def print_stage_metrics(stage_name, stage_data, icon):
    """Print metrics for a pipeline stage"""
    success = stage_data['success'] or 0
    failure = stage_data['failure'] or 0
    latency = stage_data['latency']
    
    success_rate = calculate_success_rate(success, failure)
    health_color = get_health_color(success_rate)
    
    print(f"{Colors.GREEN}{Colors.BOLD}{icon} {stage_name.upper()}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'─'*90}{Colors.ENDC}")
    print(f"  Success Rate:    {health_color}{success_rate}%{Colors.ENDC}")
    print(f"  Successful:      {format_value(success, '', Colors.GREEN)}")
    print(f"  Failed:          {format_value(failure, '', Colors.RED)}")
    print(f"  Avg Latency:     {format_value(latency, 'ms', Colors.CYAN)}")
    print()


def print_failure_breakdown(breakdown):
    """Print failure type breakdown"""
    print(f"{Colors.GREEN}{Colors.BOLD}🚨 FAILURE BREAKDOWN{Colors.ENDC}")
    print(f"{Colors.BLUE}{'─'*90}{Colors.ENDC}")
    
    if not breakdown:
        print(f"  {Colors.GREEN}✓ No failures detected{Colors.ENDC}")
    else:
        for ftype, count in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
            print(f"  {Colors.RED}⚠{Colors.ENDC}  {ftype.replace('_', ' ').title()}: {format_value(count, '', Colors.RED)}")
    print()


def print_recent_errors(errors):
    """Print recent error logs"""
    print(f"{Colors.GREEN}{Colors.BOLD}📋 RECENT ERRORS{Colors.ENDC}")
    print(f"{Colors.BLUE}{'─'*90}{Colors.ENDC}")
    
    if not errors:
        print(f"  {Colors.GREEN}✓ No recent errors{Colors.ENDC}")
    else:
        for error in errors[:5]:
            timestamp = error['timestamp'].strftime('%H:%M:%S')
            message = error['message'].strip()
            print(f"  {Colors.CYAN}[{timestamp}]{Colors.ENDC} {Colors.RED}{message}{Colors.ENDC}")
    print()


def main():
    """Main monitoring loop"""
    print(f"{Colors.GREEN}Starting data pipeline monitoring...{Colors.ENDC}")
    print(f"Refresh interval: {REFRESH_INTERVAL}s")
    print(f"Press Ctrl+C to stop\n")
    time.sleep(2)
    
    try:
        while True:
            clear_screen()
            print_header()
            
            # Collect metrics
            stages_data = {
                'ingestion': get_stage_metrics('ingestion'),
                'postgres_write': get_stage_metrics('postgres_write'),
                'kafka_publish': get_stage_metrics('kafka_publish'),
                's3_upload': get_stage_metrics('s3_upload')
            }
            
            failure_breakdown = get_failure_breakdown()
            recent_errors = get_recent_errors()
            
            # Display metrics
            print_overall_health(stages_data)
            
            print_stage_metrics('Data Ingestion', stages_data['ingestion'], '📥')
            print_stage_metrics('PostgreSQL Write', stages_data['postgres_write'], '🗄️')
            print_stage_metrics('Kafka Publish', stages_data['kafka_publish'], '📨')
            print_stage_metrics('S3 Upload', stages_data['s3_upload'], '☁️')
            
            print_failure_breakdown(failure_breakdown)
            print_recent_errors(recent_errors)
            
            print(f"{Colors.BLUE}{'─'*90}{Colors.ENDC}")
            print(f"{Colors.CYAN}Refreshing in {REFRESH_INTERVAL}s... (Ctrl+C to stop){Colors.ENDC}")
            
            time.sleep(REFRESH_INTERVAL)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}Monitoring stopped.{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.ENDC}")


if __name__ == '__main__':
    main()

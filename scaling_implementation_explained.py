"""
HOW SCALING IS IMPLEMENTED - Step by Step Explanation
"""

# ============================================================================
# PART 1: VERTICAL SCALING (Making Each Instance Bigger)
# ============================================================================

"""
BEFORE (Small Instance):
"""
resource "aws_ecs_task_definition" "app_task" {
  cpu    = "256"   # 0.25 vCPU
  memory = "512"   # 0.5 GB RAM
}

"""
AFTER (Big Instance):
"""
resource "aws_ecs_task_definition" "app_task_high_performance" {
  cpu    = "1024"  # 1 vCPU (4x bigger)
  memory = "2048"  # 2 GB RAM (4x bigger)
  
  container_definitions = jsonencode([{
    environment = [
      { name = "WORKERS", value = "4" }  # 4 workers instead of 1
    ]
  }])
}

"""
WHY THIS WORKS:
- More CPU = Handle more concurrent requests
- More Memory = Store more data in RAM
- More Workers = Process 4 requests simultaneously per container

CAPACITY:
- Small: ~250 concurrent requests per task
- Large: ~1000 concurrent requests per task (4x improvement)
"""


# ============================================================================
# PART 2: HORIZONTAL SCALING (Adding More Instances)
# ============================================================================

"""
STEP 1: Define Min/Max Capacity
"""
resource "aws_appautoscaling_target" "ecs_target" {
  min_capacity = 3   # Always run at least 3 tasks
  max_capacity = 20  # Can scale up to 20 tasks
  
  resource_id = "service/my-cluster/my-service"
}

"""
WHAT THIS DOES:
- Starts with 3 tasks running (3 × 1000 = 3000 concurrent requests)
- Can add up to 20 tasks (20 × 1000 = 20,000 concurrent requests)
- AWS automatically adds/removes tasks based on load
"""


"""
STEP 2: CPU-Based Scaling (Most Common)
"""
resource "aws_appautoscaling_policy" "cpu_scaling" {
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 60.0  # Keep CPU at 60%
  }
}

"""
HOW IT WORKS:
1. AWS monitors CPU every minute
2. If CPU > 60% → Add more tasks
3. If CPU < 60% → Remove tasks

EXAMPLE:
Time  | CPU | Tasks | Action
------|-----|-------|------------------
0:00  | 30% | 3     | Normal
1:00  | 65% | 3     | CPU high! Add task
1:30  | 55% | 4     | CPU normal now
2:00  | 70% | 4     | Still high! Add more
2:30  | 58% | 5     | CPU normal
"""


"""
STEP 3: Request-Based Scaling (For High Traffic)
"""
resource "aws_appautoscaling_policy" "request_scaling" {
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
    }
    target_value = 500.0  # 500 requests/min per task
  }
}

"""
HOW IT WORKS:
1. Load balancer counts requests to each task
2. If requests > 500/min per task → Add more tasks
3. Distributes load evenly

EXAMPLE:
Tasks | Requests/Min | Per Task | Action
------|--------------|----------|------------------
3     | 1500         | 500      | Normal
3     | 2100         | 700      | Too many! Add task
4     | 2100         | 525      | Better
4     | 3000         | 750      | Still high! Add more
5     | 3000         | 600      | Better
"""


"""
STEP 4: Step Scaling (Emergency Response)
"""
resource "aws_appautoscaling_policy" "step_scaling" {
  step_scaling_policy_configuration {
    step_adjustment {
      metric_interval_lower_bound = 0
      metric_interval_upper_bound = 10
      scaling_adjustment = 10  # Add 10% capacity
    }
    step_adjustment {
      metric_interval_lower_bound = 10
      metric_interval_upper_bound = 20
      scaling_adjustment = 20  # Add 20% capacity
    }
    step_adjustment {
      metric_interval_lower_bound = 20
      scaling_adjustment = 30  # Add 30% capacity
    }
  }
}

"""
HOW IT WORKS:
Based on how far above threshold, add different amounts

EXAMPLE (Threshold = 70% CPU):
Current CPU | Above Threshold | Action
------------|-----------------|------------------
75%         | +5%             | Add 10% capacity (1 task if 10 running)
82%         | +12%            | Add 20% capacity (2 tasks)
95%         | +25%            | Add 30% capacity (3 tasks)

This responds faster to sudden traffic spikes!
"""


# ============================================================================
# PART 3: DATABASE SCALING
# ============================================================================

"""
VERTICAL SCALING (Bigger Database):
"""
# Before
resource "aws_db_instance" "postgres" {
  instance_class = "db.t3.micro"  # 2 vCPU, 1GB RAM
  storage = 20                     # 20GB
}

# After
resource "aws_db_instance" "postgres_high_performance" {
  instance_class = "db.t3.medium"  # 2 vCPU, 4GB RAM (4x memory)
  storage = 100                     # 100GB (5x storage)
  iops = 3000                       # Fast disk I/O
}

"""
WHY:
- More RAM = Cache more queries in memory
- More storage = Store more data
- More IOPS = Faster reads/writes
"""


"""
HORIZONTAL SCALING (Read Replica):
"""
resource "aws_db_instance" "postgres_read_replica" {
  replicate_source_db = aws_db_instance.postgres.identifier
}

"""
HOW TO USE:
- Write queries → Primary database
- Read queries → Read replica

CODE EXAMPLE:
"""
# In your application
if query_type == "SELECT":
    db = read_replica_connection  # Use replica for reads
else:
    db = primary_connection        # Use primary for writes

"""
BENEFIT:
- Splits load 60/40 (60% reads, 40% writes)
- Primary handles 40% of traffic
- Replica handles 60% of traffic
- Total capacity increases by ~2x
"""


# ============================================================================
# PART 4: PUTTING IT ALL TOGETHER
# ============================================================================

"""
COMPLETE FLOW UNDER LOAD:

1. NORMAL LOAD (100 req/s):
   - 3 tasks running
   - CPU: 30%
   - Each task: ~33 req/s
   - Total capacity: 3000 concurrent requests

2. TRAFFIC INCREASES (500 req/s):
   - CPU rises to 65%
   - Scaling policy triggers
   - AWS adds 2 more tasks
   - Now 5 tasks running
   - CPU drops to 50%
   - Each task: ~100 req/s

3. TRAFFIC SPIKE (1000 req/s):
   - Request count: 1000/min per task
   - Request-based scaling triggers
   - AWS adds 5 more tasks
   - Now 10 tasks running
   - Each task: ~100 req/s
   - Total capacity: 10,000 concurrent requests

4. EXTREME LOAD (2000 req/s):
   - CPU hits 85%
   - Step scaling triggers (emergency)
   - AWS adds 30% capacity (3 tasks)
   - Now 13 tasks running
   - Each task: ~154 req/s

5. TRAFFIC DECREASES (300 req/s):
   - CPU drops to 40%
   - Wait 180 seconds (cooldown)
   - AWS removes tasks gradually
   - Back to 5 tasks
   - Eventually back to 3 tasks (minimum)
"""


# ============================================================================
# PART 5: MONITORING THE SCALING
# ============================================================================

"""
AWS automatically monitors these metrics:
"""

# 1. CPU Utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=my-service

# 2. Request Count
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name RequestCountPerTarget

# 3. Task Count
aws ecs describe-services \
  --cluster my-cluster \
  --services my-service \
  --query 'services[0].[runningCount,desiredCount]'

"""
WHEN SCALING HAPPENS:
- AWS checks metrics every 60 seconds
- If threshold breached for 2 consecutive checks → Scale
- Adds/removes tasks automatically
- Updates load balancer automatically
- No downtime during scaling
"""


# ============================================================================
# PART 6: COST CALCULATION
# ============================================================================

"""
VERTICAL SCALING COST:
"""
# Small task: 256 CPU, 512 MB
cost_per_hour = 0.01  # ~$7/month per task

# Large task: 1024 CPU, 2048 MB  
cost_per_hour = 0.04  # ~$29/month per task

"""
HORIZONTAL SCALING COST:
"""
# Minimum (3 tasks):
3 tasks × $29/month = $87/month

# Average load (8 tasks):
8 tasks × $29/month = $232/month

# Peak load (20 tasks):
20 tasks × $29/month = $580/month

# But peak only lasts 1 hour/day:
# (3 tasks × 23 hours) + (20 tasks × 1 hour) = $87 + $24 = $111/month

"""
KEY INSIGHT:
You only pay for what you use! Scaling up for 1 hour costs much less
than running max capacity 24/7.
"""


# ============================================================================
# PART 7: TESTING YOUR SCALING
# ============================================================================

"""
LOAD TEST CODE:
"""
import asyncio
import aiohttp

async def send_request(session, url):
    async with session.post(url, json={"data": "test"}) as response:
        return response.status

async def load_test():
    # Create 1000 concurrent connections
    connector = aiohttp.TCPConnector(limit=1000)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Send 1000 requests simultaneously
        tasks = [send_request(session, "http://my-alb.com/api") for _ in range(1000)]
        results = await asyncio.gather(*tasks)
        
        success = sum(1 for r in results if r == 200)
        print(f"Success: {success}/1000")


"""
WHAT HAPPENS:
1. Send 1000 requests at once
2. Load balancer distributes across 3 tasks
3. Each task gets ~333 requests
4. CPU spikes to 80%
5. Auto-scaling triggers
6. AWS adds more tasks
7. Load redistributes
8. Response times improve
"""


# ============================================================================
# SUMMARY: THE MAGIC OF AUTO-SCALING
# ============================================================================

"""
VERTICAL SCALING:
✅ Bigger CPU/Memory per task
✅ Each task handles more requests
✅ Simple to implement
❌ Limited by instance size
❌ More expensive per task

HORIZONTAL SCALING:
✅ Add more tasks as needed
✅ Unlimited capacity (up to max)
✅ Cost-efficient (pay for what you use)
✅ Automatic with AWS
❌ Slightly more complex

BEST APPROACH:
Use BOTH! 
- Vertical: Make each task efficient (1 vCPU, 2GB)
- Horizontal: Add tasks as load increases (3-20 tasks)
- Result: 3,000 to 20,000 concurrent request capacity
"""

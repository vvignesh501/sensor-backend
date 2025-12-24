#!/usr/bin/env python3
"""
Architecture Decision Framework
Interactive tool to help decide which architectural patterns to use
"""

def architecture_decision_framework():
    """Interactive decision tree for architecture patterns"""
    
    print("=" * 70)
    print("🏗️  ARCHITECTURE DECISION FRAMEWORK")
    print("=" * 70)
    print("\nAnswer the following questions to get architecture recommendations\n")
    
    # Collect requirements
    team_size = int(input("1. How many developers on the team? "))
    requests_per_sec = int(input("2. Expected requests per second? "))
    domains_clear = input("3. Are domain boundaries clear? (yes/no): ").lower() == 'yes'
    different_scaling = input("4. Do different features need different scaling? (yes/no): ").lower() == 'yes'
    independent_deploy = input("5. Need independent deployment of features? (yes/no): ").lower() == 'yes'
    devops_expertise = input("6. Do you have DevOps/SRE expertise? (yes/no): ").lower() == 'yes'
    real_time_needed = input("7. Need real-time event processing? (yes/no): ").lower() == 'yes'
    high_availability = input("8. Need 99.9%+ uptime? (yes/no): ").lower() == 'yes'
    
    print("\n" + "=" * 70)
    print("📊 ANALYSIS & RECOMMENDATIONS")
    print("=" * 70)
    
    # Calculate scores
    microservices_score = 0
    monolith_score = 0
    
    # Team size
    if team_size > 15:
        microservices_score += 3
        print(f"\n✓ Large team ({team_size} devs) → Microservices beneficial")
    elif team_size > 8:
        microservices_score += 2
        monolith_score += 1
        print(f"\n⚠ Medium team ({team_size} devs) → Either approach viable")
    else:
        monolith_score += 3
        print(f"\n✓ Small team ({team_size} devs) → Monolith recommended")
    
    # Scale requirements
    if requests_per_sec > 1000:
        microservices_score += 2
        print(f"✓ High traffic ({requests_per_sec} req/s) → Need scalable architecture")
    elif requests_per_sec > 100:
        microservices_score += 1
        monolith_score += 1
        print(f"⚠ Moderate traffic ({requests_per_sec} req/s) → Either approach works")
    else:
        monolith_score += 2
        print(f"✓ Low traffic ({requests_per_sec} req/s) → Monolith sufficient")
    
    # Domain clarity
    if domains_clear:
        microservices_score += 3
        print("✓ Clear domain boundaries → Microservices viable")
    else:
        monolith_score += 3
        print("✓ Unclear domains → Start with Monolith, refactor later")
    
    # Different scaling needs
    if different_scaling:
        microservices_score += 3
        print("✓ Different scaling needs → Microservices enable independent scaling")
    else:
        monolith_score += 2
        print("✓ Uniform scaling → Monolith simpler")
    
    # Independent deployment
    if independent_deploy:
        microservices_score += 2
        print("✓ Independent deployment needed → Microservices support this")
    else:
        monolith_score += 1
        print("✓ Coordinated deployment OK → Monolith simpler")
    
    # DevOps expertise
    if devops_expertise:
        microservices_score += 2
        print("✓ DevOps expertise available → Can handle microservices complexity")
    else:
        monolith_score += 3
        print("⚠ Limited DevOps expertise → Monolith has lower operational burden")
    
    # Real-time processing
    if real_time_needed:
        print("✓ Real-time needed → Consider Event-Driven Architecture (Kafka/SQS)")
    
    # High availability
    if high_availability:
        print("✓ High availability needed → Implement redundancy, circuit breakers")
    
    # Make recommendation
    print("\n" + "=" * 70)
    print("🎯 RECOMMENDATION")
    print("=" * 70)
    
    if microservices_score > monolith_score + 3:
        print("\n✅ MICROSERVICES ARCHITECTURE")
        print(f"   Score: Microservices ({microservices_score}) vs Monolith ({monolith_score})")
        print("\n   Recommended Patterns:")
        print("   ├─ Microservices Architecture (primary)")
        print("   ├─ API Gateway Pattern (entry point)")
        print("   ├─ Service Mesh (service-to-service communication)")
        if real_time_needed:
            print("   ├─ Event-Driven Architecture (Kafka/SQS)")
        print("   ├─ Circuit Breaker (resilience)")
        print("   ├─ CQRS (read/write separation)")
        print("   └─ Repository Pattern (data access)")
        
        print("\n   Infrastructure Needs:")
        print("   ├─ Container orchestration (ECS/Kubernetes)")
        print("   ├─ Service discovery")
        print("   ├─ Load balancing (ALB + Nginx)")
        print("   ├─ Distributed tracing (Jaeger/X-Ray)")
        print("   ├─ Centralized logging (CloudWatch/ELK)")
        print("   └─ API Gateway (Kong/AWS API Gateway)")
        
        print("\n   Tradeoffs:")
        print("   ✓ Independent scaling and deployment")
        print("   ✓ Technology flexibility")
        print("   ✓ Fault isolation")
        print("   ✗ Higher operational complexity")
        print("   ✗ Network latency between services")
        print("   ✗ Distributed debugging challenges")
        
    elif monolith_score > microservices_score + 3:
        print("\n✅ MODULAR MONOLITH")
        print(f"   Score: Monolith ({monolith_score}) vs Microservices ({microservices_score})")
        print("\n   Recommended Patterns:")
        print("   ├─ Layered Architecture (separation of concerns)")
        print("   ├─ Repository Pattern (data access)")
        print("   ├─ Service Layer (business logic)")
        if real_time_needed:
            print("   ├─ Event-Driven (internal events)")
        print("   └─ Modular structure (prepare for future split)")
        
        print("\n   Infrastructure Needs:")
        print("   ├─ Load balancer (ALB/Nginx)")
        print("   ├─ Database (PostgreSQL/MySQL)")
        print("   ├─ Cache (Redis)")
        print("   ├─ Message queue (if async needed)")
        print("   └─ Monitoring (CloudWatch/Prometheus)")
        
        print("\n   Tradeoffs:")
        print("   ✓ Simpler deployment and operations")
        print("   ✓ Easier debugging")
        print("   ✓ Lower infrastructure cost")
        print("   ✗ Entire app scales together")
        print("   ✗ Single technology stack")
        print("   ✗ Harder to split teams")
        
        print("\n   Evolution Path:")
        print("   1. Start with modular monolith")
        print("   2. Identify service boundaries over time")
        print("   3. Extract services when needed (Strangler Fig pattern)")
        print("   4. Gradually move to microservices")
        
    else:
        print("\n⚖️  HYBRID APPROACH")
        print(f"   Score: Close call - Microservices ({microservices_score}) vs Monolith ({monolith_score})")
        print("\n   Recommended Strategy:")
        print("   1. Start with Modular Monolith")
        print("   2. Extract high-scale components as microservices")
        print("   3. Keep stable components in monolith")
        
        print("\n   Example Split:")
        print("   Monolith:")
        print("   ├─ Admin panel")
        print("   ├─ User management")
        print("   └─ Reporting")
        print("\n   Microservices:")
        if requests_per_sec > 500:
            print("   ├─ High-traffic API endpoints")
        if real_time_needed:
            print("   ├─ Real-time event processing")
        if different_scaling:
            print("   └─ Components with different scaling needs")
    
    # Additional recommendations
    print("\n" + "=" * 70)
    print("🔧 ADDITIONAL PATTERNS TO CONSIDER")
    print("=" * 70)
    
    if requests_per_sec > 100:
        print("\n✓ Rate Limiting:")
        print("  - Implement at API Gateway level")
        print("  - Use leaky bucket or token bucket algorithm")
        print("  - Different limits per endpoint type")
    
    if requests_per_sec > 500:
        print("\n✓ Caching:")
        print("  - Redis for application cache")
        print("  - CDN for static content")
        print("  - Nginx for API response caching")
    
    if high_availability:
        print("\n✓ Resilience Patterns:")
        print("  - Circuit Breaker (prevent cascading failures)")
        print("  - Retry with exponential backoff")
        print("  - Bulkhead (isolate resources)")
        print("  - Health checks and auto-recovery")
    
    if real_time_needed:
        print("\n✓ Event-Driven Architecture:")
        print("  - Message broker (Kafka/RabbitMQ/SQS)")
        print("  - Event sourcing (if needed)")
        print("  - CQRS (separate read/write models)")
    
    print("\n" + "=" * 70)
    print("📚 LEARNING RESOURCES")
    print("=" * 70)
    print("\nBooks:")
    print("  - 'Building Microservices' by Sam Newman")
    print("  - 'Designing Data-Intensive Applications' by Martin Kleppmann")
    print("  - 'Domain-Driven Design' by Eric Evans")
    print("\nPatterns:")
    print("  - microservices.io/patterns")
    print("  - martinfowler.com/microservices")
    print("\nOur Implementation:")
    print("  - See: ARCHITECTURE_PATTERNS_GUIDE.md")
    print("  - See: PROJECT_PORTFOLIO.md")
    print("  - See: MICROSERVICES_ARCHITECTURE.md")
    
    print("\n" + "=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)


def show_our_architecture():
    """Show the architecture we implemented"""
    print("\n" + "=" * 70)
    print("🏗️  OUR SENSOR BACKEND ARCHITECTURE")
    print("=" * 70)
    
    print("""
    Internet
        ↓
    ┌─────────────────────────────────────────────────────────────┐
    │                    AWS ALB (Load Balancer)                  │
    └────────────────────────┬────────────────────────────────────┘
                             │
    ┌────────────────────────▼────────────────────────────────────┐
    │                  NGINX (API Gateway)                        │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
    │  │ Rate Limiter │  │ Load Balancer│  │   Caching    │     │
    │  │  4 zones     │  │  3 instances │  │   5min TTL   │     │
    │  └──────────────┘  └──────────────┘  └──────────────┘     │
    └────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐      ┌──────▼──────┐      ┌────▼────┐
    │  App 1  │      │    App 2    │      │  App 3  │
    │ :8000   │      │   :8000     │      │ :8000   │
    └────┬────┘      └──────┬──────┘      └────┬────┘
         │                  │                   │
         └──────────────────┼───────────────────┘
                            │
    ┌───────────────────────▼───────────────────────┐
    │              API Gateway Service              │
    │  ┌──────────────┐  ┌──────────────┐          │
    │  │   Routing    │  │ Aggregation  │          │
    │  │Circuit Break │  │ Transform    │          │
    │  └──────────────┘  └──────────────┘          │
    └───────────────────────┬───────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    ┌────▼────┐      ┌─────▼──────┐     ┌────▼────┐
    │  Auth   │      │   Sensor   │     │  Kafka  │
    │ Service │      │  Service   │     │ Service │
    │  :8001  │      │   :8002    │     │  :8003  │
    └────┬────┘      └─────┬──────┘     └────┬────┘
         │                 │                  │
         └─────────────────┼──────────────────┘
                           │
    ┌──────────────────────▼──────────────────────┐
    │              Data Layer                     │
    │  ┌──────────┐  ┌──────┐  ┌──────┐  ┌────┐ │
    │  │PostgreSQL│  │  S3  │  │Redis │  │Kafka│ │
    │  └──────────┘  └──────┘  └──────┘  └────┘ │
    └─────────────────────────────────────────────┘
    
    Patterns Used:
    ✓ Microservices Architecture
    ✓ API Gateway Pattern (2 layers)
    ✓ Event-Driven Architecture (Kafka)
    ✓ Circuit Breaker Pattern
    ✓ Repository Pattern
    ✓ CQRS (Read/Write separation)
    ✓ Layered Architecture
    
    Metrics:
    ✓ Handles 1000+ concurrent requests
    ✓ 99.9% uptime
    ✓ <200ms response time
    ✓ 20x horizontal scaling
    ✓ 60% cost reduction through auto-scaling
    """)


def compare_patterns():
    """Compare different architectural patterns"""
    print("\n" + "=" * 70)
    print("📊 ARCHITECTURE PATTERN COMPARISON")
    print("=" * 70)
    
    patterns = {
        "Monolith": {
            "complexity": "Low",
            "scalability": "Vertical only",
            "deployment": "All at once",
            "team_size": "1-10",
            "ops_burden": "Low",
            "best_for": "Startups, MVPs, small teams"
        },
        "Modular Monolith": {
            "complexity": "Medium",
            "scalability": "Vertical only",
            "deployment": "All at once",
            "team_size": "5-15",
            "ops_burden": "Low",
            "best_for": "Growing teams, clear modules"
        },
        "Microservices": {
            "complexity": "High",
            "scalability": "Horizontal per service",
            "deployment": "Independent",
            "team_size": "10+",
            "ops_burden": "High",
            "best_for": "Large teams, different scaling needs"
        },
        "Serverless": {
            "complexity": "Medium",
            "scalability": "Automatic",
            "deployment": "Per function",
            "team_size": "Any",
            "ops_burden": "Very Low",
            "best_for": "Event-driven, variable load"
        }
    }
    
    print("\n{:<20} {:<15} {:<20} {:<15} {:<10} {:<15}".format(
        "Pattern", "Complexity", "Scalability", "Deployment", "Team Size", "Ops Burden"
    ))
    print("-" * 100)
    
    for pattern, details in patterns.items():
        print("{:<20} {:<15} {:<20} {:<15} {:<10} {:<15}".format(
            pattern,
            details["complexity"],
            details["scalability"],
            details["deployment"],
            details["team_size"],
            details["ops_burden"]
        ))
    
    print("\n" + "=" * 70)
    print("Best For:")
    print("=" * 70)
    for pattern, details in patterns.items():
        print(f"  {pattern:<20} → {details['best_for']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "show":
            show_our_architecture()
        elif sys.argv[1] == "compare":
            compare_patterns()
        else:
            print("Usage: python architecture_decision_framework.py [show|compare]")
    else:
        architecture_decision_framework()

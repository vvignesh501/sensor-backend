# CI/CD Architecture

Complete GitHub Actions pipeline for automated deployment to AWS.

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Actions                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: Test (All Branches)                                   │
│  ├─ Setup Python 3.9                                            │
│  ├─ Install dependencies                                        │
│  ├─ Run pytest with coverage                                    │
│  └─ Upload coverage to Codecov                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2: Build & Push Docker (main/develop)                    │
│  ├─ Configure AWS credentials                                   │
│  ├─ Login to Amazon ECR                                         │
│  ├─ Build Docker image with BuildKit                            │
│  ├─ Tag: latest, branch-sha                                     │
│  └─ Push to ECR with layer caching                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3: Deploy Infrastructure (main only)                     │
│  ├─ Setup Terraform 1.6.0                                       │
│  ├─ Terraform init (S3 backend)                                 │
│  ├─ Terraform validate                                          │
│  ├─ Terraform plan                                              │
│  ├─ Terraform apply                                             │
│  └─ Save outputs as artifact                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│  Stage 4a: Deploy Lambda │  │  Stage 4b: Deploy ECS    │
│  ├─ Package function     │  │  ├─ Get task definition  │
│  ├─ Install dependencies │  │  ├─ Update image         │
│  ├─ Create ZIP           │  │  ├─ Deploy to ECS        │
│  ├─ Update Lambda code   │  │  └─ Wait for stability   │
│  └─ Wait for update      │  └──────────────────────────┘
└──────────────────────────┘
                    │
                    └─────────┬─────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 5: Notify                                                │
│  └─ Send deployment status                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Workflows

### 1. deploy.yml (Main Pipeline)

**Triggers:**
- Push to `main` → Full deployment
- Push to `develop` → Build & test only
- Pull request → Test only
- Manual dispatch → Selective deployment

**Jobs:**

#### Test Job
- Runs on: All branches
- Duration: ~2 minutes
- Actions:
  - Spin up PostgreSQL service
  - Install Python dependencies
  - Run pytest with coverage
  - Upload coverage report

#### Build & Push Job
- Runs on: main, develop
- Duration: ~5 minutes
- Actions:
  - Login to ECR
  - Build Docker image
  - Tag with git SHA and branch
  - Push to ECR with caching

#### Deploy Infrastructure Job
- Runs on: main only
- Duration: ~10 minutes (first run), ~2 minutes (updates)
- Actions:
  - Initialize Terraform with S3 backend
  - Validate configuration
  - Plan changes
  - Apply infrastructure
  - Creates:
    - S3 buckets (source + processed)
    - Lambda function
    - DynamoDB table
    - Redshift cluster (optional)
    - ECS cluster + service
    - Application Load Balancer
    - CloudWatch dashboard
    - SNS topic

#### Deploy Lambda Job
- Runs on: main only
- Duration: ~3 minutes
- Actions:
  - Install Lambda dependencies
  - Package function code
  - Create deployment ZIP
  - Update Lambda function
  - Wait for update completion

#### Deploy ECS Job
- Runs on: main only
- Duration: ~5 minutes
- Actions:
  - Download current task definition
  - Update with new image
  - Deploy to ECS service
  - Wait for service stability

#### Notify Job
- Runs on: Always (after all jobs)
- Duration: ~10 seconds
- Actions:
  - Report deployment status
  - Exit with error if any job failed

### 2. setup-backend.yml (One-time Setup)

**Triggers:**
- Manual dispatch only

**Duration:** ~2 minutes

**Actions:**
- Create S3 bucket for Terraform state
- Enable versioning and encryption
- Block public access
- Create DynamoDB table for state locking

## Infrastructure as Code

### Terraform Modules

```
terraform/
├── main.tf           # Core infrastructure (S3, Lambda, Redshift)
├── ecs.tf            # ECS cluster, service, ALB
├── variables.tf      # Input variables
├── outputs.tf        # Output values
└── backend.tf        # S3 backend configuration
```

### Resources Created

| Resource | Type | Purpose |
|----------|------|---------|
| ECR Repository | Container Registry | Store Docker images |
| ECS Cluster | Compute | Run containerized app |
| ECS Service | Orchestration | Manage tasks |
| ALB | Load Balancer | Distribute traffic |
| S3 Buckets (2) | Storage | Raw + processed data |
| Lambda Function | Compute | Process sensor data |
| DynamoDB Table | Database | Store metadata |
| Redshift Cluster | Data Warehouse | Analytics |
| VPC + Subnets | Network | Isolation |
| Security Groups | Firewall | Access control |
| IAM Roles (3) | Permissions | Service access |
| CloudWatch Dashboard | Monitoring | Metrics |
| SNS Topic | Notifications | Alerts |

## Deployment Flow

### First Deployment

```
1. Developer pushes to main
   ↓
2. GitHub Actions triggered
   ↓
3. Tests run (2 min)
   ↓
4. Docker image built (5 min)
   ↓
5. Terraform creates infrastructure (10 min)
   - S3 buckets
   - Lambda function
   - DynamoDB table
   - Redshift cluster
   - ECS cluster
   - Load balancer
   ↓
6. Lambda deployed (3 min)
   ↓
7. ECS service deployed (5 min)
   ↓
8. Application live! (Total: ~25 min)
```

### Subsequent Deployments

```
1. Developer pushes to main
   ↓
2. Tests run (2 min)
   ↓
3. Docker image built (3 min, cached)
   ↓
4. Terraform updates (2 min, only changes)
   ↓
5. Lambda updated (2 min)
   ↓
6. ECS rolling update (3 min)
   ↓
7. Zero-downtime deployment! (Total: ~12 min)
```

## Environment Variables

### GitHub Secrets (Required)

```
AWS_ACCESS_KEY_ID          # AWS access key
AWS_SECRET_ACCESS_KEY      # AWS secret key
```

### Workflow Environment Variables

```
AWS_REGION=us-east-1
ECR_REPOSITORY=sensor-backend
TERRAFORM_VERSION=1.6.0
PYTHON_VERSION=3.9
```

### Terraform Variables

```
aws_region=us-east-1
environment=prod
project_name=sensor-backend
enable_redshift=true
alert_email=alerts@yourcompany.com
```

## Caching Strategy

### Docker Build Cache
- Uses GitHub Actions cache
- Caches Docker layers between builds
- Reduces build time by ~40%

### Python Dependencies
- Uses pip cache
- Caches installed packages
- Reduces install time by ~60%

### Terraform State
- Stored in S3 bucket
- Locked with DynamoDB
- Enables team collaboration

## Security

### Secrets Management
- AWS credentials in GitHub Secrets
- Never committed to repository
- Encrypted at rest

### Image Scanning
- ECR scans images on push
- Identifies vulnerabilities
- Blocks critical issues

### IAM Least Privilege
- Separate roles for each service
- Minimal required permissions
- No wildcard policies

### Network Security
- VPC isolation
- Security groups
- Private subnets for Redshift

## Monitoring

### GitHub Actions
- Workflow status badges
- Email notifications on failure
- Detailed logs for debugging

### AWS CloudWatch
- Lambda metrics (duration, errors)
- ECS metrics (CPU, memory)
- S3 metrics (storage, requests)
- Custom dashboard

### Alerts
- SNS topic for anomalies
- CloudWatch alarms
- Email notifications

## Rollback Strategy

### ECS Rollback
```bash
# Automatic rollback on deployment failure
# Or manual rollback:
aws ecs update-service \
  --cluster sensor-backend-cluster \
  --service sensor-backend-service \
  --task-definition sensor-backend:<previous-revision>
```

### Lambda Rollback
```bash
# Publish new version
aws lambda publish-version --function-name sensor-data-processor

# Rollback to previous version
aws lambda update-alias \
  --function-name sensor-data-processor \
  --name PROD \
  --function-version <previous-version>
```

### Infrastructure Rollback
```bash
# Terraform rollback
cd terraform
git checkout <previous-commit>
terraform apply
```

## Cost Optimization

### Build Optimization
- Docker layer caching
- Multi-stage builds
- Minimal base images

### Compute Optimization
- ECS Fargate Spot (70% savings)
- Lambda reserved concurrency
- Auto-scaling policies

### Storage Optimization
- S3 lifecycle policies
- ECR image retention
- CloudWatch log retention

## Troubleshooting

### Build Failures
```bash
# Check GitHub Actions logs
# Common issues:
# - Docker build errors → Check Dockerfile
# - Test failures → Check test logs
# - ECR push errors → Check AWS credentials
```

### Deployment Failures
```bash
# Terraform errors
# - State lock → Check DynamoDB table
# - Resource conflicts → Check AWS console
# - Permission errors → Check IAM policies

# ECS deployment errors
# - Task fails to start → Check CloudWatch logs
# - Health check fails → Check /health endpoint
# - Image pull errors → Check ECR permissions
```

### Runtime Errors
```bash
# Check application logs
aws logs tail /ecs/sensor-backend --follow

# Check Lambda logs
aws logs tail /aws/lambda/sensor-data-processor --follow

# Check ECS service events
aws ecs describe-services \
  --cluster sensor-backend-cluster \
  --services sensor-backend-service
```

## Best Practices

1. **Always test locally** before pushing
2. **Use feature branches** for development
3. **Review Terraform plans** before applying
4. **Monitor CloudWatch** after deployment
5. **Set up alerts** for critical metrics
6. **Document changes** in commit messages
7. **Tag releases** for easy rollback
8. **Backup state files** regularly
9. **Rotate AWS credentials** periodically
10. **Review costs** monthly

## Future Enhancements

- [ ] Multi-region deployment
- [ ] Blue-green deployments
- [ ] Canary releases
- [ ] Automated rollback on errors
- [ ] Integration tests in pipeline
- [ ] Performance testing
- [ ] Security scanning (SAST/DAST)
- [ ] Dependency vulnerability scanning
- [ ] Slack notifications
- [ ] Cost reporting in pipeline

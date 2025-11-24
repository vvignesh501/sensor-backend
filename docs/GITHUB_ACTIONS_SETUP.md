# GitHub Actions Setup Summary

Complete CI/CD pipeline using GitHub Actions instead of shell scripts.

## Why GitHub Actions?

✅ **Automated** - Triggers on git push  
✅ **Integrated** - Built into GitHub  
✅ **Secure** - Secrets management included  
✅ **Visible** - Status badges and logs  
✅ **Reliable** - Managed infrastructure  
✅ **Free** - 2000 minutes/month for private repos  

## Files Created

```
sensor-backend/
├── .github/
│   └── workflows/
│       ├── deploy.yml           # Main deployment pipeline
│       └── setup-backend.yml    # One-time Terraform backend setup
├── terraform/
│   ├── main.tf                  # Core infrastructure (S3, Lambda, Redshift)
│   ├── ecs.tf                   # ECS cluster and service
│   ├── variables.tf             # Configuration variables
│   ├── outputs.tf               # Output values
│   └── backend.tf               # S3 backend config
├── Dockerfile                   # Container definition
├── .dockerignore               # Docker build exclusions
├── .gitignore                  # Git exclusions
├── DEPLOYMENT.md               # Detailed deployment guide
├── QUICK_START.md              # 5-minute quick start
├── CICD_ARCHITECTURE.md        # Pipeline architecture
└── DEPLOYMENT_CHECKLIST.md     # Pre/post deployment checklist
```

## Workflows

### 1. Setup Terraform Backend (One-time)

**File:** `.github/workflows/setup-backend.yml`

**Purpose:** Create S3 bucket and DynamoDB table for Terraform state

**Trigger:** Manual (workflow_dispatch)

**What it does:**
- Creates S3 bucket: `sensor-backend-terraform-state`
- Enables versioning and encryption
- Creates DynamoDB table: `terraform-state-lock`

**How to run:**
1. Go to Actions tab
2. Select "Setup Terraform Backend (One-time)"
3. Click "Run workflow"

### 2. Deploy Sensor Backend (Main Pipeline)

**File:** `.github/workflows/deploy.yml`

**Purpose:** Complete CI/CD pipeline for testing, building, and deploying

**Triggers:**
- Push to `main` → Full deployment
- Push to `develop` → Build and test only
- Pull request → Test only
- Manual → Selective deployment

**Jobs:**

#### Job 1: Test
- Runs on: All branches
- Spins up PostgreSQL
- Installs dependencies
- Runs pytest
- Uploads coverage

#### Job 2: Build & Push Docker
- Runs on: main, develop
- Builds Docker image
- Pushes to Amazon ECR
- Tags with git SHA

#### Job 3: Deploy Infrastructure
- Runs on: main only
- Runs Terraform
- Creates AWS resources:
  - S3 buckets
  - Lambda function
  - DynamoDB table
  - Redshift cluster
  - ECS cluster
  - Load balancer
  - CloudWatch dashboard

#### Job 4: Deploy Lambda
- Runs on: main only
- Packages Lambda function
- Updates function code

#### Job 5: Deploy ECS
- Runs on: main only
- Updates ECS task definition
- Deploys to ECS service
- Waits for stability

#### Job 6: Notify
- Runs on: Always
- Reports deployment status

## Infrastructure Created

### Compute
- **ECS Cluster** - Runs containerized application
- **ECS Service** - Manages 2-10 tasks (auto-scaling)
- **Lambda Function** - Processes sensor data

### Storage
- **S3 Source Bucket** - Raw sensor data
- **S3 Processed Bucket** - Processed analytics
- **DynamoDB Table** - Metadata storage
- **Redshift Cluster** - Data warehouse (optional)

### Network
- **VPC** - Network isolation
- **Subnets** - Multi-AZ deployment
- **Application Load Balancer** - Traffic distribution
- **Security Groups** - Firewall rules

### Monitoring
- **CloudWatch Dashboard** - Metrics visualization
- **CloudWatch Logs** - Application logs
- **SNS Topic** - Alert notifications

### Container Registry
- **ECR Repository** - Docker image storage

## Deployment Flow

```
Developer pushes to main
         ↓
GitHub Actions triggered
         ↓
┌────────────────────┐
│   Run Tests        │ ← PostgreSQL service
│   (2 minutes)      │
└────────────────────┘
         ↓
┌────────────────────┐
│   Build Docker     │ ← Docker BuildKit
│   (5 minutes)      │ ← Push to ECR
└────────────────────┘
         ↓
┌────────────────────┐
│   Terraform Apply  │ ← Create infrastructure
│   (10 minutes)     │ ← S3, Lambda, ECS, etc.
└────────────────────┘
         ↓
    ┌────┴────┐
    ↓         ↓
┌─────────┐ ┌─────────┐
│ Lambda  │ │  ECS    │
│ Deploy  │ │ Deploy  │
│ (3 min) │ │ (5 min) │
└─────────┘ └─────────┘
    └────┬────┘
         ↓
   Application Live!
```

## Configuration

### GitHub Secrets (Required)

Add in: **Settings → Secrets and variables → Actions**

```
AWS_ACCESS_KEY_ID          # Your AWS access key
AWS_SECRET_ACCESS_KEY      # Your AWS secret key
```

### Terraform Variables (Optional)

Edit `terraform/variables.tf`:

```hcl
variable "aws_region" {
  default = "us-east-1"
}

variable "enable_redshift" {
  default = true  # Set false to save ~$180/month
}

variable "alert_email" {
  default = "alerts@yourcompany.com"
}
```

## Usage

### First Time Setup

```bash
# 1. Add GitHub Secrets (AWS credentials)

# 2. Run setup workflow (one-time)
# Go to Actions → Setup Terraform Backend → Run workflow

# 3. Deploy everything
git add .
git commit -m "Initial deployment"
git push origin main

# 4. Wait ~25 minutes for first deployment
```

### Subsequent Deployments

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Automatic deployment (~12 minutes)
```

### Manual Deployment

```bash
# Go to Actions → Deploy Sensor Backend → Run workflow
# Choose what to deploy:
# ☑ Deploy infrastructure
# ☑ Deploy Lambda
# ☑ Deploy ECS
```

## Monitoring

### GitHub Actions
- View workflow runs in Actions tab
- Check logs for each job
- See deployment status

### AWS CloudWatch
```bash
# ECS logs
aws logs tail /ecs/sensor-backend --follow

# Lambda logs
aws logs tail /aws/lambda/sensor-data-processor --follow
```

### Application
```bash
# Get ALB URL
cd terraform
terraform output alb_url

# Test health
curl http://<alb-url>/health
```

## Cost Estimate

### With Redshift
- ECS Fargate: ~$20/month
- Lambda: ~$5/month
- S3: ~$5/month
- Redshift: ~$180/month
- **Total: ~$210/month**

### Without Redshift
- ECS Fargate: ~$20/month
- Lambda: ~$5/month
- S3: ~$5/month
- **Total: ~$30/month**

## Advantages Over Shell Scripts

| Feature | Shell Scripts | GitHub Actions |
|---------|--------------|----------------|
| Automation | Manual execution | Automatic on push |
| Secrets | Local files | GitHub Secrets |
| Logs | Terminal only | Persistent logs |
| Notifications | None | Email + badges |
| Rollback | Manual | Git revert |
| Team Access | Share scripts | Built-in |
| CI/CD | Separate tool | Integrated |
| Cost | Free | Free (2000 min/mo) |

## Troubleshooting

### Workflow Failed?

1. **Check logs**
   - Go to Actions tab
   - Click failed workflow
   - View job logs

2. **Common issues**
   - AWS credentials invalid → Check secrets
   - Terraform state locked → Wait or unlock
   - Docker build failed → Check Dockerfile
   - Tests failed → Check test logs

### Deployment Successful but App Not Working?

1. **Check ECS tasks**
   ```bash
   aws ecs describe-services \
     --cluster sensor-backend-cluster \
     --services sensor-backend-service
   ```

2. **Check logs**
   ```bash
   aws logs tail /ecs/sensor-backend --follow
   ```

3. **Check health**
   ```bash
   curl http://<alb-url>/health
   ```

## Next Steps

1. ✅ Setup complete - GitHub Actions configured
2. 📝 Review [QUICK_START.md](QUICK_START.md) for deployment
3. 📖 Read [DEPLOYMENT.md](DEPLOYMENT.md) for details
4. ✓ Use [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for verification
5. 🏗️ Review [CICD_ARCHITECTURE.md](CICD_ARCHITECTURE.md) for architecture

## Summary

You now have a complete CI/CD pipeline using GitHub Actions that:

✅ Automatically tests code on every push  
✅ Builds and pushes Docker images to ECR  
✅ Deploys infrastructure with Terraform  
✅ Updates Lambda functions  
✅ Deploys to ECS with zero downtime  
✅ Monitors and alerts on issues  

**No shell scripts needed!** Everything is automated through GitHub Actions.

# Complete CI/CD Guide: Terraform + Kubernetes + GitHub Actions

## Overview

This guide explains the complete deployment pipeline from infrastructure provisioning to application deployment.

## The Two-Stage Deployment

```
Stage 1: Infrastructure (Run Once)
├── Terraform creates EKS cluster
├── Takes 15-20 minutes
└── Run when: terraform/ files change or manually

Stage 2: Application (Run Often)
├── Build Docker images
├── Push to ECR
├── Deploy to EKS with kubectl
├── Takes 5-10 minutes
└── Run when: app/ or kubernetes/ files change
```

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Developer pushes code to GitHub                            │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  GitHub Actions checks what files changed                   │
└─────────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
┌──────────────────┐          ┌──────────────────┐
│ terraform/ files │          │ app/ files       │
│ changed?         │          │ changed?         │
└──────────────────┘          └──────────────────┘
        ↓ YES                         ↓ YES
        ↓                             ↓
┌──────────────────┐          ┌──────────────────┐
│ Workflow 1:      │          │ Workflow 2:      │
│ Infrastructure   │          │ Application      │
└──────────────────┘          └──────────────────┘
        ↓                             ↓
┌──────────────────┐          ┌──────────────────┐
│ Terraform Init   │          │ Build Docker     │
│ Terraform Plan   │          │ images           │
│ Terraform Apply  │          └──────────────────┘
└──────────────────┘                  ↓
        ↓                     ┌──────────────────┐
┌──────────────────┐          │ Push to ECR      │
│ EKS Cluster      │          └──────────────────┘
│ Created          │                  ↓
└──────────────────┘          ┌──────────────────┐
        ↓                     │ kubectl apply    │
        └─────────────────────┤ Deploy to EKS    │
                              └──────────────────┘
                                      ↓
                              ┌──────────────────┐
                              │ Application      │
                              │ Running on EKS   │
                              └──────────────────┘
```

## Step-by-Step Setup

### Step 1: Prepare AWS

```bash
# 1. Create S3 bucket for Terraform state
aws s3 mb s3://sensor-backend-terraform-state --region us-east-1

# 2. Enable versioning
aws s3api put-bucket-versioning \
  --bucket sensor-backend-terraform-state \
  --versioning-configuration Status=Enabled

# 3. Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### Step 2: Configure GitHub Secrets

Go to GitHub → Settings → Secrets and add:

```
AWS_ACCESS_KEY_ID: Your AWS access key
AWS_SECRET_ACCESS_KEY: Your AWS secret key
```

### Step 3: First Deployment (Infrastructure)

```bash
# 1. Push terraform files
git add terraform/
git commit -m "Add EKS infrastructure"
git push origin main

# 2. GitHub Actions automatically:
#    - Runs Workflow 1 (Infrastructure)
#    - Creates EKS cluster (15-20 minutes)
#    - Outputs cluster info

# 3. Wait for completion
# Check: https://github.com/your-repo/actions
```

### Step 4: Deploy Application

```bash
# 1. Push application code
git add app/ kubernetes/
git commit -m "Deploy application"
git push origin main

# 2. GitHub Actions automatically:
#    - Runs Workflow 2 (Application)
#    - Builds Docker images
#    - Pushes to ECR
#    - Deploys to EKS (5-10 minutes)

# 3. Access application
kubectl get services -n sensor-backend
```

### Step 5: Daily Development

```bash
# Make code changes
vim app/main.py

# Commit and push
git add app/main.py
git commit -m "Update API endpoint"
git push

# GitHub Actions automatically:
# - Workflow 1: SKIPS (no terraform changes)
# - Workflow 2: RUNS (app changed)
# - Deploys new version to EKS
```

## How Path-Based Triggers Work

### Workflow 1: Infrastructure

```yaml
on:
  push:
    paths:
      - 'terraform/**'  # Only these files
```

**Triggers when:**
- ✅ `terraform/eks.tf` changes
- ✅ `terraform/variables.tf` changes
- ❌ `app/main.py` changes (skips)
- ❌ `kubernetes/services/api-gateway.yaml` changes (skips)

### Workflow 2: Application

```yaml
on:
  push:
    paths:
      - 'app/**'
      - 'services/**'
      - 'kubernetes/**'
      - 'Dockerfile*'
```

**Triggers when:**
- ✅ `app/main.py` changes
- ✅ `kubernetes/services/api-gateway.yaml` changes
- ✅ `Dockerfile.api-gateway` changes
- ❌ `terraform/eks.tf` changes (skips)

## Manual Triggers

### Manually Run Infrastructure

```bash
# Go to GitHub → Actions → "1. Provision Infrastructure"
# Click "Run workflow"
# Select action: plan/apply/destroy
```

### Manually Run Application Deployment

```bash
# Go to GitHub → Actions → "2. Deploy Application"
# Click "Run workflow"
```

## How Terraform and Kubernetes Work Together

### Phase 1: Terraform Creates Infrastructure

```hcl
# terraform/eks-cluster.tf
resource "aws_eks_cluster" "main" {
  name = "sensor-backend-cluster"
  # ... configuration
}
```

**What Terraform does:**
1. Calls AWS API
2. Creates VPC, subnets, security groups
3. Creates EKS control plane
4. Creates worker nodes (EC2 instances)
5. Outputs cluster endpoint and credentials

**Result:** Empty Kubernetes cluster (no applications yet)

### Phase 2: kubectl Deploys Applications

```yaml
# kubernetes/services/api-gateway.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
```

**What kubectl does:**
1. Connects to EKS cluster (using credentials from Terraform)
2. Sends YAML manifests to Kubernetes API
3. Kubernetes schedules pods on worker nodes
4. Applications start running

**Result:** Applications running on EKS cluster

### The Connection

```bash
# After Terraform creates EKS
terraform apply  # Creates cluster

# Get credentials
aws eks update-kubeconfig --name sensor-backend-cluster

# This creates ~/.kube/config with:
# - Cluster endpoint (from Terraform output)
# - Authentication token
# - Certificate

# Now kubectl can talk to EKS
kubectl apply -f kubernetes/
```

## Terraform State Management

### Why S3 Backend?

```hcl
terraform {
  backend "s3" {
    bucket = "sensor-backend-terraform-state"
    key    = "eks/terraform.tfstate"
    region = "us-east-1"
  }
}
```

**Benefits:**
1. **Shared State**: Multiple people can run Terraform
2. **Locking**: DynamoDB prevents concurrent runs
3. **Versioning**: Can rollback if needed
4. **Secure**: State contains sensitive data

### State Locking

```
Developer A runs: terraform apply
    ↓
DynamoDB creates lock
    ↓
Developer B runs: terraform apply
    ↓
Gets error: "State is locked"
    ↓
Developer A finishes
    ↓
Lock released
    ↓
Developer B can now run
```

## Troubleshooting

### Issue: Infrastructure workflow runs on every push

**Problem:** No `paths:` filter

**Solution:**
```yaml
on:
  push:
    paths:
      - 'terraform/**'  # Add this!
```

### Issue: kubectl can't connect to cluster

**Problem:** kubeconfig not updated

**Solution:**
```bash
aws eks update-kubeconfig --name sensor-backend-cluster --region us-east-1
kubectl get nodes
```

### Issue: Docker images not found

**Problem:** ECR repository doesn't exist

**Solution:**
```bash
# Terraform creates ECR repositories
terraform apply

# Or create manually
aws ecr create-repository --repository-name sensor-backend-api-gateway
```

### Issue: Pods stuck in Pending

**Problem:** Not enough nodes

**Solution:**
```bash
# Check nodes
kubectl get nodes

# Scale node group
aws eks update-nodegroup-config \
  --cluster-name sensor-backend-cluster \
  --nodegroup-name sensor-backend-nodes \
  --scaling-config desiredSize=4
```

## Cost Optimization

### Development Environment

```hcl
# terraform/eks-cluster.tf
variable "desired_nodes" {
  default = 2  # Minimum for HA
}

variable "node_instance_type" {
  default = "t3.small"  # Cheaper
}
```

### Production Environment

```hcl
variable "desired_nodes" {
  default = 4  # More capacity
}

variable "node_instance_type" {
  default = "t3.medium"  # Better performance
}
```

### Destroy When Not Needed

```bash
# Manually trigger destroy
# GitHub Actions → "1. Provision Infrastructure" → Run workflow → destroy

# Or locally
cd terraform
terraform destroy
```

## Best Practices

### 1. Separate Environments

```
terraform/
├── environments/
│   ├── dev/
│   │   └── terraform.tfvars
│   ├── staging/
│   │   └── terraform.tfvars
│   └── prod/
│       └── terraform.tfvars
```

### 2. Use Terraform Modules

```hcl
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  # ... configuration
}
```

### 3. Tag Everything

```hcl
tags = {
  Environment = "production"
  Project     = "sensor-backend"
  ManagedBy   = "terraform"
}
```

### 4. Enable Monitoring

```yaml
# kubernetes/monitoring/prometheus.yaml
# Deploy Prometheus for metrics
```

### 5. Use Secrets Manager

```hcl
resource "aws_secretsmanager_secret" "db_password" {
  name = "sensor-backend-db-password"
}
```

## Summary

### Two Workflows:

**Workflow 1: Infrastructure (Rare)**
- Runs when: `terraform/` changes
- Creates: EKS cluster, VPC, ECR
- Time: 15-20 minutes
- Frequency: Once, or when scaling

**Workflow 2: Application (Frequent)**
- Runs when: `app/`, `kubernetes/` changes
- Deploys: Docker images to EKS
- Time: 5-10 minutes
- Frequency: Every code change

### The Flow:

```
1. Terraform creates EKS cluster (.tf files)
   ↓
2. aws eks update-kubeconfig (connects kubectl)
   ↓
3. kubectl applies manifests (.yaml files)
   ↓
4. Applications run on EKS
   ↓
5. Future changes only trigger step 3
```

This is production-ready CI/CD used by companies like Airbnb, Spotify, and Uber!

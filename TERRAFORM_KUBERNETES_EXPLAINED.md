# Terraform + Kubernetes + GitHub Actions: Complete Explanation

## Your Questions Answered

### Q1: How does Terraform (.tf) talk to Kubernetes (.yaml)?

**Answer:** Terraform creates the EKS cluster, then you use `kubectl` to deploy Kubernetes manifests.

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Terraform Creates Infrastructure                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  terraform/eks.tf (Terraform format)                        │
│  ↓                                                          │
│  Terraform calls AWS API                                    │
│  ↓                                                          │
│  AWS creates EKS cluster                                    │
│  ↓                                                          │
│  EKS cluster is ready (empty, no apps yet)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 2: kubectl Deploys Applications                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  kubernetes/*.yaml (Kubernetes format)                      │
│  ↓                                                          │
│  kubectl apply -f kubernetes/                               │
│  ↓                                                          │
│  Kubernetes API deploys pods to EKS cluster                 │
│  ↓                                                          │
│  Applications running on EKS                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Point:** Terraform and Kubernetes are separate steps!
- **Terraform**: Creates the cluster (infrastructure)
- **kubectl**: Deploys apps to the cluster (applications)

### Q2: Why does GitHub Actions run infrastructure every time?

**Answer:** Because your workflow is configured to run on every push. You need to separate infrastructure and application deployments.

## The Problem

Your current workflow probably looks like this:

```yaml
# BAD: Runs infrastructure on every code change
on:
  push:
    branches: [main]

jobs:
  deploy:
    - terraform apply  # Creates infrastructure every time
    - kubectl apply    # Deploys apps
```

**Problem:** Every code change triggers infrastructure creation (expensive and slow!)

## The Solution: Separate Workflows

### Workflow 1: Infrastructure (Run Once)
Only runs when infrastructure files change or manually triggered.

### Workflow 2: Application (Run Often)
Runs on every code change, only deploys apps.

---

## Complete CI/CD Setup

### Architecture

```
GitHub Repository
├── terraform/           ← Infrastructure code (.tf files)
│   ├── eks.tf
│   ├── vpc.tf
│   └── rds.tf
│
├── kubernetes/          ← Application manifests (.yaml files)
│   ├── services/
│   └── infrastructure/
│
└── .github/workflows/
    ├── 1-infrastructure.yml    ← Run once/rarely
    └── 2-deploy-app.yml        ← Run on every code change
```

### Flow

```
Developer pushes code
        ↓
GitHub Actions checks what changed
        ↓
    ┌───────────────────────────┐
    │ Did terraform/ change?    │
    └───────────────────────────┘
         ↓ Yes          ↓ No
         ↓              ↓
    Run infrastructure  Skip infrastructure
    workflow            ↓
         ↓              ↓
         └──────────────┘
                ↓
         Run application
         deployment workflow
                ↓
         Deploy to EKS
```

---

## Implementation

### Step 1: Infrastructure Workflow (Run Once)

```yaml
# .github/workflows/1-infrastructure.yml
name: 1. Provision Infrastructure

on:
  # Only run when infrastructure files change
  push:
    branches: [main]
    paths:
      - 'terraform/**'
      - '.github/workflows/1-infrastructure.yml'
  
  # Or run manually
  workflow_dispatch:
    inputs:
      action:
        description: 'Terraform action'
        required: true
        default: 'plan'
        type: choice
        options:
          - plan
          - apply
          - destroy

jobs:
  terraform:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS Credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    
    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
    
    - name: Terraform Init
      working-directory: terraform
      run: terraform init
    
    - name: Terraform Plan
      working-directory: terraform
      run: terraform plan -out=tfplan
    
    - name: Terraform Apply
      if: github.event.inputs.action == 'apply' || github.event_name == 'push'
      working-directory: terraform
      run: terraform apply -auto-approve tfplan
    
    - name: Save Cluster Info
      run: |
        aws eks update-kubeconfig --name sensor-backend-cluster --region us-east-1
        echo "EKS cluster configured"
```

### Step 2: Application Deployment Workflow (Run Often)

```yaml
# .github/workflows/2-deploy-app.yml
name: 2. Deploy Application

on:
  push:
    branches: [main]
    paths:
      - 'app/**'
      - 'services/**'
      - 'kubernetes/**'
      - 'Dockerfile*'
      - '.github/workflows/2-deploy-app.yml'
  
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS Credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build and Push Docker Images
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        # Build API Gateway
        docker build -f Dockerfile.api-gateway -t $ECR_REGISTRY/api-gateway:$IMAGE_TAG .
        docker push $ECR_REGISTRY/api-gateway:$IMAGE_TAG
        
        # Build Sensor Service
        docker build -f Dockerfile.sensor-service -t $ECR_REGISTRY/sensor-service:$IMAGE_TAG .
        docker push $ECR_REGISTRY/sensor-service:$IMAGE_TAG
    
    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --name sensor-backend-cluster --region us-east-1
    
    - name: Deploy to Kubernetes
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        # Update image tags in Kubernetes manifests
        sed -i "s|your-registry|$ECR_REGISTRY|g" kubernetes/services/*.yaml
        sed -i "s|latest|$IMAGE_TAG|g" kubernetes/services/*.yaml
        
        # Apply Kubernetes manifests
        kubectl apply -f kubernetes/namespace.yaml
        kubectl apply -f kubernetes/secrets/
        kubectl apply -f kubernetes/configmaps/
        kubectl apply -f kubernetes/services/
        
        # Wait for rollout
        kubectl rollout status deployment/api-gateway -n sensor-backend
        kubectl rollout status deployment/sensor-service -n sensor-backend
```

---

## How Terraform Creates EKS and Connects to Kubernetes

### Terraform EKS Module

```hcl
# terraform/eks.tf
resource "aws_eks_cluster" "main" {
  name     = "sensor-backend-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.28"

  vpc_config {
    subnet_ids = aws_subnet.private[*].id
  }
}

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "sensor-backend-nodes"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = aws_subnet.private[*].id

  scaling_config {
    desired_size = 4
    max_size     = 10
    min_size     = 2
  }

  instance_types = ["t3.medium"]
}

# Output kubeconfig
output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --name ${aws_eks_cluster.main.name} --region us-east-1"
}
```

### After Terraform Creates EKS

```bash
# Terraform creates the cluster
terraform apply

# Get kubeconfig (connects kubectl to EKS)
aws eks update-kubeconfig --name sensor-backend-cluster --region us-east-1

# Now kubectl can deploy to EKS
kubectl apply -f kubernetes/
```

**What happens:**
1. Terraform calls AWS API to create EKS cluster
2. AWS creates the cluster (takes 10-15 minutes)
3. `aws eks update-kubeconfig` downloads cluster credentials
4. `kubectl` uses these credentials to deploy apps

---

## Path-Based Triggers Explained

### How `paths:` Works

```yaml
on:
  push:
    paths:
      - 'terraform/**'  # Only run if files in terraform/ change
```

**Example:**

```
Scenario 1: Change app/main.py
├── terraform/ (no changes)
└── app/main.py (changed)
Result: Infrastructure workflow SKIPS, Application workflow RUNS

Scenario 2: Change terraform/eks.tf
├── terraform/eks.tf (changed)
└── app/ (no changes)
Result: Infrastructure workflow RUNS, Application workflow SKIPS

Scenario 3: Change both
├── terraform/eks.tf (changed)
└── app/main.py (changed)
Result: BOTH workflows RUN
```

---

## Best Practices

### 1. Manual Approval for Infrastructure

```yaml
# .github/workflows/1-infrastructure.yml
jobs:
  terraform-plan:
    runs-on: ubuntu-latest
    steps:
      - run: terraform plan
  
  approve:
    needs: terraform-plan
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    steps:
      - run: echo "Approved"
  
  terraform-apply:
    needs: approve
    runs-on: ubuntu-latest
    steps:
      - run: terraform apply
```

### 2. Separate Environments

```yaml
# .github/workflows/deploy-staging.yml
on:
  push:
    branches: [develop]

# .github/workflows/deploy-production.yml
on:
  push:
    branches: [main]
```

### 3. Terraform State in S3

```hcl
# terraform/backend.tf
terraform {
  backend "s3" {
    bucket = "sensor-backend-terraform-state"
    key    = "eks/terraform.tfstate"
    region = "us-east-1"
    
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

**Why:** Prevents multiple people from running Terraform at the same time.

---

## Complete Deployment Flow

### First Time Setup (Run Once)

```bash
# 1. Create infrastructure
git push  # Triggers infrastructure workflow
# Wait 15 minutes for EKS cluster

# 2. Verify cluster
aws eks update-kubeconfig --name sensor-backend-cluster
kubectl get nodes

# 3. Deploy applications
git push  # Triggers application workflow
```

### Daily Development (Run Often)

```bash
# 1. Make code changes
vim app/main.py

# 2. Commit and push
git add app/main.py
git commit -m "Update API"
git push

# 3. GitHub Actions automatically:
#    - Builds Docker image
#    - Pushes to ECR
#    - Deploys to EKS
#    - Infrastructure workflow SKIPS (no terraform changes)
```

---

## Summary

### Q: How does Terraform (.tf) talk to Kubernetes (.yaml)?
**A:** It doesn't directly. Terraform creates the EKS cluster, then `kubectl` deploys Kubernetes manifests to that cluster.

### Q: Why does infrastructure run every time?
**A:** Because your workflow doesn't use `paths:` to filter. Use path-based triggers to only run infrastructure when terraform files change.

### Q: How to run infrastructure once, then just deploy code?
**A:** Use two separate workflows:
1. Infrastructure workflow with `paths: ['terraform/**']`
2. Application workflow with `paths: ['app/**', 'kubernetes/**']`

### The Flow:
```
1. Terraform creates EKS cluster (once)
   ↓
2. aws eks update-kubeconfig (connects kubectl to EKS)
   ↓
3. kubectl apply -f kubernetes/ (deploys apps)
   ↓
4. Future code changes only trigger step 3
```

This is the industry-standard approach used by companies like Netflix, Airbnb, and Uber!

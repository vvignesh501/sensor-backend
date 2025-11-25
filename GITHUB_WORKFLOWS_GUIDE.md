# GitHub Workflows Guide

## Available Workflows

### 1. Deploy Lambda Only (Recommended)
**File**: `.github/workflows/deploy-lambda-only.yml`

**Purpose**: Deploy only Lambda function code updates without touching infrastructure.

**Triggers**:
- Push to `main` branch
- Manual trigger via GitHub Actions UI

**What it does**:
1. Creates Lambda deployment package
2. Checks if Lambda function exists
3. Updates Lambda function code
4. Waits for update to complete

**When to use**: 
- Regular code deployments
- Lambda function updates
- No infrastructure changes needed

**How to run manually**:
1. Go to GitHub Actions tab
2. Select "Deploy Lambda Only"
3. Click "Run workflow"
4. Select branch (main)
5. Click "Run workflow"

---

### 2. Fix Terraform State (One-time)
**File**: `.github/workflows/fix-terraform-state.yml`

**Purpose**: Clean up stuck Terraform state (subnets, Redshift resources).

**Triggers**:
- Manual only (workflow_dispatch)

**What it does**:
1. Removes stuck subnet resources from Terraform state
2. Removes Redshift resources from state
3. Verifies cleanup
4. Runs terraform plan to check

**When to use**:
- When Terraform destroy hangs on subnet deletion
- When you see "DependencyViolation" errors
- One-time cleanup after removing Redshift

**How to run**:
1. Go to GitHub Actions tab
2. Select "Fix Terraform State (Manual)"
3. Click "Run workflow"
4. Type "fix" in the confirmation field
5. Click "Run workflow"

**⚠️ Warning**: This modifies Terraform state. Only run if you understand the implications.

---

### 3. Deploy (Full Pipeline)
**File**: `.github/workflows/deploy.yml`

**Purpose**: Full CI/CD pipeline with tests and deployments.

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main`
- Manual trigger

**Jobs**:
1. **Test**: Run pytest with coverage
2. **Build & Push**: Build Docker image, push to ECR
3. **Deploy Lambda**: Update Lambda function code
4. **Notify**: Send deployment status

**When to use**:
- Full application deployments
- When you need Docker images built
- Automated deployments on merge

---

### 4. Setup Backend (One-time)
**File**: `.github/workflows/setup-backend.yml`

**Purpose**: Initial setup of Terraform backend (S3 + DynamoDB).

**Triggers**:
- Manual only

**What it does**:
1. Creates S3 bucket for Terraform state
2. Creates DynamoDB table for state locking
3. Configures backend

**When to use**:
- First-time setup
- New AWS account
- Recreating infrastructure

---

## Workflow Execution Order

### First Time Setup
```
1. setup-backend.yml (manual)
   ↓
2. Create Lambda function manually or via Terraform locally
   ↓
3. deploy-lambda-only.yml (automatic on push)
```

### Regular Deployments
```
Push to main
   ↓
deploy-lambda-only.yml (automatic)
   ↓
Lambda code updated ✅
```

### When Terraform State is Stuck
```
1. fix-terraform-state.yml (manual, type "fix")
   ↓
2. Verify state is clean
   ↓
3. Continue with regular deployments
```

---

## Common Scenarios

### Scenario 1: Deploy Lambda Code Changes
**Problem**: You updated Lambda function code and want to deploy.

**Solution**:
```bash
# Option A: Push to main (automatic)
git add lambda/lambda_data_processor.py
git commit -m "Update Lambda function"
git push origin main

# Option B: Manual trigger
# Go to Actions → Deploy Lambda Only → Run workflow
```

### Scenario 2: Terraform Destroy Hangs on Subnet
**Problem**: Terraform destroy stuck for 20+ minutes on subnet deletion.

**Solution**:
```bash
# Option A: Use GitHub Actions
# Go to Actions → Fix Terraform State → Run workflow → Type "fix"

# Option B: Run locally
cd sensor-backend/terraform
./fix_terraform_state.sh
```

### Scenario 3: Lambda Function Doesn't Exist
**Problem**: Workflow fails with "Lambda function does not exist".

**Solution**:
```bash
# Create Lambda function first using Terraform
cd sensor-backend/terraform

# Create Lambda deployment package
cd ..
mkdir -p lambda_package
pip install -r lambda/requirements.txt -t lambda_package/
cp lambda/lambda_data_processor.py lambda_package/
cd lambda_package && zip -r ../terraform/sensor_data_processor.zip . && cd ..

# Apply only Lambda resource
cd terraform
terraform init
terraform apply -target=aws_lambda_function.data_processor

# Now workflow will work
```

### Scenario 4: Need to Update Infrastructure
**Problem**: Need to change Terraform infrastructure (not just Lambda code).

**Solution**:
```bash
# Run Terraform locally (not in workflow)
cd sensor-backend/terraform

# Make your changes to main.tf
vim main.tf

# Plan and apply
terraform plan
terraform apply

# Then deploy Lambda code via workflow
git push origin main
```

---

## Workflow Configuration

### Required GitHub Secrets

Go to: Repository → Settings → Secrets and variables → Actions

Add these secrets:
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

### Environment Variables

Edit in workflow files:
```yaml
env:
  AWS_REGION: us-east-2          # Change if needed
  PYTHON_VERSION: '3.9'          # Python version
  TERRAFORM_VERSION: 1.6.0       # Terraform version
```

---

## Monitoring Workflows

### View Workflow Runs
1. Go to GitHub repository
2. Click "Actions" tab
3. See all workflow runs

### View Logs
1. Click on a workflow run
2. Click on a job (e.g., "Deploy Lambda Functions")
3. Expand steps to see logs

### Cancel Running Workflow
1. Go to workflow run
2. Click "Cancel workflow" button (top right)

---

## Troubleshooting

### Workflow Fails: "AWS credentials not configured"
**Solution**: Add AWS secrets to GitHub repository settings.

### Workflow Fails: "Lambda function not found"
**Solution**: Create Lambda function first using Terraform locally.

### Workflow Fails: "Terraform state locked"
**Solution**: 
```bash
# Unlock state
cd terraform
terraform force-unlock LOCK_ID
```

### Workflow Hangs: "Destroying subnet..."
**Solution**: Run "Fix Terraform State" workflow or cancel and use the fix script.

### Workflow Fails: "ZIP file not found"
**Solution**: This is now fixed in the new workflows. The ZIP is created before use.

---

## Best Practices

### 1. Separate Infrastructure from Code Deployments
- ✅ Use workflows for Lambda code updates
- ✅ Use local Terraform for infrastructure changes
- ❌ Don't run `terraform apply` in workflows (too slow)

### 2. Use Manual Triggers for Risky Operations
- ✅ State cleanup requires manual confirmation
- ✅ Infrastructure changes done locally
- ❌ Don't auto-deploy infrastructure changes

### 3. Monitor Workflow Execution
- ✅ Check logs after each deployment
- ✅ Set up notifications for failures
- ✅ Review changes before merging

### 4. Keep Workflows Simple
- ✅ One workflow = one purpose
- ✅ Fast feedback (< 5 minutes)
- ❌ Don't combine too many steps

---

## Workflow Comparison

| Workflow | Speed | Risk | Use Case |
|----------|-------|------|----------|
| **deploy-lambda-only** | ⚡ Fast (2 min) | 🟢 Low | Regular deployments |
| **fix-terraform-state** | ⚡ Fast (1 min) | 🟡 Medium | One-time cleanup |
| **deploy** | 🐌 Slow (10 min) | 🟡 Medium | Full pipeline |
| **setup-backend** | ⚡ Fast (2 min) | 🟢 Low | Initial setup |

---

## Quick Reference

### Deploy Lambda Code
```bash
git push origin main
# Automatic deployment via deploy-lambda-only.yml
```

### Fix Stuck Terraform State
```bash
# GitHub Actions → Fix Terraform State → Type "fix"
```

### Create Lambda Function (First Time)
```bash
cd sensor-backend/terraform
terraform init
terraform apply -target=aws_lambda_function.data_processor
```

### Update Infrastructure
```bash
cd sensor-backend/terraform
terraform plan
terraform apply
# Then push code: git push origin main
```

### View Deployment Status
```bash
# GitHub → Actions → Latest workflow run
```

---

## Summary

**For regular deployments**: Just push to main, `deploy-lambda-only.yml` handles it.

**For stuck Terraform**: Run `fix-terraform-state.yml` workflow manually.

**For infrastructure changes**: Use Terraform locally, not in workflows.

Your workflows are now optimized for fast, reliable deployments! 🚀

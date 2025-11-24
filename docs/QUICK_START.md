# Quick Start Guide

Get the Sensor Backend deployed to AWS in 5 minutes.

## Prerequisites

- AWS Account
- GitHub Account
- Git installed

## 1. Fork/Clone Repository

```bash
git clone <your-repo-url>
cd sensor-backend
```

## 2. Add GitHub Secrets

Go to: **Settings → Secrets and variables → Actions → New repository secret**

Add:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## 3. Setup Terraform Backend

Go to: **Actions → Setup Terraform Backend (One-time) → Run workflow**

## 4. Deploy Everything

```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

GitHub Actions will automatically deploy everything!

## 5. Access Your Application

After deployment completes (~10 minutes):

```bash
# Get the URL from Terraform outputs
cd terraform
terraform output alb_url
```

Visit: `http://<alb-url>/`

## What Gets Deployed?

✅ **Docker Image** → Amazon ECR  
✅ **FastAPI App** → ECS Fargate (2-10 auto-scaling tasks)  
✅ **Load Balancer** → Application Load Balancer  
✅ **Storage** → S3 buckets (source + processed data)  
✅ **Processing** → Lambda function (triggered by S3)  
✅ **Database** → DynamoDB (metadata)  
✅ **Data Warehouse** → Redshift (optional)  
✅ **Monitoring** → CloudWatch Dashboard  
✅ **Alerts** → SNS Topic  

## Test the API

```bash
# Health check
curl http://<alb-url>/health

# Login (creates test user automatically)
curl -X POST http://<alb-url>/auth/token \
  -d "username=admin&password=admin123"

# Run sensor test (requires token)
curl -X POST http://<alb-url>/test/sensor/CZT \
  -H "Authorization: Bearer <token>"
```

## View Logs

```bash
# ECS logs
aws logs tail /ecs/sensor-backend --follow

# Lambda logs
aws logs tail /aws/lambda/sensor-data-processor --follow
```

## Manual Deployment Options

Go to: **Actions → Deploy Sensor Backend → Run workflow**

Choose what to deploy:
- ☑️ Deploy infrastructure (Terraform)
- ☑️ Deploy Lambda functions
- ☑️ Deploy ECS service

## Cost Estimate

**With Redshift**: ~$200/month  
**Without Redshift**: ~$20/month

To disable Redshift:
```bash
cd terraform
terraform apply -var="enable_redshift=false"
```

## Troubleshooting

**Deployment failed?**
- Check GitHub Actions logs
- Verify AWS credentials
- Ensure Terraform backend is setup

**Can't access application?**
- Wait 2-3 minutes for ECS tasks to start
- Check security groups allow port 80
- Verify ALB health checks are passing

**Need help?**
- See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed guide
- Check CloudWatch logs
- Review Terraform outputs

## Next Steps

1. Configure custom domain
2. Enable HTTPS
3. Set up monitoring alerts
4. Review security settings
5. Configure backup policies

See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup.

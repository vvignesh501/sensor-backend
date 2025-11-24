# Deployment Checklist

Use this checklist to ensure a smooth deployment to AWS.

## Pre-Deployment

### AWS Setup
- [ ] AWS account created
- [ ] IAM user created for GitHub Actions
- [ ] IAM user has AdministratorAccess policy (or custom policy)
- [ ] Access key generated for IAM user
- [ ] AWS CLI installed and configured locally

### GitHub Setup
- [ ] Repository created/forked
- [ ] Code pushed to repository
- [ ] GitHub Secrets configured:
  - [ ] `AWS_ACCESS_KEY_ID`
  - [ ] `AWS_SECRET_ACCESS_KEY`
- [ ] Actions enabled in repository settings

### Code Review
- [ ] Review `terraform/variables.tf` for configuration
- [ ] Update `alert_email` in variables
- [ ] Set `enable_redshift` based on needs
- [ ] Review `Dockerfile` for any customizations
- [ ] Update README badge with your repo URL

## Initial Deployment

### Step 1: Setup Terraform Backend
- [ ] Go to Actions tab in GitHub
- [ ] Select "Setup Terraform Backend (One-time)"
- [ ] Click "Run workflow"
- [ ] Wait for completion (~2 minutes)
- [ ] Verify S3 bucket created: `sensor-backend-terraform-state`
- [ ] Verify DynamoDB table created: `terraform-state-lock`

### Step 2: Deploy Infrastructure
- [ ] Push code to `main` branch
- [ ] Go to Actions tab
- [ ] Monitor "Deploy Sensor Backend" workflow
- [ ] Wait for all jobs to complete (~25 minutes)
- [ ] Check for any errors in logs

### Step 3: Verify Deployment
- [ ] Check Terraform outputs:
  ```bash
  cd sensor-backend/terraform
  terraform output
  ```
- [ ] Note the `alb_url` output
- [ ] Test health endpoint:
  ```bash
  curl http://<alb-url>/health
  ```
- [ ] Verify ECS service running:
  ```bash
  aws ecs describe-services \
    --cluster sensor-backend-cluster \
    --services sensor-backend-service
  ```
- [ ] Check ECS tasks are healthy (2 running)
- [ ] Verify Lambda function exists:
  ```bash
  aws lambda get-function --function-name sensor-data-processor
  ```
- [ ] Check S3 buckets created:
  ```bash
  aws s3 ls | grep sensor
  ```

## Post-Deployment

### Testing
- [ ] Test API health endpoint
- [ ] Test authentication:
  ```bash
  curl -X POST http://<alb-url>/auth/token \
    -d "username=admin&password=admin123"
  ```
- [ ] Test sensor endpoint (with token)
- [ ] Upload test file to S3 to trigger Lambda
- [ ] Check Lambda execution in CloudWatch logs
- [ ] Verify data in DynamoDB table

### Monitoring Setup
- [ ] Access CloudWatch Dashboard
- [ ] Verify metrics are populating
- [ ] Set up CloudWatch alarms:
  - [ ] ECS CPU > 80%
  - [ ] ECS Memory > 80%
  - [ ] Lambda errors > 5
  - [ ] ALB 5xx errors > 10
- [ ] Confirm SNS email subscription
- [ ] Test alert by triggering anomaly

### Security Review
- [ ] Verify S3 buckets are not public
- [ ] Check security groups are restrictive
- [ ] Verify IAM roles follow least privilege
- [ ] Enable AWS CloudTrail for audit logs
- [ ] Enable AWS Config for compliance
- [ ] Review VPC flow logs

### Documentation
- [ ] Document ALB URL
- [ ] Document Redshift endpoint (if enabled)
- [ ] Document S3 bucket names
- [ ] Update team wiki/docs
- [ ] Share access credentials securely

## Production Readiness

### Performance
- [ ] Load test the API
- [ ] Verify auto-scaling works
- [ ] Test Lambda concurrency limits
- [ ] Check database connection pooling
- [ ] Monitor response times

### High Availability
- [ ] Verify ECS tasks in multiple AZs
- [ ] Test ALB health checks
- [ ] Verify RDS Multi-AZ (if using RDS)
- [ ] Test failover scenarios
- [ ] Document recovery procedures

### Backup & Recovery
- [ ] Enable automated backups for Redshift
- [ ] Set up S3 versioning (already enabled)
- [ ] Test restore procedures
- [ ] Document backup retention policies
- [ ] Create disaster recovery plan

### Cost Management
- [ ] Review AWS Cost Explorer
- [ ] Set up billing alerts
- [ ] Tag all resources appropriately
- [ ] Review Redshift usage (expensive!)
- [ ] Consider Reserved Instances for savings

### Compliance
- [ ] Enable encryption at rest (already enabled)
- [ ] Enable encryption in transit
- [ ] Review data retention policies
- [ ] Document data flow
- [ ] Ensure GDPR/compliance requirements met

## Optional Enhancements

### Domain & SSL
- [ ] Register domain name
- [ ] Create Route53 hosted zone
- [ ] Request ACM certificate
- [ ] Update ALB listener for HTTPS
- [ ] Redirect HTTP to HTTPS

### Advanced Monitoring
- [ ] Set up AWS X-Ray for tracing
- [ ] Configure detailed CloudWatch metrics
- [ ] Set up log aggregation (ELK/Splunk)
- [ ] Create custom dashboards
- [ ] Set up PagerDuty/Opsgenie integration

### CI/CD Enhancements
- [ ] Add integration tests to pipeline
- [ ] Set up staging environment
- [ ] Implement blue-green deployments
- [ ] Add manual approval gates
- [ ] Set up automated rollback

### Database
- [ ] Replace PostgreSQL with RDS
- [ ] Set up read replicas
- [ ] Configure automated backups
- [ ] Set up connection pooling
- [ ] Implement database migrations

### Kafka (if needed)
- [ ] Set up Amazon MSK
- [ ] Configure Kafka topics
- [ ] Deploy Kafka consumers
- [ ] Set up monitoring
- [ ] Test message processing

## Maintenance

### Regular Tasks
- [ ] Review CloudWatch logs weekly
- [ ] Check AWS costs monthly
- [ ] Update dependencies monthly
- [ ] Rotate AWS credentials quarterly
- [ ] Review security groups quarterly
- [ ] Test backup restore quarterly
- [ ] Review and update documentation

### Updates
- [ ] Monitor for security patches
- [ ] Update Docker base images
- [ ] Update Python dependencies
- [ ] Update Terraform providers
- [ ] Update Lambda runtime
- [ ] Update ECS task definitions

## Troubleshooting

### Common Issues

#### ECS Tasks Not Starting
- [ ] Check CloudWatch logs: `/ecs/sensor-backend`
- [ ] Verify Docker image exists in ECR
- [ ] Check security groups allow traffic
- [ ] Verify IAM task role permissions
- [ ] Check resource limits (CPU/memory)

#### Lambda Errors
- [ ] Check CloudWatch logs: `/aws/lambda/sensor-data-processor`
- [ ] Verify S3 trigger configuration
- [ ] Check Lambda timeout settings
- [ ] Verify IAM role permissions
- [ ] Test with sample S3 event

#### Terraform Errors
- [ ] Check state lock in DynamoDB
- [ ] Verify AWS credentials
- [ ] Check resource quotas
- [ ] Review error messages carefully
- [ ] Try `terraform refresh`

#### High Costs
- [ ] Check Redshift usage (most expensive)
- [ ] Review ECS task count
- [ ] Check S3 storage size
- [ ] Review Lambda invocations
- [ ] Check data transfer costs

## Rollback Plan

### If Deployment Fails
1. [ ] Check GitHub Actions logs
2. [ ] Identify failing stage
3. [ ] Fix issue in code
4. [ ] Push fix to main branch
5. [ ] Monitor new deployment

### If Application Has Issues
1. [ ] Check CloudWatch logs
2. [ ] Identify root cause
3. [ ] Decide: fix forward or rollback
4. [ ] If rollback needed:
   - [ ] Revert git commit
   - [ ] Push to main
   - [ ] Wait for deployment
5. [ ] Verify application working

### If Infrastructure Has Issues
1. [ ] Check Terraform state
2. [ ] Identify problematic resources
3. [ ] Decide: fix or destroy
4. [ ] If destroying:
   ```bash
   cd terraform
   terraform destroy
   ```
5. [ ] Redeploy from scratch

## Sign-Off

### Development Team
- [ ] Code reviewed and approved
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Deployment tested in staging

### Operations Team
- [ ] Infrastructure reviewed
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Runbooks created

### Security Team
- [ ] Security review completed
- [ ] Vulnerabilities addressed
- [ ] Compliance requirements met
- [ ] Access controls verified

### Management
- [ ] Budget approved
- [ ] Timeline agreed
- [ ] Stakeholders notified
- [ ] Go-live approved

---

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Approved By:** _______________  
**Notes:** _______________

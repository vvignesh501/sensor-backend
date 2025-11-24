# Production AWS S3 Setup Guide

## 1. AWS Account Organization
```
Root Account (billing only)
├── Production Account
├── Staging Account  
└── Development Account
```

## 2. IAM Role-Based Access (No Access Keys!)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::sensor-prod-data/*"
    }
  ]
}
```

## 3. S3 Bucket Configuration
- **Bucket Name**: `sensor-prod-data-{region}-{env}`
- **Versioning**: Enabled
- **Encryption**: AES-256 or KMS
- **Access Logging**: Enabled
- **Cross-Region Replication**: For disaster recovery

## 4. Security Best Practices
- Use IAM Roles (not access keys)
- Enable CloudTrail logging
- Set up bucket policies
- Enable MFA delete
- Use VPC endpoints

## 5. Cost Optimization
- Lifecycle policies (IA → Glacier → Deep Archive)
- Intelligent Tiering
- Request metrics
- Storage class analysis

## 6. Monitoring & Alerts
- CloudWatch metrics
- S3 access logs
- Cost alerts
- Performance monitoring
#!/bin/bash
# COMPLETE CLEANUP - Run this ONCE to delete all existing resources
# Then we can deploy fresh with no conflicts

set -e

REGION="us-east-2"

echo "🧹 COMPLETE AWS CLEANUP - This will delete ALL sensor-backend resources"
echo "Press Ctrl+C within 5 seconds to cancel..."
sleep 5

echo ""
echo "Step 1: Deleting ECS Services..."
aws ecs update-service --cluster sensor-app-cluster --service sensor-app-service --desired-count 0 --region $REGION 2>/dev/null || true
sleep 15
aws ecs delete-service --cluster sensor-app-cluster --service sensor-app-service --force --region $REGION 2>/dev/null || true
aws ecs delete-service --cluster sensor-cluster-clean --service sensor-service-clean --force --region $REGION 2>/dev/null || true
echo "✓ ECS services deleted"

echo ""
echo "Step 2: Waiting for services to terminate..."
sleep 30

echo ""
echo "Step 3: Deleting ECS Clusters..."
aws ecs delete-cluster --cluster sensor-app-cluster --region $REGION 2>/dev/null || true
aws ecs delete-cluster --cluster sensor-cluster-clean --region $REGION 2>/dev/null || true
echo "✓ ECS clusters deleted"

echo ""
echo "Step 4: Deleting RDS Instances..."
aws rds delete-db-instance --db-instance-identifier sensor-postgres --skip-final-snapshot --region $REGION 2>/dev/null || true
aws rds delete-db-instance --db-instance-identifier sensor-postgres-v2 --skip-final-snapshot --region $REGION 2>/dev/null || true
aws rds delete-db-instance --db-instance-identifier sensor-postgres-high-perf --skip-final-snapshot --region $REGION 2>/dev/null || true
echo "✓ RDS deletion initiated (takes 5-10 minutes)"

echo ""
echo "Step 5: Deleting Load Balancers..."
for alb in $(aws elbv2 describe-load-balancers --region $REGION --query 'LoadBalancers[?contains(LoadBalancerName, `sensor`)].LoadBalancerArn' --output text); do
  aws elbv2 delete-load-balancer --load-balancer-arn $alb --region $REGION 2>/dev/null || true
done
echo "✓ Load balancers deleted"

echo ""
echo "Step 6: Deleting Target Groups..."
for tg in $(aws elbv2 describe-target-groups --region $REGION --query 'TargetGroups[?contains(TargetGroupName, `sensor`)].TargetGroupArn' --output text); do
  aws elbv2 delete-target-group --target-group-arn $tg --region $REGION 2>/dev/null || true
done
echo "✓ Target groups deleted"

echo ""
echo "Step 7: Waiting for RDS to finish deleting..."
echo "This takes 5-10 minutes. Checking every 30 seconds..."
for i in {1..20}; do
  if aws rds describe-db-instances --region $REGION --query 'DBInstances[?contains(DBInstanceIdentifier, `sensor`)].DBInstanceIdentifier' --output text 2>/dev/null | grep -q sensor; then
    echo "  Still deleting... ($i/20)"
    sleep 30
  else
    echo "  ✓ RDS instances deleted"
    break
  fi
done

echo ""
echo "Step 8: Deleting RDS Subnet Groups..."
aws rds delete-db-subnet-group --db-subnet-group-name sensor-rds-subnet-group --region $REGION 2>/dev/null || true
echo "✓ RDS subnet groups deleted"

echo ""
echo "Step 9: Deleting Security Groups..."
for sg in $(aws ec2 describe-security-groups --region $REGION --filters "Name=group-name,Values=sensor-*" --query 'SecurityGroups[].GroupId' --output text); do
  aws ec2 delete-security-group --group-id $sg --region $REGION 2>/dev/null || true
done
echo "✓ Security groups deleted"

echo ""
echo "Step 10: Deleting Subnets..."
for subnet in $(aws ec2 describe-subnets --region $REGION --filters "Name=tag:Name,Values=*sensor*,*public*" --query 'Subnets[].SubnetId' --output text); do
  aws ec2 delete-subnet --subnet-id $subnet --region $REGION 2>/dev/null || true
done
echo "✓ Subnets deleted"

echo ""
echo "Step 11: Deleting Internet Gateways..."
for vpc in $(aws ec2 describe-vpcs --region $REGION --filters "Name=tag:Name,Values=*sensor*" --query 'Vpcs[].VpcId' --output text); do
  for igw in $(aws ec2 describe-internet-gateways --region $REGION --filters "Name=attachment.vpc-id,Values=$vpc" --query 'InternetGateways[].InternetGatewayId' --output text); do
    aws ec2 detach-internet-gateway --internet-gateway-id $igw --vpc-id $vpc --region $REGION 2>/dev/null || true
    aws ec2 delete-internet-gateway --internet-gateway-id $igw --region $REGION 2>/dev/null || true
  done
done
echo "✓ Internet gateways deleted"

echo ""
echo "Step 12: Deleting VPCs..."
for vpc in $(aws ec2 describe-vpcs --region $REGION --filters "Name=tag:Name,Values=*sensor*" --query 'Vpcs[].VpcId' --output text); do
  aws ec2 delete-vpc --vpc-id $vpc --region $REGION 2>/dev/null || true
done
echo "✓ VPCs deleted"

echo ""
echo "Step 13: Deleting IAM Roles..."
for role in sensor-ecs-execution-clean sensor-ecs-app-execution-role; do
  # Detach policies first
  for policy in $(aws iam list-attached-role-policies --role-name $role --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null); do
    aws iam detach-role-policy --role-name $role --policy-arn $policy 2>/dev/null || true
  done
  aws iam delete-role --role-name $role --region $REGION 2>/dev/null || true
done
echo "✓ IAM roles deleted"

echo ""
echo "Step 14: Cleaning Terraform State..."
aws s3 rm s3://sensor-backend-terraform-state/prod/terraform.tfstate 2>/dev/null || true
aws dynamodb delete-table --table-name terraform-state-lock --region $REGION 2>/dev/null || true
echo "✓ Terraform state cleaned"

echo ""
echo "========================================="
echo "✅ CLEANUP COMPLETE!"
echo "========================================="
echo ""
echo "Now you can deploy fresh:"
echo "1. Go to GitHub Actions"
echo "2. Run 'Deploy to AWS Cloud (ECS + RDS)'"
echo "3. It will deploy with NO conflicts"
echo ""

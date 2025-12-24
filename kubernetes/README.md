# Kubernetes Distributed Microservices Architecture

This directory contains Kubernetes manifests for deploying the sensor backend as a distributed microservices system across multiple servers.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                           │
│                    (Multiple Nodes/Servers)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Node 1 (Server 1)              Node 2 (Server 2)              │
│  ├── API Gateway (3 replicas)   ├── Sensor Service (3 reps)   │
│  ├── Ingress Controller         ├── PostgreSQL (Primary)      │
│  └── Monitoring                  └── Redis Cache              │
│                                                                 │
│  Node 3 (Server 3)              Node 4 (Server 4)              │
│  ├── Auth Service (2 replicas)  ├── Kafka (3 brokers)         │
│  ├── Analytics Service          ├── Zookeeper                 │
│  └── Kafka Consumer             └── Kafka Consumer            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Services

1. **API Gateway** - Entry point, load balancing, routing
2. **Sensor Service** - Sensor CRUD operations
3. **Auth Service** - Authentication and authorization
4. **Analytics Service** - Data processing and analytics
5. **Kafka Consumer Service** - Event processing
6. **PostgreSQL** - Primary database
7. **Redis** - Caching layer
8. **Kafka** - Message queue (3 brokers for HA)

## Quick Start

### Prerequisites
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install minikube (for local testing)
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Or use AWS EKS, GKE, or AKS for production
```

### Deploy to Kubernetes

```bash
# 1. Start local cluster (or use cloud provider)
minikube start --nodes 4 --cpus 2 --memory 4096

# 2. Create namespace
kubectl create namespace sensor-backend

# 3. Deploy infrastructure (databases, kafka)
kubectl apply -f kubernetes/infrastructure/

# 4. Deploy microservices
kubectl apply -f kubernetes/services/

# 5. Deploy ingress
kubectl apply -f kubernetes/ingress/

# 6. Check status
kubectl get pods -n sensor-backend
kubectl get services -n sensor-backend

# 7. Access the application
minikube service api-gateway -n sensor-backend
```

## Deployment Strategy

- **Rolling Updates**: Zero-downtime deployments
- **Health Checks**: Liveness and readiness probes
- **Auto-scaling**: HPA based on CPU/memory
- **Resource Limits**: CPU and memory constraints
- **Service Discovery**: Kubernetes DNS
- **Load Balancing**: Kubernetes Service + Ingress

## Monitoring

```bash
# View logs
kubectl logs -f deployment/api-gateway -n sensor-backend

# View metrics
kubectl top pods -n sensor-backend
kubectl top nodes

# Access dashboard
minikube dashboard
```

## Scaling

```bash
# Manual scaling
kubectl scale deployment api-gateway --replicas=5 -n sensor-backend

# Auto-scaling (HPA)
kubectl autoscale deployment api-gateway --cpu-percent=70 --min=3 --max=10 -n sensor-backend
```

## Production Deployment

For AWS EKS:
```bash
# Create EKS cluster
eksctl create cluster \
  --name sensor-backend \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 4 \
  --nodes-min 2 \
  --nodes-max 8

# Deploy
kubectl apply -f kubernetes/ --recursive
```

## Files Structure

```
kubernetes/
├── README.md
├── namespace.yaml
├── infrastructure/
│   ├── postgres.yaml
│   ├── redis.yaml
│   ├── kafka.yaml
│   └── zookeeper.yaml
├── services/
│   ├── api-gateway.yaml
│   ├── sensor-service.yaml
│   ├── auth-service.yaml
│   ├── analytics-service.yaml
│   └── kafka-consumer.yaml
├── ingress/
│   └── ingress.yaml
├── configmaps/
│   └── app-config.yaml
├── secrets/
│   └── db-secrets.yaml
└── monitoring/
    ├── prometheus.yaml
    └── grafana.yaml
```

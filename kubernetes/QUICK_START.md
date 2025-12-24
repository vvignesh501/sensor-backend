# Kubernetes Quick Start Guide

## Deploy Distributed Microservices in 5 Minutes

### Step 1: Create Namespace
```bash
kubectl apply -f kubernetes/namespace.yaml
```

### Step 2: Create Secrets
```bash
# Edit secrets first!
nano kubernetes/secrets/db-secrets.yaml
kubectl apply -f kubernetes/secrets/
```

### Step 3: Create ConfigMaps
```bash
kubectl apply -f kubernetes/configmaps/
```

### Step 4: Deploy Infrastructure (Databases, Kafka)
```bash
kubectl apply -f kubernetes/infrastructure/
```

### Step 5: Wait for Infrastructure
```bash
kubectl wait --for=condition=ready pod -l app=postgres -n sensor-backend --timeout=300s
kubectl wait --for=condition=ready pod -l app=kafka -n sensor-backend --timeout=300s
```

### Step 6: Deploy Microservices
```bash
kubectl apply -f kubernetes/services/
```

### Step 7: Deploy Ingress
```bash
kubectl apply -f kubernetes/ingress/
```

### Step 8: Check Status
```bash
kubectl get pods -n sensor-backend
kubectl get services -n sensor-backend
```

### Step 9: Access Application
```bash
# Get external IP
kubectl get service api-gateway -n sensor-backend

# Or port-forward for local testing
kubectl port-forward service/api-gateway 8000:80 -n sensor-backend
```

## Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n sensor-backend

# Check logs
kubectl logs -f deployment/api-gateway -n sensor-backend

# Test API
curl http://localhost:8000/health
```

## Scale Services

```bash
# Manual scaling
kubectl scale deployment sensor-service --replicas=5 -n sensor-backend

# Check HPA status
kubectl get hpa -n sensor-backend
```

## Clean Up

```bash
kubectl delete namespace sensor-backend
```

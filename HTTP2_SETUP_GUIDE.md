# HTTP/2 Setup Guide

## Overview

HTTP/2 provides significant performance improvements over HTTP/1.1:
- **Multiplexing**: Multiple requests over a single connection
- **Header Compression**: Reduces overhead
- **Server Push**: Proactive resource delivery
- **Binary Protocol**: More efficient parsing

---

## 1. AWS Application Load Balancer (Production)

### Current Setup
The ALB now has HTTP/2 enabled with these settings:

```hcl
resource "aws_lb" "app_alb" {
  enable_http2 = true
  enable_cross_zone_load_balancing = true
  idle_timeout = 60
}
```

### Important Notes
- **HTTP/2 is enabled by default** on AWS ALB (we made it explicit)
- HTTP/2 works on **both HTTP and HTTPS** listeners on ALB
- For best performance, use HTTPS (HTTP/2 over TLS)

### To Verify HTTP/2 on ALB
```bash
# After deployment, test with curl
curl -I --http2 http://your-alb-url.amazonaws.com

# Or use nghttp (HTTP/2 client)
nghttp -nv http://your-alb-url.amazonaws.com
```

---

## 2. Local Nginx Setup

### Current Configuration
The nginx.conf has been optimized with:
- Gzip compression
- Keep-alive connections
- Connection pooling to backend
- Optimized timeouts

### HTTP/2 Requires HTTPS
HTTP/2 technically works over plain HTTP, but **browsers only support HTTP/2 over HTTPS**.

### Option A: Use HTTP/1.1 with Optimizations (Current)
The current setup uses HTTP/1.1 with performance optimizations:
- Keep-alive connections
- Connection pooling
- Gzip compression

This is sufficient for local development.

### Option B: Enable HTTPS + HTTP/2 (Recommended for Production-like Testing)

#### Step 1: Generate Self-Signed Certificate
```bash
cd sensor-backend

# Create SSL directory
mkdir -p ssl

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/nginx-selfsigned.key \
  -out ssl/nginx-selfsigned.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

#### Step 2: Update docker-compose.loadbalancer.yml
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"  # Add HTTPS port
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - ./ssl:/etc/nginx/ssl:ro  # Mount SSL certificates
  depends_on:
    - app1
    - app2
    - app3
```

#### Step 3: Update nginx.conf
Uncomment the HTTPS section:
```nginx
server {
    listen 80;
    listen 443 ssl http2;  # Enable HTTP/2 on HTTPS
    
    ssl_certificate /etc/nginx/ssl/nginx-selfsigned.crt;
    ssl_certificate_key /etc/nginx/ssl/nginx-selfsigned.key;
    
    # SSL optimization
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # ... rest of config
}
```

#### Step 4: Test HTTP/2
```bash
# Start services
docker-compose -f docker-compose.loadbalancer.yml up -d

# Test HTTP/2 (ignore self-signed cert warning)
curl -I --http2 --insecure https://localhost

# Or use browser DevTools:
# 1. Open https://localhost (accept security warning)
# 2. Open DevTools > Network tab
# 3. Check Protocol column - should show "h2"
```

---

## 3. FastAPI Application (Backend Services)

### Enable HTTP/2 in FastAPI with Hypercorn

FastAPI with Uvicorn doesn't support HTTP/2, but you can use **Hypercorn** instead:

#### Update requirements.txt
```txt
fastapi==0.104.1
hypercorn==0.15.0  # Add this
pydantic==2.5.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
```

#### Update Dockerfile (for each service)
```dockerfile
# Change from uvicorn to hypercorn
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:8000", "--workers", "2"]
```

#### Or use Uvicorn with h11 (HTTP/1.1 optimizations)
```bash
# Current approach - optimized HTTP/1.1
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

---

## 4. Testing HTTP/2

### Install Testing Tools
```bash
# macOS
brew install nghttp2

# Ubuntu/Debian
apt-get install nghttp2-client

# Or use Docker
docker run --rm -it alpine/curl curl --http2 -I https://example.com
```

### Test Commands
```bash
# Test with curl
curl -I --http2 --http2-prior-knowledge http://localhost

# Test with nghttp (detailed)
nghttp -nv http://localhost

# Test with h2load (load testing)
h2load -n 1000 -c 10 http://localhost
```

### Browser Testing
1. Open Chrome DevTools
2. Network tab > Right-click columns > Enable "Protocol"
3. Refresh page
4. Check Protocol column:
   - `h2` = HTTP/2
   - `http/1.1` = HTTP/1.1

---

## 5. Performance Comparison

### HTTP/1.1 vs HTTP/2 Benefits

| Feature | HTTP/1.1 | HTTP/2 |
|---------|----------|--------|
| Connections | 6-8 per domain | 1 connection |
| Header Size | ~800 bytes | ~200 bytes (compressed) |
| Multiplexing | No | Yes |
| Server Push | No | Yes |
| Latency | Higher | Lower |

### Expected Performance Gains
- **20-30% faster** page load times
- **50% reduction** in connection overhead
- **Better performance** on high-latency networks

---

## 6. Current Status

### ✅ Enabled
- AWS ALB HTTP/2 support
- Nginx keep-alive and compression
- Connection pooling
- Optimized timeouts

### 🔄 Optional Enhancements
- Local HTTPS + HTTP/2 (for production-like testing)
- Hypercorn for FastAPI HTTP/2 support
- gRPC for inter-service communication (HTTP/2 based)

### 📝 Recommendations
1. **For AWS Production**: HTTP/2 is already enabled on ALB
2. **For Local Dev**: Current HTTP/1.1 optimizations are sufficient
3. **For Production-like Testing**: Add HTTPS + HTTP/2 to local Nginx
4. **For Microservices**: Consider gRPC (built on HTTP/2) for service-to-service calls

---

## 7. Monitoring HTTP/2

### CloudWatch Metrics (AWS ALB)
```bash
# Check ALB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=app/sensor-app-alb/xxx \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

### Nginx Logs
```bash
# Add to nginx.conf for HTTP version logging
log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                '$status $body_bytes_sent "$http_referer" '
                '"$http_user_agent" "$http_x_forwarded_for" '
                'protocol=$server_protocol';
```

---

## Quick Start

### For AWS Deployment
```bash
# HTTP/2 is already enabled - just deploy
cd sensor-backend/terraform
terraform apply
```

### For Local Testing with HTTP/2
```bash
# Generate SSL certificate
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/nginx-selfsigned.key \
  -out ssl/nginx-selfsigned.crt \
  -subj "/C=US/ST=State/L=City/O=Org/CN=localhost"

# Update nginx.conf (uncomment HTTPS section)
# Update docker-compose.loadbalancer.yml (add SSL volume)

# Start services
docker-compose -f docker-compose.loadbalancer.yml up -d

# Test
curl -I --http2 --insecure https://localhost
```

---

## Troubleshooting

### Issue: "HTTP/2 not working"
- Check if using HTTPS (browsers require it)
- Verify Nginx version supports HTTP/2 (1.9.5+)
- Check browser support (all modern browsers support it)

### Issue: "curl: option --http2: is unknown"
- Update curl: `brew upgrade curl` or `apt-get update && apt-get upgrade curl`

### Issue: "Protocol shows http/1.1 in browser"
- Ensure using HTTPS (not HTTP)
- Check SSL certificate is valid
- Verify `listen 443 ssl http2;` in nginx.conf

---

## Summary

✅ **AWS ALB**: HTTP/2 enabled and ready
✅ **Local Nginx**: Optimized with keep-alive and compression
📋 **Optional**: Add HTTPS locally for full HTTP/2 testing
🚀 **Result**: Better performance, lower latency, reduced overhead

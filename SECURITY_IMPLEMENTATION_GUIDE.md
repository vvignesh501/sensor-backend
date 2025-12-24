# 🔐 Security Implementation Guide

## Step 1: JWT OAuth2 Authentication ✅

### What We Implemented

1. **JWT Token System**
   - Access tokens (15 min expiry)
   - Refresh tokens (7 day expiry)
   - Secure token generation with HS256 algorithm

2. **Password Security**
   - Bcrypt hashing (industry standard)
   - Automatic salt generation
   - Protection against rainbow table attacks

3. **Role-Based Access Control (RBAC)**
   - User scopes: `read`, `write`, `admin`
   - Endpoint-level permission checks
   - Granular access control

4. **Security Headers**
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY
   - Strict-Transport-Security (HSTS)
   - Content-Security-Policy (CSP)
   - X-XSS-Protection

5. **CORS Protection**
   - Whitelist specific origins
   - Credential support
   - Method restrictions

---

## How to Run

### 1. Install Dependencies

```bash
cd sensor-backend
pip install -r requirements-security.txt
```

### 2. Start the Secure API

```bash
python app/secure_app.py
```

The API will start at: http://localhost:8000

### 3. Access API Documentation

Open your browser: http://localhost:8000/docs

---

## How to Test Authentication

### Test Users

| Username | Password | Scopes |
|----------|----------|--------|
| admin | admin123 | read, write, admin |
| sensor_user | sensor123 | read, write |

### 1. Login to Get Tokens

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Access Protected Endpoint

```bash
curl -X GET "http://localhost:8000/api/v1/sensors/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Get Current User Info

```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Refresh Access Token

```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

### 5. Create Sensor Data (Requires 'write' scope)

```bash
curl -X POST "http://localhost:8000/api/v1/sensors/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "SENSOR_003",
    "temperature": 24.5,
    "humidity": 50.0,
    "timestamp": "2024-01-01T12:00:00",
    "location": "Building_C"
  }'
```

### 6. Delete Sensor (Requires 'admin' scope)

```bash
curl -X DELETE "http://localhost:8000/api/v1/sensors/SENSOR_003" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Security Features Explained

### 1. JWT Tokens

**Access Token:**
- Short-lived (15 minutes)
- Used for API requests
- Contains user identity and scopes
- Signed with SECRET_KEY

**Refresh Token:**
- Long-lived (7 days)
- Used to get new access tokens
- Signed with separate REFRESH_SECRET_KEY
- Should be stored securely (HttpOnly cookie in production)

### 2. Password Hashing

```python
# Bcrypt automatically:
# - Generates random salt
# - Uses 12 rounds (2^12 iterations)
# - Produces 60-character hash
hashed = get_password_hash("mypassword")
# Result: $2b$12$KIXxLV8...
```

### 3. Scope-Based Authorization

```python
# Endpoint requires specific scope
if "admin" not in current_user.scopes:
    raise HTTPException(status_code=403, detail="Not enough permissions")
```

### 4. Security Headers

- **X-Content-Type-Options**: Prevents MIME sniffing
- **X-Frame-Options**: Prevents clickjacking
- **HSTS**: Forces HTTPS connections
- **CSP**: Prevents XSS attacks
- **X-XSS-Protection**: Browser XSS filter

---

## Production Deployment Checklist

### ⚠️ Before Production

1. **Secrets Management**
   ```python
   # DON'T: Hardcode secrets
   SECRET_KEY = "hardcoded-secret"
   
   # DO: Use AWS Secrets Manager
   import boto3
   client = boto3.client('secretsmanager')
   secret = client.get_secret_value(SecretId='jwt-secret')
   SECRET_KEY = secret['SecretString']
   ```

2. **Database Integration**
   - Replace `fake_users_db` with PostgreSQL
   - Use SQLAlchemy async queries
   - Implement proper user management

3. **Token Blacklisting**
   - Use Redis for logout/revocation
   - Store invalidated tokens with TTL
   - Check blacklist on each request

4. **HTTPS Only**
   - Configure SSL/TLS certificates
   - Redirect HTTP to HTTPS
   - Use Let's Encrypt or AWS ACM

5. **Rate Limiting**
   - Implement per-user rate limits
   - Use Redis for distributed rate limiting
   - Add IP-based throttling

6. **Logging & Monitoring**
   - Log all authentication attempts
   - Monitor failed login attempts
   - Alert on suspicious activity
   - Use CloudWatch or ELK stack

7. **CORS Configuration**
   - Whitelist only production domains
   - Remove wildcard origins
   - Validate Origin header

---

## Next Steps

### Step 2: Input Validation & SQL Injection Prevention
- Pydantic models for all inputs
- Parameterized queries
- SQL injection testing

### Step 3: Rate Limiting
- Token bucket algorithm
- Redis-based distributed limiting
- Per-user and per-IP limits

### Step 4: Data Encryption
- TLS/SSL for data in transit
- AWS KMS for data at rest
- Field-level encryption for PII

### Step 5: Container Security
- Non-root Docker containers
- Minimal base images
- Vulnerability scanning

---

## Common Issues & Solutions

### Issue: "Could not validate credentials"
**Solution:** Token expired or invalid. Get new token via `/auth/token` or `/auth/refresh`

### Issue: "Not enough permissions"
**Solution:** User doesn't have required scope. Check user scopes in `/auth/me`

### Issue: CORS error in browser
**Solution:** Add your frontend origin to `allow_origins` in `secure_app.py`

### Issue: Token not working after restart
**Solution:** SECRET_KEY changed. In production, use persistent secrets from AWS Secrets Manager

---

## Testing with Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/auth/token",
    data={"username": "admin", "password": "admin123"}
)
tokens = response.json()
access_token = tokens["access_token"]

# Access protected endpoint
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(
    "http://localhost:8000/api/v1/sensors/",
    headers=headers
)
print(response.json())
```

---

## Architecture Diagram

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ 1. POST /auth/token
       │    (username, password)
       ▼
┌─────────────────────────────┐
│   FastAPI Application       │
│  ┌────────────────────────┐ │
│  │  Auth Middleware       │ │
│  │  - Verify JWT          │ │
│  │  - Check scopes        │ │
│  └────────────────────────┘ │
│  ┌────────────────────────┐ │
│  │  Security Headers      │ │
│  │  - HSTS, CSP, etc      │ │
│  └────────────────────────┘ │
└──────────┬──────────────────┘
           │ 2. Return tokens
           │    (access + refresh)
           ▼
    ┌──────────────┐
    │   Client     │
    │  (stores     │
    │   tokens)    │
    └──────┬───────┘
           │ 3. API requests with
           │    Authorization: Bearer <token>
           ▼
    ┌──────────────────┐
    │  Protected       │
    │  Endpoints       │
    │  /api/v1/sensors │
    └──────────────────┘
```

---

## Security Best Practices Implemented

✅ JWT with short expiry (15 min)
✅ Refresh token rotation
✅ Bcrypt password hashing
✅ Role-based access control (RBAC)
✅ Security headers (HSTS, CSP, etc.)
✅ CORS whitelist
✅ Input validation with Pydantic
✅ Error handling without stack traces
✅ Request timing monitoring
✅ Health check endpoints

---

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OAuth 2.0 RFC](https://tools.ietf.org/html/rfc6749)

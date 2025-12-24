# SDK vs Backend: Where Code Lives and How It's Deployed

## The Confusion

It's easy to think: "My SDK is in my repo, so it must go in my Docker container, right?"

**NO!** They're completely separate deployment paths.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                YOUR COMPANY                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  GitHub Repository: sensor-backend/                         │
│  ├── app/              ← Backend code                       │
│  ├── Dockerfile        ← For backend only                   │
│  └── sdk/              ← SDK code (separate)                │
│                                                             │
│  Two Deployment Paths:                                      │
│                                                             │
│  Path 1: Backend → Docker → AWS                             │
│  Path 2: SDK → PyPI → Customer's machine                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Path 1: Backend (Docker Container)

### What Goes in Docker:
```
sensor-backend/
├── app/                    ✅ Goes in Docker
│   ├── main.py
│   ├── routers/
│   └── services/
├── requirements.txt        ✅ Goes in Docker
├── Dockerfile              ✅ Builds the container
└── sdk/                    ❌ Does NOT go in Docker
```

### Dockerfile:
```dockerfile
FROM python:3.11

WORKDIR /app

# Backend dependencies only
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy ONLY backend code
COPY app/ ./app/

# SDK is NOT copied - it's not needed here!

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Where It Runs:
```
Your Docker Container (AWS ECS/EC2)
├── /app/main.py           ← Your FastAPI backend
├── /app/routers/
└── Python packages (FastAPI, SQLAlchemy, etc.)

No SDK code here! The backend doesn't need the SDK.
```

## Deployment Path 2: SDK (Python Package)

### What Gets Published:
```
sensor-backend/sdk/         ← This folder becomes a package
├── redlen_sdk/
│   ├── __init__.py
│   ├── client.py
│   └── resources.py
├── setup.py                ← Package configuration
└── README.md
```

### Publishing Process:
```bash
# Navigate to SDK folder
cd sensor-backend/sdk/

# Build the package
python setup.py sdist bdist_wheel

# Upload to PyPI (Python Package Index)
twine upload dist/*

# Now it's available globally
```

### Where It Lives:
```
PyPI (Python Package Index)
└── redlen-sdk-1.0.0.tar.gz

Anyone can now:
pip install redlen-sdk
```

## How Customers Use Your SDK

### Customer's Machine (NOT your Docker container):
```python
# Customer's laptop/server
pip install redlen-sdk

# Customer's code
from redlen_sdk import Client

client = Client(api_key="key")
sensor = client.sensors.create("S1", "temp")
```

This makes HTTP requests to YOUR backend running in Docker on AWS.

## The Complete Flow

```
┌──────────────────────────────────────────────────────────────┐
│  YOUR INFRASTRUCTURE                                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Docker Container (AWS ECS)                                  │
│  ┌────────────────────────────────┐                         │
│  │  FastAPI Backend               │                         │
│  │  - app/main.py                 │                         │
│  │  - Handles HTTP requests       │                         │
│  │  - Talks to database           │                         │
│  └────────────────────────────────┘                         │
│           ↑                                                  │
│           │ HTTP Requests                                    │
│           │                                                  │
└───────────┼──────────────────────────────────────────────────┘
            │
            │
┌───────────┼──────────────────────────────────────────────────┐
│  CUSTOMER'S INFRASTRUCTURE                                   │
├───────────┼──────────────────────────────────────────────────┤
│           │                                                  │
│  Customer's Server/Laptop                                    │
│  ┌────────┴───────────────────────┐                         │
│  │  pip install redlen-sdk        │                         │
│  │                                │                         │
│  │  from redlen_sdk import Client │                         │
│  │  client = Client(api_key="key")│                         │
│  │  client.sensors.create(...)    │ ← SDK makes HTTP call   │
│  └────────────────────────────────┘                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Repository Structure Best Practices

### Option 1: Monorepo (What You Have)
```
sensor-backend/
├── app/                    ← Backend code
├── Dockerfile              ← Backend deployment
├── docker-compose.yml
├── sdk/                    ← SDK code (separate deployment)
│   ├── redlen_sdk/
│   └── setup.py
└── .github/
    └── workflows/
        ├── deploy-backend.yml      ← Deploys backend to AWS
        └── publish-sdk.yml         ← Publishes SDK to PyPI
```

### Option 2: Separate Repos (Alternative)
```
Backend Repo:
sensor-backend/
├── app/
├── Dockerfile
└── docker-compose.yml

SDK Repo:
sensor-sdk/
├── redlen_sdk/
├── setup.py
└── README.md
```

Both work! Monorepo is easier for development, separate repos for larger teams.

## CI/CD Pipelines

### Backend Pipeline (.github/workflows/deploy-backend.yml):
```yaml
name: Deploy Backend

on:
  push:
    branches: [main]
    paths:
      - 'app/**'          # Only trigger on backend changes
      - 'Dockerfile'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      # Build Docker image
      - name: Build Docker image
        run: docker build -t sensor-backend .
      
      # Push to AWS ECR
      - name: Push to ECR
        run: |
          aws ecr get-login-password | docker login ...
          docker push sensor-backend
      
      # Deploy to ECS
      - name: Deploy to ECS
        run: aws ecs update-service ...
```

### SDK Pipeline (.github/workflows/publish-sdk.yml):
```yaml
name: Publish SDK

on:
  push:
    branches: [main]
    paths:
      - 'sdk/**'          # Only trigger on SDK changes

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      # Build SDK package
      - name: Build package
        run: |
          cd sdk
          python setup.py sdist bdist_wheel
      
      # Publish to PyPI
      - name: Publish to PyPI
        run: |
          cd sdk
          twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```

## Common Misconceptions

### ❌ WRONG: "SDK goes in Docker container"
```dockerfile
# DON'T DO THIS
COPY sdk/ ./sdk/
RUN pip install -e ./sdk/
```
Your backend doesn't need the SDK! The SDK is for customers.

### ✅ CORRECT: "SDK is published separately"
```bash
# Backend deployment
docker build -t backend .
docker push backend

# SDK deployment (separate)
cd sdk/
python setup.py sdist
twine upload dist/*
```

### ❌ WRONG: "Customers clone my repo to use SDK"
```bash
# DON'T make customers do this
git clone https://github.com/company/sensor-backend
cd sensor-backend/sdk
pip install -e .
```

### ✅ CORRECT: "Customers install from PyPI"
```bash
# Customers just do this
pip install redlen-sdk
```

## When Would SDK Be in Docker?

There's ONE scenario where SDK might be in a Docker container:

### Internal Testing Container
```dockerfile
# Dockerfile.test (for testing only)
FROM python:3.11

# Install backend
COPY app/ ./app/
RUN pip install -r requirements.txt

# Install SDK for integration tests
COPY sdk/ ./sdk/
RUN pip install -e ./sdk/

# Run tests that use SDK to call backend
CMD ["pytest", "tests/integration/"]
```

But this is a **test container**, not your production backend container.

## Summary

| Component | Where Code Lives | Where It Runs | Deployment Method |
|-----------|-----------------|---------------|-------------------|
| **Backend** | `sensor-backend/app/` | Your Docker container on AWS | `docker build` → `docker push` → ECS |
| **SDK** | `sensor-backend/sdk/` | Customer's machine | `python setup.py` → `twine upload` → PyPI |

**Key Insight:** They're in the same repo for convenience during development, but they deploy to completely different places and serve different purposes.

Your backend serves HTTP requests. Your SDK makes HTTP requests. They never run in the same place!

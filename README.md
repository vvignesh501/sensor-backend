# Sensor Backend System

[![Deploy](https://github.com/<your-username>/<your-repo>/actions/workflows/deploy.yml/badge.svg)](https://github.com/<your-username>/<your-repo>/actions/workflows/deploy.yml)

A scalable backend application for handling 5000+ concurrent sensor orders with real-time data processing and AI-powered routing.

**🚀 [Quick Start Guide](docs/QUICK_START.md)** | **📖 [Deployment Guide](docs/DEPLOYMENT.md)** | **📁 [Project Structure](PROJECT_STRUCTURE.md)**

## Project Structure

```
sensor-backend/
├── app/                    # Application code (FastAPI)
├── lambda/                 # AWS Lambda functions
├── infrastructure/         # IaC (Docker, Terraform, K8s)
├── tests/                  # Test suite
├── sql/                    # Database scripts
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── config/                 # Configuration files
└── .github/workflows/      # CI/CD pipelines
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed layout.

## Features

- **FastAPI Backend**: Async endpoints with JWT authentication
- **Kafka Integration**: Message broker for order processing
- **PostgreSQL**: Persistent storage for orders and sensor data
- **S3 Integration**: Raw sensor data storage in AWS
- **AI Agent**: LangChain-powered intelligent routing and anomaly detection
- **Real-time Dashboard**: Plotly Dash for monitoring
- **Containerized**: Docker and Kubernetes ready
- **CI/CD**: Automated testing and deployment via GitHub Actions

## Quick Start

### AWS Deployment (Recommended)

Deploy to AWS in 5 minutes using GitHub Actions:

1. **Add GitHub Secrets**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
2. **Run Setup**: Actions → "Setup Terraform Backend" → Run workflow
3. **Deploy**: Push to `main` branch

See [docs/QUICK_START.md](docs/QUICK_START.md) for detailed instructions.

### Local Development

1. **Start services**:
```bash
docker-compose -f infrastructure/docker/docker-compose.yml up -d postgres
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run application**:
```bash
python -m app.main
# Or with uvicorn
uvicorn app.main:app --reload
```

4. **Access services**:
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8000/

### Docker Development

```bash
# Build and run with Docker
docker build -f infrastructure/docker/Dockerfile -t sensor-backend .
docker run -p 8000:8000 sensor-backend

# Or use Docker Compose
docker-compose -f infrastructure/docker/docker-compose.yml up
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/token` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Orders
- `POST /orders/` - Create new order
- `GET /orders/` - List orders
- `GET /orders/{id}` - Get specific order
- `PUT /orders/{id}/status` - Update order status

### Sensors
- `POST /sensors/data` - Upload sensor test data
- `GET /sensors/data` - Get sensor data with filters
- `GET /sensors/anomalies/count` - Get anomaly count
- `GET /sensors/stats` - Get sensor statistics

### Dashboard
- `GET /dashboard/metrics` - Get dashboard metrics
- `GET /dashboard/health` - Health check

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Frontend      │    │   FastAPI    │    │   Kafka     │
│   Dashboard     │◄──►│   Backend    │◄──►│   Broker    │
└─────────────────┘    └──────────────┘    └─────────────┘
                              │                     │
                              ▼                     ▼
                       ┌──────────────┐    ┌─────────────┐
                       │ PostgreSQL   │    │ Order       │
                       │ Database     │    │ Processor   │
                       └──────────────┘    └─────────────┘
                              │
                              ▼
                       ┌──────────────┐    ┌─────────────┐
                       │   AWS S3     │    │ LangChain   │
                       │ Data Lake    │    │ AI Agent    │
                       └──────────────┘    └─────────────┘
```

## Scaling for 5000+ Concurrent Users

### Backend Scaling
- **Horizontal Pod Autoscaler**: Scales 3-20 pods based on CPU/memory
- **Async FastAPI**: Non-blocking I/O for high concurrency
- **Connection Pooling**: Efficient database connections
- **Redis Caching**: Reduces database load

### Database Scaling
- **Read Replicas**: Distribute read queries
- **Connection Pooling**: SQLAlchemy async pool
- **Indexing**: Optimized queries on customer_id, timestamps

### Message Processing
- **Kafka Partitioning**: Parallel order processing
- **Consumer Groups**: Multiple processors
- **Async Processing**: Background tasks for S3 uploads

## Monitoring & Logging

### Health Checks
- Kubernetes liveness/readiness probes
- Database connection monitoring
- Kafka broker health

### Metrics
- Order processing rates
- Sensor data anomalies
- System resource usage
- API response times

### Logging
- Structured JSON logging
- Centralized log aggregation
- Error tracking and alerting

## AI Agent Features

### Intelligent Routing
- Request analysis and endpoint routing
- Business logic validation
- Load balancing optimization

### Anomaly Detection
- Real-time sensor data analysis
- Pattern recognition
- Automated alerting

### Business Logic
- Order validation rules
- Quantity limits and approvals
- Customer-specific routing

## Security

### Authentication
- JWT tokens with expiration
- Password hashing with bcrypt
- Role-based access control

### Data Protection
- S3 encryption at rest
- Database encryption
- Secrets management in K8s

### Network Security
- VPC isolation
- Security groups
- TLS/SSL encryption

## Development

### Running Tests
```bash
pytest tests/ -v --cov=app
```

### Code Quality
```bash
black app/
flake8 app/
mypy app/
```

### Local Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

See `.env.example` for all required configuration variables.

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit pull request

## License

MIT License
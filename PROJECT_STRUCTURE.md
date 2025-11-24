# Project Structure

Clean, organized structure for the Sensor Backend project.

## Directory Layout

```
sensor-backend/
├── .github/                    # GitHub Actions workflows
│   └── workflows/
│       ├── deploy.yml          # Main CI/CD pipeline
│       └── setup-backend.yml   # Terraform backend setup
│
├── app/                        # Application code
│   ├── __init__.py            # Package initialization
│   ├── main.py                # FastAPI application (entry point)
│   ├── kafka_producer.py      # Kafka producer for events
│   ├── kafka_consumer.py      # Kafka consumer for processing
│   ├── kafka_monitoring.py    # Kafka monitoring utilities
│   └── templates/             # HTML templates
│       ├── dashboard.html     # Main dashboard
│       ├── kafka_dashboard.html
│       └── kafka_processing_dashboard.html
│
├── lambda/                     # AWS Lambda functions
│   ├── lambda_data_processor.py           # Main data processor
│   ├── lambda_redshift_processor.py       # Redshift integration
│   ├── sensor_lambda_integration.py       # Sensor integration
│   ├── optimized_redshift_processor.py    # Optimized processor
│   └── requirements.txt                   # Lambda dependencies
│
├── infrastructure/             # Infrastructure as Code
│   ├── docker/                # Docker configuration
│   │   ├── Dockerfile         # Application container
│   │   ├── .dockerignore      # Docker build exclusions
│   │   ├── docker-compose.yml # Local development
│   │   ├── docker-compose.kafka.yml  # Kafka setup
│   │   └── nginx.conf         # Nginx configuration
│   │
│   ├── kubernetes/            # Kubernetes manifests (future)
│   │   └── (to be added)
│   │
│   └── terraform/             # Terraform infrastructure
│       ├── main.tf            # Core infrastructure
│       ├── ecs.tf             # ECS cluster & service
│       ├── variables.tf       # Input variables
│       ├── outputs.tf         # Output values
│       └── backend.tf         # State management
│
├── terraform/                  # Terraform (legacy location, to be removed)
│   └── (moved to infrastructure/terraform/)
│
├── tests/                      # Test files
│   ├── test_integration.py    # Integration tests
│   ├── test_lambda_processor.py  # Lambda tests
│   ├── load_test_1000_kafka.py   # Load testing
│   └── fix_login.py           # Test utilities
│
├── sql/                        # SQL scripts
│   ├── create_redshift_tables.sql
│   ├── redshift_table_schemas.sql
│   ├── redshift_optimization_example.sql
│   └── redshift_spectrum_setup.sql
│
├── docs/                       # Documentation
│   ├── DEPLOYMENT.md          # Deployment guide
│   ├── QUICK_START.md         # Quick start guide
│   ├── CICD_ARCHITECTURE.md   # CI/CD details
│   ├── DEPLOYMENT_CHECKLIST.md  # Deployment checklist
│   ├── GITHUB_ACTIONS_SETUP.md  # GitHub Actions guide
│   ├── SETUP_COMPLETE.md      # Setup summary
│   ├── production_setup.md    # Production setup
│   ├── hands_on_integration_guide.md
│   ├── technical_description.txt
│   ├── redshift_data_flow_example.py
│   └── spectrum_architecture_example.py
│
├── scripts/                    # Utility scripts
│   ├── deploy.sh              # Deployment script
│   ├── deploy_code_changes.sh
│   ├── deploy_lambda.sh
│   ├── quick_deploy.sh
│   ├── setup_aws.sh
│   ├── setup_complete_pipeline.sh
│   ├── install_kafka.sh
│   └── start_kafka.sh
│
├── config/                     # Configuration files
│   ├── .env                   # Environment variables
│   └── .gitignore             # Git exclusions
│
├── logs/                       # Application logs
│   ├── app.log
│   ├── fastapi.log
│   ├── kafka_consumer.log
│   └── (other log files)
│
├── data/                       # Data files
│   ├── load_test_100_results.json
│   └── load_test_1000_kafka_results.json
│
├── .gitignore                 # Git exclusions (root)
├── requirements.txt           # Python dependencies
├── README.md                  # Project overview
└── PROJECT_STRUCTURE.md       # This file
```

## Key Directories

### `/app` - Application Code
Contains the main FastAPI application and related modules:
- **main.py**: Entry point for the FastAPI application
- **kafka_*.py**: Kafka integration modules
- **templates/**: HTML templates for dashboards

### `/lambda` - Serverless Functions
AWS Lambda functions for data processing:
- Data processors for sensor data
- Redshift integration
- Optimized processing pipelines

### `/infrastructure` - Infrastructure as Code
All infrastructure definitions:
- **docker/**: Container definitions and compose files
- **terraform/**: AWS infrastructure (S3, Lambda, ECS, Redshift)
- **kubernetes/**: K8s manifests (future)

### `/tests` - Test Suite
All test files:
- Unit tests
- Integration tests
- Load tests

### `/sql` - Database Scripts
SQL scripts for:
- Table creation
- Schema definitions
- Optimization queries
- Redshift Spectrum setup

### `/docs` - Documentation
Comprehensive documentation:
- Deployment guides
- Architecture documentation
- Setup instructions
- Technical descriptions

### `/scripts` - Utility Scripts
Helper scripts for:
- Deployment automation
- AWS setup
- Kafka management

### `/config` - Configuration
Configuration files:
- Environment variables
- Git configuration

## File Naming Conventions

### Python Files
- `main.py` - Application entry point
- `*_producer.py` - Producer modules
- `*_consumer.py` - Consumer modules
- `*_processor.py` - Processing modules
- `test_*.py` - Test files

### Infrastructure Files
- `Dockerfile` - Container definition
- `docker-compose*.yml` - Compose configurations
- `*.tf` - Terraform files
- `*.sql` - SQL scripts

### Documentation Files
- `*.md` - Markdown documentation
- `README.md` - Project overview
- `*_GUIDE.md` - Specific guides

## Import Paths

With the new structure, imports should be:

```python
# From app/main.py
from app.kafka_producer import SensorEventProducer
from app.kafka_consumer import SensorEventConsumer

# From tests
from app.main import app
from app.kafka_producer import SensorEventProducer
```

## Docker Context

The Dockerfile now expects this structure:

```dockerfile
# Build context: sensor-backend/
# Dockerfile: sensor-backend/infrastructure/docker/Dockerfile

COPY requirements.txt .
COPY app/ ./app/
```

## Running the Application

### Local Development
```bash
# From sensor-backend/
python -m app.main

# Or with uvicorn
uvicorn app.main:app --reload
```

### Docker
```bash
# From sensor-backend/
docker build -f infrastructure/docker/Dockerfile -t sensor-backend .
docker run -p 8000:8000 sensor-backend
```

### Docker Compose
```bash
# From sensor-backend/
docker-compose -f infrastructure/docker/docker-compose.yml up
```

## Testing

```bash
# From sensor-backend/
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## Deployment

### GitHub Actions
Push to main branch triggers automatic deployment:
```bash
git add .
git commit -m "Deploy changes"
git push origin main
```

### Manual Terraform
```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

## Environment Variables

Located in `config/.env`:
```bash
DATABASE_URL=postgresql://...
AWS_REGION=us-east-1
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

## Benefits of This Structure

✅ **Clear Separation** - Code, infrastructure, docs separated  
✅ **Scalable** - Easy to add new modules  
✅ **Professional** - Industry-standard layout  
✅ **Maintainable** - Easy to find files  
✅ **CI/CD Ready** - Clear paths for automation  
✅ **Docker Friendly** - Optimized for containerization  
✅ **Team Friendly** - Easy for new developers  

## Migration Notes

### Old → New Paths

| Old Path | New Path |
|----------|----------|
| `simple_app.py` | `app/main.py` |
| `kafka_producer.py` | `app/kafka_producer.py` |
| `lambda_data_processor.py` | `lambda/lambda_data_processor.py` |
| `Dockerfile` | `infrastructure/docker/Dockerfile` |
| `*.sql` | `sql/*.sql` |
| `*.md` (except README) | `docs/*.md` |
| `test_*.py` | `tests/test_*.py` |

### Updated References

All file references have been updated in:
- ✅ Dockerfile
- ✅ GitHub Actions workflows
- ✅ Application imports
- ✅ Documentation

## Next Steps

1. ✅ Structure reorganized
2. ✅ File references updated
3. ✅ Documentation updated
4. 🔄 Test the application locally
5. 🔄 Deploy to AWS via GitHub Actions
6. 🔄 Verify all paths work correctly

## Maintenance

When adding new files:
- **Application code** → `/app`
- **Lambda functions** → `/lambda`
- **Infrastructure** → `/infrastructure`
- **Tests** → `/tests`
- **SQL scripts** → `/sql`
- **Documentation** → `/docs`
- **Utility scripts** → `/scripts`

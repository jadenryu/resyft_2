# Antibody Backend API

FastAPI-based backend for the Antibody knowledge integrity platform.

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys and database credentials. See `../CONFIGURATION_GUIDE.md` for details.

### 3. Start Database Services

If using Docker:

```bash
# From project root
docker-compose up -d postgres neo4j redis qdrant
```

### 4. Run the API Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python -m app.main
```

### 5. Start Celery Workers

In separate terminals:

```bash
# Main worker
celery -A app.workers.celery_app worker --loglevel=info --concurrency=4

# Beat scheduler (for periodic tasks)
celery -A app.workers.celery_app beat --loglevel=info
```

## API Documentation

Once running, access interactive API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app & startup
│   ├── config.py            # Configuration settings
│   ├── models/              # Pydantic models
│   │   ├── claim.py
│   │   ├── user.py
│   │   └── remediation.py
│   ├── routers/             # API endpoints
│   │   ├── ingest.py        # Article ingestion
│   │   ├── graph.py         # Graph queries
│   │   ├── retrieve.py      # Adversarial retrieval
│   │   ├── triage.py        # Remediation queue
│   │   └── auth.py          # Authentication
│   ├── services/            # Business logic & clients
│   │   ├── grok_client.py
│   │   ├── neo4j_client.py
│   │   ├── qdrant_client.py
│   │   ├── x_api_client.py
│   │   ├── embedding_service.py
│   │   ├── decay_forecaster.py
│   │   └── adversarial_retriever.py
│   ├── workers/             # Celery background tasks
│   │   ├── celery_app.py
│   │   ├── extraction_worker.py
│   │   ├── retrieval_worker.py
│   │   └── decay_worker.py
│   └── utils/               # Utilities
│       ├── auth.py
│       └── rate_limiter.py
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker image
└── .env.example            # Environment template
```

## Key Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user info

### Ingestion
- `POST /api/ingest/article` - Ingest article for processing
- `GET /api/ingest/status/{job_id}` - Check job status

### Graph
- `GET /api/graph/claim/{claim_id}` - Get claim with dependencies
- `GET /api/graph/impact/{claim_id}` - Get downstream impact
- `GET /api/graph/vulnerable` - Get vulnerable claims queue

### Retrieval
- `POST /api/retrieve/adversarial` - Find contradicting sources
- `POST /api/retrieve/similar` - Semantic similarity search

### Triage
- `GET /api/triage/queue` - Get remediation queue
- `POST /api/triage/action` - Record remediation action
- `GET /api/triage/claim/{claim_id}/history` - Get remediation history

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

## Deployment

### Docker

```bash
docker build -t antibody-backend .
docker run -p 8000:8000 --env-file .env antibody-backend
```

### Kubernetes

```bash
kubectl apply -f ../kubernetes/
```

## Monitoring

- Health check: `GET /health`
- Metrics: Available via Prometheus (configure separately)
- Logs: Structured JSON logs to stdout

## Troubleshooting

**Service won't start:**
- Check all environment variables are set in `.env`
- Verify database services are running
- Check logs for specific errors

**Database connection errors:**
- Ensure PostgreSQL, Neo4j, Redis, Qdrant are accessible
- Verify credentials in `.env`
- Check network connectivity

**Celery tasks not processing:**
- Make sure Redis is running (message broker)
- Check Celery worker logs
- Verify task routing configuration

## License

See LICENSE file in project root.

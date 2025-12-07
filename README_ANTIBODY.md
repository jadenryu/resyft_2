# Antibody: Knowledge Integrity Platform for GrokiPedia

Antibody is a proactive knowledge integrity platform that monitors encyclopedia articles, extracts and tracks claims, predicts which claims will decay over time, and actively searches for contradicting sources across multiple languages.

## Overview

The platform processes millions of articles, serving thousands of concurrent users while maintaining real-time monitoring of claim health through an interactive dashboard where editors can review and remediate issues before misinformation propagates.

## Architecture

### Core Components

1. **Ingestion Layer**: Accepts article dumps and streaming updates
2. **Processing Layer**: Extracts claims via Grok API, computes decay scores, runs adversarial retrieval
3. **Storage Layer**:
   - **Neo4j**: Graph database for claim dependencies
   - **Qdrant**: Vector database for semantic search
   - **PostgreSQL**: User data and audit logs
4. **Presentation Layer**: Next.js application with interactive visualizations

## Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Task Queue**: Celery + Redis
- **Databases**: Neo4j 5.x, Qdrant, PostgreSQL 16
- **LLM**: Grok API (xAI)
- **Embeddings**: Cohere embed-multilingual-v3
- **Real-time Signals**: X (Twitter) API v2
- **Frontend**: Next.js 14 with TypeScript
- **Visualization**: D3.js for dependency graphs
- **Deployment**: Docker + Kubernetes

## Quick Start

### Prerequisites

- Docker Desktop installed
- API keys for: Grok (xAI), Cohere, X (Twitter)
- At least 8GB RAM available

### 1. Clone and Configure

```bash
cd /Users/jadenryu/Desktop/resyft_2

# Copy environment template
cp backend/.env.example backend/.env

# Edit backend/.env and add your API keys
# See CONFIGURATION_GUIDE.md for details
nano backend/.env
```

### 2. Start All Services

```bash
# Start all infrastructure (databases, backend, workers)
docker-compose up -d

# Check status
docker-compose ps
```

### 3. Access the Platform

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Neo4j Browser**: http://localhost:7474
- **Qdrant Dashboard**: http://localhost:6333/dashboard

### 4. Ingest Your First Article

```bash
curl -X POST http://localhost:8000/api/ingest/article \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": "test_001",
    "title": "Climate Change Effects",
    "content": "Global temperatures have risen by 1.1°C since pre-industrial times...",
    "source_urls": ["https://example.com/source"]
  }'
```

## Configuration Guide

**See `CONFIGURATION_GUIDE.md` for comprehensive setup instructions**, including:
- Required API keys and where to get them
- Database configuration options
- Security best practices
- Cost estimates
- Troubleshooting guide

## Project Structure

```
antibody/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── models/      # Data models
│   │   ├── routers/     # API endpoints
│   │   ├── services/    # Business logic
│   │   ├── workers/     # Celery tasks
│   │   └── utils/       # Utilities
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # Next.js frontend (resyft-frontend/)
├── kubernetes/          # K8s manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
├── docker-compose.yml   # Local development
├── nginx.conf          # Reverse proxy config
└── CONFIGURATION_GUIDE.md
```

## Key Features

### 1. Claim Extraction
- Automatically extracts atomic claims from articles
- Uses Grok API for intelligent parsing
- Identifies mutable vs immutable claims
- Preserves source attribution

### 2. Dependency Mapping
- Builds knowledge graph in Neo4j
- Tracks epistemic support relationships
- Calculates downstream impact scores
- Efficient graph traversal at scale

### 3. Decay Prediction
- Forecasts claim reliability over time
- Monitors X (Twitter) for trending signals
- Adjusts half-life based on volatility
- Prioritizes high-risk claims

### 4. Adversarial Retrieval
- Searches for contradicting sources
- Works across 100+ languages
- Uses semantic similarity (Cohere embeddings)
- Ranks by confidence score

### 5. Triage Dashboard
- Interactive claim dependency visualization (D3.js)
- Prioritized remediation queue
- Automated workflow for editors
- Full audit trail

## API Endpoints

### Ingestion
- `POST /api/ingest/article` - Queue article for processing
- `GET /api/ingest/status/{job_id}` - Check processing status

### Graph Operations
- `GET /api/graph/claim/{claim_id}` - Get claim with dependencies
- `GET /api/graph/impact/{claim_id}` - Calculate downstream impact
- `GET /api/graph/vulnerable` - Get prioritized triage queue

### Retrieval
- `POST /api/retrieve/adversarial` - Find contradicting sources
- `POST /api/retrieve/similar` - Semantic similarity search

### Triage
- `GET /api/triage/queue` - Get remediation queue
- `POST /api/triage/action` - Record remediation (verify/update/flag/dismiss)
- `GET /api/triage/claim/{claim_id}/history` - View remediation history

### Authentication
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Get JWT token
- `GET /api/auth/me` - Get current user

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run in development mode
uvicorn app.main:app --reload

# Run tests
pytest

# Start Celery worker
celery -A app.workers.celery_app worker --loglevel=info
```

### Frontend Development

```bash
cd resyft-frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## Deployment

### Docker Compose (Development/Staging)

```bash
docker-compose up -d
```

### Kubernetes (Production)

```bash
# Create secrets
kubectl create secret generic antibody-secrets \
  --from-literal=grok-api-key=$GROK_API_KEY \
  --from-literal=cohere-api-key=$COHERE_API_KEY \
  # ... other secrets

# Deploy
kubectl apply -f kubernetes/

# Check status
kubectl get pods
```

## Scalability Features

- **Horizontal Scaling**: All services are stateless
- **Async Processing**: Non-blocking LLM calls via Celery
- **Caching**: Redis with 5-minute TTL for frequent queries
- **Database Sharding**: Qdrant auto-shards collections
- **Load Balancing**: NGINX reverse proxy
- **Rate Limiting**: Per-user and per-IP limits

## Monitoring & Observability

- **Health Checks**: `/health` endpoint reports all service status
- **Structured Logging**: JSON logs to stdout
- **Metrics**: Prometheus-compatible (add prometheus client)
- **Tracing**: OpenTelemetry integration (optional)
- **Alerts**: Configure based on vulnerability queue depth

## Security

- JWT authentication for all protected endpoints
- Role-based access control (admin/editor/viewer)
- Rate limiting (100/min authenticated, 20/min anonymous)
- Input validation via Pydantic
- SQL injection prevention via parameterized queries
- XSS protection in frontend

## Cost Estimation

### Development (Docker Compose)
- Infrastructure: $0 (local)
- APIs: ~$10-50/month (low volume)

### Production (Managed Services)
- Infrastructure: $175-600/month
- APIs: $50-1000/month (depends on volume)
- **Total**: $225-1,600/month

See `CONFIGURATION_GUIDE.md` for detailed cost breakdown.

## Troubleshooting

**Services won't start:**
```bash
# Check logs
docker-compose logs backend

# Restart specific service
docker-compose restart backend
```

**Database connection errors:**
- Verify all services are running: `docker-compose ps`
- Check environment variables in `.env`
- Ensure no port conflicts

**API errors:**
- Verify API keys are valid
- Check rate limits haven't been exceeded
- Review backend logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

See LICENSE file for details.

## Support

- Documentation: See `/docs` directory
- Issues: GitHub Issues
- API Docs: http://localhost:8000/docs

---

**Built for GrokiPedia • Powered by xAI Grok, Cohere, and Neo4j**

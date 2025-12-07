# Antibody Configuration Guide

This guide lists all the information you must manually configure before running the Antibody platform.

---

## Required API Keys and Credentials

### 1. Grok API (xAI) - **REQUIRED**
**Purpose:** Core functionality for claim extraction and synthesis

- **GROK_API_KEY**: Your Grok API key from xAI
  - Get it from: https://x.ai/ (sign up for API access)
  - Used for: Extracting claims from articles, synthesizing updated claims
  - Cost: Pay-per-use based on xAI pricing

**Where to add:**
```bash
GROK_API_KEY=your_grok_api_key_here
GROK_API_BASE=https://api.x.ai/v1
GROK_MODEL=grok-beta
```

---

### 2. Cohere API - **REQUIRED**
**Purpose:** Generating multilingual embeddings for semantic search

- **COHERE_API_KEY**: Your Cohere API key
  - Get it from: https://dashboard.cohere.com/api-keys
  - Sign up for free trial or paid plan
  - Used for: Embedding multilingual claim text (embed-multilingual-v3)
  - Cost: Free tier available, then pay-per-use

**Where to add:**
```bash
COHERE_API_KEY=your_cohere_api_key_here
COHERE_MODEL=embed-multilingual-v3.0
```

---

### 3. X (Twitter) API v2 - **REQUIRED**
**Purpose:** Real-time trend monitoring for decay prediction

You need **ALL** of these credentials from Twitter Developer Portal:

- **X_API_KEY**: API Key (Consumer Key)
- **X_API_SECRET**: API Secret (Consumer Secret)
- **X_ACCESS_TOKEN**: Access Token
- **X_ACCESS_TOKEN_SECRET**: Access Token Secret
- **X_BEARER_TOKEN**: Bearer Token

**How to get:**
1. Go to: https://developer.twitter.com/en/portal/dashboard
2. Create a new project and app
3. Generate API keys and tokens
4. Make sure you have "Elevated" access (required for v2 API)

**Where to add:**
```bash
X_API_KEY=your_x_api_key_here
X_API_SECRET=your_x_api_secret_here
X_ACCESS_TOKEN=your_x_access_token_here
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret_here
X_BEARER_TOKEN=your_x_bearer_token_here
```

**Cost:** Free tier available (limited requests), paid tiers for higher volume

---

### 4. PostgreSQL Database - **REQUIRED**
**Purpose:** Storing user accounts, audit logs, remediation history

- **POSTGRES_USER**: Database username (create your own)
- **POSTGRES_PASSWORD**: Database password (create a strong password)
- **POSTGRES_HOST**: Database host (default: `localhost` for local, service name for Docker)
- **POSTGRES_PORT**: Database port (default: `5432`)
- **POSTGRES_DB**: Database name (default: `antibody`)

**Setup Options:**

**Option A: Docker (Recommended for Development)**
The provided `docker-compose.yml` will set this up automatically. Just set:
```bash
POSTGRES_USER=antibody
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=antibody
POSTGRES_HOST=postgres  # for Docker
```

**Option B: Managed Service (Recommended for Production)**
- AWS RDS PostgreSQL
- Google Cloud SQL for PostgreSQL
- Heroku Postgres
- Railway PostgreSQL
- Supabase

Set the connection details provided by your service.

---

### 5. Neo4j Graph Database - **REQUIRED**
**Purpose:** Storing claim dependency graph

- **NEO4J_URI**: Connection URI (default: `bolt://localhost:7687`)
- **NEO4J_USER**: Username (default: `neo4j`)
- **NEO4J_PASSWORD**: Password (set your own)
- **NEO4J_DATABASE**: Database name (default: `neo4j`)

**Setup Options:**

**Option A: Docker (Recommended for Development)**
The provided `docker-compose.yml` will set this up. Set:
```bash
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password_here
NEO4J_DATABASE=neo4j
```

**Option B: Neo4j AuraDB (Managed Cloud)**
1. Go to: https://neo4j.com/cloud/aura/
2. Create a free or paid instance
3. Copy connection URI and credentials

```bash
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=generated_password_from_aura
NEO4J_DATABASE=neo4j
```

**Important:** Neo4j 5.x Enterprise is specified in the spec. For development, Community Edition works. For production with APOC plugins, use Enterprise or AuraDB.

---

### 6. Qdrant Vector Database - **REQUIRED**
**Purpose:** Storing and searching claim embeddings

- **QDRANT_HOST**: Host address (default: `localhost`)
- **QDRANT_PORT**: Port (default: `6333`)
- **QDRANT_API_KEY**: API key (optional for local, required for cloud)
- **QDRANT_COLLECTION_NAME**: Collection name (default: `claims`)

**Setup Options:**

**Option A: Docker (Recommended for Development)**
The provided `docker-compose.yml` will set this up:
```bash
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=claims
# QDRANT_API_KEY not needed for local Docker
```

**Option B: Qdrant Cloud**
1. Go to: https://cloud.qdrant.io/
2. Create a cluster
3. Get API key and cluster URL

```bash
QDRANT_HOST=your-cluster.cloud.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_COLLECTION_NAME=claims
```

---

### 7. Redis - **REQUIRED**
**Purpose:** Message broker for Celery, caching

- **REDIS_HOST**: Host (default: `localhost`)
- **REDIS_PORT**: Port (default: `6379`)
- **REDIS_PASSWORD**: Password (optional for local, recommended for production)
- **REDIS_DB**: Database number (default: `0`)

**Setup Options:**

**Option A: Docker (Recommended for Development)**
```bash
REDIS_HOST=redis
REDIS_PORT=6379
# REDIS_PASSWORD not needed for local Docker
```

**Option B: Managed Redis**
- AWS ElastiCache
- Redis Cloud
- Upstash
- Railway Redis

Set the connection details from your provider.

---

### 8. Security & Authentication - **REQUIRED**

- **SECRET_KEY**: JWT secret key (generate a strong random string)

**Generate a secure key:**
```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32
```

```bash
SECRET_KEY=your_generated_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**IMPORTANT:** Never commit this key to version control. Keep it secret!

---

## Environment Variable Files

### Backend `.env` File

Create `/backend/.env` with all the variables above:

```bash
# Application
SECRET_KEY=your_generated_secret_key_here
DEBUG=False
HOST=0.0.0.0
PORT=8000

# PostgreSQL
POSTGRES_USER=antibody
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=antibody

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=claims

# Grok API (xAI)
GROK_API_KEY=your_grok_api_key
GROK_API_BASE=https://api.x.ai/v1
GROK_MODEL=grok-beta

# X (Twitter) API
X_API_KEY=your_x_api_key
X_API_SECRET=your_x_api_secret
X_ACCESS_TOKEN=your_x_access_token
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret
X_BEARER_TOKEN=your_x_bearer_token

# Cohere API
COHERE_API_KEY=your_cohere_api_key
COHERE_MODEL=embed-multilingual-v3.0

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### Root `.env` File for Docker Compose

Create `/.env` in the project root:

```bash
# Same as backend .env, but adjust hosts for Docker networking
POSTGRES_HOST=postgres
NEO4J_URI=bolt://neo4j:7687
REDIS_HOST=redis
QDRANT_HOST=qdrant

# Plus all other variables from above
```

---

## Kubernetes Secrets

For Kubernetes deployment, create secrets:

```bash
kubectl create secret generic antibody-secrets \
  --from-literal=secret-key=your_secret_key \
  --from-literal=postgres-password=your_postgres_password \
  --from-literal=neo4j-password=your_neo4j_password \
  --from-literal=grok-api-key=your_grok_api_key \
  --from-literal=cohere-api-key=your_cohere_api_key \
  --from-literal=x-api-key=your_x_api_key \
  --from-literal=x-bearer-token=your_x_bearer_token
```

---

## Cost Estimates

### Monthly Costs (Approximate)

**API Services (Pay-per-use):**
- Grok API: $50-500/month (depends on article volume)
- Cohere API: $0-100/month (free tier available, then pay-per-embed)
- X API: $0-100/month (free tier available)

**Infrastructure (if using cloud):**
- PostgreSQL (managed): $20-100/month
- Neo4j AuraDB: $65-500/month
- Qdrant Cloud: $25-200/month
- Redis (managed): $15-50/month

**Total estimated range:** $175-1,550/month depending on scale and usage

**Cost-saving options:**
- Use free tiers where available
- Run databases self-hosted on VPS (cheaper but requires maintenance)
- Start with Docker Compose locally (free for development)

---

## Quick Start Checklist

- [ ] Sign up for Grok API at x.ai
- [ ] Sign up for Cohere API
- [ ] Create X Developer account and get API keys
- [ ] Generate a secure SECRET_KEY
- [ ] Choose database hosting strategy (Docker or managed)
- [ ] Create `/backend/.env` file with all credentials
- [ ] Create `/.env` file in project root for Docker Compose
- [ ] Install Docker Desktop (if using Docker)
- [ ] Run `docker-compose up -d` to start all services
- [ ] Access backend API at http://localhost:8000
- [ ] Access frontend at http://localhost:3000

---

## Verification

After setting up, verify connections:

1. **Backend Health Check:**
   ```bash
   curl http://localhost:8000/health
   ```
   Should return status of all services.

2. **Neo4j Browser:**
   Open http://localhost:7474 and login with your credentials

3. **Qdrant Dashboard:**
   Open http://localhost:6333/dashboard

4. **API Documentation:**
   Open http://localhost:8000/docs for interactive API docs

---

## Troubleshooting

**"Connection refused" errors:**
- Make sure all services are running: `docker-compose ps`
- Check if ports are already in use: `lsof -i :8000` (macOS/Linux)

**"Authentication failed" errors:**
- Double-check all passwords in `.env` files
- Make sure there are no trailing spaces in environment variables

**API key errors:**
- Verify API keys are valid and active
- Check API rate limits haven't been exceeded
- Ensure billing is set up for paid APIs

---

## Security Best Practices

1. **Never commit `.env` files to git** - They're in `.gitignore`
2. **Use different passwords** for each service
3. **Rotate API keys** periodically
4. **Use HTTPS** in production
5. **Enable database backups**
6. **Set up monitoring and alerts**
7. **Use environment-specific secrets** (dev, staging, prod)

---

## Need Help?

- Grok API: https://docs.x.ai/
- Cohere: https://docs.cohere.com/
- X API: https://developer.twitter.com/en/docs
- Neo4j: https://neo4j.com/docs/
- Qdrant: https://qdrant.tech/documentation/
- PostgreSQL: https://www.postgresql.org/docs/

---

**Last Updated:** December 2024

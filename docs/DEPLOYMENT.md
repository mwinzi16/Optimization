# Deployment Guide

This guide covers deployment options for the Portfolio Optimizer, from local development to production environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Production Checklist](#production-checklist)
5. [Monitoring](#monitoring)

---

## Local Development

### Prerequisites

- Python 3.10+ with pip
- Node.js 18+ with npm
- Git

### Backend Setup

```bash
# Navigate to project root
cd portfolio-optimizer

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start development server
cd backend
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Access Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Docker Deployment

### Dockerfile (Backend)

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run with Gunicorn
CMD ["gunicorn", "api:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

### Dockerfile (Frontend)

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Build application
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - API_URL=http://backend:8000

  # Optional: Redis for caching
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Cloud Deployment

### AWS (Elastic Beanstalk)

1. **Prepare application:**
   ```bash
   # Create .ebextensions for configuration
   mkdir .ebextensions
   ```

2. **Create Procfile:**
   ```
   web: gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```

3. **Deploy:**
   ```bash
   eb init -p python-3.11 portfolio-optimizer
   eb create production
   eb deploy
   ```

### Google Cloud Run

```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/ils-optimizer

# Deploy
gcloud run deploy ils-optimizer \
  --image gcr.io/PROJECT_ID/ils-optimizer \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

### Azure Container Apps

```bash
# Create container app
az containerapp create \
  --name ils-optimizer \
  --resource-group myResourceGroup \
  --environment myEnvironment \
  --image myregistry.azurecr.io/ils-optimizer:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 2 \
  --memory 4Gi
```

### Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ils-optimizer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ils-optimizer
  template:
    metadata:
      labels:
        app: ils-optimizer
    spec:
      containers:
      - name: backend
        image: ils-optimizer:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: ils-optimizer-service
spec:
  selector:
    app: ils-optimizer
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## Production Checklist

### Security

- [ ] Enable HTTPS/TLS certificates
- [ ] Configure CORS for specific origins only
- [ ] Implement rate limiting
- [ ] Add authentication (OAuth2/JWT)
- [ ] Sanitize file uploads
- [ ] Enable security headers (HSTS, CSP, etc.)

### Performance

- [ ] Enable response compression (gzip/brotli)
- [ ] Configure CDN for static assets
- [ ] Set up Redis for optimization caching
- [ ] Use multiple Gunicorn workers (2-4 per CPU)
- [ ] Enable HTTP/2

### Reliability

- [ ] Configure health checks
- [ ] Set up auto-scaling
- [ ] Implement graceful shutdown
- [ ] Configure connection timeouts
- [ ] Set up database backups (if applicable)

### Observability

- [ ] Configure structured logging
- [ ] Set up error tracking (Sentry)
- [ ] Enable metrics collection (Prometheus)
- [ ] Create dashboards (Grafana)
- [ ] Set up alerting

### Environment Variables

```bash
# Backend
LOG_LEVEL=INFO              # Logging verbosity
CORS_ORIGINS=https://app.example.com  # Allowed origins
CACHE_TTL=3600              # Cache time-to-live (seconds)
MAX_UPLOAD_SIZE=10485760    # Max file upload (bytes)

# Frontend (build-time)
VITE_API_URL=https://api.example.com  # API base URL
```

---

## Monitoring

### Health Endpoint

The `/api/health` endpoint returns:

```json
{
  "status": "healthy",
  "data_loaded": true,
  "timestamp": "2026-01-27T12:00:00Z"
}
```

### Prometheus Metrics

Add metrics collection with `prometheus-fastapi-instrumentator`:

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### Logging Format

Structured JSON logs for log aggregation:

```json
{
  "timestamp": "2026-01-27T12:00:00.000Z",
  "level": "INFO",
  "message": "Optimization completed",
  "request_id": "abc-123",
  "method": "max_sharpe",
  "duration_ms": 150,
  "status": "optimal"
}
```

### Recommended Tools

| Purpose | Tool |
|---------|------|
| Error Tracking | Sentry |
| Metrics | Prometheus + Grafana |
| Logging | ELK Stack / Loki |
| APM | Datadog / New Relic |
| Uptime | Pingdom / UptimeRobot |

---

## Troubleshooting

### Common Issues

**1. CVXPY solver errors:**
```
Problem: Solver returns "infeasible"
Solution: Relax constraints (increase max_weight, decrease min_weight)
```

**2. Memory issues:**
```
Problem: OOM with large datasets
Solution: Increase container memory, chunk large optimizations
```

**3. Slow optimization:**
```
Problem: Optimization takes > 10 seconds
Solution: Enable caching, reduce n_points for frontier
```

**4. File upload fails:**
```
Problem: Large file upload timeout
Solution: Increase upload timeout, chunk file processing
```

### Support

For issues, please file a GitHub issue with:
- Error message and stack trace
- Steps to reproduce
- Environment details (OS, Python version, etc.)

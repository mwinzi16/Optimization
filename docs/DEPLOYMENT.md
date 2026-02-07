# Deployment Guide

This guide covers deployment options for the Cat Bond Portfolio Optimizer, from local development to production environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Production Checklist](#production-checklist)
5. [Monitoring](#monitoring)

---

## Local Development

### Prerequisites

- Python 3.12+ with pip
- Git

### Setup

```bash
# Navigate to project root
cd Optimization

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start development server
python run.py
```

### Access Application

- Web UI: http://localhost:5000
- API Health: http://localhost:5000/api/v1/health

The development server runs with `debug=True` by default when started via `python run.py`.

---

## Docker Deployment

### Dockerfile

The project uses a multi-stage Dockerfile for a minimal production image:

```dockerfile
# Stage 1: install dependencies
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: runtime
FROM python:3.12-slim
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app/ ./app/
COPY run.py .
COPY data/ ./data/
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/v1/health')" || exit 1
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120"]
```

### Docker Compose

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - LOG_LEVEL=INFO
      - SECRET_KEY=${SECRET_KEY:-change-me}
      - ALLOW_ANONYMOUS=${ALLOW_ANONYMOUS:-true}
      - BIND_HOST=0.0.0.0
      - BIND_PORT=5000
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/v1/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```

### Build and Run

```bash
# Build and start
docker compose up --build -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

---

## Cloud Deployment

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
  --cpu 2 \
  --port 5000
```

### Azure Container Apps

```bash
# Create container app
az containerapp create \
  --name ils-optimizer \
  --resource-group myResourceGroup \
  --environment myEnvironment \
  --image myregistry.azurecr.io/ils-optimizer:latest \
  --target-port 5000 \
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
      - name: app
        image: ils-optimizer:latest
        ports:
        - containerPort: 5000
        env:
        - name: BIND_HOST
          value: "0.0.0.0"
        - name: BIND_PORT
          value: "5000"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: ils-optimizer-secrets
              key: secret-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 5000
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
    targetPort: 5000
  type: LoadBalancer
```

---

## Production Checklist

### Security

- [ ] Set `SECRET_KEY` to a strong random value
- [ ] Enable HTTPS/TLS certificates (set `force_https=True` in Talisman)
- [ ] Configure `CORS_ORIGINS` for specific domains only
- [ ] Set `ALLOW_ANONYMOUS=false` and configure `API_KEY` if auth is needed
- [ ] Configure `RATE_LIMIT_DEFAULT` appropriately
- [ ] Sanitize file uploads (max size via `MAX_UPLOAD_SIZE`)
- [ ] Review Flask-Talisman CSP settings per environment

### Performance

- [ ] Enable response compression (gzip/brotli via reverse proxy or middleware)
- [ ] Configure CDN for static assets (`/static/`)
- [ ] Set up Redis for optimization caching (future enhancement)
- [ ] Use 2–4 gunicorn workers per CPU core
- [ ] Tune `--timeout` for long-running optimizations

### Reliability

- [ ] Configure health checks (`/api/v1/health`)
- [ ] Set up auto-scaling (Kubernetes HPA or cloud-native)
- [ ] Implement graceful shutdown (`--graceful-timeout`)
- [ ] Configure connection timeouts
- [ ] Set up database backups (if applicable)

### Observability

- [ ] Configure structured logging (`LOG_LEVEL=INFO`)
- [ ] Set up error tracking (Sentry)
- [ ] Enable metrics collection (Prometheus)
- [ ] Create dashboards (Grafana)
- [ ] Set up alerting

### Environment Variables

```bash
# Application
SECRET_KEY=<strong-random-value>
BIND_HOST=0.0.0.0
BIND_PORT=5000
LOG_LEVEL=INFO
ALLOW_ANONYMOUS=false
API_KEY=<your-api-key>
CORS_ORIGINS=https://app.example.com
MAX_UPLOAD_SIZE=10485760
RATE_LIMIT_DEFAULT=60/minute
DATA_PATH=/app/data/scenario_returns.csv
```

---

## Monitoring

### Health Endpoint

The `/api/v1/health` endpoint returns:

```json
{
  "data": {
    "status": "healthy",
    "data_loaded": true
  },
  "meta": {
    "timestamp": "2026-02-14T12:00:00Z"
  },
  "errors": []
}
```

### Logging Format

Structured JSON logs via structlog for log aggregation:

```json
{
  "timestamp": "2026-02-14T12:00:00.000Z",
  "level": "INFO",
  "message": "Optimization completed",
  "correlation_id": "abc-123",
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
Solution: Increase MAX_UPLOAD_SIZE env var, increase gunicorn --timeout
```

**5. gunicorn worker timeout:**
```
Problem: Worker killed due to timeout on large frontier computation
Solution: Increase --timeout (default 120s), or reduce frontier n_points
```

### Support

For issues, please file a GitHub issue with:
- Error message and stack trace
- Steps to reproduce
- Environment details (OS, Python version, etc.)

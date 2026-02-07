# Cat Bond Portfolio Optimizer

An enterprise-grade **catastrophe bond portfolio optimization** platform with a FastAPI backend, React frontend, and standalone Streamlit app. Supports six optimization strategies, scenario-based risk analysis, efficient frontier computation, drag-and-drop file upload, and interactive visualizations.

## Features

- **6 Optimization Methods** — Max Sharpe, Min Variance, Min CVaR, Mean-CVaR Trade-off, Max Return (constrained), Exponential Utility (CARA)
- **Scenario-Based Analysis** — VaR/CVaR at multiple confidence levels, return-period analysis, loss probability
- **Efficient Frontier** — Full frontier computation with configurable resolution
- **File Upload** — CSV / Excel drag-and-drop with automatic validation
- **Interactive UI** — Recharts visualizations, dark theme, glassmorphism, keyboard shortcuts, ARIA accessibility
- **Export** — CSV, JSON, portfolio weights, shareable URLs

## Architecture

| Layer | Technology | Port |
|-------|-----------|------|
| **Backend API** | FastAPI + CVXPY + NumPy/Pandas/SciPy | 8000 |
| **Frontend** | React 18 + TypeScript + Vite + Tailwind CSS + Recharts | 3000 |
| **Streamlit App** | Streamlit + Plotly (standalone alternative UI) | 8501 |

## Quick Start

### Docker Compose (recommended)

```bash
docker compose up --build
```

This starts all three services:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/v1/health |
| Streamlit | http://localhost:8501 |

### Manual Setup

#### Backend

```bash
cd Optimization
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt

cd backend
uvicorn api:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

#### Streamlit (standalone)

```bash
pip install -r requirements-streamlit.txt
streamlit run app.py
```

Open http://localhost:8501.

## Project Structure

```
Optimization/
├── backend/
│   ├── api.py                  # FastAPI application
│   └── utils/
│       ├── cache.py            # LRU caching with TTL
│       ├── exceptions.py       # Custom exception hierarchy
│       ├── logger.py           # Structured logging + correlation IDs
│       └── validation.py       # Pydantic input validation
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── hooks/              # Custom React hooks
│   │   ├── utils/              # Helpers (format, export, constants)
│   │   ├── App.tsx             # Main application
│   │   └── api.ts              # API client
│   ├── Dockerfile              # Multi-stage Node + nginx
│   ├── nginx.conf              # SPA routing + API proxy
│   └── package.json
├── data/
│   ├── scenario_returns.csv    # Sample scenario data
│   └── asset_info.csv          # Asset metadata
├── app.py                      # Standalone Streamlit app
├── Dockerfile                  # Backend (multi-stage)
├── Dockerfile.streamlit        # Streamlit container
├── docker-compose.yml          # Full-stack orchestration
├── requirements.txt            # Runtime dependencies
├── requirements-dev.txt        # Dev/test dependencies
├── requirements-streamlit.txt  # Streamlit dependencies
├── CHANGELOG.md
└── README.md
```

## API Endpoints

All endpoints are served under the `/api/v1/` prefix.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/assets` | GET | List available assets with metadata |
| `/api/v1/scenarios` | GET | Scenario data summary |
| `/api/v1/optimize` | POST | Run portfolio optimization |
| `/api/v1/efficient-frontier` | GET | Compute efficient frontier |
| `/api/v1/upload` | POST | Upload CSV/Excel data file |
| `/api/v1/reset` | POST | Reset to sample data |

## Optimization Methods

| Method | Key | Description |
|--------|-----|-------------|
| Maximum Sharpe Ratio | `max_sharpe` | Maximizes risk-adjusted return (return − RF) / volatility |
| Minimum Variance | `min_variance` | Minimizes portfolio volatility |
| Minimum CVaR | `min_cvar` | Minimizes conditional value-at-risk (tail risk) |
| Mean-CVaR Trade-off | `mean_cvar` | Balances expected return against CVaR via λ parameter |
| Maximum Return | `max_return` | Maximizes return subject to a CVaR constraint |
| Exponential Utility (CARA) | `exponential_utility` | Maximizes expected exponential utility with risk-aversion γ |

## Configuration

### Optimization Parameters

| Parameter | Description | Range |
|-----------|-------------|-------|
| Min Weight | Minimum allocation per asset | 0–100 % |
| Max Weight | Maximum allocation per asset | 0–100 % |
| Risk-Free Rate | Base rate for Sharpe calculation | 0–20 % |
| CVaR Alpha | Confidence level for CVaR | 90–99 % |
| Risk Aversion (γ) | Trade-off / utility parameter | 0.01–10 |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | `8000` | Backend listen port |
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `VITE_API_BASE` | `http://localhost:8000` | Frontend API base URL (`.env`) |

## Testing

### Backend

```bash
pip install -r requirements-dev.txt

# Unit + integration tests
pytest --cov=backend --cov-report=term-missing

# Linting & formatting
ruff check backend/
black --check backend/

# Security scan
bandit -r backend/
```

### Frontend

```bash
cd frontend
npm run lint
npm run format
```

## Deployment

### Docker

```bash
# Build and run all services
docker compose up --build -d

# Build individual images
docker build -t portfolio-backend .
docker build -t portfolio-frontend frontend/
docker build -f Dockerfile.streamlit -t portfolio-streamlit .
```

### Production Notes

- Backend runs with 2 Uvicorn workers by default
- Frontend is served via nginx with SPA fallback routing
- API requests from the frontend are proxied through nginx at `/api/v1/`
- All containers run as non-root users
- Health checks are configured for backend and Streamlit containers

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design and data flow |
| [API Reference](docs/API.md) | Complete REST API docs |
| [Deployment Guide](docs/DEPLOYMENT.md) | Docker and cloud deployment |
| [Contributing](docs/CONTRIBUTING.md) | Development workflow |
| [Glossary](docs/GLOSSARY.md) | Financial terms |
| [Changelog](CHANGELOG.md) | Version history |

## License

This project is proprietary software.

## Acknowledgments

- [CVXPY](https://www.cvxpy.org/) for convex optimization
- [Recharts](https://recharts.org/) for React chart components
- [Tailwind CSS](https://tailwindcss.com/) for utility-first styling

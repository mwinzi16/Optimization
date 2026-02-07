# Cat Bond Portfolio Optimizer

An enterprise-grade **catastrophe bond portfolio optimization** platform built with Flask, HTMX, Tailwind CSS, and Plotly.js. Supports six optimization strategies, scenario-based risk analysis, efficient frontier computation, drag-and-drop file upload, and interactive visualizations — all served from a single Flask application.

## Features

- **6 Optimization Methods** — Max Sharpe, Min Variance, Min CVaR, Mean-CVaR Trade-off, Max Return (constrained), Exponential Utility (CARA)
- **Scenario-Based Analysis** — VaR/CVaR at multiple confidence levels, return-period analysis, loss probability
- **Efficient Frontier** — Full frontier computation with configurable resolution
- **File Upload** — CSV / Excel drag-and-drop with automatic validation
- **Interactive UI** — Plotly.js visualizations, HTMX-driven partial updates, dark theme, glassmorphism, keyboard shortcuts, ARIA accessibility
- **Export** — CSV, JSON, portfolio weights, shareable URLs

## Architecture

| Layer | Technology | Port |
|-------|-----------|------|
| **Flask Application** | Flask + Jinja2 + HTMX + Tailwind CSS + Plotly.js | 5000 |
| **API (Blueprint)** | REST API at `/api/v1/` — CVXPY + NumPy/Pandas/SciPy | 5000 |
| **Web UI (Blueprint)** | Server-rendered templates at `/` with HTMX interactivity | 5000 |

## Quick Start

### Docker Compose (recommended)

```bash
docker compose up --build
```

Single service available at http://localhost:5000.

### Manual Setup

```bash
cd Optimization
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt

python run.py
```

Open http://localhost:5000.

### Production (gunicorn)

```bash
gunicorn run:app --bind 0.0.0.0:5000 --workers 2
```

## Project Structure

```
Optimization/
├── app/
│   ├── __init__.py             # create_app() application factory
│   ├── config.py               # Settings dataclass (env vars)
│   ├── extensions.py           # CORS, Limiter, CSRF, Talisman
│   ├── blueprints/
│   │   ├── api_v1.py           # REST API endpoints (/api/v1/)
│   │   └── web.py              # Web UI routes (/)
│   ├── services/
│   │   ├── optimizer.py        # CatBondOptimizer (CVXPY/SciPy)
│   │   ├── data_store.py       # Thread-safe data management
│   │   └── stats.py            # Portfolio statistics
│   ├── schemas/
│   │   ├── optimization.py     # Pydantic request models
│   │   └── responses.py        # Pydantic response envelopes
│   ├── utils/
│   │   ├── auth.py             # API key authentication
│   │   ├── cache.py            # LRU caching with TTL
│   │   ├── charts.py           # Plotly chart generators
│   │   ├── exceptions.py       # Custom exception hierarchy
│   │   ├── logger.py           # Structured logging + correlation IDs
│   │   └── validation.py       # Input validation helpers
│   ├── templates/
│   │   ├── base.html           # Jinja2 base layout
│   │   ├── index.html          # Main application page
│   │   ├── partials/           # HTMX swap targets
│   │   │   ├── data_status.html
│   │   │   ├── method_params.html
│   │   │   ├── optimization_results.html
│   │   │   └── toast.html
│   │   └── errors/
│   │       ├── 404.html
│   │       └── 500.html
│   └── static/
│       ├── css/app.css         # Tailwind CSS output
│       └── js/app.js           # Client-side JS (HTMX helpers)
├── data/
│   ├── scenario_returns.csv    # Sample scenario data
│   └── asset_info.csv          # Asset metadata
├── tests/                      # pytest test suite (192+ tests)
│   ├── conftest.py             # Flask app/client fixtures
│   └── test_*.py               # Unit + integration tests
├── docs/                       # Documentation
├── run.py                      # Entry point (direct + gunicorn)
├── Dockerfile                  # Multi-stage production image
├── docker-compose.yml          # Single-service orchestration
├── requirements.txt            # Runtime dependencies
├── requirements-dev.txt        # Dev/test dependencies
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
| `SECRET_KEY` | `dev-secret-change-in-production` | Flask secret key (change in production) |
| `BIND_HOST` | `127.0.0.1` | Server bind address |
| `BIND_PORT` | `5000` | Server listen port |
| `ALLOW_ANONYMOUS` | `true` | Allow unauthenticated access |
| `API_KEY` | *(none)* | API key for authenticated access |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `RATE_LIMIT_DEFAULT` | `60/minute` | Default rate limit |
| `MAX_UPLOAD_SIZE` | `10485760` | Maximum file upload size (bytes) |
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `DATA_PATH` | `data/scenario_returns.csv` | Path to default scenario data |

## Testing

```bash
pip install -r requirements-dev.txt

# Unit + integration tests
pytest --cov=app --cov-report=term-missing

# Linting & formatting
ruff check app/
black --check app/

# Security scan
bandit -r app/
```

## Deployment

### Docker

```bash
# Build and run
docker compose up --build -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

### Production Notes

- Application runs with gunicorn (2 workers by default, 120 s timeout)
- Flask serves both templates and API — no separate frontend build or nginx required
- Container runs as non-root user (`appuser`)
- Health check configured at `/api/v1/health`
- Set `SECRET_KEY` to a strong random value in production
- Configure `CORS_ORIGINS` to specific domains in production

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
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [HTMX](https://htmx.org/) for hypermedia-driven interactivity
- [Plotly](https://plotly.com/python/) for interactive chart visualizations
- [Tailwind CSS](https://tailwindcss.com/) for utility-first styling

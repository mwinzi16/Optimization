# Architecture Documentation

## System Overview

The Portfolio Optimizer is a unified Flask application that serves both a server-rendered Web UI (Jinja2 + HTMX) and a RESTful JSON API from a single process. The application follows the Flask **application factory** pattern with Blueprints, services, and a clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Client (Browser)                            │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  HTMX + Plotly.js + Tailwind CSS                              │  │
│   │  Server-rendered HTML — partial swaps via HTMX                │  │
│   └──────────────────────────┬───────────────────────────────────┘  │
└──────────────────────────────┼──────────────────────────────────────┘
                               │ HTTP (HTML partials + JSON)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Flask Application (gunicorn)                    │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     Application Factory                        │  │
│  │  create_app() → Settings → Extensions → Blueprints → Errors   │  │
│  └───────────────────────────┬───────────────────────────────────┘  │
│                              │                                       │
│  ┌───────────────────────────┴───────────────────────────────────┐  │
│  │                       Extensions                               │  │
│  │  ┌──────┐  ┌────────┐  ┌──────┐  ┌──────────┐                │  │
│  │  │ CORS │  │Limiter │  │ CSRF │  │ Talisman │                │  │
│  │  └──────┘  └────────┘  └──────┘  └──────────┘                │  │
│  └───────────────────────────┬───────────────────────────────────┘  │
│                              │                                       │
│  ┌──────────────────┐  ┌────┴──────────────────────────────────┐   │
│  │  Web Blueprint   │  │         API v1 Blueprint              │   │
│  │  GET /            │  │  GET  /api/v1/health                 │   │
│  │  POST /optimize   │  │  GET  /api/v1/assets                 │   │
│  │  POST /upload     │  │  GET  /api/v1/scenarios              │   │
│  │  POST /reset      │  │  POST /api/v1/optimize               │   │
│  │  GET /method-…    │  │  GET  /api/v1/efficient-frontier     │   │
│  │  GET /data-status │  │  POST /api/v1/upload                 │   │
│  │  (returns HTML)   │  │  POST /api/v1/reset                  │   │
│  └────────┬─────────┘  │  (returns JSON envelopes)             │   │
│           │             └────────────┬──────────────────────────┘   │
│           └──────────┬───────────────┘                               │
│                      ▼                                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     Services Layer                             │  │
│  │  ┌──────────────┐  ┌────────────┐  ┌────────────────────┐    │  │
│  │  │  optimizer   │  │ data_store │  │       stats        │    │  │
│  │  │ (CVXPY/SciPy)│  │(thread-safe)│  │ (portfolio metrics)│    │  │
│  │  └──────────────┘  └────────────┘  └────────────────────┘    │  │
│  └───────────────────────────┬───────────────────────────────────┘  │
│                              │                                       │
│  ┌───────────────────────────┴───────────────────────────────────┐  │
│  │                       Utils Layer                              │  │
│  │  ┌───────┐ ┌───────┐ ┌────────┐ ┌────────┐ ┌──────────────┐ │  │
│  │  │ auth  │ │ cache │ │ charts │ │ logger │ │  exceptions  │ │  │
│  │  └───────┘ └───────┘ └────────┘ └────────┘ └──────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│  ┌───────────────────────────┴───────────────────────────────────┐  │
│  │                    Optimization Engine                         │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │  │
│  │  │  CVXPY  │ │ SciPy   │ │ NumPy   │ │ Pandas  │            │  │
│  │  │(Convex) │ │(SLSQP)  │ │(Compute)│ │ (Data)  │            │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘            │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Application Factory

The `create_app()` function in `app/__init__.py` follows the standard Flask factory pattern:

1. Create `Flask(__name__)` instance
2. Load `Settings` dataclass from environment variables
3. Map settings to `app.config`
4. Initialize extensions (CORS, Limiter, CSRF, Talisman)
5. Register blueprints (`api_v1_bp` at `/api/v1`, `web_bp` at `/`)
6. Exempt the API blueprint from CSRF
7. Register central error handlers

## Data Flow

### 1. Web UI Request Flow (HTMX)

```
Browser Click/Form → HTMX Request (HX-Request header)
    ↓
Web Blueprint Route → Service Layer → Template Partial Rendering
    ↓
HTML Fragment Response → HTMX Swaps Target Element in DOM
```

Example: User clicks "Optimize" button:
1. HTMX sends `POST /optimize` with form data
2. Web blueprint validates input, calls `optimizer.optimize()`
3. Service returns portfolio weights + metrics
4. Blueprint renders `partials/optimization_results.html` with Plotly chart JSON
5. HTMX swaps response into `#results` container
6. Plotly.js renders interactive charts client-side

### 2. API Request Flow (JSON)

```
API Client → JSON Request → API v1 Blueprint
    ↓
Pydantic Validation → Service Layer → Optimization Engine
    ↓
JSON Envelope Response: {"data": …, "meta": …, "errors": …}
```

### 3. File Upload Flow

```
User Drops File → HTMX POST /upload (multipart/form-data)
    ↓
Blueprint validates MIME type → Pandas reads CSV/Excel
    ↓
DataStore updates thread-safe state → Cache invalidated
    ↓
Response: HTML partial (Web) or JSON envelope (API)
```

## Template Architecture

```
templates/
├── base.html                   # Root layout: <head>, navbar, scripts
├── index.html                  # Main page: sidebar + results area
├── partials/                   # HTMX swap targets
│   ├── method_params.html      # Method-specific parameter controls
│   ├── optimization_results.html  # Results: metrics + charts
│   ├── data_status.html        # Current data summary
│   └── toast.html              # Notification toast (hx-swap-oob)
└── errors/
    ├── 404.html
    └── 500.html
```

### HTMX Partial Rendering

Partials are rendered when the server detects an HTMX request (`HX-Request` header).
The Web blueprint returns only the partial HTML fragment, which HTMX swaps into the
appropriate target element. Out-of-band swaps (`hx-swap-oob`) are used for toast
notifications so they can be injected alongside any response.

## State Management

### Server-Side State (DataStore)

| Component | Type | Purpose |
|-----------|------|---------|
| `DataStore.returns_df` | `pd.DataFrame` | Scenario returns (thread-lock guarded) |
| `DataStore.optimizer` | `CatBondOptimizer` | Optimizer instance |
| `LRUCache` | `dict` | Optimization + frontier result caching with TTL |

State is managed in `app/services/data_store.py` with a threading lock for
concurrent request safety under gunicorn workers.

### Client-Side State (HTMX)

HTMX manages UI state through the DOM itself — there is no JavaScript state store.
Form values are preserved in HTML inputs; results are swapped in-place by the server.

## API Design

### RESTful Endpoints (API v1 Blueprint)

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| GET | `/api/v1/health` | - | `{status, data_loaded}` |
| GET | `/api/v1/assets` | - | `{data: AssetInfo[]}` |
| GET | `/api/v1/scenarios` | - | `{data: ScenarioSummary}` |
| POST | `/api/v1/optimize` | `OptimizationRequest` (JSON) | `{data: OptimizationResponse}` |
| GET | `/api/v1/efficient-frontier` | Query params | `{data: FrontierPoint[]}` |
| POST | `/api/v1/upload` | FormData (file) | `{data: {n_assets, n_scenarios, asset_names}}` |
| POST | `/api/v1/reset` | - | `{data: {status, message}}` |

### Error Response Format

```json
{
  "data": null,
  "meta": {},
  "errors": [
    {
      "code": "ERR_2001",
      "message": "Optimization failed: infeasible constraints",
      "details": {
        "method": "max_sharpe",
        "min_weight": 0.1,
        "max_weight": 0.3
      }
    }
  ]
}
```

## Security

1. **CSRF**: Flask-WTF protects all form submissions; API blueprint is exempt
2. **CORS**: Flask-CORS configured for `/api/*` routes
3. **Security Headers**: Flask-Talisman (HSTS, X-Content-Type-Options, etc.)
4. **Rate Limiting**: Flask-Limiter (default 60/minute, configurable)
5. **Input Validation**: Pydantic models with constraints
6. **File Upload**: Extension + MIME type validation, size limits
7. **API Key Auth**: Optional `X-API-Key` header authentication
8. **Error Handling**: Structured errors, no stack traces in production

## Performance Optimizations

1. **Server-Side**:
   - LRU caching for optimization results and efficient frontiers
   - Cache invalidation on data upload/reset
   - NumPy vectorized operations
   - CLARABEL solver for convex problems
   - Thread-safe data store with minimal lock contention

2. **Client-Side**:
   - HTMX partial rendering (no full-page reloads)
   - Plotly.js renders charts client-side from JSON data
   - Tailwind CSS (compiled, minimal CSS payload)
   - No JavaScript framework overhead

## Deployment Architecture

```
┌───────────────┐
│   gunicorn    │
│  (2 workers)  │
│       │       │
│  ┌────┴────┐  │
│  │  Flask  │  │
│  │  App    │  │
│  └────┬────┘  │
│       │       │
│  Port 5000    │
└───────┬───────┘
        │
   HTTP Traffic
   (API + HTML)
```

- **Single process** — gunicorn with sync workers (2 per CPU recommended)
- **No reverse proxy required** — Flask serves templates and static files directly
- **Docker** — single container, non-root user, health check at `/api/v1/health`

## Future Enhancements

1. **Authentication**: OAuth2/JWT for multi-user support
2. **Database**: PostgreSQL for persistent portfolios
3. **Real-time**: WebSocket for live optimization updates (Flask-SocketIO)
4. **Batch Processing**: Celery for long-running optimizations
5. **Reporting**: PDF generation with charts

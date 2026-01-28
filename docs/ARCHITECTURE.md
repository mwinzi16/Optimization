# Architecture Documentation

## System Overview

The Portfolio Optimizer is a full-stack application built with a modern, decoupled architecture that separates concerns between data processing, optimization algorithms, and user interface.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Client (Browser)                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    React Frontend (Vite)                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │   │
│  │  │   App    │ │Components│ │  Hooks   │ │    Utils     │   │   │
│  │  │  State   │ │ (UI/UX)  │ │ (Logic)  │ │   (Export)   │   │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────────────┘   │   │
│  │       └────────────┴────────────┘                            │   │
│  │                         │                                     │   │
│  │                    ┌────┴────┐                                │   │
│  │                    │ API.ts  │                                │   │
│  │                    │ Client  │                                │   │
│  │                    └────┬────┘                                │   │
│  └─────────────────────────┼────────────────────────────────────┘   │
└────────────────────────────┼────────────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Python)                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                       API Layer                               │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │   │
│  │  │ Routing  │ │Validation│ │  Cache   │ │   Logging    │   │   │
│  │  │ /api/*   │ │ Pydantic │ │   LRU    │ │  Structured  │   │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────────────┘   │   │
│  │       └────────────┴────────────┘                            │   │
│  │                         │                                     │   │
│  │  ┌──────────────────────┴───────────────────────────────┐   │   │
│  │  │                 CatBondOptimizer                       │   │   │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │   │   │
│  │  │  │Max Sharp│ │Min Var  │ │Min CVaR │ │Mean-CVaR│    │   │   │
│  │  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘    │   │   │
│  │  │  ┌─────────────┐ ┌─────────────────────────────┐    │   │   │
│  │  │  │Max Return   │ │  Exponential Utility (CARA) │    │   │   │
│  │  │  │(Constrained)│ │                             │    │   │   │
│  │  │  └─────────────┘ └─────────────────────────────┘    │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│  ┌───────────────────────────┴───────────────────────────────────┐ │
│  │                    Optimization Engine                         │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                         │ │
│  │  │  CVXPY  │ │ SciPy   │ │ NumPy   │                         │ │
│  │  │(Convex) │ │(SLSQP)  │ │(Compute)│                         │ │
│  │  └─────────┘ └─────────┘ └─────────┘                         │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Optimization Request Flow

```
User Input → Sidebar Component → App State → API Client → FastAPI
    ↓
Request Validation (Pydantic) → CatBondOptimizer → CVXPY/SciPy
    ↓
Portfolio Weights + Metrics → Response Model → Frontend State
    ↓
Visualization Components (Recharts) → User Display
```

### 2. File Upload Flow

```
User Drops File → Sidebar Drop Zone → FormData API
    ↓
POST /api/upload → File Validation → Pandas DataFrame
    ↓
Update Global State → Reset Optimizer → Return Asset Info
    ↓
Frontend Refreshes Assets → Triggers Re-optimization
```

## Component Hierarchy

```
App (Root)
├── ToastProvider (Context)
│   └── ErrorBoundary
│       └── AppContent
│           ├── Sidebar
│           │   ├── Data Upload Zone
│           │   ├── Method Selector
│           │   ├── Parameter Controls
│           │   └── Run Button
│           │
│           └── Main Content
│               ├── Header
│               │   ├── Title
│               │   ├── Status Badge
│               │   └── Mobile Menu
│               │
│               ├── Key Metrics (8 cards)
│               │   └── MetricCard × 8 (with Tooltips)
│               │
│               ├── Tab Navigation
│               │
│               └── Tab Content (ErrorBoundary)
│                   ├── DistributionTab
│                   │   ├── Return Period Chart
│                   │   ├── Histogram
│                   │   └── Scenario Returns
│                   │
│                   ├── AllocationTab
│                   │   ├── Pie Chart
│                   │   ├── Bar Chart (paginated)
│                   │   └── Holdings Table
│                   │
│                   ├── RiskAnalysisTab
│                   │   ├── Efficient Frontier
│                   │   ├── Loss Probability
│                   │   └── Risk Gauges
│                   │
│                   └── StatsTab
│                       ├── Return Statistics
│                       ├── Risk Statistics
│                       ├── Probability Analysis
│                       ├── Percentiles
│                       └── Export Section
```

## State Management

### Frontend State (React useState)

| State Variable | Type | Purpose |
|---------------|------|---------|
| `isLoading` | boolean | Loading indicator |
| `isConnected` | boolean | API health status |
| `error` | string \| null | Error message |
| `activeTab` | TabType | Current tab |
| `result` | OptimizationResponse \| null | Optimization results |
| `assets` | AssetInfo[] | Available assets |
| `frontier` | EfficientFrontierPoint[] | Efficient frontier data |
| `method` | OptimizationMethod | Selected method |
| `minWeight`, `maxWeight` | number | Weight constraints |
| `riskFreeRate` | number | Risk-free rate |
| `cvarAlpha` | number | CVaR confidence |
| `riskAversion` | number | Mean-CVaR trade-off |
| `expRiskAversion` | number | CARA risk aversion |
| `constraintType` | 'volatility' \| 'cvar' | Constraint type |
| `maxVolatility`, `maxCvar` | number | Constraint limits |

### Backend State (Global)

| Variable | Type | Purpose |
|----------|------|---------|
| `returns_df` | pd.DataFrame | Scenario returns data |
| `optimizer` | CatBondOptimizer | Optimizer instance |
| `optimization_cache` | LRUCache | Result caching |
| `frontier_cache` | LRUCache | Frontier caching |

## API Design

### RESTful Endpoints

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| GET | `/api/health` | - | `{status, data_loaded}` |
| GET | `/api/assets` | - | `AssetInfo[]` |
| POST | `/api/optimize` | `OptimizationRequest` | `OptimizationResponse` |
| GET | `/api/efficient-frontier` | Query params | `EfficientFrontierPoint[]` |
| POST | `/api/upload` | FormData (file) | `{n_assets, n_scenarios, asset_names}` |
| POST | `/api/reset` | - | `{status, message}` |

### Error Response Format

```json
{
  "error": true,
  "code": "ERR_2001",
  "message": "Optimization failed: infeasible constraints",
  "details": {
    "method": "max_sharpe",
    "min_weight": 0.1,
    "max_weight": 0.3
  }
}
```

## Security Considerations

1. **CORS**: Configured for development (`allow_origins=["*"]`)
2. **Input Validation**: Pydantic models with constraints
3. **File Upload**: Extension validation, size limits
4. **Error Handling**: No sensitive data in error messages

## Performance Optimizations

1. **Frontend**:
   - React.memo for expensive components
   - useMemo/useCallback for computed values
   - Pagination for large asset lists
   - Skeleton loading states

2. **Backend**:
   - LRU caching for optimization results
   - Efficient frontier caching
   - NumPy vectorized operations
   - CLARABEL solver for convex problems

## Deployment Considerations

### Development
```bash
# Backend: uvicorn with reload
uvicorn api:app --reload --port 8000

# Frontend: Vite dev server
npm run dev
```

### Production
```bash
# Backend: Gunicorn with Uvicorn workers
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker

# Frontend: Build and serve static files
npm run build
# Serve dist/ with nginx or similar
```

## Future Enhancements

1. **Authentication**: OAuth2/JWT for multi-user support
2. **Database**: PostgreSQL for persistent portfolios
3. **Real-time**: WebSocket for live optimization updates
4. **Batch Processing**: Celery for long-running optimizations
5. **Reporting**: PDF generation with charts

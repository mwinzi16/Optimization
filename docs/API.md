# API Reference

## Base URL

```
Development: http://localhost:8000
Production:  https://your-domain.com/api
```

---

## Health Check

### GET /api/health

Check if the API is running and data is loaded.

**Response**

```typescript
interface HealthResponse {
  status: "healthy" | "error";
  data_loaded: boolean;
  timestamp?: string;
  version?: string;
}
```

**Example**

```bash
curl http://localhost:8000/api/health
```

```json
{
  "status": "healthy",
  "data_loaded": true
}
```

---

## Assets

### GET /api/assets

Retrieve information about all available assets.

**Response**

```typescript
interface AssetInfo {
  name: string;           // Asset identifier (e.g., "CAT_BOND_001")
  expected_return: number; // Annualized expected return (0.05 = 5%)
  volatility: number;      // Annualized volatility (0.12 = 12%)
  cvar_95: number;         // 95% CVaR (positive = loss)
  min_return: number;      // Minimum historical return
  max_return: number;      // Maximum historical return
}

type AssetsResponse = AssetInfo[];
```

**Example**

```bash
curl http://localhost:8000/api/assets
```

```json
[
  {
    "name": "CAT_BOND_001",
    "expected_return": 0.082,
    "volatility": 0.156,
    "cvar_95": 0.234,
    "min_return": -0.45,
    "max_return": 0.15
  }
]
```

---

## Optimization

### POST /api/optimize

Run portfolio optimization with specified method and parameters.

**Request Body**

```typescript
interface OptimizationRequest {
  // Optimization method (required)
  method: 
    | "max_sharpe"           // Maximum Sharpe Ratio
    | "min_volatility"       // Minimum Volatility
    | "min_cvar"             // Minimum CVaR
    | "mean_cvar"            // Mean-CVaR Trade-off
    | "max_return_constrained" // Maximum Return with Risk Constraint
    | "exponential_utility"; // CARA Exponential Utility
  
  // Weight constraints
  min_weight?: number;      // Default: 0.0 (range: 0-1)
  max_weight?: number;      // Default: 1.0 (range: 0-1)
  
  // Risk-free rate for Sharpe calculation
  risk_free_rate?: number;  // Default: 0.02 (2%)
  
  // CVaR confidence level
  cvar_alpha?: number;      // Default: 0.95 (95%), range: 0.9-0.99
  
  // Mean-CVaR trade-off parameter
  risk_aversion?: number;   // Default: 0.5 (range: 0-1)
                            // 0 = minimize CVaR only
                            // 1 = maximize return only
  
  // CARA exponential utility risk aversion
  exp_risk_aversion?: number; // Default: 2.0 (range: 0.1-50)
  
  // For max_return_constrained method
  constraint_type?: "volatility" | "cvar"; // Default: "volatility"
  max_volatility?: number;  // Default: 0.1 (10%)
  max_cvar?: number;        // Default: 0.15 (15%)
}
```

**Response**

```typescript
interface OptimizationResponse {
  weights: Record<string, number>;  // Asset -> weight mapping
  
  // Portfolio metrics
  expected_return: number;   // Annualized return
  volatility: number;        // Annualized standard deviation
  sharpe_ratio: number;      // Risk-adjusted return
  
  // Risk metrics
  cvar_95: number;           // 95% Conditional Value at Risk
  max_drawdown: number;      // Maximum peak-to-trough loss
  calmar_ratio: number;      // Return / Max Drawdown
  
  // Distribution metrics
  skewness: number;          // Return distribution skewness
  kurtosis: number;          // Return distribution kurtosis
  
  // Percentiles
  percentile_1: number;      // 1st percentile return
  percentile_5: number;      // 5th percentile return
  percentile_10: number;     // 10th percentile return
  percentile_25: number;     // 25th percentile return
  percentile_50: number;     // Median return
  percentile_75: number;     // 75th percentile return
  percentile_90: number;     // 90th percentile return
  percentile_95: number;     // 95th percentile return
  percentile_99: number;     // 99th percentile return
  
  // Return statistics
  min_return: number;        // Minimum scenario return
  max_return: number;        // Maximum scenario return
  positive_return_prob: number; // P(return > 0)
  
  // Probability analysis
  probability_analysis: ProbabilityPoint[];
  
  // Scenario-level returns
  scenario_returns: number[];
  
  // Return period analysis
  return_period_analysis: ReturnPeriodPoint[];
}

interface ProbabilityPoint {
  threshold: number;
  probability: number;
}

interface ReturnPeriodPoint {
  return_period: number;     // 1-in-N year event
  loss: number;              // Loss magnitude
  probability: number;       // Annual probability
}
```

**Example**

```bash
curl -X POST http://localhost:8000/api/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "method": "max_sharpe",
    "min_weight": 0.01,
    "max_weight": 0.15,
    "risk_free_rate": 0.02,
    "cvar_alpha": 0.95
  }'
```

---

## Efficient Frontier

### GET /api/efficient-frontier

Calculate the efficient frontier for visualization.

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_points` | int | 20 | Number of frontier points |
| `min_weight` | float | 0.0 | Minimum asset weight |
| `max_weight` | float | 1.0 | Maximum asset weight |
| `cvar_alpha` | float | 0.95 | CVaR confidence level |

**Response**

```typescript
interface EfficientFrontierPoint {
  return: number;      // Expected return at this point
  risk: number;        // Portfolio volatility
  cvar: number;        // CVaR at this point
  sharpe: number;      // Sharpe ratio
}

type EfficientFrontierResponse = EfficientFrontierPoint[];
```

**Example**

```bash
curl "http://localhost:8000/api/efficient-frontier?n_points=50&min_weight=0.01&max_weight=0.1"
```

---

## Data Upload

### POST /api/upload

Upload a custom returns data file (CSV or Excel).

**Request**

- Content-Type: `multipart/form-data`
- Body: `file` - CSV or Excel file

**File Format Requirements**

```
- First column: scenario identifiers (ignored in calculations)
- Remaining columns: asset returns per scenario
- Column headers: asset names
- Values: decimal returns (-0.1 = -10%, 0.05 = 5%)
```

**Example CSV**

```csv
Scenario,Bond_A,Bond_B,Bond_C
1,0.05,0.03,0.08
2,-0.02,0.04,-0.15
3,0.07,0.02,0.06
```

**Response**

```typescript
interface UploadResponse {
  status: "success";
  n_assets: number;
  n_scenarios: number;
  asset_names: string[];
}
```

**Error Response**

```typescript
interface UploadError {
  error: true;
  code: "ERR_1001" | "ERR_1002";
  message: string;
  details?: {
    allowed_extensions?: string[];
    max_size?: number;
  };
}
```

**Example**

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@returns_data.csv"
```

---

## Reset Data

### POST /api/reset

Reset to default sample data.

**Response**

```typescript
interface ResetResponse {
  status: "success";
  message: string;
  n_assets: number;
  n_scenarios: number;
}
```

**Example**

```bash
curl -X POST http://localhost:8000/api/reset
```

---

## Error Codes

| Code | Category | Description |
|------|----------|-------------|
| `ERR_1001` | Data | Invalid file type (not CSV/Excel) |
| `ERR_1002` | Data | Invalid file content/structure |
| `ERR_1003` | Data | No data loaded |
| `ERR_2001` | Optimization | Optimization failed |
| `ERR_2002` | Optimization | Invalid parameters |
| `ERR_2003` | Optimization | Infeasible constraints |
| `ERR_3001` | Validation | Invalid request body |
| `ERR_3002` | Validation | Parameter out of range |

---

## Rate Limiting

**Development**: No rate limiting

**Production** (recommended):
- 100 requests/minute per IP for optimization
- 1000 requests/minute per IP for read operations
- 10 file uploads per hour per IP

---

## TypeScript SDK

A TypeScript API client is available in `frontend/src/api/api.ts`:

```typescript
import { optimizePortfolio, fetchAssets, uploadFile } from './api/api';

// Optimize portfolio
const result = await optimizePortfolio({
  method: 'max_sharpe',
  min_weight: 0.01,
  max_weight: 0.15,
});

// Get assets
const assets = await fetchAssets();

// Upload custom data
await uploadFile(file);
```

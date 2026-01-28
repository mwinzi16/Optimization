# Portfolio Optimizer

An enterprise-grade portfolio optimization application featuring scenario-based optimization with multiple strategies, interactive visualizations, and comprehensive risk analytics.

![Portfolio Optimizer](docs/screenshot.png)

## � Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design, data flow, and component hierarchy |
| [API Reference](docs/API.md) | Complete REST API documentation |
| [Deployment Guide](docs/DEPLOYMENT.md) | Docker, cloud, and production deployment |
| [Contributing](docs/CONTRIBUTING.md) | Development workflow and code standards |
| [Glossary](docs/GLOSSARY.md) | Financial terms and definitions |
| [Changelog](CHANGELOG.md) | Version history and release notes |

## �🚀 Features

### Optimization Methods
- **Maximum Sharpe Ratio** - Optimal risk-adjusted returns
- **Minimum Variance** - Lowest volatility portfolio
- **Minimum CVaR** - Tail risk optimization
- **Mean-CVaR Trade-off** - Balancing return vs. tail risk
- **Maximum Return (Constrained)** - Return maximization with risk limits
- **Exponential Utility (CARA)** - Constant absolute risk aversion optimization

### Risk Analytics
- VaR/CVaR at multiple confidence levels (90%, 95%, 98%, 99%)
- Return period analysis with visualization
- Loss probability analysis
- Efficient frontier visualization
- Risk gauges and indicators

### Enterprise Features
- 📊 **Interactive Charts** - Recharts-powered visualizations
- 📁 **File Upload** - CSV/Excel support with drag-and-drop
- 💾 **Export Options** - CSV, JSON, and shareable URLs
- ⌨️ **Keyboard Shortcuts** - Ctrl+R to run optimization
- ♿ **Accessibility** - ARIA labels, keyboard navigation, screen reader support
- 📱 **Responsive Design** - Mobile and tablet optimized
- 🔔 **Toast Notifications** - Success/error feedback
- 🎨 **Professional UI** - Dark theme with glassmorphism effects

## 🛠️ Tech Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development
- **Tailwind CSS** for styling
- **Recharts** for data visualization
- **Lucide React** for icons

### Backend
- **FastAPI** with Python 3.13
- **CVXPY** with CLARABEL solver
- **NumPy/Pandas** for data processing
- **SciPy** for optimization

## 📦 Installation

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- Git

### Backend Setup

```bash
# Navigate to project root
cd Optimization

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn pandas numpy scipy cvxpy python-multipart openpyxl clarabel
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Running the Application

1. **Start the backend:**
```bash
cd backend
uvicorn api:app --reload --port 8000
```

2. **Start the frontend:**
```bash
cd frontend
npm run dev
```

3. **Open in browser:** http://localhost:3000

## 📁 Project Structure

```
Optimization/
├── backend/
│   ├── api.py              # FastAPI application
│   └── utils/
│       ├── __init__.py     # Utils package
│       ├── cache.py        # LRU caching
│       ├── exceptions.py   # Custom exceptions
│       ├── logger.py       # Logging configuration
│       └── validation.py   # Input validation
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── AllocationTab.tsx
│   │   │   ├── DistributionTab.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   ├── RiskAnalysisTab.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   ├── StatsTab.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── Tooltip.tsx
│   │   ├── hooks/          # Custom React hooks
│   │   ├── utils/          # Utility functions
│   │   ├── api.ts          # API client
│   │   ├── types.ts        # TypeScript types
│   │   ├── App.tsx         # Main application
│   │   └── index.css       # Global styles
│   ├── package.json
│   └── vite.config.ts
├── data/
│   └── scenario_returns.csv  # Sample data
└── README.md
```

## 🎯 Usage

### Uploading Custom Data

1. Prepare a CSV or Excel file with:
   - Rows representing scenarios (10,000+ recommended)
   - Columns representing assets
   - Values as decimal returns (e.g., 0.05 for 5%)

2. Drag and drop the file onto the upload zone, or click to browse

3. The optimizer will automatically recalculate with your data

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + R` | Run optimization |
| `Escape` | Close mobile sidebar |

### Exporting Results

- **CSV** - Full report with metrics, statistics, and weights
- **JSON** - Programmatic export for integration
- **Weights CSV** - Portfolio weights only
- **Share Link** - URL with encoded parameters

## 🔧 Configuration

### Optimization Parameters

| Parameter | Description | Range |
|-----------|-------------|-------|
| Min Weight | Minimum allocation per asset | 0-100% |
| Max Weight | Maximum allocation per asset | 0-100% |
| Risk-Free Rate | Base rate for Sharpe calculation | 0-20% |
| CVaR Alpha | Confidence level for CVaR | 90-99% |
| Risk Aversion | Trade-off parameter | 0.01-10 |

### Environment Variables

```bash
# Backend
API_PORT=8000
LOG_LEVEL=INFO

# Frontend (in .env)
VITE_API_BASE=http://localhost:8000
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/assets` | GET | Get asset information |
| `/api/optimize` | POST | Run optimization |
| `/api/efficient-frontier` | GET | Get efficient frontier |
| `/api/upload` | POST | Upload data file |
| `/api/reset` | POST | Reset to sample data |

## 🧪 Testing

```bash
# Run tests
npm run test

# Run with coverage
npm run test:coverage

# Type checking
npm run type-check

# Linting
npm run lint
npm run lint:fix
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software.

## 🙏 Acknowledgments

- CVXPY team for the optimization framework
- Recharts for beautiful visualizations
- Tailwind CSS for utility-first styling

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- User authentication (OAuth2)
- Portfolio save/load functionality
- PDF report generation
- Real-time WebSocket updates
- Monte Carlo simulation
- Black-Litterman model support

---

## [2.0.0] - 2026-01-27

### Added

#### Backend
- **Structured logging** with request timing and correlation IDs
- **Custom exceptions** with error codes for better error handling
- **Pydantic validation** for all request models
- **LRU caching** with TTL for optimization and frontier results
- **Utils package** (`backend/utils/`) with modular utilities

#### Frontend
- **ErrorBoundary** component for graceful error handling
- **Toast notifications** for user feedback (success, error, warning, info)
- **Tooltip system** with financial metric explanations
- **Skeleton loading** components for better perceived performance
- **Custom hooks**:
  - `useAsync` - Async operation handling with loading/error states
  - `useDebounce` - Debounced value updates
  - `useThrottle` - Throttled callback execution
  - `useLocalStorage` - Persistent state with localStorage
  - `useMediaQuery` - Responsive design utilities
  - `useKeyboardShortcut` - Keyboard navigation support
- **Export utilities**:
  - Export to CSV
  - Export to JSON
  - Export portfolio weights
  - Shareable URL generation
- **Accessibility improvements**:
  - ARIA labels and roles
  - Keyboard navigation (Ctrl+R to run, Escape to close)
  - Skip links
  - Focus management
  - Reduced motion support
  - High contrast support
- **Responsive design** for tablet and mobile devices
- **Mobile sidebar** with hamburger menu

#### Documentation
- Comprehensive README with quick start guide
- Architecture documentation with diagrams
- API reference with all endpoints
- Contributing guide
- Changelog

#### Code Quality
- ESLint configuration with TypeScript and accessibility rules
- Prettier configuration for consistent formatting
- Vitest setup for unit testing
- Type-safe development with strict TypeScript

### Changed
- Renamed package to `portfolio-optimizer`
- Bumped version to 2.0.0
- Updated MetricCard to support tooltips and accessibility
- Enhanced StatsTab with export functionality
- Improved main App layout with skip links and mobile support

### Fixed
- TypeScript timer types for browser compatibility (`ReturnType<typeof setTimeout>`)

---

## [1.0.0] - 2026-01-15

### Added
- Initial release of Portfolio Optimizer
- **6 optimization methods**:
  - Maximum Sharpe Ratio
  - Minimum Volatility
  - Minimum CVaR
  - Mean-CVaR Trade-off
  - Maximum Return (Constrained)
  - Exponential Utility (CARA)
- **Portfolio analysis tabs**:
  - Distribution analysis with histograms
  - Allocation visualization (pie/bar charts)
  - Risk analysis with efficient frontier
  - Statistics with comprehensive metrics
- **Interactive sidebar** with:
  - Drag-and-drop file upload
  - Method selection
  - Parameter controls
  - Constraint settings
- **Key metrics display**:
  - Expected Return
  - Volatility
  - Sharpe Ratio
  - CVaR (95%)
  - Max Drawdown
  - Skewness
  - Kurtosis
  - Calmar Ratio
- **Data upload** support for CSV and Excel files
- **FastAPI backend** with async endpoints
- **React frontend** with TypeScript and Tailwind CSS
- **Recharts** visualizations

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 2.0.0 | 2026-01-27 | Enterprise features: A11Y, exports, docs, code quality |
| 1.0.0 | 2026-01-15 | Initial release with 6 optimization methods |

---

## Migration Guides

### Upgrading from 1.x to 2.x

**Breaking Changes:** None - fully backward compatible

**New Dependencies:**
```bash
# Frontend
npm install
# Installs new dev dependencies: eslint, prettier, vitest, etc.

# Backend (no new dependencies)
```

**New Features to Enable:**
1. Wrap your app with `ToastProvider` for notifications
2. Add `ErrorBoundary` for graceful error handling
3. Import hooks from `@/hooks` for custom functionality
4. Use export utilities from `@/utils/export`

**Configuration:**
- ESLint and Prettier configs are pre-configured
- Run `npm run lint` to check code quality
- Run `npm run format` to auto-format code

---

## Links

- [Repository](https://github.com/OWNER/portfolio-optimizer)
- [Documentation](./docs/)
- [Issues](https://github.com/OWNER/portfolio-optimizer/issues)
- [Releases](https://github.com/OWNER/portfolio-optimizer/releases)

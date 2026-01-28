# Contributing Guide

Thank you for your interest in contributing to the Portfolio Optimizer! This document provides guidelines and information for contributors.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Testing](#testing)
6. [Pull Request Process](#pull-request-process)
7. [Issue Guidelines](#issue-guidelines)

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please:

- Be respectful and constructive in discussions
- Focus on the issue, not the person
- Accept constructive criticism gracefully
- Help others learn and grow

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/portfolio-optimizer.git
cd portfolio-optimizer

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/portfolio-optimizer.git
```

### Environment Setup

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend
cd ../frontend
npm install
```

---

## Development Workflow

### Branching Strategy

```
main          # Production-ready code
├── develop   # Integration branch
    ├── feature/add-monte-carlo    # New features
    ├── fix/sharpe-calculation     # Bug fixes
    ├── docs/api-reference         # Documentation
    └── refactor/optimizer-class   # Code improvements
```

### Branch Naming

- `feature/` - New functionality
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes
- `chore/` - Build, CI, tooling

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Maintenance

**Examples:**

```bash
feat(optimizer): add Black-Litterman model support

fix(frontend): correct Sharpe ratio calculation with negative returns

docs(api): add authentication section to API reference

refactor(hooks): extract useOptimization from App component
```

---

## Code Standards

### Python (Backend)

**Style Guide:** PEP 8 + Black formatting

```python
# Good
def calculate_cvar(
    returns: np.ndarray,
    alpha: float = 0.95,
    weights: np.ndarray | None = None,
) -> float:
    """
    Calculate Conditional Value at Risk.

    Args:
        returns: Array of scenario returns.
        alpha: Confidence level (default: 95%).
        weights: Optional portfolio weights.

    Returns:
        CVaR as a positive number (loss).

    Raises:
        ValueError: If alpha is not in (0, 1).

    Example:
        >>> returns = np.array([-0.1, 0.05, -0.2, 0.08])
        >>> calculate_cvar(returns, alpha=0.95)
        0.15
    """
    if not 0 < alpha < 1:
        raise ValueError(f"Alpha must be in (0, 1), got {alpha}")

    sorted_returns = np.sort(returns)
    cutoff = int(np.ceil(len(returns) * (1 - alpha)))
    return -np.mean(sorted_returns[:cutoff])
```

**Type Hints:** Required for all functions

```python
# Use modern Python 3.10+ syntax
from typing import TypeAlias

Weights: TypeAlias = dict[str, float]

def optimize(method: str, **kwargs: float) -> Weights:
    ...
```

### TypeScript (Frontend)

**Style Guide:** ESLint + Prettier (configured in project)

```typescript
// Good
interface MetricCardProps {
  /** Display label for the metric */
  label: string;
  /** Formatted value to display */
  value: string;
  /** Lucide icon component */
  icon: React.ComponentType<{ className?: string }>;
  /** Optional color scheme */
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple';
  /** Optional tooltip text */
  tooltip?: string;
}

/**
 * Displays a single metric in a card format.
 * Used in the dashboard header for key portfolio statistics.
 */
export const MetricCard: React.FC<MetricCardProps> = memo(({
  label,
  value,
  icon: Icon,
  color = 'blue',
  tooltip,
}) => {
  return (
    <div className={`metric-card metric-card--${color}`} role="region">
      <Icon className="metric-card__icon" aria-hidden />
      <div className="metric-card__content">
        <span className="metric-card__label">{label}</span>
        <span className="metric-card__value">{value}</span>
      </div>
      {tooltip && <InfoTooltip content={tooltip} />}
    </div>
  );
});
```

**React Best Practices:**

1. Use functional components with hooks
2. Memoize expensive components with `React.memo`
3. Use `useMemo` and `useCallback` for expensive computations
4. Keep components focused (single responsibility)
5. Extract reusable logic into custom hooks

### CSS/Tailwind

```css
/* Use semantic class names */
.portfolio-chart { }
.portfolio-chart__legend { }
.portfolio-chart__legend--active { }

/* Prefer Tailwind utilities for one-off styles */
<div className="flex items-center gap-4 p-4" />

/* Extract repeated patterns to components */
@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-blue-600 text-white rounded-lg 
           hover:bg-blue-700 focus:ring-2 focus:ring-blue-500;
  }
}
```

---

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v --cov=.

# Run specific test file
pytest tests/test_optimizer.py -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html
```

**Test Structure:**

```python
# tests/test_optimizer.py
import pytest
import numpy as np
from catbond_optimizer import CatBondOptimizer


class TestCatBondOptimizer:
    """Tests for the CatBondOptimizer class."""

    @pytest.fixture
    def sample_returns(self) -> np.ndarray:
        """Generate sample returns for testing."""
        np.random.seed(42)
        return np.random.randn(1000, 10) * 0.1 + 0.05

    @pytest.fixture
    def optimizer(self, sample_returns: np.ndarray) -> CatBondOptimizer:
        """Create optimizer with sample data."""
        return CatBondOptimizer(sample_returns)

    def test_max_sharpe_weights_sum_to_one(
        self, optimizer: CatBondOptimizer
    ) -> None:
        """Portfolio weights should sum to 1."""
        weights = optimizer.max_sharpe()
        assert abs(sum(weights.values()) - 1.0) < 1e-6

    def test_min_volatility_lower_than_equal_weight(
        self, optimizer: CatBondOptimizer
    ) -> None:
        """Min volatility should be <= equal-weighted portfolio."""
        weights = optimizer.min_volatility()
        # ... assertions
```

### Frontend Tests

```bash
cd frontend
npm run test

# Watch mode
npm run test -- --watch

# Coverage
npm run test:coverage
```

**Test Structure:**

```typescript
// src/components/__tests__/MetricCard.test.tsx
import { render, screen } from '@testing-library/react';
import { MetricCard } from '../MetricCard';
import { TrendingUp } from 'lucide-react';

describe('MetricCard', () => {
  it('renders label and value', () => {
    render(
      <MetricCard
        label="Expected Return"
        value="8.5%"
        icon={TrendingUp}
      />
    );

    expect(screen.getByText('Expected Return')).toBeInTheDocument();
    expect(screen.getByText('8.5%')).toBeInTheDocument();
  });

  it('shows tooltip on hover', async () => {
    render(
      <MetricCard
        label="Sharpe Ratio"
        value="1.25"
        icon={TrendingUp}
        tooltip="Risk-adjusted return measure"
      />
    );

    // ... hover and assert tooltip
  });
});
```

---

## Pull Request Process

### Before Submitting

1. **Update from upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```

2. **Run all checks:**
   ```bash
   # Backend
   black .
   ruff check .
   pytest tests/ -v

   # Frontend
   npm run lint
   npm run type-check
   npm run test
   ```

3. **Update documentation** if needed

### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings

## Screenshots (if UI change)
Before | After
-------|------
  ...  |  ...
```

### Review Process

1. Automated checks must pass
2. At least one maintainer approval required
3. All conversations must be resolved
4. Squash merge into develop

---

## Issue Guidelines

### Bug Reports

```markdown
**Describe the bug**
Clear description of what the bug is.

**To Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable.

**Environment:**
- OS: [e.g., Windows 11]
- Browser: [e.g., Chrome 120]
- Version: [e.g., 2.0.0]

**Additional context**
Any other relevant information.
```

### Feature Requests

```markdown
**Is your feature request related to a problem?**
Description of the problem.

**Describe the solution you'd like**
Clear description of what you want.

**Describe alternatives you've considered**
Other solutions or features you've considered.

**Additional context**
Mockups, examples, etc.
```

---

## Questions?

- Open a [Discussion](https://github.com/OWNER/portfolio-optimizer/discussions)
- Email: maintainer@example.com

Thank you for contributing! 🎉

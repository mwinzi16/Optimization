# Financial Terms Glossary

This glossary defines key financial and technical terms used in the Portfolio Optimizer.

## Portfolio Metrics

### Expected Return
The weighted average of possible returns, calculated as the mean of scenario returns.
- **Formula:** $E[R] = \frac{1}{n} \sum_{i=1}^{n} R_i$
- **Interpretation:** Higher is better (more profit expected)
- **Typical Range:** -5% to +15% annually for ILS

### Volatility (Standard Deviation)
A measure of the dispersion of returns around the mean.
- **Formula:** $\sigma = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (R_i - \bar{R})^2}$
- **Interpretation:** Lower is better (more predictable returns)
- **Typical Range:** 5% to 30% for ILS portfolios

### Sharpe Ratio
Risk-adjusted return measuring excess return per unit of risk.
- **Formula:** $SR = \frac{E[R] - R_f}{\sigma}$
- **Interpretation:** Higher is better (more return per unit of risk)
- **Typical Range:**
  - < 0: Underperforming risk-free rate
  - 0-1: Acceptable
  - 1-2: Good
  - > 2: Excellent

### Value at Risk (VaR)
The maximum expected loss at a given confidence level.
- **VaR 95%:** 5% of scenarios have worse returns than this value
- **VaR 99%:** 1% of scenarios have worse returns
- **Interpretation:** More negative = higher potential loss
- **Example:** VaR 95% = -0.10 means 5% chance of losing 10%+

### Conditional Value at Risk (CVaR / Expected Shortfall)
The expected loss given that losses exceed VaR.
- **Formula:** $CVaR_\alpha = E[R | R \leq VaR_\alpha]$
- **Interpretation:** More negative = worse tail risk
- **Why It's Better Than VaR:** CVaR is coherent (subadditive) and considers severity of tail losses

### Maximum Drawdown
The largest peak-to-trough decline in portfolio value.
- **Interpretation:** More negative = larger potential loss
- **For ILS:** Often the worst single scenario return

### Calmar Ratio
Risk-adjusted return using maximum drawdown as the risk measure.
- **Formula:** $Calmar = \frac{E[R]}{|MaxDrawdown|}$
- **Interpretation:** Higher is better

---

## Distribution Statistics

### Skewness
Measures asymmetry of the return distribution.
- **Negative Skew:** Fat left tail (more extreme losses)
- **Zero Skew:** Symmetric distribution
- **Positive Skew:** Fat right tail (more extreme gains)
- **ILS Typical:** Negative skew due to catastrophe risk

### Kurtosis
Measures the "tailedness" of the distribution.
- **Low Kurtosis (<3):** Thin tails, fewer extreme events
- **Normal (=3):** Gaussian distribution
- **High Kurtosis (>3):** Fat tails, more extreme events
- **ILS Typical:** High kurtosis due to catastrophe events

### Percentiles
Points that divide the distribution into 100 equal parts.
- **P1:** 1% of returns are below this value
- **P50 (Median):** Half of returns are above/below this
- **P99:** 99% of returns are below this value

---

## Optimization Methods

### Maximum Sharpe Ratio
Finds the portfolio with the highest risk-adjusted return.
- **Use When:** You want the best return per unit of risk
- **Characteristics:** Tends to concentrate in high Sharpe assets
- **Solver:** CVXPY with transformation method

### Minimum Variance
Finds the portfolio with the lowest volatility.
- **Use When:** You want the most stable returns
- **Characteristics:** Often underweight high-risk, high-return assets
- **Solver:** Quadratic programming (CVXPY)

### Minimum CVaR
Minimizes expected loss in worst-case scenarios.
- **Use When:** You want to protect against tail risk
- **Characteristics:** More conservative than minimum variance
- **Solver:** Linear programming formulation (CVXPY)

### Mean-CVaR Trade-off
Balances expected return against tail risk.
- **Formula:** $\min -E[R] + \lambda \cdot CVaR$
- **Parameter λ:** Risk aversion (higher = more conservative)
- **Use When:** You want to tune risk-return preference

### Maximum Return (Constrained)
Maximizes return subject to risk limits.
- **Volatility Constraint:** $\sigma \leq \sigma_{max}$
- **CVaR Constraint:** $CVaR \leq CVaR_{max}$
- **Use When:** You have specific risk budgets

### Exponential Utility (CARA)
Uses Constant Absolute Risk Aversion utility function.
- **Utility:** $U(W) = -e^{-cW}$
- **Parameter c:** Risk aversion coefficient
  - c < 0: Risk-seeking (unusual)
  - c = 0: Risk-neutral (maximize expected return)
  - c > 0: Risk-averse (penalize downside)
- **Use When:** You have theoretical risk preferences

---

## ILS-Specific Terms

### Insurance-Linked Securities (ILS)
Financial instruments whose value is affected by insurance loss events.

### Catastrophe Bond (Cat Bond)
A bond that transfers catastrophic risk from insurers to investors.
- **Trigger:** Natural disaster or specified event
- **If Triggered:** Principal is reduced or lost
- **If Not Triggered:** Investor receives premium + principal

### No-Loss Return
The return achieved if no catastrophe event occurs.
- **Calculation:** Maximum return in the scenario distribution
- **Represents:** Coupon/premium without losses

### Expected Loss
The expected reduction in return due to potential catastrophes.
- **Formula:** $ExpectedLoss = NoLossReturn - ExpectedReturn$

### Return Period
The average time between events of a certain magnitude.
- **Example:** 1-in-100 year event has 1% annual probability
- **Use:** Understanding tail risk frequency

---

## Technical Terms

### Scenario-Based Optimization
Using discrete scenarios (simulations) instead of parametric distributions.
- **Advantage:** Captures non-normal distributions
- **Typical:** 1,000-100,000 scenarios

### Convex Optimization
Optimization where the objective and constraints form a convex set.
- **Property:** Any local minimum is a global minimum
- **Solver:** CVXPY with CLARABEL

### Efficient Frontier
The set of portfolios that maximize return for each level of risk.
- **Visualization:** Upper boundary of the risk-return scatter
- **Property:** All frontier portfolios are Pareto-optimal

### Diversification
Reducing risk by spreading investments across assets.
- **Effect:** Portfolio volatility < weighted average of asset volatilities
- **Measure:** Correlation between assets

### Correlation
Statistical measure of how two assets move together.
- **+1:** Perfect positive correlation (move together)
- **0:** No correlation (independent)
- **-1:** Perfect negative correlation (move opposite)

---

## Abbreviations

| Abbreviation | Full Term |
|--------------|-----------|
| CVaR | Conditional Value at Risk |
| VaR | Value at Risk |
| ILS | Insurance-Linked Securities |
| CARA | Constant Absolute Risk Aversion |
| SR | Sharpe Ratio |
| MVO | Mean-Variance Optimization |
| EW | Equal Weight |
| RF | Risk-Free Rate |

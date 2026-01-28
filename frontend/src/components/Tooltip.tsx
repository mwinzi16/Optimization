import { useState, useRef, useEffect, ReactNode } from 'react';
import { HelpCircle } from 'lucide-react';

interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
  maxWidth?: number;
}

/**
 * Tooltip component with smart positioning and delay.
 */
export function Tooltip({
  content,
  children,
  position = 'top',
  delay = 300,
  maxWidth = 300,
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const calculatePosition = () => {
    if (!triggerRef.current || !tooltipRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const padding = 8;

    let x = 0;
    let y = 0;

    switch (position) {
      case 'top':
        x = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2;
        y = triggerRect.top - tooltipRect.height - padding;
        break;
      case 'bottom':
        x = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2;
        y = triggerRect.bottom + padding;
        break;
      case 'left':
        x = triggerRect.left - tooltipRect.width - padding;
        y = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
        break;
      case 'right':
        x = triggerRect.right + padding;
        y = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
        break;
    }

    // Keep tooltip within viewport
    x = Math.max(padding, Math.min(x, window.innerWidth - tooltipRect.width - padding));
    y = Math.max(padding, Math.min(y, window.innerHeight - tooltipRect.height - padding));

    setCoords({ x, y });
  };

  const handleMouseEnter = () => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
      // Calculate position after render
      requestAnimationFrame(calculatePosition);
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onFocus={handleMouseEnter}
        onBlur={handleMouseLeave}
        className="inline-flex"
      >
        {children}
      </div>
      {isVisible && (
        <div
          ref={tooltipRef}
          className="fixed z-50 px-3 py-2 text-sm rounded-lg shadow-lg animate-fadeIn"
          style={{
            left: coords.x,
            top: coords.y,
            maxWidth,
            background: 'rgba(24, 24, 27, 0.98)',
            border: '1px solid rgba(63, 63, 70, 0.8)',
            color: '#e4e4e7',
            backdropFilter: 'blur(8px)',
          }}
          role="tooltip"
        >
          {content}
        </div>
      )}
    </>
  );
}

interface InfoTooltipProps {
  content: ReactNode;
  size?: number;
}

/**
 * Info icon with tooltip - use for inline help.
 */
export function InfoTooltip({ content, size = 14 }: InfoTooltipProps) {
  return (
    <Tooltip content={content} position="top">
      <HelpCircle
        size={size}
        className="text-zinc-500 hover:text-zinc-400 cursor-help transition-colors ml-1"
        aria-label="More information"
      />
    </Tooltip>
  );
}

// Metric explanations for tooltips
export const METRIC_TOOLTIPS = {
  noLossReturn: "The maximum possible return (if no losses occur). This represents the 'no-loss' scenario where all cat bond coupons are received.",
  expectedLoss: "The average loss across all scenarios. Calculated as Mean Return minus No-Loss Return.",
  expectedReturn: "The probability-weighted average return across all 10,000 simulated scenarios.",
  volatility: "Standard deviation of portfolio returns. Measures how spread out returns are from the mean.",
  var90: "Value at Risk at 90% confidence. The return level exceeded 90% of the time (or 10th percentile).",
  var95: "Value at Risk at 95% confidence. The return level exceeded 95% of the time (or 5th percentile).",
  var99: "Value at Risk at 99% confidence. The return level exceeded 99% of the time (or 1st percentile).",
  tvar90: "Tail VaR (CVaR) at 90%. Expected return in the worst 10% of scenarios.",
  tvar95: "Tail VaR (CVaR) at 95%. Expected return in the worst 5% of scenarios.",
  tvar99: "Tail VaR (CVaR) at 99%. Expected return in the worst 1% of scenarios.",
  sharpeRatio: "Risk-adjusted return measure: (Expected Return - Risk Free Rate) / Volatility. Higher is better.",
  maxDrawdown: "The worst-case scenario return (minimum across all simulations).",
} as const;

export const METHOD_TOOLTIPS = {
  maxSharpe: "Finds the portfolio with the highest risk-adjusted return by maximizing the Sharpe Ratio (return per unit of risk).",
  minVariance: "Creates the portfolio with the lowest possible volatility, regardless of expected return. Best for highly risk-averse investors.",
  minCvar: "Minimizes expected losses in the worst scenarios (tail risk). Uses Conditional Value-at-Risk at the specified confidence level.",
  meanCvar: "Balances expected return against tail risk. The risk aversion parameter controls the trade-off between higher returns and lower CVaR.",
  maxReturnConstrained: "Maximizes expected return while staying within a specified risk limit (either volatility or CVaR constraint).",
  exponentialUtility: "Uses CARA (Constant Absolute Risk Aversion) utility function. Risk aversion controls whether the optimizer is risk-seeking (0) or risk-averse (1).",
} as const;

export default Tooltip;

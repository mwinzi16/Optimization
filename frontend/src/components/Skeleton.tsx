import { memo } from 'react';

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'rect' | 'circle';
  animation?: 'pulse' | 'wave' | 'none';
}

/**
 * Skeleton loading placeholder component.
 */
export const Skeleton = memo(function Skeleton({
  className = '',
  width,
  height,
  variant = 'rect',
  animation = 'pulse',
}: SkeletonProps) {
  const baseStyles = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
    background: 'rgba(255, 255, 255, 0.06)',
  };

  const variantClasses = {
    text: 'rounded',
    rect: 'rounded-lg',
    circle: 'rounded-full',
  };

  const animationClasses = {
    pulse: 'animate-pulse',
    wave: 'skeleton-wave',
    none: '',
  };

  return (
    <div
      className={`${variantClasses[variant]} ${animationClasses[animation]} ${className}`}
      style={baseStyles}
      aria-hidden="true"
      role="presentation"
    />
  );
});

/**
 * Skeleton card for metric loading state.
 */
export function MetricCardSkeleton() {
  return (
    <div
      className="rounded-xl p-4"
      style={{
        background: 'rgba(255, 255, 255, 0.02)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
      }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <Skeleton height={32} width="80%" className="mb-2" />
          <Skeleton height={14} width="60%" variant="text" />
        </div>
        <Skeleton width={32} height={32} variant="circle" />
      </div>
    </div>
  );
}

/**
 * Skeleton row for table loading.
 */
export function TableRowSkeleton({ columns = 4 }: { columns?: number }) {
  return (
    <tr>
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton height={16} width={i === 0 ? '70%' : '50%'} variant="text" />
        </td>
      ))}
    </tr>
  );
}

/**
 * Skeleton for chart loading.
 */
export function ChartSkeleton({ height = 300 }: { height?: number }) {
  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{
        background: 'rgba(255, 255, 255, 0.02)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
      }}
    >
      <div className="px-6 py-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <Skeleton height={20} width="40%" className="mb-2" />
        <Skeleton height={14} width="60%" variant="text" />
      </div>
      <div className="p-6">
        <div className="flex items-end justify-between gap-2" style={{ height }}>
          {Array.from({ length: 12 }).map((_, i) => (
            <Skeleton
              key={i}
              width="7%"
              height={`${30 + Math.random() * 60}%`}
              animation="wave"
            />
          ))}
        </div>
        <div className="flex justify-between mt-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} height={12} width={40} variant="text" />
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * Full page skeleton for initial loading.
 */
export function PageSkeleton() {
  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Metrics row */}
      <div className="grid grid-cols-4 lg:grid-cols-8 gap-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <MetricCardSkeleton key={i} />
        ))}
      </div>
      
      {/* Main chart */}
      <ChartSkeleton height={350} />
      
      {/* Secondary charts */}
      <div className="grid grid-cols-2 gap-6">
        <ChartSkeleton height={250} />
        <ChartSkeleton height={250} />
      </div>
    </div>
  );
}

export default Skeleton;

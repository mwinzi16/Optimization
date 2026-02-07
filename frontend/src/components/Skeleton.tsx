interface SkeletonProps {
  variant?: 'line' | 'card' | 'chart';
  className?: string;
}

const VARIANT_CLASSES: Record<string, string> = {
  line: 'h-4 w-full rounded',
  card: 'h-24 w-full rounded-xl',
  chart: 'h-64 w-full rounded-xl',
};

export function Skeleton({ variant = 'line', className = '' }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-bg-elevated ${VARIANT_CLASSES[variant]} ${className}`}
    />
  );
}

export function SkeletonGroup({ count = 3 }: { count?: number }) {
  return (
    <div className="flex flex-col gap-3">
      {Array.from({ length: count }, (_, i) => (
        <Skeleton key={i} variant="line" className={i === count - 1 ? 'w-2/3' : ''} />
      ))}
    </div>
  );
}

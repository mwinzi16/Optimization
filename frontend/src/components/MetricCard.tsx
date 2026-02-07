interface MetricCardProps {
  label: string;
  value: string;
  gradient: string;
}

export function MetricCard({ label, value, gradient }: MetricCardProps) {
  return (
    <div
      className="rounded-xl p-4 shadow-lg"
      style={{ background: gradient }}
    >
      <p className="metric-label">{label}</p>
      <p className="metric-value mt-1 text-white">{value}</p>
    </div>
  );
}

export default function QualityMetric({ metrics = [] }) {
  return (
    <div className="space-y-6">
      {metrics.map((metric) => (
        <Metric
          key={metric.label}
          label={metric.label}
          value={metric.value}
          variant={metric.variant}
        />
      ))}
    </div>
  );
}

function Metric({ label, value, variant = "default" }) {
  const progressColor = {
    default: "bg-[#062444]",
    success: "bg-green-500",
    warning: "bg-yellow-500",
    danger: "bg-red-500",
  };

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-medium text-slate-700">{label}</span>

        <span className="text-xs font-semibold text-slate-900">{value}%</span>
      </div>

      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
        <div
          className={`h-full rounded-full ${progressColor[variant]}`}
          style={{
            width: `${value}%`,
          }}
        />
      </div>
    </div>
  );
}

"use client";

import { TrendingUp, TrendingDown, Target, CheckSquare, RefreshCw, Award } from "lucide-react";

export default function EvaluationMetricsGrid({
  accuracy = 94,
  accuracyTrend = "+1.5% vs prev",
  precision = 92,
  recall = 89,
  recallTrend = "-1.2% vs prev",
  f1Score = 91,
  f1Trend = "+0.8% vs prev",
}) {
  const metrics = [
    {
      label: "Accuracy",
      value: `${accuracy}%`,
      trend: accuracyTrend,
      trendUp: true,
      icon: Target,
      iconColor: "text-blue-600 bg-blue-50",
    },
    {
      label: "Precision",
      value: `${precision}%`,
      trend: null,
      icon: CheckSquare,
      iconColor: "text-indigo-600 bg-indigo-50",
    },
    {
      label: "Recall",
      value: `${recall}%`,
      trend: recallTrend,
      trendUp: false,
      icon: RefreshCw,
      iconColor: "text-amber-600 bg-amber-50",
    },
    {
      label: "F1 Score",
      value: `${f1Score}%`,
      trend: f1Trend,
      trendUp: true,
      icon: Award,
      iconColor: "text-emerald-600 bg-emerald-50",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 h-full">
      {metrics.map((m) => {
        const Icon = m.icon;
        return (
          <div
            key={m.label}
            className="bg-white rounded-2xl border border-gray-200/80 p-5 shadow-sm flex flex-col justify-between"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-500">
                {m.label}
              </span>
              <div className={`flex h-7 w-7 items-center justify-center rounded-lg ${m.iconColor}`}>
                <Icon size={15} />
              </div>
            </div>

            <div className="mt-4 flex items-baseline justify-between">
              <span className="font-mono text-3xl font-extrabold text-gray-900 tracking-tight">
                {m.value}
              </span>

              {m.trend && (
                <div
                  className={`flex items-center gap-1 text-[11px] font-mono font-bold ${
                    m.trendUp ? "text-emerald-600" : "text-amber-600"
                  }`}
                >
                  {m.trendUp ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                  <span>{m.trend}</span>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

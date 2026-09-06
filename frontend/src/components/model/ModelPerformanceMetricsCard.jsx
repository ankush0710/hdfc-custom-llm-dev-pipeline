"use client";

import { Activity, TrendingUp, Clock, Zap } from "lucide-react";

export default function ModelPerformanceMetricsCard({
  accuracy = null,
  accuracyTrend = null,
  f1Score = null,
  f1Trend = null,
  latency = null,
  throughput = null,
  lastEvaluated = "Pending evaluation",
}) {
  const displayAccuracy = accuracy || "-";
  const displayF1 = f1Score || "-";
  const isSeconds = latency && String(latency).trim().endsWith("s") && !String(latency).trim().endsWith("ms");
  const displayLatency = latency
    ? String(latency).replace(/\s*(ms|s)/i, "").trim()
    : "-";
  const latencyUnit = isSeconds ? "s" : "ms";
  const displayThroughput = throughput ? String(throughput).replace(/\s*req\/s/i, "").trim() : "-";

  return (
    <div className="bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm">
      {/* Title & Subtitle */}
      <div className="flex items-center justify-between pb-4 border-b border-gray-100 mb-5">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700">
            <Activity size={16} />
          </div>
          <h3 className="text-base font-bold text-gray-900">
            Performance Metrics
          </h3>
        </div>
        <span className="text-xs text-gray-400 font-medium">
          Last evaluated: {lastEvaluated || "Pending evaluation"}
        </span>
      </div>

      {/* 4 Metric Cards in Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Accuracy */}
        <div className="bg-[#FAFBFE] rounded-xl p-4 border border-gray-100 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-gray-400">
            <span>Accuracy</span>
            <TrendingUp size={14} className={accuracy ? "text-emerald-500" : "text-gray-300"} />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-gray-900 tracking-tight font-mono">
              {displayAccuracy}
            </span>
            {accuracyTrend && accuracy && (
              <span className="text-xs font-bold text-emerald-600 font-mono">
                {accuracyTrend}
              </span>
            )}
          </div>
        </div>

        {/* Metric 2: F1 Score */}
        <div className="bg-[#FAFBFE] rounded-xl p-4 border border-gray-100 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-gray-400">
            <span>F1 Score</span>
            <TrendingUp size={14} className={f1Score ? "text-emerald-500" : "text-gray-300"} />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-gray-900 tracking-tight font-mono">
              {displayF1}
            </span>
            {f1Trend && f1Score && (
              <span className="text-xs font-bold text-emerald-600 font-mono">
                {f1Trend}
              </span>
            )}
          </div>
        </div>

        {/* Metric 3: Latency (P95) */}
        <div className="bg-[#FAFBFE] rounded-xl p-4 border border-gray-100 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-gray-400">
            <span>Latency (P95)</span>
            <Clock size={14} className={latency ? "text-blue-500" : "text-gray-300"} />
          </div>
          <div className="mt-3 flex items-baseline gap-1">
            <span className="text-3xl font-extrabold text-gray-900 tracking-tight font-mono">
              {displayLatency}
            </span>
            {latency && <span className="text-sm font-semibold text-gray-500">{latencyUnit}</span>}
          </div>
        </div>

        {/* Metric 4: Throughput */}
        <div className="bg-[#FAFBFE] rounded-xl p-4 border border-gray-100 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-gray-400">
            <span>Throughput</span>
            <Zap size={14} className={throughput ? "text-amber-500" : "text-gray-300"} />
          </div>
          <div className="mt-3 flex items-baseline gap-1">
            <span className="text-3xl font-extrabold text-gray-900 tracking-tight font-mono">
              {displayThroughput}
            </span>
            {throughput && <span className="text-sm font-semibold text-gray-500">req/s</span>}
          </div>
        </div>
      </div>
    </div>
  );
}

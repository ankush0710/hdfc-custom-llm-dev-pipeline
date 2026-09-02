"use client";

import { useState, useMemo } from "react";
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { TrendingUp, RefreshCw } from "lucide-react";

export default function LineChart({
  data = [],
  xKey = "step",
  lines = [],
  title = "Training Performance",
  subtitle = null,
  status = null,
  runs = [],
  selectedRunId = null,
  onSelectRun = null,
  loadingRun = false,
  height = 320,
}) {
  const [range, setRange] = useState("all");

  const filteredData = useMemo(() => {
    if (!Array.isArray(data) || data.length === 0) return [];
    switch (range) {
      case "10":
        return data.slice(-10);
      case "25":
        return data.slice(-25);
      case "50":
        return data.slice(-50);
      case "all":
      default:
        return data;
    }
  }, [data, range]);

  return (
    <div className="w-full rounded-xl border border-gray-200 bg-white p-5 shadow-xs flex flex-col">
      {/* Title & Filters Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-gray-100 pb-4 mb-4 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-gray-900 font-bold text-base tracking-tight">{title}</h3>
            {status && (
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${
                  status === "COMPLETED"
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : status === "RUNNING"
                    ? "bg-blue-50 text-blue-700 border border-blue-200 animate-pulse"
                    : status === "STOPPED"
                    ? "bg-amber-50 text-amber-700 border border-amber-200"
                    : status === "FAILED"
                    ? "bg-red-50 text-red-700 border border-red-200"
                    : "bg-gray-100 text-gray-700 border border-gray-200"
                }`}
              >
                {status}
              </span>
            )}
          </div>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>
          )}
        </div>

        {/* Controls: Run Selector & Range Selector */}
        <div className="flex flex-wrap items-center gap-2.5">
          {runs && runs.length > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-500 font-medium">Run:</span>
              <select
                value={selectedRunId || ""}
                onChange={(e) => onSelectRun?.(Number(e.target.value))}
                disabled={loadingRun}
                className="rounded-lg border border-gray-300 bg-white px-2.5 py-1 text-xs font-semibold text-gray-800 outline-none focus:border-[#002B55] focus:ring-1 focus:ring-[#002B55] cursor-pointer shadow-xs disabled:opacity-60 transition-colors max-w-[240px] truncate"
              >
                {runs.map((r) => (
                  <option key={r.id} value={r.id}>
                    Run #{r.id} · {r.base_model} ({r.status || "UNKNOWN"}){r.has_telemetry ? "" : " — No Loss Data"}
                  </option>
                ))}
              </select>
            </div>
          )}

          {data.length > 10 && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-500 font-medium">Range:</span>
              <select
                value={range}
                onChange={(e) => setRange(e.target.value)}
                disabled={loadingRun}
                className="rounded-lg border border-gray-300 bg-white px-2.5 py-1 text-xs font-semibold text-gray-800 outline-none focus:border-[#002B55] focus:ring-1 focus:ring-[#002B55] cursor-pointer shadow-xs transition-colors"
              >
                <option value="all">All Steps ({data.length})</option>
                {data.length >= 50 && <option value="50">Last 50 Steps</option>}
                {data.length >= 25 && <option value="25">Last 25 Steps</option>}
                <option value="10">Last 10 Steps</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Chart Canvas */}
      {loadingRun ? (
        <div
          className="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-200 p-8 text-center"
          style={{ height: `${height}px` }}
        >
          <RefreshCw size={26} className="animate-spin text-[#002B55] mb-2" />
          <p className="text-xs font-semibold text-gray-700">Loading telemetry for Run #{selectedRunId}. Please wait...</p>
          <p className="text-[10px] text-gray-400 mt-0.5">Fetching step-level metrics and loss curves</p>
        </div>
      ) : filteredData.length === 0 ? (
        <div
          className="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-200 p-8 text-center"
          style={{ height: `${height}px` }}
        >
          <TrendingUp size={28} className="text-gray-300 mb-2" />
          <p className="text-xs font-semibold text-gray-600">
            {selectedRunId ? `No step-level loss telemetry recorded for Run #${selectedRunId}` : "No telemetry data points available"}
          </p>
          <p className="text-[10px] text-gray-400 mt-0.5">
            Step-level loss values will render here during or after fine-tuning execution.
          </p>
        </div>
      ) : (
        <div className="w-full min-w-0" style={{ height: `${height}px` }}>
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={height}>
            <RechartsLineChart
              data={filteredData}
              margin={{ top: 10, right: 25, left: -5, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey={xKey}
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                tickFormatter={(val) => (typeof val === "number" ? `Step ${val}` : val)}
              />
              <YAxis
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                domain={["auto", "auto"]}
                tickFormatter={(val) => (typeof val === "number" ? val.toFixed(2) : val)}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#ffffff",
                  border: "1px solid #e2e8f0",
                  borderRadius: "0.5rem",
                  boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                  fontSize: "12px",
                  padding: "8px 12px",
                }}
                labelStyle={{ color: "#0f172a", fontWeight: "600", marginBottom: "4px" }}
                formatter={(value, name) => {
                  if (typeof value === "number") {
                    if (value < 0.001) return [value.toExponential(3), name];
                    return [value.toFixed(4), name];
                  }
                  return [value, name];
                }}
                labelFormatter={(label) => (typeof label === "number" ? `Step ${label}` : label)}
              />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ color: "#64748b", fontSize: "12px", paddingTop: "8px" }}
              />
              {lines.map((line) => (
                <Line
                  key={line.dataKey}
                  type="monotone"
                  dataKey={line.dataKey}
                  name={line.label || line.dataKey}
                  stroke={line.color || "#002B55"}
                  strokeWidth={2.5}
                  dot={filteredData.length <= 25 ? { r: 3, strokeWidth: 1.5, stroke: line.color } : false}
                  activeDot={{ r: 5 }}
                />
              ))}
            </RechartsLineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

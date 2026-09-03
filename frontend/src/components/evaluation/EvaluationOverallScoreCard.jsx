"use client";

import { CheckCircle2, Award } from "lucide-react";

export default function EvaluationOverallScoreCard({
  score = null,
  status = "QUEUED",
  targetMet = null,
  threshold = null,
}) {
  const normStatus = String(status || "").toLowerCase();
  const isCompleted = normStatus === "completed" || normStatus === "passed";
  const isFailed = normStatus === "failed";
  const isRunning = normStatus === "running";

  const numScore =
    score !== null && score !== undefined
      ? typeof score === "number"
        ? score
        : parseFloat(score) || 0
      : null;
  const displayScore = numScore !== null ? `${numScore.toFixed(1)}%` : "—";

  // Calculate SVG stroke circle parameters
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset =
    numScore !== null
      ? circumference - (numScore / 100) * circumference
      : circumference;

  // Stroke color: failed = red (#E11D48); running = blue (#2563EB); completed = brand navy (#002B55)
  const strokeColor = isFailed ? "#E11D48" : isRunning ? "#2563EB" : "#002B55";

  return (
    <div className="h-full bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm flex flex-col justify-between">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-base font-bold text-gray-900">
            Overall Score
          </h3>
          <p className="text-xs text-gray-400 font-medium mt-0.5">
            Aggregate performance metric
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isCompleted && targetMet !== null && (
            <span
              className={`inline-flex items-center px-2 py-0.5 text-[11px] font-semibold rounded-full border ${
                targetMet
                  ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                  : "bg-amber-50 border-amber-200 text-amber-700"
              }`}
            >
              {targetMet ? "Target Met" : "Below Target"}
            </span>
          )}

          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
              isCompleted
                ? "bg-emerald-50 border border-emerald-200 text-emerald-700"
                : isFailed
                ? "bg-rose-50 border border-rose-200 text-rose-700"
                : isRunning
                ? "bg-blue-50 border border-blue-200 text-blue-700"
                : "bg-slate-100 border border-slate-200 text-slate-700"
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                isCompleted
                  ? "bg-emerald-500"
                  : isFailed
                  ? "bg-rose-500"
                  : isRunning
                  ? "bg-blue-500 animate-pulse"
                  : "bg-slate-400"
              }`}
            />
            <span>{isCompleted ? "completed" : isFailed ? "failed" : normStatus}</span>
          </span>
        </div>
      </div>

      {/* Radial / Circular Progress Gauge */}
      <div className="flex items-center justify-center my-6">
        <div className="relative flex items-center justify-center">
          <svg className="h-44 w-44 -rotate-90 transform" viewBox="0 0 160 160">
            {/* Background Track */}
            <circle
              cx="80"
              cy="80"
              r={radius}
              stroke="#F1F5F9"
              strokeWidth="12"
              fill="transparent"
            />
            {/* Progress Stroke */}
            <circle
              cx="80"
              cy="80"
              r={radius}
              stroke={strokeColor}
              strokeWidth="12"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-1000 ease-out"
            />
          </svg>

          {/* Centered Score */}
          <div className="absolute flex flex-col items-center justify-center text-center">
            <span className="font-mono text-3xl font-extrabold text-gray-900 tracking-tight">
              {displayScore}
            </span>
            <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mt-0.5">
              Score
            </span>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="rounded-xl bg-[#FAFBFE] border border-gray-100 px-4 py-2.5 flex items-center justify-between text-xs">
        <span className="text-gray-500 font-medium">Quality Target</span>
        <span className="font-mono font-bold text-gray-900">
          {threshold != null
            ? `\u2265 ${Number(threshold).toFixed(1)}%`
            : targetMet !== null
            ? targetMet
              ? "Target Met"
              : "Below Target"
            : "—"}
        </span>
      </div>
    </div>
  );
}

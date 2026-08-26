"use client";

import { Clock, CheckCircle2, AlertCircle, RefreshCcw } from "lucide-react";

export default function TrainingProgressCard({
  progress = 0,
  status = "RUNNING",
  epochs = 3,
  currentStep = 0,
  totalSteps = 3000,
  startedAt = null,
  completedAt = null,
}) {
  const isRunning = status === "RUNNING";
  const isCompleted = status === "COMPLETED";
  const isFailed = status === "FAILED";
  const isQueued = status === "QUEUED";
  const isCreated = status === "CREATED";

  const numProgress =
    typeof progress === "number"
      ? Math.min(100, Math.max(0, Math.round(progress)))
      : isCompleted
      ? 100
      : 0;

  // Calculate estimated time or duration
  const getDurationText = () => {
    if (isCompleted && startedAt && completedAt) {
      const diffMs = new Date(completedAt) - new Date(startedAt);
      const mins = Math.max(1, Math.round(diffMs / 60000));
      return `Completed in ${mins}m`;
    }
    if (isRunning && numProgress > 0) {
      const remainingPct = 100 - numProgress;
      const estimatedMins = Math.max(1, Math.round((remainingPct / numProgress) * 15));
      return `~${estimatedMins}m remaining`;
    }
    if (isQueued || isCreated) {
      return "Waiting to start";
    }
    return "-";
  };

  const currentEpoch = Math.min(
    epochs,
    Math.max(1, Math.ceil((Math.max(1, numProgress) / 100) * epochs))
  );

  const barColor = isFailed
    ? "bg-rose-500"
    : isCompleted
    ? "bg-emerald-600"
    : isRunning
    ? "bg-[#002B55]"
    : "bg-gray-300";

  return (
    <div className="h-full bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm flex flex-col justify-between">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-gray-500">
          Training Progress
        </span>
        <div className="flex items-center gap-1.5 text-xs text-gray-500 font-medium bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200/60">
          <Clock size={13} className="text-blue-600" />
          <span>{getDurationText()}</span>
        </div>
      </div>

      {/* Progress Value & Status */}
      <div className="my-4">
        <div className="flex items-baseline justify-between">
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">
            {numProgress}% <span className="text-base font-semibold text-gray-500">Complete</span>
          </h2>
          <span className="text-xs font-mono font-semibold text-gray-700 bg-slate-100 px-2 py-0.5 rounded">
            Epoch {currentEpoch}/{epochs}
          </span>
        </div>

        {/* High-visibility Progress Bar */}
        <div className="mt-3.5 h-2.5 w-full bg-gray-100 rounded-full overflow-hidden p-0.5 border border-gray-200/50">
          <div
            className={`h-full rounded-full transition-all duration-700 ${barColor} ${
              isRunning ? "animate-pulse" : ""
            }`}
            style={{ width: `${Math.max(isRunning && numProgress === 0 ? 5 : 0, numProgress)}%` }}
          />
        </div>
      </div>

      {/* Step Counter Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500 pt-2.5 border-t border-gray-100">
        <span className="font-mono font-medium text-gray-600">
          Step {currentStep.toLocaleString()} / {totalSteps.toLocaleString()}
        </span>
        <span className="font-semibold text-gray-700 capitalize">
          Status: {status.toLowerCase()}
        </span>
      </div>
    </div>
  );
}

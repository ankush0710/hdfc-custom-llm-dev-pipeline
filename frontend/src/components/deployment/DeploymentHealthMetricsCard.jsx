"use client";

import { HeartPulse, Activity, Clock } from "lucide-react";

export default function DeploymentHealthMetricsCard({
  status = "ACTIVE",
  lastRequestTime = "18:03 (TODAY)",
}) {
  const isHealthy = String(status).toUpperCase() === "ACTIVE";

  return (
    <div className="h-full bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm flex flex-col justify-between">
      {/* Title */}
      <div className="flex items-center gap-2 mb-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-rose-50 text-rose-600">
          <HeartPulse size={16} />
        </div>
        <h3 className="text-base font-bold text-gray-900">
          Health Metrics
        </h3>
      </div>

      <div className="space-y-4">
        {/* Status Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
              API Status
            </span>
            <div className="flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${isHealthy ? "bg-emerald-500" : "bg-slate-400"}`} />
              <span className={`text-sm font-bold ${isHealthy ? "text-emerald-700" : "text-slate-600"}`}>
                {isHealthy ? "Healthy" : "Offline"}
              </span>
            </div>
          </div>

          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
              Model Status
            </span>
            <p className="text-sm font-bold text-gray-900 font-mono">
              {isHealthy ? "Loaded" : "Unloaded"}
            </p>
          </div>
        </div>

        {/* Last Request */}
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
            Last Request
          </span>
          <div className="rounded-xl bg-[#FAFBFE] border border-gray-100 px-3.5 py-2 flex items-center justify-between">
            <span className="font-mono text-xs font-semibold text-gray-700">
              {lastRequestTime}
            </span>
            <Clock size={14} className="text-gray-400" />
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import { CheckCircle2, ShieldCheck, Activity, XCircle } from "lucide-react";

export default function DeploymentRuntimeStatusCard({
  status = "ACTIVE",
  modelLoaded = true,
  adapterLoaded = true,
  inferenceReady = true,
}) {
  const isHealthy = String(status).toUpperCase() === "ACTIVE";

  const checklist = [
    { label: "Model Loaded", ready: isHealthy && modelLoaded },
    { label: "Adapter Loaded", ready: isHealthy && adapterLoaded },
    { label: "Inference Ready", ready: isHealthy && inferenceReady },
  ];

  return (
    <div className="h-full bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm flex flex-col justify-between">
      {/* Title */}
      <div className="flex items-center gap-2 mb-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700">
          <Activity size={16} />
        </div>
        <h3 className="text-base font-bold text-gray-900">
          Runtime Status
        </h3>
      </div>

      {/* Checklist items matching Screenshot */}
      <div className="space-y-3">
        {checklist.map((item, idx) => (
          <div
            key={idx}
            className="flex items-center justify-between p-2.5 rounded-xl bg-[#FAFBFE] border border-gray-100"
          >
            <span className="text-xs font-semibold text-gray-800">
              {item.label}
            </span>
            {item.ready ? (
              <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                <CheckCircle2 size={14} />
              </div>
            ) : (
              <div className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                <XCircle size={14} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

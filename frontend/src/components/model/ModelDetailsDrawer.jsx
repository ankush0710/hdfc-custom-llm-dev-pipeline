"use client";

import { useState } from "react";
import { X, Box, Cpu, HardDrive, Sparkles, Check, Clock, ShieldCheck, Layers, ExternalLink } from "lucide-react";
import { updateModelStatus } from "@/app/services/modelService/modelServices";
import { useAuth } from "@/app/context/AuthContext";
import { toast } from "sonner";

export default function ModelDetailsDrawer({ isOpen, onClose, model, onStatusUpdated }) {
  const { hasRole } = useAuth();
  const [updating, setUpdating] = useState(false);

  if (!isOpen || !model) return null;

  const canUpdateStatus = hasRole("ADMIN", "REVIEWER");

  const handleStatusChange = async (newStatus) => {
    try {
      setUpdating(true);
      await updateModelStatus(model.id, newStatus);
      toast.success(`Model status updated to ${newStatus}`);
      if (onStatusUpdated) onStatusUpdated();
      onClose();
    } catch (err) {
      console.error("Failed to update status:", err);
      toast.error("Failed to update model status.");
    } finally {
      setUpdating(false);
    }
  };

  const verDisplay = model.version?.startsWith("v") ? model.version : `v${model.version || "1.0.0"}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-[#FAFBFE]">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#002B55]/10 text-[#002B55]">
              <Box size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-gray-900">
                  {model.model_name}
                </h2>
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-100 font-semibold text-slate-700">
                  {verDisplay}
                </span>
              </div>
              <p className="text-xs text-gray-500">
                Registered on {model.created_at ? new Date(model.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "Recently"}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4 text-xs">
          {/* Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200/60">
              <span className="text-[10px] font-bold uppercase text-gray-500 tracking-wider block mb-1">
                Base Model
              </span>
              <span className="font-bold text-gray-900 text-sm">
                {model.base_model}
              </span>
            </div>

            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200/60">
              <span className="text-[10px] font-bold uppercase text-gray-500 tracking-wider block mb-1">
                Status
              </span>
              <span className="font-bold text-emerald-700 text-sm uppercase">
                {model.status}
              </span>
            </div>

            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200/60">
              <span className="text-[10px] font-bold uppercase text-gray-500 tracking-wider block mb-1">
                Accuracy Benchmark
              </span>
              <span className="font-mono font-bold text-blue-700 text-sm">
                {model.accuracy || "—"}
              </span>
            </div>

            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200/60">
              <span className="text-[10px] font-bold uppercase text-gray-500 tracking-wider block mb-1">
                Avg. Latency
              </span>
              <span className="font-mono font-bold text-slate-800 text-sm">
                {model.latency || "—"}
              </span>
            </div>

            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200/60">
              <span className="text-[10px] font-bold uppercase text-gray-500 tracking-wider block mb-1">
                Throughput
              </span>
              <span className="font-mono font-bold text-amber-700 text-sm">
                {model.throughput || "—"}
              </span>
            </div>
          </div>

          {/* Artifact Storage Path */}
          <div className="rounded-xl border border-gray-200 p-3.5 bg-[#FAFBFE]">
            <span className="text-[11px] font-semibold text-gray-600 block mb-1">
              Artifact / Weights Storage Path:
            </span>
            <span className="font-mono text-xs text-gray-800 break-all bg-white p-2 rounded border border-gray-200 block">
              {model.artifact_path || model.adapter_path || `ai/artifacts/runs/run_${model.id}/adapter_model.safetensors`}
            </span>
          </div>

          {/* Linked Training Job */}
          {model.training_job_id && (
            <div className="flex items-center justify-between p-3 rounded-xl bg-blue-50/50 border border-blue-100">
              <div className="flex items-center gap-2">
                <Layers size={15} className="text-blue-600" />
                <span className="font-semibold text-blue-900">
                  Linked Training Job #{model.training_job_id}
                </span>
              </div>
              <span className="text-blue-700 font-mono">Automated Pipeline</span>
            </div>
          )}

          {/* Status Actions */}
          {canUpdateStatus && (
            <div className="pt-3 border-t border-gray-100">
              <span className="text-[11px] font-semibold text-gray-600 block mb-2">
                Update Deployment State (Admin / Reviewer):
              </span>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={updating || model.status === "ACTIVE"}
                  onClick={() => handleStatusChange("ACTIVE")}
                  className="px-3 py-1.5 rounded-lg border border-emerald-300 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-semibold text-xs transition disabled:opacity-50 cursor-pointer"
                >
                  Set Active / Deployed
                </button>
                <button
                  type="button"
                  disabled={updating || model.status === "ARCHIVED"}
                  onClick={() => handleStatusChange("ARCHIVED")}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition disabled:opacity-50 cursor-pointer"
                >
                  Archive Model
                </button>
                <button
                  type="button"
                  disabled={updating || model.status === "READY"}
                  onClick={() => handleStatusChange("READY")}
                  className="px-3 py-1.5 rounded-lg border border-blue-300 bg-blue-50 hover:bg-blue-100 text-blue-800 font-semibold text-xs transition disabled:opacity-50 cursor-pointer"
                >
                  Set Ready
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end px-6 py-3.5 border-t border-gray-100 bg-[#FAFBFE]">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-200 bg-gray-100 rounded-lg transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

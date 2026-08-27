"use client";

import { useState } from "react";
import { Info, Copy, Check, Server, Globe } from "lucide-react";
import { toast } from "sonner";

export default function DeploymentOverviewCard({
  modelVersion = "HDFC-Qwen v2",
  environment = "Production",
  status = "ACTIVE",
  endpointUrl = "https://inference.capital.ai/v1/models/hdfc-qwen-v2/generate",
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(endpointUrl);
    setCopied(true);
    toast.success("Endpoint URL copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  const isActive = String(status).toUpperCase() === "ACTIVE";

  return (
    <div className="h-full bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm flex flex-col justify-between">
      {/* Title */}
      <div className="flex items-center gap-2 mb-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-50 text-[#002B55]">
          <Info size={16} />
        </div>
        <h3 className="text-base font-bold text-gray-900">
          Overview
        </h3>
      </div>

      <div className="space-y-4">
        {/* 3 Columns: Model Version, Environment, Status */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
              Model Version
            </span>
            <p className="text-sm font-bold text-gray-900 truncate">
              {modelVersion}
            </p>
          </div>

          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
              Environment
            </span>
            <span className="inline-flex rounded-md bg-blue-50 border border-blue-200 px-2.5 py-0.5 text-xs font-semibold text-blue-700">
              {environment}
            </span>
          </div>

          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
              Status
            </span>
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                isActive
                  ? "bg-emerald-50 border border-emerald-200 text-emerald-700"
                  : "bg-slate-100 border border-slate-200 text-slate-600"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  isActive ? "bg-emerald-500" : "bg-slate-400"
                }`}
              />
              <span>{isActive ? "Active" : status}</span>
            </span>
          </div>
        </div>

        {/* Endpoint URL with copy button */}
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
            Endpoint URL
          </span>
          <div className="flex items-center justify-between rounded-xl bg-slate-50 border border-slate-200 px-3.5 py-2">
            <span className="font-mono text-xs text-gray-600 truncate max-w-sm lg:max-w-md" title={endpointUrl}>
              {endpointUrl}
            </span>
            <button
              type="button"
              onClick={handleCopy}
              className="p-1 rounded-md text-gray-500 hover:text-gray-900 hover:bg-slate-200 transition cursor-pointer shrink-0 ml-2"
              title="Copy endpoint"
            >
              {copied ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

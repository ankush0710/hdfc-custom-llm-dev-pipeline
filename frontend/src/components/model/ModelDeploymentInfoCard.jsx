"use client";

import { useState } from "react";
import { Server, Copy, Check, ExternalLink } from "lucide-react";
import { toast } from "sonner";

export default function ModelDeploymentInfoCard({
  environment = "Production",
  instanceType = "ml.g5.2xlarge",
  endpointUrl = "https://api.forge.hdfc.com/v1/models/banking-v1-2",
  status = "ACTIVE",
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(endpointUrl);
    setCopied(true);
    toast.success("Endpoint URL copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="h-full bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm flex flex-col justify-between">
      {/* Title */}
      <div className="flex items-center gap-2 mb-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-50 text-indigo-700">
          <Server size={16} />
        </div>
        <h3 className="text-base font-bold text-gray-900">
          Deployment Info
        </h3>
      </div>

      <div className="space-y-3">
        {/* Environment & Instance */}
        <div className="flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
              Environment
            </span>
            <span className="inline-flex rounded-md bg-blue-50 border border-blue-200/80 px-2.5 py-0.5 text-xs font-semibold text-blue-700">
              {environment}
            </span>
          </div>

          <div className="text-right">
            <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
              Instance Type
            </span>
            <span className="text-xs font-mono font-semibold text-gray-800">
              {instanceType}
            </span>
          </div>
        </div>

        {/* Endpoint URL with copy button */}
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
            Endpoint URL
          </span>
          <div className="flex items-center justify-between rounded-xl bg-slate-50 border border-slate-200 px-3 py-1.5">
            <span className="font-mono text-xs text-gray-600 truncate max-w-[280px]" title={endpointUrl}>
              {endpointUrl}
            </span>
            <button
              type="button"
              onClick={handleCopy}
              className="p-1 rounded-md text-gray-500 hover:text-gray-900 hover:bg-slate-200 transition cursor-pointer"
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

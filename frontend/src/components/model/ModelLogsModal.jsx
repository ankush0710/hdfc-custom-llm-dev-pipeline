"use client";

import { useState } from "react";
import { Terminal, Copy, Check, X } from "lucide-react";
import { toast } from "sonner";

export default function ModelLogsModal({ isOpen, onClose, modelName = "Model", logs = [] }) {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleCopy = () => {
    if (!logs || logs.length === 0) return;
    navigator.clipboard.writeText(logs.join("\n"));
    setCopied(true);
    toast.success("Logs copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl bg-[#0B132B] text-slate-200 rounded-2xl border border-slate-800 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-[#070D1F] border-b border-slate-800/80">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-full bg-red-500/80 inline-block"></span>
              <span className="h-3 w-3 rounded-full bg-amber-500/80 inline-block"></span>
              <span className="h-3 w-3 rounded-full bg-emerald-500/80 inline-block"></span>
            </div>
            <div className="flex items-center gap-1.5 ml-2 font-mono text-xs font-semibold text-slate-300">
              <Terminal size={14} className="text-blue-400" />
              <span>LOGS: {modelName}</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1 px-2.5 py-1 text-xs rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
            >
              {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>

            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition cursor-pointer"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Log content */}
        <div className="p-6 font-mono text-xs overflow-y-auto space-y-2 leading-relaxed selection:bg-blue-600 selection:text-white">
          {logs && logs.length > 0 ? (
            logs.map((line, idx) => (
              <div key={idx} className="text-slate-300">
                {line}
              </div>
            ))
          ) : (
            <div className="text-slate-500 italic py-6 text-center">
              No logs recorded for this model yet.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end px-6 py-3 bg-[#070D1F] border-t border-slate-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-800 rounded-lg transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

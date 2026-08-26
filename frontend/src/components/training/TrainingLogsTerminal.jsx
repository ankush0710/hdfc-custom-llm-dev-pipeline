"use client";

import { useState } from "react";
import { Terminal, Copy, Check, RefreshCw } from "lucide-react";
import { toast } from "sonner";

export default function TrainingLogsTerminal({ logs = [], isLive = false, onRefresh = null }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!logs || logs.length === 0) return;
    const text = logs.join("\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success("Logs copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-[#0B132B] text-slate-200 rounded-2xl border border-slate-800 shadow-sm flex flex-col h-full overflow-hidden">
      {/* Terminal Titlebar */}
      <div className="flex items-center justify-between px-5 py-3.5 bg-[#070D1F] border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full bg-red-500/80 inline-block"></span>
            <span className="h-3 w-3 rounded-full bg-amber-500/80 inline-block"></span>
            <span className="h-3 w-3 rounded-full bg-emerald-500/80 inline-block"></span>
          </div>
          <div className="flex items-center gap-1.5 ml-2 font-mono text-xs font-semibold text-slate-300">
            <Terminal size={14} className="text-blue-400" />
            <span>STD_OUT.LOG</span>
          </div>
          {isLive && (
            <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/50 px-2 py-0.5 rounded-full">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />
              STREAMING
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition"
              title="Refresh logs"
            >
              <RefreshCw size={13} />
            </button>
          )}

          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1 px-2.5 py-1 text-xs rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Copy logs"
          >
            {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>
        </div>
      </div>

      {/* Terminal Content Body */}
      <div className="p-4 font-mono text-xs overflow-y-auto max-h-[320px] space-y-1.5 leading-relaxed selection:bg-blue-600 selection:text-white">
        {logs.length > 0 ? (
          logs.map((line, idx) => {
            const isError = line.includes("[ERROR]") || line.toLowerCase().includes("failed");
            const isWarning = line.includes("[WARNING]");
            const isStep = line.includes("Step");
            const isSuccess = line.includes("completed") || line.includes("READY");

            return (
              <div
                key={idx}
                className={`transition-colors ${
                  isError
                    ? "text-rose-400 font-semibold"
                    : isWarning
                    ? "text-amber-400"
                    : isSuccess
                    ? "text-emerald-300 font-medium"
                    : isStep
                    ? "text-sky-300"
                    : "text-slate-300"
                }`}
              >
                {line}
              </div>
            );
          })
        ) : (
          <div className="text-slate-500 italic py-6 text-center">
            No stdout logs generated yet. Launch training to start capturing execution logs.
          </div>
        )}
      </div>
    </div>
  );
}

"use client";

import { X, Download, FileCode, HardDrive, Sparkles, Check, Copy } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export default function TrainingArtifactsDrawer({
  isOpen,
  onClose,
  displayId = "TRN-2024-001",
  artifacts = [],
}) {
  const [copiedPath, setCopiedPath] = useState(null);

  if (!isOpen) return null;

  const handleCopyPath = (path) => {
    navigator.clipboard.writeText(path);
    setCopiedPath(path);
    toast.success("Path copied to clipboard");
    setTimeout(() => setCopiedPath(null), 2000);
  };

  const formatSize = (sizeKb) => {
    if (!sizeKb && sizeKb !== 0) return "-";
    if (sizeKb >= 1024 * 1024) {
      return `${(sizeKb / (1024 * 1024)).toFixed(1)} GB`;
    }
    if (sizeKb >= 1024) {
      return `${(sizeKb / 1024).toFixed(1)} MB`;
    }
    return `${sizeKb.toFixed(1)} KB`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-[#FAFBFE]">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
              <HardDrive size={18} />
            </div>
            <div>
              <h2 className="text-base font-bold text-gray-900">
                Training Artifacts: {displayId}
              </h2>
              <p className="text-xs text-gray-500">
                Generated files and models from the fine-tuning run.
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

        {/* Artifacts Table */}
        <div className="p-6">
          <div className="rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#FAFBFE] border-b border-gray-200">
                  <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500">
                    Artifact Name
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500">
                    Path / File
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500">
                    Size
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500 text-right">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-xs">
                {artifacts.length > 0 ? (
                  artifacts.map((art, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition">
                      <td className="px-4 py-3.5 font-semibold text-gray-900 flex items-center gap-2">
                        <FileCode size={15} className="text-blue-600 shrink-0" />
                        <span>{art.name}</span>
                      </td>
                      <td className="px-4 py-3.5 font-mono text-gray-600 max-w-[200px] truncate" title={art.path}>
                        {art.path}
                      </td>
                      <td className="px-4 py-3.5 font-mono font-medium text-gray-700">
                        {formatSize(art.size_kb)}
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <button
                          type="button"
                          onClick={() => handleCopyPath(art.path)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded transition"
                          title="Copy file path"
                        >
                          {copiedPath === art.path ? (
                            <Check size={12} className="text-emerald-600" />
                          ) : (
                            <Copy size={12} />
                          )}
                          <span>Copy Path</span>
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                      No artifacts generated yet. Artifacts are produced upon successful training completion.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
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

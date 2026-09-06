import Link from "next/link";
import { Box, Cpu, Sparkles, Binary, Check, ChevronRight } from "lucide-react";

// Helper to format relative time
const formatRelativeTime = (dateStr) => {
  if (!dateStr) return "Just now";
  const date = new Date(dateStr);
  const now = new Date();
  const diffSec = Math.floor((now - date) / 1000);

  if (diffSec < 60) return "Just now";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin} min${diffMin > 1 ? "s" : ""} ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours} hr${diffHours > 1 ? "s" : ""} ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 30) return `${diffDays} days ago`;

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

export const createModelColumns = ({ onViewDetails } = {}) => [
  {
    key: "model_name",
    label: "MODEL NAME",
    render: (row) => {
      const isClassifier = row.model_name?.toLowerCase().includes("risk") || row.model_name?.toLowerCase().includes("fraud") || row.model_name?.toLowerCase().includes("class");
      const isEmbedding = row.model_name?.toLowerCase().includes("embed") || row.base_model?.toLowerCase().includes("bge");
      const modelType = isEmbedding
        ? "Type: Embedding"
        : isClassifier
        ? "Type: Classifier"
        : "Type: LLM (Generative)";

      const Icon = isEmbedding ? Binary : isClassifier ? Sparkles : Cpu;
      const modelId = row.id ?? row.model_id ?? 1;

      return (
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
            <Icon size={16} />
          </div>
          <div>
            <Link
              href={`/model/${modelId}`}
              className="font-bold text-xs text-gray-900 block hover:text-[#002B55] transition"
            >
              {row.model_name}
            </Link>
            <span className="text-[11px] text-gray-500 font-normal">
              {modelType}
            </span>
          </div>
        </div>
      );
    },
  },
  {
    key: "version",
    label: "VERSION",
    render: (row) => {
      const ver = row.version?.startsWith("v") ? row.version : `v${row.version || "1.0.0"}`;
      return (
        <span className="inline-flex rounded-md bg-slate-100 px-2 py-0.5 text-xs font-mono font-medium text-slate-700">
          {ver}
        </span>
      );
    },
  },
  {
    key: "accuracy",
    label: "ACCURACY",
    render: (row) => {
      const accuracy = row.accuracy || "—";

      return (
        <span className="font-mono font-bold text-xs text-gray-800">
          {accuracy}
        </span>
      );
    },
  },
  {
    key: "latency",
    label: "AVG. LATENCY",
    render: (row) => {
      const latency = row.latency || "—";
      return (
        <span className="font-mono font-bold text-xs text-gray-800">
          {latency}
        </span>
      );
    },
  },
  {
    key: "throughput",
    label: "THROUGHPUT",
    render: (row) => {
      const throughput = row.throughput || "—";
      return (
        <span className="font-mono font-bold text-xs text-gray-800">
          {throughput}
        </span>
      );
    },
  },
  {
    key: "status",
    label: "STATUS",
    render: (row) => {
      const rawStatus = (row.status || "READY").toUpperCase();

      if (rawStatus === "ACTIVE" || rawStatus === "APPROVED" || rawStatus === "READY" || rawStatus === "DEPLOYED") {
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 border border-emerald-200/80 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-700">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            <span>Active</span>
          </span>
        );
      }

      if (rawStatus === "TRAINING" || rawStatus === "EVALUATING") {
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 border border-blue-200/80 px-2.5 py-0.5 text-[11px] font-semibold text-blue-700">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse" />
            <span>Training</span>
          </span>
        );
      }

      if (rawStatus === "ARCHIVED" || rawStatus === "DEPRECATED" || rawStatus === "REJECTED") {
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 border border-slate-200 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600">
            <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
            <span>Archived</span>
          </span>
        );
      }

      // Default: Created
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 border border-amber-200 px-2.5 py-0.5 text-[11px] font-semibold text-amber-700">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
          <span>Created</span>
        </span>
      );
    },
  },
  {
    key: "updated_at",
    label: "LAST UPDATED",
    render: (row) => (
      <span className="text-xs text-gray-500 font-medium">
        {formatRelativeTime(row.updated_at || row.created_at)}
      </span>
    ),
  },
  {
    key: "actions",
    label: "ACTIONS",
    align: "right",
    render: (row) => {
      const modelId = row.id ?? row.model_id ?? 1;
      return (
        <div className="flex items-center justify-end gap-2">
          {onViewDetails && (
            <button
              type="button"
              onClick={() => onViewDetails(row)}
              className="text-xs font-semibold text-slate-600 hover:text-[#002B55] px-2 py-1 rounded hover:bg-slate-100 transition"
            >
              Drawer
            </button>
          )}
          <Link
            href={`/model/${modelId}`}
            className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 transition cursor-pointer"
          >
            <span>View Details</span>
            <ChevronRight size={13} />
          </Link>
        </div>
      );
    },
  },
];

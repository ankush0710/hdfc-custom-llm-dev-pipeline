import Link from "next/link";
import {
  Square,
  BarChart2,
  FileText,
  XCircle,
  Play,
  Check,
  X,
  Eye,
} from "lucide-react";

export const createTrainingColumns = ({ onStartRun, onStopRun, onViewMetrics, onViewLogs, onCancelRun } = {}) => [
  {
    key: "id",
    label: "Training ID",
    render: (row) => {
      const formattedId = row.display_id || (row.id ? `trn-${String(row.id).padStart(4, "0").toLowerCase()}` : "trn-xxxx");
      return (
        <span className="font-mono text-xs font-semibold text-slate-700">
          {formattedId}
        </span>
      );
    },
  },
  {
    key: "base_model",
    label: "Base Model",
    render: (row) => (
      <span className="text-xs font-semibold text-gray-900">
        {row.base_model || "Qwen/Qwen3-0.6B"}
      </span>
    ),
  },
  {
    key: "dataset",
    label: "Dataset",
    render: (row) => {
      const datasetName = row.dataset_name || (row.dataset_version_id ? `Dataset_v${row.dataset_version_id}` : "Q3_Financial_Transcripts");
      return (
        <span className="font-mono text-xs text-gray-600">
          {datasetName}
        </span>
      );
    },
  },
  {
    key: "status",
    label: "Status",
    render: (row) => {
      const rawStatus = (row.status || "QUEUED").toUpperCase();

      if (rawStatus === "RUNNING") {
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 border border-blue-200/80 px-2.5 py-1 text-xs font-medium text-blue-700">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-600 animate-pulse" />
            <span>Running</span>
          </span>
        );
      }

      if (rawStatus === "COMPLETED") {
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 border border-emerald-200/80 px-2.5 py-1 text-xs font-medium text-emerald-700">
            <Check size={12} strokeWidth={2.5} />
            <span>Completed</span>
          </span>
        );
      }

      if (rawStatus === "FAILED") {
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 border border-rose-200/80 px-2.5 py-1 text-xs font-medium text-rose-700">
            <X size={12} strokeWidth={2.5} />
            <span>Failed</span>
          </span>
        );
      }

      // Default: QUEUED / CREATED
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-sky-50 border border-sky-200/80 px-2.5 py-1 text-xs font-medium text-sky-700">
          <span className="h-1.5 w-1.5 rounded-full bg-sky-500" />
          <span>{rawStatus === "CREATED" ? "Created" : "Queued"}</span>
        </span>
      );
    },
  },
  {
    key: "progress",
    label: "Progress",
    render: (row) => {
      const rawStatus = (row.status || "CREATED").toUpperCase();
      const numProgress =
        typeof row.progress === "number"
          ? Math.max(0, Math.min(100, Math.round(row.progress)))
          : typeof row.job_progress === "number"
            ? Math.max(0, Math.min(100, Math.round(row.job_progress)))
            : rawStatus === "COMPLETED"
              ? 100
              : 0;

      const isRunning = rawStatus === "RUNNING";
      const isCompleted = rawStatus === "COMPLETED";
      const isFailed = rawStatus === "FAILED";
      const isQueued = rawStatus === "QUEUED";
      const isCreated = rawStatus === "CREATED";

      const barColor = isFailed
        ? "bg-rose-500"
        : isCompleted
          ? "bg-emerald-600"
          : isRunning
            ? "bg-[#002B55]"
            : "bg-gray-300";

      return (
        <div className="flex items-center gap-3 min-w-[140px] max-w-[210px]">
          {/* Progress bar track */}
          <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden p-0.5 border border-gray-200/50">
            <div
              className={`h-full rounded-full transition-all duration-500 ${barColor} ${isRunning ? "animate-pulse" : ""
                }`}
              style={{ width: `${Math.max(isRunning && numProgress === 0 ? 5 : 0, numProgress)}%` }}
            />
          </div>

          {/* Progress label */}
          <div className="shrink-0 text-right min-w-[45px]">
            {isFailed ? (
              <span className="text-[11px] font-semibold text-rose-600 truncate block max-w-[90px]" title={row.error_message || "Failed"}>
                {row.error_message ? "Error" : "Failed"}
              </span>
            ) : isQueued ? (
              <span className="text-[11px] font-semibold text-sky-600 font-mono">
                Queued
              </span>
            ) : isCreated ? (
              <span className="text-[11px] font-medium text-gray-500 font-mono">
                Ready
              </span>
            ) : (
              <span className="text-xs font-mono font-bold text-gray-800">
                {numProgress}%
              </span>
            )}
          </div>
        </div>
      );
    },
  },
  {
    key: "actions",
    label: "Actions",
    align: "right",
    render: (row) => {
      const rawStatus = (row.status || "QUEUED").toUpperCase();

      return (
        <div className="flex items-center justify-end gap-2">
          {rawStatus === "CREATED" && onStartRun && (
            <button
              type="button"
              onClick={() => onStartRun(row)}
              className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 px-2 py-0.5 rounded transition-colors"
              title="Start Run"
            >
              <Play size={11} className="fill-emerald-700" />
              <span>Start</span>
            </button>
          )}

          {rawStatus === "RUNNING" && (
            <button
              type="button"
              onClick={() => onStopRun && onStopRun(row)}
              className="p-1 rounded-md text-red-500 hover:text-red-700 hover:bg-red-50 transition"
              title="Stop Training"
            >
              <div className="h-4 w-4 rounded-full border-2 border-red-500 flex items-center justify-center">
                <div className="h-1.5 w-1.5 rounded-full bg-red-500" />
              </div>
            </button>
          )}

          {rawStatus === "COMPLETED" && (
            <button
              type="button"
              onClick={() => onViewMetrics && onViewMetrics(row)}
              className="p-1 rounded-md text-gray-500 hover:text-blue-700 hover:bg-blue-50 transition"
              title="View Metrics"
            >
              <BarChart2 size={16} />
            </button>
          )}

          {rawStatus === "QUEUED" && (
            <button
              type="button"
              onClick={() => onCancelRun && onCancelRun(row)}
              className="p-1 rounded-md text-gray-400 hover:text-rose-600 hover:bg-rose-50 transition"
              title="Cancel Queue"
            >
              <XCircle size={16} />
            </button>
          )}
        </div>
      );
    },
  },
];

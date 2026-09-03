import Link from "next/link";
import { Cpu, ChevronRight, Activity, Database, CheckCircle2, XCircle, Clock, Loader2 } from "lucide-react";

export const createEvaluationColumns = ({ onStartEval } = {}) => [
  {
    key: "display_id",
    label: "EVALUATION ID",
    render: (row) => {
      const evalId = row.evaluation_id ?? row.id ?? 1;
      const displayId = row.display_id || `EV-${String(evalId).padStart(3, "0")}`;
      return (
        <Link
          href={`/evaluation/${evalId}`}
          className="font-mono text-xs font-bold text-blue-700 hover:text-blue-900 hover:underline transition"
        >
          {displayId}
        </Link>
      );
    },
  },
  {
    key: "model",
    label: "MODEL",
    render: (row) => {
      const evalId = row.evaluation_id ?? row.id ?? 1;
      return (
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-[#002B55]">
            <Cpu size={14} />
          </div>
          <div>
            <Link
              href={`/evaluation/${evalId}`}
              className="font-bold text-xs text-gray-900 block hover:text-blue-700 transition"
            >
              {row.model_name || `Model-${row.model_id}`}
            </Link>
            <span className="text-[11px] text-gray-400 font-normal">
              {row.base_model || "Qwen/Qwen3-0.6B"}
            </span>
          </div>
        </div>
      );
    },
  },
  {
    key: "dataset",
    label: "DATASET",
    render: (row) => (
      <div className="flex items-center gap-1.5">
        <span className="inline-flex rounded-md bg-slate-100 px-2 py-0.5 text-xs font-mono font-medium text-slate-700">
          {row.dataset_name || `Dataset-${row.test_dataset_id}`}
        </span>
        {row.dataset_version && (
          <span className="text-[10px] text-gray-400 font-mono">
            {row.dataset_version}
          </span>
        )}
      </div>
    ),
  },
  {
    key: "score",
    label: "SCORE",
    render: (row) => {
      const scoreStr = row.score || "-";
      const scoreVal = row.score_value;
      const isHigh = scoreVal && scoreVal >= 85;
      const isMedium = scoreVal && scoreVal >= 70 && scoreVal < 85;

      return (
        <span
          className={`font-mono text-xs font-bold ${
            isHigh
              ? "text-emerald-700"
              : isMedium
              ? "text-blue-700"
              : scoreVal
              ? "text-amber-700"
              : "text-gray-400"
          }`}
        >
          {scoreStr}
        </span>
      );
    },
  },
  {
    key: "status",
    label: "STATUS",
    render: (row) => {
      const status = (row.evaluation_status || "QUEUED").toUpperCase();

      if (status === "COMPLETED" || status === "PASSED") {
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 border border-emerald-200/80 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-700">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            <span>completed</span>
          </span>
        );
      }

      if (status === "FAILED") {
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-50 border border-rose-200 px-2.5 py-0.5 text-[11px] font-semibold text-rose-700">
            <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
            <span>failed</span>
          </span>
        );
      }

      if (status === "RUNNING") {
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 border border-blue-200 px-2.5 py-0.5 text-[11px] font-semibold text-blue-700">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse" />
            <span>running</span>
          </span>
        );
      }

      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 border border-slate-200 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600">
          <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
          <span>queued</span>
        </span>
      );
    },
  },
  {
    key: "actions",
    label: "ACTIONS",
    align: "right",
    render: (row) => {
      const evalId = row.evaluation_id ?? row.id ?? 1;
      return (
        <Link
          href={`/evaluation/${evalId}`}
          className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 transition cursor-pointer"
        >
          <span>View Details</span>
          <ChevronRight size={13} />
        </Link>
      );
    },
  },
];

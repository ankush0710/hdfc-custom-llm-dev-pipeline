import Link from "next/link";
import { Server, Eye } from "lucide-react";

// Maps backend deployment status values to UI styles
const statusStyles = {
  active: {
    bg: "bg-emerald-50 border border-emerald-200",
    text: "text-emerald-700",
    dot: "bg-emerald-500",
    label: "Active",
  },
  stopped: {
    bg: "bg-gray-100 border border-gray-200",
    text: "text-gray-600",
    dot: "bg-gray-500",
    label: "Stopped",
  },
  deployed: {
    bg: "bg-blue-50 border border-blue-200",
    text: "text-blue-700",
    dot: "bg-blue-500",
    label: "Deployed",
  },
  degraded: {
    bg: "bg-amber-50 border border-amber-200",
    text: "text-amber-700",
    dot: "bg-amber-500",
    label: "Degraded",
  },
};

const defaultStyle = {
  bg: "bg-gray-100 border border-gray-200",
  text: "text-gray-600",
  dot: "bg-gray-400",
  label: "Active",
};

export const DashboardModelColumns = [
  {
    key: "name",
    label: "Model Name",
    render: (model) => (
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-[#002B55]">
          <Server size={15} />
        </div>
        <div>
          <Link
            href={`/deployment/${model.id}`}
            className="font-bold text-xs text-gray-900 block hover:text-blue-700 transition"
          >
            {model.name || model.model_name || `Model-${model.model_id || model.id}`}
          </Link>
          <span className="text-[11px] text-gray-400 font-normal">
            {model.environment || "Production"}
          </span>
        </div>
      </div>
    ),
  },

  {
    key: "version",
    label: "Version",
    render: (model) => (
      <span className="inline-flex rounded-md bg-slate-100 px-2 py-0.5 text-xs font-mono font-medium text-slate-700">
        {model.version?.startsWith("v") ? model.version : `v${model.version || "1.0"}`}
      </span>
    ),
  },

  {
    key: "status",
    label: "Status",
    render: (model) => {
      const key = (model.status || "active").toLowerCase();
      const style = statusStyles[key] || defaultStyle;
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${style.bg} ${style.text}`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
          {style.label}
        </span>
      );
    },
  },

  {
    key: "latency",
    label: "Avg. Latency",
    render: (model) => (
      <span className="font-mono text-xs text-gray-700">
        {model.latency && model.latency !== "—" ? model.latency : "N/A"}
      </span>
    ),
  },

  {
    key: "action",
    label: "Actions",
    align: "right",
    render: (model) => (
      <Link
        href={`/deployment/${model.id}`}
        className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 transition"
      >
        <Eye size={13} />
        <span>View</span>
      </Link>
    ),
  },
];

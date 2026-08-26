import Link from "next/link";
import { Cpu, ChevronRight, Server, Globe } from "lucide-react";

export const createDeploymentColumns = () => [
  {
    key: "model_name",
    label: "MODEL NAME",
    render: (row) => {
      const formattedName = row.model_name || `Model-${row.model_id}`;
      return (
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-[#002B55]">
            <Server size={15} />
          </div>
          <div>
            <Link
              href={`/deployment/${row.id}`}
              className="font-bold text-xs text-gray-900 block hover:text-blue-700 transition"
            >
              {formattedName}
            </Link>
            <span className="text-[11px] text-gray-400 font-normal">
              {row.base_model || "Llama-3-8B"}
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
      const ver = String(row.version || "v1").startsWith("v")
        ? row.version
        : `v${row.version || "1"}`;
      return (
        <span className="inline-flex rounded-md bg-slate-100 px-2 py-0.5 text-xs font-mono font-medium text-slate-700">
          {ver}
        </span>
      );
    },
  },
  {
    key: "environment",
    label: "ENVIRONMENT",
    render: (row) => {
      const env = (row.environment || "Production").toUpperCase();
      const isProd = env === "PRODUCTION";
      const isStaging = env === "STAGING";

      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
            isProd
              ? "bg-blue-50 border border-blue-200 text-blue-700"
              : isStaging
              ? "bg-purple-50 border border-purple-200 text-purple-700"
              : "bg-slate-100 border border-slate-200 text-slate-700"
          }`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              isProd ? "bg-blue-600" : isStaging ? "bg-purple-600" : "bg-slate-500"
            }`}
          />
          <span>{row.environment || "Production"}</span>
        </span>
      );
    },
  },
  {
    key: "status",
    label: "STATUS",
    render: (row) => {
      const status = (row.status || "ACTIVE").toUpperCase();
      const isActive = status === "ACTIVE" || status === "READY" || status === "HEALTHY";

      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
            isActive
              ? "bg-emerald-50 border border-emerald-200/80 text-emerald-700"
              : "bg-slate-100 border border-slate-200 text-slate-600"
          }`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              isActive ? "bg-emerald-500" : "bg-slate-400"
            }`}
          />
          <span>{status}</span>
        </span>
      );
    },
  },
  {
    key: "actions",
    label: "ACTIONS",
    align: "right",
    render: (row) => (
      <Link
        href={`/deployment/${row.id}`}
        className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 transition cursor-pointer"
      >
        <span>View Details</span>
        <ChevronRight size={13} />
      </Link>
    ),
  },
];

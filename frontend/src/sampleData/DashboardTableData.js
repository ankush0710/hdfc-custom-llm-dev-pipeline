export const DashboardTableData = [
  {
    id: 1,
    name: "Customer-Support-LLM",
    version: "v1.2.0",
    status: "live",
    latency: "124ms",
    action: "Metrics",
  },
  {
    id: 2,
    name: "Fraud-Detect-Alpha",
    version: "v0.9.5-beta",
    status: "degraded",
    latency: "850ms",
    action: "Metrics",
  },
  {
    id: 3,
    name: "Doc-Summarizer-V2",
    version: "v2.1.1",
    status: "idle",
    latency: "-",
    action: "Wake",
  },
  {
    id: 4,
    name: "Internal-Knowledge-Base",
    version: "v3.0.0",
    status: "live",
    latency: "210ms",
    action: "Metrics",
  },
  {
    id: 5,
    name: "Internal-Knowledge-Base",
    version: "v3.0.0",
    status: "live",
    latency: "210ms",
    action: "Metrics",
  },
  {
    id: 6,
    name: "Customer-Support-LLM",
    version: "v1.2.0",
    status: "live",
    latency: "124ms",
    action: "Metrics",
  },
  {
    id: 7,
    name: "Doc-Summarizer-V2",
    version: "v2.1.1",
    status: "idle",
    latency: "-",
    action: "Wake",
  },
  {
    id: 8,
    name: "Internal-Knowledge-Base",
    version: "v3.0.0",
    status: "live",
    latency: "210ms",
    action: "Metrics",
  },
];

// status styles here

import { Box } from "lucide-react";

const statusStyles = {
  live: {
    bg: "bg-green-100",
    text: "text-green-700",
    dot: "bg-green-500",
    label: "Live",
  },

  degraded: {
    bg: "bg-yellow-100",
    text: "text-yellow-700",
    dot: "bg-yellow-500",
    label: "Degraded",
  },

  idle: {
    bg: "bg-gray-100",
    text: "text-gray-600",
    dot: "bg-gray-500",
    label: "Idle",
  },
};

// columns here
export const ModelColumns = [
  {
    key: "name",
    label: "Model Name",
    render: (model) => (
      <div className="flex items-center gap-3">
        <Box size={18} className="text-gray-500" />
        <span className="text-gray-900">{model.name}</span>
      </div>
    ),
  },

  {
    key: "version",
    label: "Version",
  },

  {
    key: "status",
    label: "Status",
    render: (model) => {
      const status = statusStyles[model.status];

      return (
        <span
          className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${status.bg} ${status.text}`}
        >
          <span className={`h-2 w-2 rounded-full ${status.dot}`} />

          {status.label}
        </span>
      );
    },
  },

  {
    key: "latency",
    label: "Avg. Latency (ms)",
    render: (model) => (
      <span
        className={model.latency === "850ms" ? "text-red-500" : "text-gray-700"}
      >
        {model.latency}
      </span>
    ),
  },

  {
    key: "action",
    label: "Actions",
    align: "right",
    render: (model) => (
      <button className="font-medium text-blue-600 hover:text-blue-700">
        {model.action}
      </button>
    ),
  },
];

// DashboardTableData.js
// The hardcoded data array has been removed.
// Real deployment data now comes from GET /deployments via the dashboard page.
// This file only exports the column definitions for the Deployed Models table.

import { Box } from "lucide-react";

// Maps real backend deployment status values to display styles
const statusStyles = {
  active: {
    bg: "bg-green-100",
    text: "text-green-700",
    dot: "bg-green-500",
    label: "Active",
  },
  stopped: {
    bg: "bg-gray-100",
    text: "text-gray-600",
    dot: "bg-gray-500",
    label: "Stopped",
  },
  deployed: {
    bg: "bg-blue-100",
    text: "text-blue-700",
    dot: "bg-blue-500",
    label: "Deployed",
  },
  degraded: {
    bg: "bg-yellow-100",
    text: "text-yellow-700",
    dot: "bg-yellow-500",
    label: "Degraded",
  },
};

const defaultStyle = {
  bg: "bg-gray-100",
  text: "text-gray-500",
  dot: "bg-gray-400",
  label: "Unknown",
};

// Column definitions — no business data, only rendering logic
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
      // Normalize backend status (ACTIVE → active) for lookup
      const key = (model.status || "").toLowerCase();
      const style = statusStyles[key] || defaultStyle;
      return (
        <span
          className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${style.bg} ${style.text}`}
        >
          <span className={`h-2 w-2 rounded-full ${style.dot}`} />
          {style.label}
        </span>
      );
    },
  },

  {
    key: "latency",
    label: "Avg. Latency",
    render: (model) => (
      <span className="text-gray-700">{model.latency || "—"}</span>
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

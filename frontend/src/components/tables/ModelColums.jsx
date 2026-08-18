import Link from "next/link";
import { RefreshCcwDot, CircleAlert, CircleCheck } from "lucide-react";
import { Box } from "lucide-react";

const statusStyles = {
  Validated: {
    bg: "bg-green-100",
    text: "text-green-700",
    icon: CircleCheck,
    label: "Validated",
  },

  Processing: {
    bg: "bg-blue-100",
    text: "text-blue-700",
    icon: RefreshCcwDot,
    label: "Processing",
  },

  Failed: {
    bg: "bg-red-100",
    text: "text-red-600",
    icon: CircleAlert,
    label: "Failed",
  },
};

// columns here
export const ModelColums = [
  {
    key: "name",
    label: "Model Name",
    render: (model) => (
      <div className="flex items-center gap-3">
        <Box size={18} className="text-gray-500" />
        <span className="text-gray-900">
          {model.name} <p className="text-gray-600">{model.version}</p>
        </span>
      </div>
    ),
  },
  {
    key: "Type",
    label: "Type",
    render: (model) => (
      <div className="flex items-center gap-3">
        <span className="text-gray-600">{model.type}</span>
      </div>
    ),
  },
  {
    key: "Size",
    label: "Size",
    render: (model) => (
      <div className="flex items-center gap-3">
        <span className="text-gray-600">{model.size} GB</span>
      </div>
    ),
  },

  {
    key: "date",
    label: "Created on",
    render: (model) => (
      <div className="flex items-center gap-3">
        <span className="text-gray-600">{model.date}</span>
      </div>
    ),
  },
  {
    key: "status",
    label: "Status",
    render: (model) => {
      const status = statusStyles[model.status];

      return (
        <span
          className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${statusStyles.bg} ${statusStyles.text}`}
        >
          {statusStyles.icon && <statusStyles.icon size={18} />}
          <span className={`h-2 w-2 rounded-full`} />
          {statusStyles.label}
        </span>
      );
    },
  },

  {
    key: "action",
    label: "Actions",
    align: "right",
    render: (dataset) => (
      <Link
        href={`/dataset/${dataset.id}`}
        className="font-medium text-blue-600 hover:text-blue-700"
      >
        Details
      </Link>
    ),
  },
];

import Link from "next/link";
import { RefreshCcwDot, CircleAlert, CircleCheck } from "lucide-react";

export const DatasetTableData = [
  {
    id: 1,
    name: "Financial Transcript Cleaned",
    version: "v1.2.0",
    type: "CSV",
    size: 4.2,
    date: "Oct 24, 2023",
    status: "Validated",
  },
  {
    id: 2,
    name: "Customer Support Logs",
    version: "v1.6.0",
    type: "JSONL",
    size: 41.2,
    date: "Oct 24, 2023",
    status: "Processing",
  },
  {
    id: 3,
    name: "Banking related FAQs",
    version: "v1.2.0",
    type: "PDF",
    size: 12.2,
    date: "Oct 24, 2023",
    status: "Validated",
  },
  {
    id: 4,
    name: "Legacy Email Cleanup",
    version: "v1.2.0",
    type: "Excel",
    size: 6,
    date: "Oct 24, 2023",
    status: "Processing",
  },
  {
    id: 5,
    name: "Loan Related Query",
    version: "v1.2.0",
    type: "JSONL",
    size: 8.9,
    date: "Oct 24, 2023",
    status: "Validated",
  },
  {
    id: 6,
    name: "Legal Data Corpus",
    version: "v1.2.0",
    type: "JSONL",
    size: 4.2,
    date: "Oct 24, 2023",
    status: "Failed",
  },
  {
    id: 7,
    name: "Financial Transcript Cleaned",
    version: "v1.2.0",
    type: "JSONL",
    size: 19,
    date: "Oct 24, 2023",
    status: "Validated",
  },
  {
    id: 8,
    name: "Financial Transcript Cleaned",
    version: "v1.2.0",
    type: "PDF",
    size: 4.2,
    date: "Oct 24, 2023",
    status: "Failed",
  },
];

// status styles here

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
export const ModelColumns = [
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
    render: () => (
      <Link href="/" className="font-medium text-blue-600 hover:text-blue-700">
        Details
      </Link>
    ),
  },
];

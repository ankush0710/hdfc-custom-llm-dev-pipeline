import Link from "next/link";
import {
  RefreshCcwDot,
  CircleAlert,
  CircleCheck,
  Box,
  Trash2,
  Eye,
  FileCheck2,
  UploadCloud,
} from "lucide-react";

export const statusStyles = {
  Uploaded: {
    bg: "bg-blue-50 border border-blue-200",
    text: "text-blue-700",
    icon: UploadCloud,
    label: "Uploaded",
  },
  Processed: {
    bg: "bg-emerald-50 border border-emerald-200",
    text: "text-emerald-700",
    icon: FileCheck2,
    label: "Processed",
  },
  Validated: {
    bg: "bg-green-50 border border-green-200",
    text: "text-green-700",
    icon: CircleCheck,
    label: "Validated",
  },
  Processing: {
    bg: "bg-amber-50 border border-amber-200",
    text: "text-amber-700",
    icon: RefreshCcwDot,
    label: "Processing",
  },
  Failed: {
    bg: "bg-red-50 border border-red-200",
    text: "text-red-600",
    icon: CircleAlert,
    label: "Failed",
  },
};

const getLatestVersion = (dataset) => {
  if (dataset.versions && dataset.versions.length > 0) {
    // Return latest version by created_at or last item
    return dataset.versions[dataset.versions.length - 1];
  }
  return null;
};

const formatFileSize = (sizeInMb) => {
  if (sizeInMb === undefined || sizeInMb === null) return "-";
  const num = Number(sizeInMb);
  if (isNaN(num)) return "-";
  if (num < 0.01) {
    return `${(num * 1024).toFixed(1)} KB`;
  }
  if (num >= 1024) {
    return `${(num / 1024).toFixed(2)} GB`;
  }
  return `${num.toFixed(2)} MB`;
};

export const createDatasetColumns = ({ onDelete } = {}) => [
  {
    key: "name",
    label: "Dataset Name",
    render: (dataset) => {
      const latest = getLatestVersion(dataset);
      const versionStr = latest?.version || dataset.version || "1.0.0";
      return (
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
            <Box size={18} />
          </div>
          <div>
            <Link
              href={`/dataset/${dataset.id}`}
              className="font-medium text-gray-900 hover:text-blue-600 transition-colors"
            >
              {dataset.dataset_name}
            </Link>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="font-mono text-blue-600">v{versionStr}</span>
              {dataset.category && (
                <>
                  <span>•</span>
                  <span className="capitalize">{dataset.category}</span>
                </>
              )}
            </div>
          </div>
        </div>
      );
    },
  },
  {
    key: "category",
    label: "Category",
    render: (dataset) => (
      <span className="inline-flex rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700 capitalize">
        {dataset.category || "General"}
      </span>
    ),
  },
  {
    key: "Type",
    label: "Type",
    render: (dataset) => {
      const latest = getLatestVersion(dataset);
      const type = latest?.file_type || dataset.file_type || "CSV";
      return (
        <span className="font-mono text-xs font-semibold text-slate-600 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded">
          {type}
        </span>
      );
    },
  },
  {
    key: "Size",
    label: "Size",
    render: (dataset) => {
      const latest = getLatestVersion(dataset);
      const size = latest?.file_size ?? dataset.file_size;
      return (
        <span className="text-xs text-gray-600 font-medium">
          {formatFileSize(size)}
        </span>
      );
    },
  },
  {
    key: "date",
    label: "Created on",
    render: (dataset) => (
      <span className="text-xs text-gray-600">
        {dataset.created_at
          ? new Date(dataset.created_at).toLocaleDateString("en-GB", {
              day: "2-digit",
              month: "short",
              year: "numeric",
            })
          : "-"}
      </span>
    ),
  },
  {
    key: "status",
    label: "Status",
    render: (dataset) => {
      const latest = getLatestVersion(dataset);
      const rawStatus = latest?.status || dataset.status || "Uploaded";
      const status = statusStyles[rawStatus] || statusStyles.Uploaded;
      const StatusIcon = status.icon;

      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${status.bg} ${status.text}`}
        >
          {StatusIcon && <StatusIcon size={13} />}
          <span>{status.label}</span>
        </span>
      );
    },
  },
  {
    key: "action",
    label: "Actions",
    align: "right",
    render: (dataset) => (
      <div className="flex items-center justify-end gap-2">
        <Link
          href={`/dataset/${dataset.id}`}
          className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-2.5 py-1 rounded transition-colors"
        >
          <Eye size={13} />
          Details
        </Link>
        {onDelete && (
          <button
            type="button"
            onClick={() => onDelete(dataset)}
            className="inline-flex items-center gap-1 text-xs font-medium text-red-600 hover:text-red-800 hover:bg-red-50 p-1 rounded transition-colors"
            title="Delete dataset"
          >
            <Trash2 size={14} />
          </button>
        )}
      </div>
    ),
  },
];

// Default export for backward compatibility
export const DatasetColumns = createDatasetColumns();

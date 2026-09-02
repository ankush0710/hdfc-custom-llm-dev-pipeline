"use client";

import { useState, useEffect, useCallback } from "react";
import {
  CheckCircle2,
  RefreshCw,
  CircleAlert,
  Rocket,
  Loader2,
  Clock,
  Box,
  Database,
  X,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { getActivities } from "@/app/services/dashboardService/dashboardService";

// Maps event_type from the backend to icon + color styling
const EVENT_STYLES = {
  training_completed: {
    icon: CheckCircle2,
    iconBg: "bg-green-100",
    iconColor: "text-green-600",
  },
  training_failed: {
    icon: CircleAlert,
    iconBg: "bg-red-100",
    iconColor: "text-red-600",
    isError: true,
  },
  training_running: {
    icon: RefreshCw,
    iconBg: "bg-blue-100",
    iconColor: "text-blue-600",
    animate: true,
  },
  training_queued: {
    icon: Clock,
    iconBg: "bg-gray-100",
    iconColor: "text-gray-500",
  },
  evaluation_completed: {
    icon: CheckCircle2,
    iconBg: "bg-emerald-100",
    iconColor: "text-emerald-600",
  },
  evaluation_failed: {
    icon: CircleAlert,
    iconBg: "bg-red-100",
    iconColor: "text-red-600",
    isError: true,
  },
  evaluation_running: {
    icon: RefreshCw,
    iconBg: "bg-indigo-100",
    iconColor: "text-indigo-600",
    animate: true,
  },
  model_deployed: {
    icon: Rocket,
    iconBg: "bg-purple-100",
    iconColor: "text-purple-600",
  },
  model_registered: {
    icon: Box,
    iconBg: "bg-amber-100",
    iconColor: "text-amber-600",
  },
  dataset_uploaded: {
    icon: Database,
    iconBg: "bg-cyan-100",
    iconColor: "text-cyan-600",
  },
};

const DEFAULT_STYLE = {
  icon: Clock,
  iconBg: "bg-gray-100",
  iconColor: "text-gray-400",
};

function formatRelativeTime(timestamp) {
  if (!timestamp) return "";
  const date = new Date(timestamp);
  if (isNaN(date.getTime())) return "";
  const diffMs = Date.now() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin} min${diffMin > 1 ? "s" : ""} ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr} hour${diffHr > 1 ? "s" : ""} ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay === 1) return "Yesterday";
  return `${diffDay} days ago`;
}

function formatFullDateTime(timestamp) {
  if (!timestamp) return "";
  const date = new Date(timestamp);
  if (isNaN(date.getTime())) return "";
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

/**
 * ActivityCard — displays the recent activity feed from the backend.
 * On Dashboard: strictly displays up to 5 latest items.
 * View Details: opens a modal with paginated historical activities fetched dynamically from GET /pipeline/activities.
 */
export default function ActivityCard({ activities = [], loading = false }) {
  const [modalOpen, setModalOpen] = useState(false);
  const [allActivities, setAllActivities] = useState([]);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState(null);
  const [page, setPage] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [filterType, setFilterType] = useState("all");
  const pageSize = 10;

  // Display only the first 5 activities on the dashboard
  const displayActivities = activities.slice(0, 5);

  const fetchModalActivities = useCallback(async (currentPage, filter) => {
    setModalLoading(true);
    setModalError(null);
    try {
      const params = {
        limit: pageSize,
        offset: currentPage * pageSize,
      };
      if (filter && filter !== "all") {
        params.event_type = filter;
      }
      const data = await getActivities(params);
      setAllActivities(data?.activities || []);
      setTotalCount(data?.total || 0);
    } catch (err) {
      console.error("Failed to load paginated activities:", err);
      setModalError(err?.response?.data?.detail || "Failed to load activities. Please try again.");
    } finally {
      setModalLoading(false);
    }
  }, []);

  const handleOpenModal = () => {
    setModalOpen(true);
    setPage(0);
    setFilterType("all");
    fetchModalActivities(0, "all");
  };

  const handleCloseModal = () => {
    setModalOpen(false);
  };

  const handlePageChange = (newPage) => {
    setPage(newPage);
    fetchModalActivities(newPage, filterType);
  };

  const handleFilterChange = (type) => {
    setFilterType(type);
    setPage(0);
    fetchModalActivities(0, type);
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <>
      <div className="w-full overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm flex flex-col h-full">
        {/* Header */}
        <div className="border-b border-gray-200 px-4 py-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">
            Recent Activity
          </h2>
          <span className="text-[11px] font-medium text-gray-400 bg-gray-50 px-2 py-0.5 rounded-full border border-gray-200">
            Latest 5
          </span>
        </div>

        {/* Body */}
        <div className="flex-1">
          {loading ? (
            // Loading skeleton
            <div className="divide-y divide-gray-100">
              {[1, 2, 3, 4, 5].map((n) => (
                <div key={n} className="flex gap-3 px-3 py-3 animate-pulse">
                  <div className="h-9 w-9 shrink-0 rounded-full bg-gray-200" />
                  <div className="flex-1 space-y-1.5 pt-1">
                    <div className="h-3 w-3/4 rounded bg-gray-200" />
                    <div className="h-2.5 w-1/2 rounded bg-gray-100" />
                  </div>
                </div>
              ))}
            </div>
          ) : displayActivities.length === 0 ? (
            // Empty state
            <div className="flex flex-col items-center justify-center px-4 py-12 text-center">
              <Clock size={28} className="text-gray-300 mb-2" />
              <p className="text-xs text-gray-400 font-medium">No recent activity</p>
              <p className="text-[10px] text-gray-300 mt-0.5">
                Activity will appear here as training runs and evaluations complete.
              </p>
            </div>
          ) : (
            // Real activity items from backend (strictly top 5)
            <div>
              {displayActivities.map((activity) => {
                const style = EVENT_STYLES[activity.event_type] || DEFAULT_STYLE;
                const Icon = style.icon;
                const relTime = formatRelativeTime(activity.timestamp);

                return (
                  <div
                    key={activity.id}
                    className="flex gap-3 border-b border-gray-100 px-3 py-3 last:border-b-0 hover:bg-gray-50/60 transition-colors"
                  >
                    {/* Icon */}
                    <div
                      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${style.iconBg}`}
                    >
                      <Icon
                        size={18}
                        strokeWidth={2}
                        className={`${style.iconColor}${style.animate ? " animate-spin" : ""}`}
                      />
                    </div>

                    {/* Content */}
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold leading-5 text-gray-900 truncate">
                        {activity.title}
                      </p>
                      <p
                        className={`mt-0.5 text-[10px] truncate ${
                          style.isError ? "text-red-500" : "text-gray-500"
                        }`}
                      >
                        {relTime && <span>{relTime} · </span>}
                        {activity.description}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer with "View Details" */}
        <div className="border-t border-gray-100 bg-gray-50/50">
          <button
            type="button"
            onClick={handleOpenModal}
            className="w-full px-4 py-3 text-center text-xs font-semibold text-[#002B55] hover:text-blue-700 hover:bg-blue-50/50 transition cursor-pointer flex items-center justify-center gap-1"
          >
            <span>View Details</span>
            <ExternalLink size={12} />
          </button>
        </div>
      </div>

      {/* ── All Activities Modal (Paginated from Backend) ────────────────────── */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="relative w-full max-w-2xl max-h-[85vh] rounded-2xl bg-white shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 bg-gray-50/80">
              <div className="flex items-center gap-2">
                <Clock className="text-[#002B55]" size={20} />
                <h3 className="text-base font-bold text-gray-900">
                  All Pipeline Activities
                </h3>
                <span className="ml-2 rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-[#002B55]">
                  {totalCount} Total
                </span>
              </div>
              <button
                onClick={handleCloseModal}
                className="rounded-lg p-1 text-gray-400 hover:bg-gray-200 hover:text-gray-700 transition"
              >
                <X size={18} />
              </button>
            </div>

            {/* Filter Pills */}
            <div className="flex items-center gap-2 border-b border-gray-100 px-6 py-3 overflow-x-auto text-xs">
              {[
                { id: "all", label: "All Activities" },
                { id: "training_completed", label: "Training Completed" },
                { id: "training_failed", label: "Training Failed" },
                { id: "evaluation_completed", label: "Evaluations" },
                { id: "model_deployed", label: "Deployments" },
                { id: "dataset_uploaded", label: "Datasets" },
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => handleFilterChange(f.id)}
                  className={`rounded-full px-3 py-1 font-medium transition cursor-pointer whitespace-nowrap ${
                    filterType === f.id
                      ? "bg-[#002B55] text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto px-6 py-4">
              {modalLoading ? (
                <div className="flex flex-col items-center justify-center py-16">
                  <RefreshCw className="h-8 w-8 animate-spin text-[#002B55] mb-2" />
                  <p className="text-xs text-gray-500 font-medium">
                    Loading activities. Please wait...
                  </p>
                </div>
              ) : modalError ? (
                <div className="my-6 rounded-lg border border-red-200 bg-red-50 p-4 text-center">
                  <p className="text-sm font-semibold text-red-700">{modalError}</p>
                  <button
                    onClick={() => fetchModalActivities(page, filterType)}
                    className="mt-2 text-xs font-semibold text-red-600 underline hover:no-underline"
                  >
                    Retry
                  </button>
                </div>
              ) : allActivities.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <Clock size={36} className="text-gray-300 mb-2" />
                  <p className="text-sm font-semibold text-gray-700">No activities found</p>
                  <p className="text-xs text-gray-400 mt-1">
                    No pipeline events match the selected criteria.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100">
                  {allActivities.map((item) => {
                    const style = EVENT_STYLES[item.event_type] || DEFAULT_STYLE;
                    const Icon = style.icon;
                    const relTime = formatRelativeTime(item.timestamp);
                    const fullTime = formatFullDateTime(item.timestamp);

                    return (
                      <div
                        key={item.id}
                        className="flex items-start gap-4 py-3.5 hover:bg-gray-50/70 transition rounded-lg px-2"
                      >
                        <div
                          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${style.iconBg}`}
                        >
                          <Icon
                            size={18}
                            strokeWidth={2}
                            className={`${style.iconColor}${style.animate ? " animate-spin" : ""}`}
                          />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-2">
                            <p className="text-xs font-bold text-gray-900">
                              {item.title}
                            </p>
                            <span className="text-[10px] text-gray-400 whitespace-nowrap">
                              {relTime}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 mt-0.5">
                            {item.description}
                          </p>
                          {fullTime && (
                            <p className="text-[10px] text-gray-400 mt-1 font-mono">
                              {fullTime}
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Modal Pagination Footer */}
            <div className="flex items-center justify-between border-t border-gray-200 px-6 py-3 bg-gray-50">
              <span className="text-xs text-gray-500 font-medium">
                {totalCount > 0 ? (
                  <>
                    Showing{" "}
                    <span className="font-semibold text-gray-800">
                      {page * pageSize + 1}
                    </span>{" "}
                    to{" "}
                    <span className="font-semibold text-gray-800">
                      {Math.min((page + 1) * pageSize, totalCount)}
                    </span>{" "}
                    of{" "}
                    <span className="font-semibold text-gray-800">
                      {totalCount}
                    </span>
                  </>
                ) : (
                  "0 items"
                )}
              </span>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page === 0 || modalLoading}
                  className="inline-flex items-center gap-1 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 shadow-xs hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  <ChevronLeft size={14} />
                  <span>Previous</span>
                </button>
                <span className="text-xs font-semibold text-gray-700 px-1">
                  Page {page + 1} of {Math.max(1, totalPages)}
                </span>
                <button
                  type="button"
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page >= totalPages - 1 || modalLoading}
                  className="inline-flex items-center gap-1 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 shadow-xs hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  <span>Next</span>
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

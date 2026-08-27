"use client";

import { CheckCircle2, RefreshCw, CircleAlert, Rocket, Loader2, Clock, Box } from "lucide-react";

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

/**
 * ActivityCard — displays the recent activity feed from the backend.
 * Accepts `activities` as a prop (array from GET /pipeline/dashboard/stats).
 * Shows a loading skeleton when `loading` is true.
 * Shows an empty state when `activities` is empty.
 * No hardcoded activity data.
 */
export default function ActivityCard({ activities = [], loading = false }) {
  return (
    <div className="w-full overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      {/* Header */}
      <div className="border-b border-gray-200 px-4 py-4">
        <h2 className="text-base font-semibold text-gray-900">
          Recent Activity
        </h2>
      </div>

      {/* Body */}
      {loading ? (
        // Loading skeleton
        <div className="divide-y divide-gray-100">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="flex gap-3 px-3 py-3 animate-pulse">
              <div className="h-9 w-9 shrink-0 rounded-full bg-gray-200" />
              <div className="flex-1 space-y-1.5 pt-1">
                <div className="h-3 w-3/4 rounded bg-gray-200" />
                <div className="h-2.5 w-1/2 rounded bg-gray-100" />
              </div>
            </div>
          ))}
        </div>
      ) : activities.length === 0 ? (
        // Empty state
        <div className="flex flex-col items-center justify-center px-4 py-8 text-center">
          <Clock size={24} className="text-gray-300 mb-2" />
          <p className="text-xs text-gray-400 font-medium">No recent activity</p>
          <p className="text-[10px] text-gray-300 mt-0.5">
            Activity will appear here as training runs and evaluations complete.
          </p>
        </div>
      ) : (
        // Real activity items from backend
        <div>
          {activities.map((activity) => {
            const style = EVENT_STYLES[activity.event_type] || DEFAULT_STYLE;
            const Icon = style.icon;
            const relTime = formatRelativeTime(activity.timestamp);

            return (
              <div
                key={activity.id}
                className="flex gap-3 border-b border-gray-200 px-3 py-3 last:border-b-0"
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

      {/* Footer */}
      <button
        type="button"
        className="w-full px-4 py-4 text-center text-xs font-semibold text-[#002B55] transition hover:bg-gray-50 hover:text-blue-700 cursor-pointer"
      >
        View All Activity
      </button>
    </div>
  );
}

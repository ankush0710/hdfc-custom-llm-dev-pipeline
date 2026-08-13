"use client";

import {
  CheckCircle2,
  RefreshCw,
  CircleAlert,
  Rocket,
} from "lucide-react";

const activities = [
  {
    id: 1,
    icon: CheckCircle2,
    iconBg: "bg-green-100",
    iconColor: "text-green-600",
    title: "Model-v4 Training Completed",
    time: "10 mins ago",
    description: "Checkpoint saved",
  },
  {
    id: 2,
    icon: RefreshCw,
    iconBg: "bg-blue-100",
    iconColor: "text-blue-600",
    title: "Dataset 'Banking-FAQ' updated",
    time: "45 mins ago",
    description: "+2,400 records added",
  },
  {
    id: 3,
    icon: CircleAlert,
    iconBg: "bg-red-100",
    iconColor: "text-red-600",
    title: "Pipeline 'Fraud-Detect-Alpha' failed",
    time: "2 hours ago",
    description: "OOM Error at Epoch 4",
    error: true,
  },
  {
    id: 4,
    icon: Rocket,
    iconBg: "bg-purple-100",
    iconColor: "text-purple-600",
    title: "Customer-Support-LLM deployed to Prod",
    time: "Yesterday",
    description: "Version 1.2.0",
  },
];

export default function ActivityCard() {
  return (
    <div className="w-full overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      
      {/* Header */}
      <div className="border-b border-gray-200 px-4 py-4">
        <h2 className="text-base font-semibold text-gray-900">
          Recent Activity
        </h2>
      </div>

      {/* Activities */}
      <div>
        {activities.map((activity) => {
          const Icon = activity.icon;

          return (
            <div
              key={activity.id}
              className="flex gap-3 border-b border-gray-200 px-3 py-3"
            >
              {/* Icon */}
              <div
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${activity.iconBg}`}
              >
                <Icon
                  size={18}
                  strokeWidth={2}
                  className={activity.iconColor}
                />
              </div>

              {/* Content */}
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold leading-5 text-gray-900">
                  {activity.title}
                </p>

                <p
                  className={`mt-0.5 text-[10px] ${
                    activity.error
                      ? "text-red-500"
                      : "text-gray-500"
                  }`}
                >
                  {activity.time} • {activity.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <button
        type="button"
        className="w-full px-4 py-4 text-center text-xs font-semibold text-blue-600 transition hover:bg-gray-50 hover:text-blue-700 cursor-pointer"
      >
        View All Activity
      </button>
    </div>
  );
}
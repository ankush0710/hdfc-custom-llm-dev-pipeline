"use client";

import { Activity, CircleCheck, CircleAlert, Clock } from "lucide-react";

export default function TrainingJobStats({ stats }) {
  const {
    activeJobs = 0,
    completedJobs = 0,
    failedJobs = 0,
    queuedJobs = 0,
  } = stats || {};

  const cards = [
    {
      title: "Active Jobs",
      value: activeJobs,
      valueColor: "text-[#002B55]",
      icon: Activity,
      iconColor: "text-blue-600 bg-blue-50 border-blue-100",
    },
    {
      title: "Completed",
      value: completedJobs,
      valueColor: "text-[#002B55]",
      icon: CircleCheck,
      iconColor: "text-emerald-600 bg-emerald-50 border-emerald-100",
    },
    {
      title: "Failed",
      value: failedJobs,
      valueColor: "text-red-600",
      icon: CircleAlert,
      iconColor: "text-red-600 bg-red-50 border-red-100",
    },
    {
      title: "Queued",
      value: queuedJobs,
      valueColor: "text-[#002B55]",
      icon: Clock,
      iconColor: "text-slate-500 bg-slate-50 border-slate-200",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.title}
            className="bg-white rounded-2xl border border-gray-200/80 p-5 shadow-sm hover:shadow transition duration-200 flex flex-col justify-between"
          >
            {/* Top row: Title and Icon */}
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                {card.title}
              </span>
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full border ${card.iconColor}`}
              >
                <Icon size={16} />
              </div>
            </div>

            {/* Bottom row: Value */}
            <div className="mt-3">
              <span className={`text-3xl font-extrabold tracking-tight ${card.valueColor}`}>
                {card.value}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

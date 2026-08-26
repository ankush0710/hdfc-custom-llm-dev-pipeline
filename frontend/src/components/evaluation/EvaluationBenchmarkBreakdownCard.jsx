"use client";

import { BarChart3, Layers, CheckCircle2 } from "lucide-react";

export default function EvaluationBenchmarkBreakdownCard({ tasks = [] }) {
  const defaultTasks = [
    {
      task_name: "Task A (Reasoning / Intent Structured Validity)",
      score: 94,
      category: "Intent Reasoning",
    },
    {
      task_name: "Task B (Structured Entity Extraction / Generation)",
      score: 92,
      category: "Extraction",
    },
    {
      task_name: "Task C (Banking Policy & Safety Compliance)",
      score: 89,
      category: "Safety Alignment",
    },
  ];

  const taskList = tasks && tasks.length > 0 ? tasks : defaultTasks;

  return (
    <div className="bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm">
      {/* Title */}
      <div className="flex items-center justify-between pb-4 border-b border-gray-100 mb-6">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-50 text-[#002B55]">
            <BarChart3 size={16} />
          </div>
          <div>
            <h3 className="text-base font-bold text-gray-900">
              Benchmark Results Breakdown
            </h3>
            <p className="text-xs text-gray-400 font-medium">
              Granular performance across key banking domain tasks
            </p>
          </div>
        </div>
      </div>

      {/* Task Progress Bars */}
      <div className="space-y-6">
        {taskList.map((item, index) => {
          const numScore = typeof item.score === "number" ? item.score : parseFloat(item.score) || 0;
          return (
            <div key={index} className="space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="text-gray-800">
                  {item.task_name}
                </span>
                <span className="font-mono text-xs font-bold text-gray-900">
                  {numScore}%
                </span>
              </div>

              {/* Progress Track */}
              <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden p-0.5">
                <div
                  className="h-full bg-[#002B55] rounded-full transition-all duration-700 ease-out"
                  style={{ width: `${Math.min(numScore, 100)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

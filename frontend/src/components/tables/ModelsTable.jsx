"use client";

import {
  MoreVertical,
  Filter,
  Box,
} from "lucide-react";

export default function ModelsTable({ data = [] }) {

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

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">

      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Deployed Models Overview
        </h2>

        <div className="flex items-center gap-3">
          <button className="text-gray-500 hover:text-gray-700">
            <Filter size={18} />
          </button>

          <button className="text-gray-500 hover:text-gray-700">
            <MoreVertical size={18} />
          </button>
        </div>
      </div>

      {/* Desktop Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          
          <thead className="bg-blue-50">
            <tr>
              <th className="px-5 py-3 text-left text-xs font-semibold uppercase text-gray-600">
                Model Name
              </th>

              <th className="px-5 py-3 text-left text-xs font-semibold uppercase text-gray-600">
                Version
              </th>

              <th className="px-5 py-3 text-left text-xs font-semibold uppercase text-gray-600">
                Status
              </th>

              <th className="px-5 py-3 text-left text-xs font-semibold uppercase text-gray-600">
                Avg. Latency (ms)
              </th>

              <th className="px-5 py-3 text-right text-xs font-semibold uppercase text-gray-600">
                Actions
              </th>
            </tr>
          </thead>

          <tbody>
            {data.map((model) => (
              <tr
                key={model.id}
                className="border-b border-gray-100 hover:bg-gray-50"
              >
                {/* Model Name */}
                <td className="px-5 py-4">
                  <div className="flex items-center gap-3">
                    <Box
                      size={18}
                      className="text-gray-500"
                    />

                    <span className="text-sm text-gray-900">
                      {model.name}
                    </span>
                  </div>
                </td>

                {/* Version */}
                <td className="px-5 py-4 text-sm text-gray-700">
                  {model.version}
                </td>

                {/* Status */}
                <td className="px-5 py-4">
                  <span
                    className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium
                    ${statusStyles[model.status].bg}
                    ${statusStyles[model.status].text}`}
                  >
                    <span
                      className={`h-2 w-2 rounded-full ${statusStyles[model.status].dot}`}
                    />

                    {statusStyles[model.status].label}
                  </span>
                </td>

                {/* Latency */}
                <td
                  className={`px-5 py-4 text-sm
                    ${
                      model.latency === "850ms"
                        ? "text-red-500"
                        : "text-gray-700"
                    }`}
                >
                  {model.latency}
                </td>

                {/* Action */}
                <td className="px-5 py-4 text-right">
                  <button className="text-sm font-medium text-blue-600 hover:text-blue-700">
                    {model.action}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>

        </table>
      </div>
    </div>
  );
}
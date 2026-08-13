//========================================================================================//
/*
Line chart component which show the data in form of line
*/
//=======================================================================================//
"use client";
import { useState, useMemo } from "react";
import {
  LineChart as RecharLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export default function LineChart({
  data = [],
  xKey,
  lines = [],
  title,
  height = 300,
}) {
  const [range, setRange] = useState("today");

  const filteredData = useMemo(() => {
    switch (range) {
      case "yesterday":
        return data.slice(-2, -1);

      case "Last7":
        return data.slice(-7);

      case "Last10":
        return data.slice(-10);

      default:
        return data.slice(-1);
    }
  }, [data, range]);
  return (
    <div className="w-full max-w-6xl rounded-xl border border-gray-200 bg-white p-4">
      {/* title of the chart  */}
      {
        <div className="flex items-center justify-between border-b-2 border-gray-300 py-5 mb-5">
          <h3 className="text-gray-900 font-semibold text-lg">{title}</h3>

          <select
            value={range}
            onChange={(e) => setRange(e.target.value)}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          >
            <option value="today">Today</option>
            <option value="yesterday">Yesterday</option>
            <option value="last7">Last 7 Days</option>
            <option value="last8">Last 8 Days</option>
          </select>
        </div>
      }

      {/* Responsive container for the chart */}
      <div className="w-full" style={{ height: `${height}px` }}>
        <ResponsiveContainer width="100%" height="100%">
          <RecharLineChart
            data={data}
            margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey={xKey} stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip
              contentStyle={{
                backgroundColor: "#fff",
                border: "1px solid #e5e7eb",
              }}
              itemStyle={{ color: "#374151" }}
              labelStyle={{ color: "#111827", fontWeight: "bold" }}
            />
            <Legend
              iconType="circle"
              iconSize={10}
              wrapperStyle={{ color: "#6b7280", fontSize: "12px" }}
            />
            {/* Render the Line component */}
            {lines.map((line) => {
              return (
                <Line
                  key={line.dataKey}
                  type="monotone"
                  dataKey={line.dataKey}
                  stroke={line.color}
                  strokeWidth={3}
                  dot={{ r: 4, strokeWidth: 2, stroke: line.color }}
                  activeDot={{ r: 6 }}
                />
              );
            })}
          </RecharLineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

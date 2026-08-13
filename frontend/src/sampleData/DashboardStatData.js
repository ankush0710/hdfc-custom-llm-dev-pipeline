import { Database, RefreshCcwDot, Box, TrendingUp } from "lucide-react";

export const DashboardStatData = [
  {
    statName: "Total Datasets",
    value: 42,
    icon: Database,
    status: "+5%",
    statusIcon: TrendingUp,
    statusBg: "bg-[#C4F7CA] text-[#499A13]",
    iconBg: "bg-blue-50 text-blue-600 border-blue-100",
    cardBg:
      "border-t-5 border-t-[#E0E0E0] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#002B55]",
  },
  {
    statName: "Active Trainings",
    value: 8,
    icon: RefreshCcwDot,
    status: "Active",
    statusBg: "bg-blue-50 text-gray-500",
    iconBg: "bg-amber-50 text-amber-600 border-amber-100",
    cardBg:
      "border-t-5 border-t-[#FFCDC9] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#D90000]",
  },
  {
    statName: "Total Models",
    value: 124,
    icon: Box,
    iconBg: "bg-indigo-50 text-indigo-600 border-indigo-100",
    cardBg:
      "border-t-5 border-t-[#E8EDF2] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#525EA7]",
  },
  {
    statName: "Avg Evaluation Score",
    value: "89%",
    icon: TrendingUp,
    status: "MMLU",
    statusBg: "text-gray-500",
    iconBg: "bg-emerald-50 text-emerald-600 border-emerald-100",
    cardBg:
      "border-t-5 border-t-[#A5D6A7] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#266210]",
  },
];

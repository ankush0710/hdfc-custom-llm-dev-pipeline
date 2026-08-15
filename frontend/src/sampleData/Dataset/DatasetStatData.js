import {
  Database,
  CircleCheck,
  RefreshCcwDot,
  CircleAlert,
  TrendingUp,
} from "lucide-react";

export const DatasetStatData = [
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
    valueColor: "text-[#002B55]",
  },
  {
    statName: "Validated",
    value: 38,
    icon: CircleCheck,
    statusBg: "bg-green-50 text-gray-500",
    iconBg: "bg-amber-50 text-amber-600 border-amber-100",
    cardBg:
      "border-t-5 border-t-[#A5D6A7] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#266210]",
    valueColor: "text-[#002B55]",
  },
  {
    statName: "Processing",
    value: 3,
    icon: RefreshCcwDot,
    iconBg: "bg-indigo-50 text-indigo-600 border-indigo-100",
    cardBg:
      "border-t-5 border-t-[#E8EDF2] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#525EA7]",
    valueColor: "text-[#002B55]",
  },
  {
    statName: "Failed",
    value: "1",
    icon: CircleAlert,
    statusBg: "text-red-500",
    iconBg: "bg-red-50 text-red-600 border-emerald-100",
    cardBg:
      "border-t-5 border-t-[#FFCDC9] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#D90000]",
    valueColor: "text-[#D90000]",
  },
];

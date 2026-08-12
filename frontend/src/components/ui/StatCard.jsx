//========================================================================================//
/* 
stats card for displaying the stats related information 
*/
//=======================================================================================//
import {
    Database,
    RefreshCcwDot,
    Box,
    TrendingUp,
} from "lucide-react";


const statData = [
    {
        statName: "Total Datasets",
        value: 42,
        icon: Database,
        status: "+5%",
        statusIcon: TrendingUp,
        statusBg: "bg-[#C4F7CA] text-[#499A13]",
        iconBg: "bg-blue-50 text-blue-600 border-blue-100",
        cardBg: "border-t-5 border-t-[#E0E0E0] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#002B55]"
    },
    {
        statName: "Active Trainings",
        value: 8,
        icon: RefreshCcwDot,
        status: "Active",
        statusBg: "bg-blue-50 text-gray-500",
        iconBg: "bg-amber-50 text-amber-600 border-amber-100",
        cardBg: "border-t-5 border-t-[#FFCDC9] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#D90000]"

    },
    {
        statName: "Total Models",
        value: 124,
        icon: Box,
        iconBg: "bg-indigo-50 text-indigo-600 border-indigo-100",
        cardBg: "border-t-5 border-t-[#E8EDF2] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#525EA7]"

    },
    {
        statName: "Avg Evaluation Score",
        value: "89%",
        icon: TrendingUp,
        status: "MMLU",
        statusBg: "text-gray-500",
        iconBg: "bg-emerald-50 text-emerald-600 border-emerald-100",
        cardBg: "border-t-5 border-t-[#A5D6A7] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#266210]"

    }
];

export default function StatCard() {
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 w-full">
            {
                statData.map((item) => {
                    const Icon = item.icon;
                    const StatusIcon = item.statusIcon;
                    return (
                        <div
                            key={item.statName}
                            className={`relative overflow-hidden bg-white ${item.cardBg} flex flex-col justify-between h-42`}
                        >
                            {/* Decorative subtle background gradient element */}
                            <div className="absolute right-0 top-0 -mr-6 -mt-6 w-24 h-24 rounded-full bg-gray-50 -z-10" />

                            {/* Upper section: Icon & Details */}
                            <div className="flex items-center justify-between">
                                <div className={`h-11 w-11 rounded-xl flex items-center justify-center border ${item.iconBg}`}>
                                    <Icon size={22} strokeWidth={2} />
                                </div>
                                {
                                    item.status && (
                                        <span className={`flex items-center gap-1 text-[15px] font-bold tracking-wider ${item.statusBg} px-3 py-1 rounded-full`}>
                                            {item.statusIcon &&
                                                <StatusIcon size={18} />}{item.status}
                                        </span>
                                    )
                                }
                            </div>

                            {/* Lower section: Name and Value */}
                            <div className="mt-3">
                                <p className="text-gray-500 text-xs font-semibold uppercase tracking-wider">{item.statName}</p>
                                <h3 className="text-3xl font-extrabold text-blue-900 mt-1 tracking-tight">
                                    {item.value}
                                </h3>
                            </div>
                        </div>
                    );
                })
            }
        </div>
    );
}
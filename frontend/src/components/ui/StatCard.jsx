//========================================================================================//
/* 
stats card for displaying the stats related information 
*/
//=======================================================================================//

export default function StatCard({ statData }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 w-full">
      {statData.map((item) => {
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
              <div
                className={`h-11 w-11 rounded-xl flex items-center justify-center border ${item.iconBg}`}
              >
                <Icon size={22} strokeWidth={2} />
              </div>
              {item.status && (
                <span
                  className={`flex items-center gap-1 text-[15px] font-bold tracking-wider ${item.statusBg} px-3 py-1 rounded-full`}
                >
                  {item.statusIcon && <StatusIcon size={18} />}
                  {item.status}
                </span>
              )}
            </div>

            {/* Lower section: Name and Value */}
            <div className="mt-3">
              <p
                className={`text-sm font-semibold uppercase tracking-wider ${item.valueColor}`}
              >
                {item.statName}
              </p>
              <h3 className="text-2xl font-extrabold text-blue-900 mt-1 tracking-tight">
                {item.value}
              </h3>
            </div>
          </div>
        );
      })}
    </div>
  );
}

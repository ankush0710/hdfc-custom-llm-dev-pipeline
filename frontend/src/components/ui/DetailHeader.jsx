"use client";

export default function DetailHeader({
  title,
  badges = [],
  actions,
  children,
  className = "",
}) {
  const getBadgeStyle = (variant) => {
    switch (variant) {
      case "success":
      case "valid":
        return "bg-[#EAF8EE] text-[#16A34A] border-[#BDECC9]";
      case "warning":
      case "pending":
        return "bg-amber-50 text-amber-700 border-amber-200";
      case "processing":
      case "running":
        return "bg-sky-50 text-sky-700 border-sky-200";
      case "info":
        return "bg-[#EEF2FF] text-[#4F46E5] border-[#D5DEFD]";
      case "error":
      case "failed":
        return "bg-red-50 text-red-700 border-red-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  return (
    <div
      className={`flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200 mb-6 ${className}`}
    >
      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-2xl lg:text-3xl font-bold text-[#0F172A] tracking-tight">
          {title}
        </h1>

        {badges.map((badge, idx) => {
          if (!badge) return null;
          if (typeof badge === "string") {
            return (
              <span
                key={idx}
                className="inline-flex items-center rounded-full bg-[#EAF8EE] px-2.5 py-0.5 text-[11px] font-bold tracking-wider text-[#16A34A] uppercase border border-[#BDECC9]"
              >
                {badge}
              </span>
            );
          }

          const {
            label,
            variant = "success",
            bg = getBadgeStyle(variant),
          } = badge;

          return (
            <span
              key={idx}
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider border ${bg}`}
            >
              {label}
            </span>
          );
        })}

        {children}
      </div>

      {actions && (
        <div className="flex items-center gap-3 flex-wrap">{actions}</div>
      )}
    </div>
  );
}

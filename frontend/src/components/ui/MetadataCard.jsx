"use client";

export default function MetadataCard({
  title = "Metadata",
  items = [],
  columns = 4,
  className = "",
}) {
  const gridClasses = {
    2: "grid-cols-1 sm:grid-cols-2",
    3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-2 md:grid-cols-4",
    5: "grid-cols-2 md:grid-cols-5",
  };

  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white p-6 shadow-sm ${className}`}
    >
      {title && (
        <>
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
          <div className="border-b border-slate-100 my-4" />
        </>
      )}

      <div className={`grid gap-6 ${gridClasses[columns] || gridClasses[4]}`}>
        {items.map((item, idx) => (
          <div key={item.label || idx}>
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
              {item.label}
            </p>
            <p
              className={`font-bold text-slate-900 tracking-tight ${
                item.size === "small"
                  ? "text-lg mt-1"
                  : "text-2xl"
              }`}
            >
              {item.value ?? "-"}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function MetadataGrid({ items = [], columns = 3 }) {
  const columnClasses = {
    1: "grid-cols-1",
    2: "grid-cols-1 sm:grid-cols-2",
    3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
  };

  return (
    <div
      className={`
        grid
        gap-x-8
        gap-y-6
        ${columnClasses[columns]}
      `}
    >
      {items.map((item) => (
        <MetadataItem key={item.label} {...item} />
      ))}
    </div>
  );
}

function MetadataItem({ label, value, badge = false }) {
  return (
    <div>
      <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </p>

      {badge ? (
        <span className="inline-flex rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700">
          {value}
        </span>
      ) : (
        <p className="text-sm font-semibold text-slate-900">{value}</p>
      )}
    </div>
  );
}

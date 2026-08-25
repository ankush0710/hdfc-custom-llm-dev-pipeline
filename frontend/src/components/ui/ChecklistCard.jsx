"use client";
import { CheckCircle2, AlertCircle, Clock, XCircle } from "lucide-react";

export default function ChecklistCard({
  title = "Validation Status",
  items = [],
  className = "",
}) {
  const getIcon = (status = "valid") => {
    switch (status) {
      case "valid":
      case "success":
        return (
          <CheckCircle2
            size={19}
            className="text-[#16A34A] fill-[#16A34A] stroke-white shrink-0"
          />
        );
      case "warning":
        return (
          <AlertCircle
            size={19}
            className="text-amber-500 fill-amber-100 shrink-0"
          />
        );
      case "error":
      case "failed":
        return (
          <XCircle
            size={19}
            className="text-red-500 fill-red-100 shrink-0"
          />
        );
      case "pending":
      default:
        return (
          <Clock
            size={19}
            className="text-slate-400 shrink-0"
          />
        );
    }
  };

  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white p-6 shadow-sm ${className}`}
    >
      <h2 className="text-base font-semibold text-slate-900 mb-4">{title}</h2>
      <div className="border-b border-slate-100 mb-5" />

      <ul className="space-y-3.5">
        {items.map((item, idx) => {
          const label = typeof item === "string" ? item : item.label;
          const status = typeof item === "string" ? "valid" : item.status || "valid";

          return (
            <li
              key={label || idx}
              className="flex items-center gap-3 text-sm text-slate-800 font-medium"
            >
              {getIcon(status)}
              <span>{label}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

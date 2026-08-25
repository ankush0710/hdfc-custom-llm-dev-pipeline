"use client";
import Link from "next/link";
import { GitBranch, ArrowUpRight } from "lucide-react";

export default function LineageCard({
  title = "Used By (Lineage)",
  icon: HeaderIcon = GitBranch,
  items = [],
  emptyText = "No downstream dependencies linked.",
  className = "",
}) {
  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white p-6 shadow-sm ${className}`}
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-slate-900">{title}</h2>
        {HeaderIcon && <HeaderIcon size={18} className="text-slate-400" />}
      </div>
      <div className="border-b border-slate-100 mb-5" />

      {items.length > 0 ? (
        <div className="space-y-3">
          {items.map((item, idx) => {
            const label = typeof item === "string" ? item : item.label;
            const href = typeof item === "object" ? item.href : "#";

            return (
              <Link
                key={label || idx}
                href={href}
                className="flex items-center gap-2.5 text-sm font-medium text-slate-700 hover:text-blue-700 transition-colors group"
              >
                <ArrowUpRight
                  size={16}
                  className="text-slate-400 group-hover:text-blue-700 transition-colors"
                />
                <span>{label}</span>
              </Link>
            );
          })}
        </div>
      ) : (
        <p className="text-xs text-slate-500">{emptyText}</p>
      )}
    </div>
  );
}

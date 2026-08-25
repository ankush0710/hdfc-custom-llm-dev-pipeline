"use client";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function Breadcrumbs({
  backHref,
  backLabel = "Back",
  className = "",
}) {
  return (
    <div
      className={`flex flex-wrap items-center justify-between gap-3 mb-4 ${className}`}
    >
      {backHref && (
        <Link
          href={backHref}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 px-3 py-1.5 rounded-md shadow-xs transition-colors"
        >
          <ArrowLeft size={14} />
          <span>{backLabel}</span>
        </Link>
      )}
    </div>
  );
}

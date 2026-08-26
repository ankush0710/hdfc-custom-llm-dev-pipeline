"use client";

import { Info, Database, Calendar, Cpu, Layers } from "lucide-react";

export default function ModelOverviewCard({
  baseModel = "Llama-3-70B-Instruct",
  totalParameters = "70.0 Billion",
  datasetName = "hdfc-kb-v4",
  trainingDate = "Oct 24, 2023",
}) {
  return (
    <div className="h-full bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm flex flex-col justify-between">
      {/* Title */}
      <div className="flex items-center gap-2 mb-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-50 text-[#002B55]">
          <Info size={16} />
        </div>
        <h3 className="text-base font-bold text-gray-900">
          Model Overview
        </h3>
      </div>

      {/* 4-Grid of Metadata */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {/* Item 1: Base Model */}
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
            Base Model
          </span>
          <p className="text-sm font-bold text-gray-900 truncate" title={baseModel}>
            {baseModel}
          </p>
        </div>

        {/* Item 2: Total Parameters */}
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
            Total Parameters
          </span>
          <p className="text-sm font-bold text-gray-900 font-mono">
            {totalParameters}
          </p>
        </div>

        {/* Item 3: Fine-Tuned Dataset */}
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
            Fine-Tuned Dataset
          </span>
          <span className="inline-flex rounded-md bg-slate-100 px-2.5 py-0.5 text-xs font-mono font-medium text-slate-700 truncate max-w-full">
            {datasetName}
          </span>
        </div>

        {/* Item 4: Training Date */}
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
            Training Date
          </span>
          <p className="text-sm font-medium text-gray-700 font-mono">
            {trainingDate}
          </p>
        </div>
      </div>
    </div>
  );
}

"use client";

import { Database, Cpu, Layers, Hash, Zap, Boxes } from "lucide-react";

export default function TrainingConfigCard({
  datasetName = "HDFC Dataset v3",
  datasetVersion = "1.0",
  baseModel = "Llama-3-8B",
  trainingMethod = "LoRA",
  epochs = 3,
  learningRate = 0.0002,
  batchSize = 4,
}) {
  return (
    <div className="bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm flex flex-col justify-between">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-bold text-gray-900">
          Configuration
        </h3>
        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
          PEFT / SFT
        </span>
      </div>

      {/* Config list */}
      <div className="space-y-3.5">
        {/* Dataset */}
        <div className="flex items-center justify-between text-xs pb-2.5 border-b border-gray-100">
          <div className="flex items-center gap-2 text-gray-500 font-semibold uppercase tracking-wider">
            <Database size={14} className="text-blue-600" />
            <span>Dataset</span>
          </div>
          <span className="font-semibold text-gray-900 font-mono">
            {datasetName} <span className="text-blue-600 font-normal">(v{datasetVersion})</span>
          </span>
        </div>

        {/* Model */}
        <div className="flex items-center justify-between text-xs pb-2.5 border-b border-gray-100">
          <div className="flex items-center gap-2 text-gray-500 font-semibold uppercase tracking-wider">
            <Cpu size={14} className="text-indigo-600" />
            <span>Model</span>
          </div>
          <span className="font-semibold text-gray-900 font-mono">
            {baseModel}
          </span>
        </div>

        {/* Method */}
        <div className="flex items-center justify-between text-xs pb-2.5 border-b border-gray-100">
          <div className="flex items-center gap-2 text-gray-500 font-semibold uppercase tracking-wider">
            <Layers size={14} className="text-purple-600" />
            <span>Method</span>
          </div>
          <span className="font-mono font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded text-[11px]">
            {trainingMethod}
          </span>
        </div>

        {/* Epochs */}
        <div className="flex items-center justify-between text-xs pb-2.5 border-b border-gray-100">
          <div className="flex items-center gap-2 text-gray-500 font-semibold uppercase tracking-wider">
            <Hash size={14} className="text-emerald-600" />
            <span>Epochs</span>
          </div>
          <span className="font-mono font-bold text-gray-800 bg-blue-50 text-blue-700 px-2 py-0.5 rounded">
            {epochs}
          </span>
        </div>

        {/* Learning Rate */}
        <div className="flex items-center justify-between text-xs pb-2.5 border-b border-gray-100">
          <div className="flex items-center gap-2 text-gray-500 font-semibold uppercase tracking-wider">
            <Zap size={14} className="text-amber-500" />
            <span>Learning Rate</span>
          </div>
          <span className="font-mono font-semibold text-gray-800 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded">
            {learningRate}
          </span>
        </div>

        {/* Batch Size */}
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-gray-500 font-semibold uppercase tracking-wider">
            <Boxes size={14} className="text-cyan-600" />
            <span>Batch Size</span>
          </div>
          <span className="font-mono font-semibold text-gray-800">
            {batchSize}
          </span>
        </div>
      </div>
    </div>
  );
}

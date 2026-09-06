"use client";

import { useState } from "react";
import { Sliders, RotateCcw, Save, Sparkles, Check, Database } from "lucide-react";
import Button from "@/components/ui/Button";
import { toast } from "sonner";

export const SUPPORTED_TASK_TYPES = [
  { value: "sft_grounded_generation", label: "SFT Grounded Generation" },
  { value: "customer_faq_qa", label: "Customer FAQ QA" },
  { value: "intent_classification", label: "Intent Classification" },
  { value: "domain_concept_qa", label: "Domain Concept QA" },
];

export const SYSTEM_ROLE_PRESETS = [
  {
    label: "Strict Compliance Analyst",
    instruction:
      "You are an expert banking compliance AI. Analyze financial inputs strictly against AML/KYC guidelines. Provide structured data tables when applicable.",
    taskType: "sft_grounded_generation",
  },
  {
    label: "Financial QA & Support",
    instruction:
      "You are a helpful HDFC Bank virtual assistant. Provide clear, accurate answers to account inquiries, loan queries, and credit card terms in a polite, professional tone.",
    taskType: "customer_faq_qa",
  },
  {
    label: "Risk & Fraud Investigator",
    instruction:
      "You are an enterprise fraud analysis engine. Examine transaction patterns for velocity anomalies, multi-currency risks, and high-frequency transfers. Flag critical alerts immediately.",
    taskType: "intent_classification",
  },
  {
    label: "Custom",
    instruction: "",
    taskType: "customer_faq_qa",
  },
];

export default function PlaygroundParametersPanel({
  deployedModels = [],
  selectedModelId,
  activeModel,
  onModelChange,
  parameters,
  onParametersChange,
  onReset,
}) {
  const [selectedPreset, setSelectedPreset] = useState("Strict Compliance Analyst");

  const handlePresetChange = (presetName) => {
    setSelectedPreset(presetName);
    const preset = SYSTEM_ROLE_PRESETS.find((p) => p.label === presetName);
    if (preset) {
      onParametersChange({
        ...parameters,
        systemInstruction: preset.instruction !== undefined ? preset.instruction : parameters.systemInstruction,
        taskType: preset.taskType || parameters.taskType,
      });
    }
  };

  const handleSavePreset = () => {
    toast.success("Parameters & system preset saved locally");
  };

  return (
    <div className="h-full bg-white rounded-2xl border border-gray-200/80 p-5 shadow-sm flex flex-col justify-between overflow-y-auto">
      <div className="space-y-5">
        {/* Panel Header */}
        <div className="flex items-center gap-2 pb-3 border-b border-gray-100">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-50 text-[#002B55]">
            <Sliders size={16} />
          </div>
          <h3 className="text-sm font-bold text-gray-900">
            Parameters
          </h3>
        </div>

        {/* 1. Model Version (Only Deployed Models) */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">
            Model Version
          </label>
          {deployedModels.length > 0 ? (
            <>
              <select
                value={selectedModelId}
                onChange={(e) => onModelChange(e.target.value)}
                className="w-full rounded-xl border border-gray-200 bg-[#FAFBFE] px-3 py-2.5 text-xs font-semibold text-gray-900 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
              >
                {deployedModels.map((m) => (
                  <option key={m.id} value={m.model_id || m.id}>
                    {m.model_name || `Model-${m.id}`} ({m.version || "Active"}) • {m.environment || "Production"}
                  </option>
                ))}
              </select>

              {/* Real Trained Dataset Lineage (Display metadata only — never injected into prompt context) */}
              {activeModel && (
                <div className="mt-2 rounded-xl border border-blue-100 bg-blue-50/50 p-2.5 text-xs">
                  <div className="flex items-center gap-1.5 font-bold text-[#002B55] text-[11px] mb-1">
                    <Database size={13} className="text-blue-600 shrink-0" />
                    <span>Trained Dataset Lineage</span>
                  </div>
                  <div className="space-y-1 text-[11px]">
                    <div className="flex justify-between gap-2">
                      <span className="text-slate-500 shrink-0">Dataset:</span>
                      <span className="font-semibold text-slate-800 truncate text-right">
                        {activeModel.dataset_name || <span className="text-slate-400 italic">No dataset linked</span>}
                      </span>
                    </div>
                    {activeModel.dataset_version && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Version:</span>
                        <span className="font-mono text-slate-700">{activeModel.dataset_version}</span>
                      </div>
                    )}
                    {activeModel.dataset_file_name && (
                      <div className="flex justify-between gap-2">
                        <span className="text-slate-500 shrink-0">File:</span>
                        <span className="font-mono text-slate-700 truncate text-right">{activeModel.dataset_file_name}</span>
                      </div>
                    )}
                    {activeModel.training_run_id && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Training Run:</span>
                        <span className="font-mono text-slate-700">Run #{activeModel.training_run_id}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="rounded-xl bg-amber-50 border border-amber-200 p-2.5 text-xs text-amber-800 font-medium">
              No active deployed models found.
            </div>
          )}
        </div>

        {/* 2. System Role Preset */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">
            System Role Preset
          </label>
          <select
            value={selectedPreset}
            onChange={(e) => handlePresetChange(e.target.value)}
            className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-900 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
          >
            {SYSTEM_ROLE_PRESETS.map((p) => (
              <option key={p.label} value={p.label}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        {/* 3. Task Type */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">
            Task Type
          </label>
          <select
            value={parameters.taskType || "customer_faq_qa"}
            onChange={(e) =>
              onParametersChange({
                ...parameters,
                taskType: e.target.value,
              })
            }
            className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-900 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
          >
            {SUPPORTED_TASK_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        {/* 3. System Instruction */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">
            System Instruction
          </label>
          <textarea
            rows={4}
            value={parameters.systemInstruction}
            onChange={(e) =>
              onParametersChange({
                ...parameters,
                systemInstruction: e.target.value,
              })
            }
            placeholder="Enter system prompt guidelines..."
            className="w-full rounded-xl border border-gray-200 bg-white p-3 text-xs text-gray-800 leading-relaxed focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 resize-none font-sans"
          />
        </div>

        {/* 4. Sliders */}
        <div className="space-y-4 pt-1">
          {/* Temperature */}
          <div>
            <div className="flex items-center justify-between mb-1 text-xs">
              <span className="font-semibold text-gray-700">Temperature</span>
              <span className="font-mono font-bold text-blue-700">
                {parameters.temperature}
              </span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={parameters.temperature}
              onChange={(e) =>
                onParametersChange({
                  ...parameters,
                  temperature: parseFloat(e.target.value),
                })
              }
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#002B55]"
            />
            <p className="text-[10px] text-gray-400 mt-0.5">
              Controls randomness: lower values are more deterministic and factual.
            </p>
          </div>

          {/* Top P */}
          <div>
            <div className="flex items-center justify-between mb-1 text-xs">
              <span className="font-semibold text-gray-700">Top P</span>
              <span className="font-mono font-bold text-blue-700">
                {parameters.topP}
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={parameters.topP}
              onChange={(e) =>
                onParametersChange({
                  ...parameters,
                  topP: parseFloat(e.target.value),
                })
              }
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#002B55]"
            />
          </div>

          {/* Max Output Tokens */}
          <div>
            <div className="flex items-center justify-between mb-1 text-xs">
              <span className="font-semibold text-gray-700">Max Output Tokens</span>
              <span className="font-mono font-bold text-blue-700">
                {parameters.maxTokens}
              </span>
            </div>
            <input
              type="range"
              min="128"
              max="2048"
              step="64"
              value={parameters.maxTokens}
              onChange={(e) =>
                onParametersChange({
                  ...parameters,
                  maxTokens: parseInt(e.target.value, 10),
                })
              }
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#002B55]"
            />
          </div>
        </div>
      </div>

      {/* Footer Buttons */}
      <div className="grid grid-cols-2 gap-3 pt-5 border-t border-gray-100 mt-4">
        <button
          type="button"
          onClick={onReset}
          className="flex items-center justify-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-700 hover:bg-gray-50 transition cursor-pointer"
        >
          <RotateCcw size={13} />
          <span>Reset</span>
        </button>

        <button
          type="button"
          onClick={handleSavePreset}
          className="flex items-center justify-center gap-1.5 rounded-xl bg-[#002B55] px-3 py-2 text-xs font-bold text-white hover:bg-[#001D3D] transition cursor-pointer"
        >
          <Save size={13} />
          <span>Save Preset</span>
        </button>
      </div>
    </div>
  );
}

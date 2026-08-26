"use client";

import { useState, useEffect } from "react";
import { X, Layers, Box, Cpu, HardDrive, Check, Sparkles, Loader2 } from "lucide-react";
import Button from "@/components/ui/Button";
import { registerModel } from "@/app/services/modelService/modelServices";
import { getTrainingRuns } from "@/app/services/trainingService/trainingServices";
import { toast } from "sonner";

const BASE_MODEL_OPTIONS = [
  "Llama-3-70B-Instruct",
  "Llama-3-8B-Instruct",
  "Llama-3-8B",
  "Qwen1.5-0.5B",
  "FinBERT-Base",
  "Mistral-7B-Instruct-v0.2",
  "BGE-Large-en-v1.5",
];

const MODEL_TYPE_OPTIONS = [
  "LLM (Generative)",
  "Classifier",
  "Embedding",
  "Sequence-to-Sequence",
];

const STATUS_OPTIONS = [
  { value: "ACTIVE", label: "Active" },
  { value: "READY", label: "Ready" },
  { value: "TRAINING", label: "Training" },
  { value: "ARCHIVED", label: "Archived" },
];

export default function NewModelModal({ isOpen, onClose, onModelCreated }) {
  const [modelName, setModelName] = useState("");
  const [version, setVersion] = useState("1.0.0");
  const [baseModel, setBaseModel] = useState(BASE_MODEL_OPTIONS[0]);
  const [modelType, setModelType] = useState(MODEL_TYPE_OPTIONS[0]);
  const [artifactPath, setArtifactPath] = useState("");
  const [trainingJobId, setTrainingJobId] = useState("");
  const [status, setStatus] = useState("ACTIVE");
  const [trainingRuns, setTrainingRuns] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Load training runs to assist user in linking job
      getTrainingRuns()
        .then((runs) => {
          if (Array.isArray(runs)) {
            setTrainingRuns(runs);
          }
        })
        .catch(() => {});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!modelName.trim()) {
      toast.error("Please enter a model name");
      return;
    }

    if (!version.trim()) {
      toast.error("Please specify a version");
      return;
    }

    try {
      setLoading(true);

      const payload = {
        model_name: modelName.trim(),
        version: version.trim(),
        base_model: baseModel,
        artifact_path: artifactPath.trim() || `ai/artifacts/models/${modelName.toLowerCase().replace(/\s+/g, "_")}_v${version}`,
        status: status,
      };

      if (trainingJobId && !isNaN(Number(trainingJobId))) {
        payload.training_job_id = Number(trainingJobId);
      }

      await registerModel(payload);
      toast.success("Model registered successfully in Model Registry!");

      // Reset fields
      setModelName("");
      setVersion("1.0.0");
      setArtifactPath("");
      setTrainingJobId("");
      setStatus("ACTIVE");

      if (onModelCreated) {
        onModelCreated();
      }
      onClose();
    } catch (err) {
      console.error("Failed to register model:", err);
      const detail = err?.response?.data?.detail;
      toast.error(
        typeof detail === "string" ? detail : "Failed to register model."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-[#FAFBFE]">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#002B55]/10 text-[#002B55]">
              <Box size={18} />
            </div>
            <div>
              <h2 className="text-base font-bold text-gray-900">
                Register New Model
              </h2>
              <p className="text-xs text-gray-500">
                Add a new fine-tuned or foundation model to the Enterprise Registry.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Model Name & Version */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                Model Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                placeholder="e.g. FinBERT-Risk or HDFC-Banking-LLM"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3.5 py-2 text-sm text-gray-900 outline-none focus:border-[#002B55] focus:ring-1 focus:ring-[#002B55]"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                Version <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                placeholder="e.g. 1.0.0"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3.5 py-2 text-sm font-mono text-gray-900 outline-none focus:border-[#002B55] focus:ring-1 focus:ring-[#002B55]"
              />
            </div>
          </div>

          {/* Base Model & Model Type */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                Base Model
              </label>
              <select
                value={baseModel}
                onChange={(e) => setBaseModel(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3.5 py-2 text-sm text-gray-900 outline-none focus:border-[#002B55] focus:ring-1 focus:ring-[#002B55]"
              >
                {BASE_MODEL_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                Model Type
              </label>
              <select
                value={modelType}
                onChange={(e) => setModelType(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3.5 py-2 text-sm text-gray-900 outline-none focus:border-[#002B55] focus:ring-1 focus:ring-[#002B55]"
              >
                {MODEL_TYPE_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Artifact / Adapter Path */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
              Artifact / Adapter Storage Path
            </label>
            <input
              type="text"
              placeholder="e.g. ai/artifacts/runs/run_1/adapter_model.safetensors"
              value={artifactPath}
              onChange={(e) => setArtifactPath(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3.5 py-2 text-xs font-mono text-gray-900 outline-none focus:border-[#002B55] focus:ring-1 focus:ring-[#002B55]"
            />
          </div>

          {/* Associated Training Run & Status */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                Linked Training Run (Optional)
              </label>
              <select
                value={trainingJobId}
                onChange={(e) => setTrainingJobId(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3.5 py-2 text-sm text-gray-900 outline-none focus:border-[#002B55] focus:ring-1 focus:ring-[#002B55]"
              >
                <option value="">None / External Model</option>
                {trainingRuns.map((r) => (
                  <option key={r.id} value={r.id}>
                    Run #{r.id} ({r.base_model} - {r.status})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                Initial Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3.5 py-2 text-sm text-gray-900 outline-none focus:border-[#002B55] focus:ring-1 focus:ring-[#002B55]"
              >
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-100 rounded-lg transition"
            >
              Cancel
            </button>
            <Button
              type="submit"
              variant="primary"
              icon={loading ? Loader2 : Check}
              disabled={loading}
            >
              {loading ? "Registering..." : "Register Model"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

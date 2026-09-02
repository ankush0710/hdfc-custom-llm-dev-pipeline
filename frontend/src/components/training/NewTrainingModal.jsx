"use client";

import { useState, useEffect, useCallback } from "react";
import { X, Sparkles, AlertCircle, Loader2 } from "lucide-react";
import { getDataset } from "@/app/services/datasetService/datasetServices";
import { createTrainingRun, startTrainingRun } from "@/app/services/trainingService/trainingServices";
import { toast } from "sonner";

export const SUPPORTED_BASE_MODELS = [
  {
    id: "qwen2_5_1_5b_instruct",
    displayName: "Qwen 2.5 1.5B Instruct",
    hfModelId: "Qwen/Qwen2.5-1.5B-Instruct",
    params: "1.54B",
    description: "High-accuracy instruction-tuned enterprise model (1.54B params)",
  },
  {
    id: "qwen3_0_6b",
    displayName: "Qwen 3 0.6B",
    hfModelId: "Qwen/Qwen3-0.6B",
    params: "0.6B",
    description: "Ultra-lightweight base model (0.6B params) optimized for edge & fast fine-tuning",
  },
  {
    id: "smollm2_1_7b_instruct",
    displayName: "SmolLM2 1.7B Instruct",
    hfModelId: "HuggingFaceTB/SmolLM2-1.7B-Instruct",
    params: "1.7B",
    description: "High-efficiency compact reasoning model (1.7B params)",
  },
];

export default function NewTrainingModal({ isOpen, onClose, onRunCreated }) {
  const [datasets, setDatasets] = useState([]);
  const [loadingDatasets, setLoadingDatasets] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    base_model: SUPPORTED_BASE_MODELS[0].id,
    dataset_version_id: "",
    training_method: "LoRA",
    epochs: 3,
    learning_rate: 0.0002,
    batch_size: 4,
    autoStart: true,
  });

  const loadDatasets = useCallback(async () => {
    try {
      setLoadingDatasets(true);
      const data = await getDataset();
      const datasetList = Array.isArray(data) ? data : [];
      setDatasets(datasetList);

      // Collect all versions across datasets
      const allVersions = [];
      datasetList.forEach((d) => {
        (d.versions || []).forEach((v) => {
          allVersions.push({
            ...v,
            dataset_name: d.dataset_name,
          });
        });
      });

      // Prefer first processed version or fallback to first available version
      if (allVersions.length > 0 && !formData.dataset_version_id) {
        const processedVer = allVersions.find(
          (v) => String(v.status || "").toLowerCase() === "processed"
        );
        const defaultVer = processedVer || allVersions[0];
        setFormData((prev) => ({
          ...prev,
          dataset_version_id: String(defaultVer.id),
        }));
      }
    } catch (err) {
      console.error("Failed to load datasets:", err);
    } finally {
      setLoadingDatasets(false);
    }
  }, [formData.dataset_version_id]);

  useEffect(() => {
    if (isOpen) {
      loadDatasets();
    }
  }, [isOpen, loadDatasets]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    const versionId = Number(formData.dataset_version_id);
    if (!formData.dataset_version_id || isNaN(versionId) || versionId <= 0) {
      toast.error("Please select a valid dataset version.");
      return;
    }

    const epochs = Number(formData.epochs);
    if (isNaN(epochs) || epochs < 1 || epochs > 20) {
      toast.error("Epochs must be a number between 1 and 20.");
      return;
    }

    const lr = Number(formData.learning_rate);
    if (isNaN(lr) || lr <= 0) {
      toast.error("Learning rate must be greater than 0.");
      return;
    }

    const batchSize = Number(formData.batch_size);
    if (isNaN(batchSize) || batchSize < 1) {
      toast.error("Batch size must be at least 1.");
      return;
    }

    try {
      setSubmitting(true);
      const runPayload = {
        base_model: formData.base_model || SUPPORTED_BASE_MODELS[0].id,
        dataset_version_id: versionId,
        training_method: formData.training_method || "LoRA",
        epochs: epochs,
        learning_rate: lr,
        batch_size: batchSize,
      };

      const createdRun = await createTrainingRun(runPayload);

      if (formData.autoStart && createdRun?.id) {
        try {
          await startTrainingRun(createdRun.id);
        } catch (startErr) {
          console.error("Failed to auto-start training run:", startErr);
        }
      }

      toast.success(`Training Run #${createdRun.id || ""} created successfully!`);
      if (onRunCreated) onRunCreated();
      onClose();
    } catch (err) {
      console.error("Failed to create training run:", err);
      let errorMsg = "Failed to create training run.";
      const detail = err?.response?.data?.detail;
      if (typeof detail === "string") {
        errorMsg = detail;
      } else if (Array.isArray(detail)) {
        errorMsg = detail
          .map((d) => (d.msg ? `${d.loc ? d.loc.slice(1).join(".") + ": " : ""}${d.msg}` : JSON.stringify(d)))
          .join(", ");
      } else if (err?.message) {
        errorMsg = err.message;
      }
      toast.error(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-[#FAFBFE]">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
              <Sparkles size={18} />
            </div>
            <div>
              <h2 className="text-base font-bold text-gray-900">New Training Job</h2>
              <p className="text-xs text-gray-500">Configure parameters for LLM fine-tuning</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Base Model selection */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
              Base Model
            </label>
            <select
              value={formData.base_model}
              onChange={(e) => setFormData({ ...formData, base_model: e.target.value })}
              className="w-full px-3.5 py-2.5 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#002B55] bg-white font-medium text-gray-800"
            >
              {SUPPORTED_BASE_MODELS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.displayName} ({m.params})
                </option>
              ))}
            </select>
            <p className="mt-1 text-[11px] text-gray-500">
              {SUPPORTED_BASE_MODELS.find((m) => m.id === formData.base_model)?.description}
            </p>
          </div>

          {/* Dataset selection */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
              Dataset Version
            </label>
            {loadingDatasets ? (
              <div className="flex items-center gap-2 text-xs text-gray-500 py-2">
                <Loader2 size={14} className="animate-spin text-blue-600" />
                <span>Loading datasets. Please wait...</span>
              </div>
            ) : datasets.length === 0 ? (
              <div className="flex items-center gap-2 p-3 bg-amber-50 rounded-lg text-xs text-amber-800 border border-amber-200">
                <AlertCircle size={15} />
                <span>No datasets found. Please upload a dataset first.</span>
              </div>
            ) : (
              <select
                value={formData.dataset_version_id}
                onChange={(e) => setFormData({ ...formData, dataset_version_id: e.target.value })}
                className="w-full px-3.5 py-2.5 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#002B55] bg-white font-medium text-gray-800"
                required
              >
                <option value="">Select a dataset version</option>
                {datasets.map((d) =>
                  (d.versions || []).map((v) => {
                    const isProcessed = String(v.status || "").toLowerCase() === "processed";
                    return (
                      <option key={v.id} value={v.id}>
                        {d.dataset_name} (v{v.version}) — {isProcessed ? "PROCESSED ✓" : `${v.status || "PENDING"}`} — {v.file_type || "CSV"}
                      </option>
                    );
                  })
                )}
              </select>
            )}
          </div>

          {/* Method and Hyperparameters Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Method
              </label>
              <select
                value={formData.training_method}
                onChange={(e) => setFormData({ ...formData, training_method: e.target.value })}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#002B55] bg-white font-medium text-gray-800"
              >
                <option value="LoRA">LoRA (PEFT)</option>
                <option value="QLoRA">QLoRA (4-bit)</option>
                <option value="Full">Full Fine-Tuning</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Epochs
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={formData.epochs}
                onChange={(e) => setFormData({ ...formData, epochs: e.target.value })}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#002B55] text-gray-800 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Learning Rate
              </label>
              <input
                type="number"
                step="0.00005"
                value={formData.learning_rate}
                onChange={(e) => setFormData({ ...formData, learning_rate: e.target.value })}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#002B55] text-gray-800 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Batch Size
              </label>
              <input
                type="number"
                min="1"
                max="64"
                value={formData.batch_size}
                onChange={(e) => setFormData({ ...formData, batch_size: e.target.value })}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#002B55] text-gray-800 font-mono"
              />
            </div>
          </div>

          {/* Auto-start checkbox */}
          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="autoStart"
              checked={formData.autoStart}
              onChange={(e) => setFormData({ ...formData, autoStart: e.target.checked })}
              className="h-4 w-4 rounded border-gray-300 text-[#002B55] focus:ring-[#002B55]"
            />
            <label htmlFor="autoStart" className="text-xs font-medium text-gray-700 cursor-pointer">
              Launch training immediately upon creation
            </label>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white bg-[#002B55] hover:bg-[#001D3A] rounded-lg shadow-sm transition disabled:opacity-50"
            >
              {submitting && <Loader2 size={16} className="animate-spin" />}
              <span>{submitting ? "Launching..." : "Start Training"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

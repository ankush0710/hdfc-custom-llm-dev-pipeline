"use client";

import { useState, useEffect } from "react";
import { X, Play, Loader2, Cpu, Database, Activity } from "lucide-react";
import Button from "@/components/ui/Button";
import { getModels } from "@/app/services/modelService/modelServices";
import { getTrainingRuns } from "@/app/services/trainingService/trainingServices";
import { getDatasets } from "@/app/services/datasetService/datasetServices";
import { createEvaluation } from "@/app/services/evaluationService/evaluationServices";
import { toast } from "sonner";

export default function NewEvaluationModal({ isOpen, onClose, onEvaluationCreated }) {
  const [models, setModels] = useState([]);
  const [runs, setRuns] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [loadingData, setLoadingData] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    model_id: "",
    run_id: "",
    test_dataset_id: "",
  });

  useEffect(() => {
    if (!isOpen) return;

    const loadOptions = async () => {
      try {
        setLoadingData(true);
        const [modelsData, runsData, datasetsData] = await Promise.all([
          getModels().catch(() => []),
          getTrainingRuns().catch(() => []),
          getDatasets().catch(() => []),
        ]);

        const validModels = Array.isArray(modelsData) ? modelsData : [];
        const validRuns = Array.isArray(runsData) ? runsData : [];
        const validDatasets = Array.isArray(datasetsData) ? datasetsData : [];

        setModels(validModels);
        setRuns(validRuns);
        setDatasets(validDatasets);

        // Pre-select first items if available
        const firstDatasetVersion = validDatasets.find((d) => d.versions && d.versions.length > 0)?.versions[0];
        setFormData({
          model_id: validModels.length > 0 ? String(validModels[0].id) : "",
          run_id: validRuns.length > 0 ? String(validRuns[0].id) : "",
          test_dataset_id: firstDatasetVersion ? String(firstDatasetVersion.id) : "",
        });
      } catch (err) {
        console.error("Failed to load evaluation options:", err);
      } finally {
        setLoadingData(false);
      }
    };

    loadOptions();
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.model_id || !formData.run_id || !formData.test_dataset_id) {
      toast.error("Please complete all required fields");
      return;
    }

    try {
      setSubmitting(true);
      await createEvaluation({
        model_id: parseInt(formData.model_id, 10),
        run_id: parseInt(formData.run_id, 10),
        test_dataset_id: parseInt(formData.test_dataset_id, 10),
        auto_start: true,
      });

      toast.success("Evaluation initiated successfully!", {
        description: "Benchmark scoring worker is now running in the background.",
      });

      if (onEvaluationCreated) onEvaluationCreated();
      onClose();
    } catch (err) {
      console.error("Failed to create evaluation:", err);
      toast.error(err?.response?.data?.detail || "Failed to start evaluation");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg bg-white rounded-2xl border border-gray-200/80 shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-[#FAFBFE]">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-[#002B55]">
              <Activity size={18} />
            </div>
            <div>
              <h2 className="text-base font-bold text-gray-900">
                Launch New Evaluation
              </h2>
              <p className="text-xs text-gray-500">
                Run benchmark scoring against validation test sets.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form Body */}
        {loadingData ? (
          <div className="p-12 flex flex-col items-center justify-center gap-3">
            <Loader2 className="h-7 w-7 animate-spin text-[#002B55]" />
            <p className="text-xs text-gray-500 font-medium">
              Loading models and datasets. Please wait...
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {/* Model Select */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Target Model <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.model_id}
                onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
                className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-xs font-medium text-gray-900 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                required
              >
                <option value="">Select a registered model</option>
                {models.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.model_name} (v{m.version}) - {m.base_model}
                  </option>
                ))}
              </select>
            </div>

            {/* Training Run */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Training Run Origin <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.run_id}
                onChange={(e) => setFormData({ ...formData, run_id: e.target.value })}
                className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-xs font-medium text-gray-900 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                required
              >
                <option value="">Select training run</option>
                {runs.map((r) => (
                  <option key={r.id} value={r.id}>
                    Run #{r.id} ({r.base_model} - {r.status})
                  </option>
                ))}
              </select>
            </div>

            {/* Test Dataset Version */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Test Dataset Version <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.test_dataset_id}
                onChange={(e) => setFormData({ ...formData, test_dataset_id: e.target.value })}
                className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-xs font-medium text-gray-900 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                required
              >
                <option value="">Select test dataset version</option>
                {datasets.map((d) =>
                  (d.versions || []).map((v) => (
                    <option key={v.id} value={v.id}>
                      {d.dataset_name} (v{v.version}) - {v.status || "Ready"}
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-100">
              <Button variant="default" onClick={onClose} type="button">
                Cancel
              </Button>
              <Button
                variant="primary"
                icon={submitting ? Loader2 : Play}
                type="submit"
                disabled={submitting}
              >
                {submitting ? "Launching..." : "Start Evaluation"}
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

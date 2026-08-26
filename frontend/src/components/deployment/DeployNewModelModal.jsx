"use client";

import { useState, useEffect } from "react";
import { X, Rocket, Loader2, Server } from "lucide-react";
import Button from "@/components/ui/Button";
import { getModels } from "@/app/services/modelService/modelServices";
import { deployModel } from "@/app/services/deploymentService/deploymentServices";
import { toast } from "sonner";

export default function DeployNewModelModal({ isOpen, onClose, onModelDeployed }) {
  const [models, setModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    model_id: "",
    version: "1.0",
    environment: "Production",
  });

  useEffect(() => {
    if (!isOpen) return;

    const loadModels = async () => {
      try {
        setLoadingModels(true);
        const data = await getModels();
        const validList = Array.isArray(data) ? data : [];
        setModels(validList);

        if (validList.length > 0) {
          setFormData({
            model_id: String(validList[0].id),
            version: validList[0].version || "1.0",
            environment: "Production",
          });
        }
      } catch (err) {
        console.error("Failed to load models for deployment:", err);
      } finally {
        setLoadingModels(false);
      }
    };

    loadModels();
  }, [isOpen]);

  if (!isOpen) return null;

  const handleModelChange = (modelId) => {
    const selected = models.find((m) => String(m.id) === String(modelId));
    setFormData({
      ...formData,
      model_id: modelId,
      version: selected?.version || "1.0",
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.model_id) {
      toast.error("Please select a target model to deploy");
      return;
    }

    try {
      setSubmitting(true);
      await deployModel({
        model_id: parseInt(formData.model_id, 10),
        version: formData.version,
        environment: formData.environment,
      });

      toast.success("Model deployed successfully!", {
        description: `Serving endpoint provisioned in ${formData.environment}.`,
      });

      if (onModelDeployed) onModelDeployed();
      onClose();
    } catch (err) {
      console.error("Failed to deploy model:", err);
      toast.error(err?.response?.data?.detail || "Failed to deploy model");
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
              <Server size={18} />
            </div>
            <div>
              <h2 className="text-base font-bold text-gray-900">
                Deploy New Model
              </h2>
              <p className="text-xs text-gray-500">
                Deploy registered weights to an enterprise serving cluster.
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
        {loadingModels ? (
          <div className="p-12 flex flex-col items-center justify-center gap-3">
            <Loader2 className="h-7 w-7 animate-spin text-[#002B55]" />
            <p className="text-xs text-gray-500 font-medium">
              Loading available models...
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {/* Target Model */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Target Model <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.model_id}
                onChange={(e) => handleModelChange(e.target.value)}
                className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-xs font-medium text-gray-900 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                required
              >
                {models.length > 0 ? (
                  models.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.model_name} (v{m.version}) - {m.base_model}
                    </option>
                  ))
                ) : (
                  <option value="1">HDFC Banking Assistant (v1.2)</option>
                )}
              </select>
            </div>

            {/* Version */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Version Tag <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.version}
                onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-xs font-medium text-gray-900 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                required
              />
            </div>

            {/* Environment */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Target Environment <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.environment}
                onChange={(e) => setFormData({ ...formData, environment: e.target.value })}
                className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-xs font-medium text-gray-900 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                required
              >
                <option value="Production">Production</option>
                <option value="Staging">Staging</option>
                <option value="Development">Development</option>
              </select>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-100">
              <Button variant="default" onClick={onClose} type="button">
                Cancel
              </Button>
              <Button
                variant="primary"
                icon={submitting ? Loader2 : Rocket}
                type="submit"
                disabled={submitting}
              >
                {submitting ? "Deploying..." : "Deploy Model"}
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

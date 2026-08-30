"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Cpu,
  Database,
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
  RefreshCw,
  FolderArchive,
  Activity,
  Layers,
  FileCode,
  Terminal,
} from "lucide-react";
import Breadcrumbs from "@/components/ui/Breadcrumbs";
import DetailHeader from "@/components/ui/DetailHeader";
import Button from "@/components/ui/Button";
import MetadataCard from "@/components/ui/MetadataCard";
import { getTrainingRunById } from "@/app/services/trainingService/trainingServices";
import { toast } from "sonner";

export default function TrainingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id;

  const [trainingRun, setTrainingRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchDetail = useCallback(async (isSilent = false) => {
    if (!id) return;
    try {
      if (!isSilent) setLoading(true);
      else setRefreshing(true);

      const data = await getTrainingRunById(id);
      if (data) {
        setTrainingRun(data);
        setError(null);
      } else {
        setError(`Training run #${id} not found`);
      }
    } catch (err) {
      console.error("Failed to fetch training run detail:", err);
      setError(err?.response?.data?.detail || "Failed to load training run detail");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDetail();

    // Auto poll while running
    const interval = setInterval(() => {
      fetchDetail(true);
    }, 3000);

    return () => clearInterval(interval);
  }, [fetchDetail]);

  const status = (trainingRun?.status || "QUEUED").toUpperCase();
  const progress = trainingRun?.progress ?? trainingRun?.job_progress ?? (status === "COMPLETED" ? 100 : 0);

  const overviewItems = useMemo(() => {
    if (!trainingRun) return [];
    return [
      { label: "Run ID", value: `#${trainingRun.id}` },
      { label: "Status", value: status },
      { label: "Base Model", value: trainingRun.base_model || "Qwen/Qwen3-0.6B" },
      { label: "Training Method", value: trainingRun.training_method || "LoRA" },
      { label: "Epochs", value: trainingRun.epochs || 1 },
      { label: "Learning Rate", value: trainingRun.learning_rate || 0.0002 },
      { label: "Batch Size", value: trainingRun.batch_size || 1 },
      { label: "Dataset Version ID", value: `#${trainingRun.dataset_version_id}` },
      { label: "Created At", value: trainingRun.created_at ? new Date(trainingRun.created_at).toLocaleString() : "N/A" },
    ];
  }, [trainingRun, status]);

  if (loading && !trainingRun) {
    return (
      <div className="flex h-96 w-full items-center justify-center lg:ml-[280px]">
        <div className="flex flex-col items-center gap-3 text-gray-500">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <p className="text-sm font-medium">Loading training details...</p>
        </div>
      </div>
    );
  }

  if (error || !trainingRun) {
    return (
      <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px] pb-16">
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
          <AlertCircle className="mx-auto h-10 w-10 text-red-500 mb-2" />
          <h2 className="text-base font-bold text-red-900">Training Run Not Found</h2>
          <p className="text-xs text-red-600 mt-1">{error || "Requested training run does not exist."}</p>
          <Button
            variant="outline"
            className="mt-4"
            icon={ArrowLeft}
            onClick={() => router.push("/training")}
          >
            Back to Training Runs
          </Button>
        </div>
      </main>
    );
  }

  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px] pb-16">
      {/* 1. Header Section */}
      <div className="mb-6">
        <div className="mb-3">
          <Breadcrumbs
            items={[
              { label: "Training", href: "/training" },
              { label: `Run #${trainingRun.id}` },
            ]}
          />
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <DetailHeader
            title={`Training Run #${trainingRun.id}`}
            status={status}
            displayId={`TR-${String(trainingRun.id).padStart(3, "0")}`}
            badgeVariant={
              status === "COMPLETED"
                ? "success"
                : status === "RUNNING"
                ? "processing"
                : status === "FAILED"
                ? "error"
                : "default"
            }
            actions={
              <Button
                variant="default"
                icon={RefreshCw}
                onClick={() => fetchDetail(true)}
                disabled={refreshing}
              >
                {refreshing ? "Refreshing..." : "Refresh"}
              </Button>
            }
          />
        </div>
      </div>

      {/* 2. Top Metric & Live Progress Banner */}
      <div className="mb-6 rounded-2xl border border-blue-100 bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 p-6 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 text-xs text-blue-300 font-semibold uppercase tracking-wider">
              <Activity size={15} className="text-blue-400" />
              <span>Live Training Execution Status</span>
            </div>
            <h2 className="text-xl font-black mt-1">
              {status === "RUNNING" ? `Training in Progress (${progress}%)` : status === "COMPLETED" ? "Training Completed (100%)" : `Status: ${status}`}
            </h2>
            <p className="text-xs text-slate-300 mt-1 font-mono">
              Model: {trainingRun.base_model} • Method: {trainingRun.training_method} • Epochs: {trainingRun.epochs}
            </p>
          </div>

          <div className="w-full md:w-80 shrink-0">
            <div className="flex justify-between text-xs font-bold font-mono text-blue-200 mb-1.5">
              <span>Overall Progress</span>
              <span>{progress}%</span>
            </div>
            <div className="h-3 w-full rounded-full bg-blue-950 border border-blue-800/60 overflow-hidden p-0.5">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  status === "COMPLETED"
                    ? "bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.8)]"
                    : status === "FAILED"
                    ? "bg-red-500"
                    : "bg-blue-400 animate-pulse shadow-[0_0_12px_rgba(96,165,250,0.8)]"
                }`}
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 3. Detail Grid: Overview & Hyperparameters */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <MetadataCard title="Training Overview" items={overviewItems} />

        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 border-b border-gray-100 pb-3 mb-4">
            <Layers size={16} className="text-blue-600" />
            <h3 className="text-sm font-bold text-gray-900">Hyperparameters & Configuration</h3>
          </div>

          <div className="grid grid-cols-2 gap-4 text-xs font-medium">
            <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
              <span className="text-gray-400 block text-[11px]">Base Model</span>
              <span className="font-bold text-gray-900 font-mono mt-0.5 block">{trainingRun.base_model}</span>
            </div>

            <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
              <span className="text-gray-400 block text-[11px]">Fine-Tuning Method</span>
              <span className="font-bold text-blue-700 font-mono mt-0.5 block">{trainingRun.training_method}</span>
            </div>

            <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
              <span className="text-gray-400 block text-[11px]">Epochs</span>
              <span className="font-bold text-gray-900 font-mono mt-0.5 block">{trainingRun.epochs}</span>
            </div>

            <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
              <span className="text-gray-400 block text-[11px]">Learning Rate</span>
              <span className="font-bold text-gray-900 font-mono mt-0.5 block">{trainingRun.learning_rate}</span>
            </div>

            <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
              <span className="text-gray-400 block text-[11px]">Batch Size</span>
              <span className="font-bold text-gray-900 font-mono mt-0.5 block">{trainingRun.batch_size}</span>
            </div>

            <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
              <span className="text-gray-400 block text-[11px]">Target Modules</span>
              <span className="font-bold text-gray-900 font-mono mt-0.5 block">q_proj, v_proj, k_proj</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Artifacts Location & Output Storage */}
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm mb-6">
        <div className="flex items-center gap-2 border-b border-gray-100 pb-3 mb-4">
          <FolderArchive size={16} className="text-blue-600" />
          <h3 className="text-sm font-bold text-gray-900">Training Artifacts & Model Checkpoints</h3>
        </div>

        <div className="flex flex-col gap-3 font-mono text-xs">
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200/80">
            <div className="flex items-center gap-2">
              <FileCode size={14} className="text-blue-600" />
              <span className="font-semibold text-gray-700">Model Artifact Directory:</span>
            </div>
            <span className="text-blue-700 font-bold">backend/ai/artifacts/runs/run_{trainingRun.id}</span>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200/80">
            <div className="flex items-center gap-2">
              <FileCode size={14} className="text-purple-600" />
              <span className="font-semibold text-gray-700">LoRA Adapter Weights:</span>
            </div>
            <span className="text-purple-700 font-bold">backend/ai/artifacts/runs/run_{trainingRun.id}/adapter_model.safetensors</span>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200/80">
            <div className="flex items-center gap-2">
              <FileCode size={14} className="text-emerald-600" />
              <span className="font-semibold text-gray-700">Tokenizer & Config:</span>
            </div>
            <span className="text-emerald-700 font-bold">backend/ai/artifacts/runs/run_{trainingRun.id}/adapter_config.json</span>
          </div>
        </div>
      </div>

      {/* 5. Chronological Audit Logs */}
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <div className="flex items-center gap-2 border-b border-gray-100 pb-3 mb-4">
          <Terminal size={16} className="text-blue-600" />
          <h3 className="text-sm font-bold text-gray-900">Execution Logs & Event Audit Feed</h3>
        </div>

        <div className="space-y-2.5 font-mono text-xs">
          <div className="flex items-start gap-3 p-2.5 rounded-lg bg-slate-50">
            <span className="text-gray-400 shrink-0">[{trainingRun.created_at ? new Date(trainingRun.created_at).toLocaleTimeString() : "00:00:00"}]</span>
            <span className="text-slate-700 font-semibold">Training run #{trainingRun.id} created and queued.</span>
          </div>

          <div className="flex items-start gap-3 p-2.5 rounded-lg bg-slate-50">
            <span className="text-blue-500 shrink-0">[{trainingRun.created_at ? new Date(trainingRun.created_at).toLocaleTimeString() : "00:00:00"}]</span>
            <span className="text-slate-800 font-semibold">Background training worker started. Initialized base model {trainingRun.base_model}.</span>
          </div>

          <div className="flex items-start gap-3 p-2.5 rounded-lg bg-slate-50">
            <span className="text-emerald-600 shrink-0">[{trainingRun.created_at ? new Date(trainingRun.created_at).toLocaleTimeString() : "00:00:00"}]</span>
            <span className="text-slate-800 font-semibold">Dataset pre-processing complete. LoRA adapter initialized.</span>
          </div>

          {status === "COMPLETED" && (
            <div className="flex items-start gap-3 p-2.5 rounded-lg bg-emerald-50 border border-emerald-200">
              <span className="text-emerald-700 font-bold shrink-0">[COMPLETE]</span>
              <span className="text-emerald-900 font-bold">Training finished successfully. Artifacts persisted to disk and marked 100%.</span>
            </div>
          )}

          {status === "FAILED" && (
            <div className="flex items-start gap-3 p-2.5 rounded-lg bg-red-50 border border-red-200">
              <span className="text-red-700 font-bold shrink-0">[FAILED]</span>
              <span className="text-red-900 font-bold">{trainingRun.error_message || "Training run failed during execution."}</span>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

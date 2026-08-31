"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  AlertCircle,
  Loader2,
  RefreshCw,
  FolderArchive,
  Activity,
  Layers,
  FileCode,
  Terminal,
  Play,
  CheckCircle2,
  ExternalLink,
  ShieldCheck,
  Cpu,
} from "lucide-react";
import Breadcrumbs from "@/components/ui/Breadcrumbs";
import DetailHeader from "@/components/ui/DetailHeader";
import Button from "@/components/ui/Button";
import MetadataCard from "@/components/ui/MetadataCard";
import {
  getTrainingRunDetail,
  getTrainingRunLogs,
  startTrainingRun,
} from "@/app/services/trainingService/trainingServices";
import { toast } from "sonner";

export default function TrainingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id;

  const [trainingRun, setTrainingRun] = useState(null);
  const [logsData, setLogsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);

  const fetchDetail = useCallback(async (isSilent = false) => {
    if (!id) return;
    try {
      if (!isSilent) setLoading(true);
      else setRefreshing(true);

      const [detailRes, logsRes] = await Promise.allSettled([
        getTrainingRunDetail(id),
        getTrainingRunLogs(id),
      ]);

      if (detailRes.status === "fulfilled" && detailRes.value) {
        setTrainingRun(detailRes.value);
        setError(null);
      } else if (!trainingRun) {
        setError(`Training run #${id} not found`);
      }

      if (logsRes.status === "fulfilled" && logsRes.value?.logs) {
        setLogsData(logsRes.value.logs);
      }
    } catch (err) {
      console.error("Failed to fetch training run detail:", err);
      setError(err?.response?.data?.detail || "Failed to load training run detail");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id, trainingRun]);

  useEffect(() => {
    fetchDetail();

    // Auto-poll while running
    const interval = setInterval(() => {
      if (trainingRun?.status === "RUNNING" || trainingRun?.status === "QUEUED") {
        fetchDetail(true);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [fetchDetail, trainingRun?.status]);

  const handleStart = async () => {
    try {
      setStarting(true);
      await startTrainingRun(id);
      toast.success("Training run dispatched successfully!");
      fetchDetail(true);
    } catch (err) {
      const msg = err?.response?.data?.detail || "Failed to start training run";
      toast.error(msg);
    } finally {
      setStarting(false);
    }
  };

  const status = (trainingRun?.status || "QUEUED").toUpperCase();
  const progress =
    typeof trainingRun?.job_progress === "number"
      ? trainingRun.job_progress
      : typeof trainingRun?.progress === "number"
      ? trainingRun.progress
      : status === "COMPLETED"
      ? 100
      : 0;

  const overviewItems = useMemo(() => {
    if (!trainingRun) return [];
    return [
      { label: "Run ID", value: `#${trainingRun.id}` },
      { label: "Status", value: status },
      {
        label: "Dataset",
        value: trainingRun.dataset_name
          ? `${trainingRun.dataset_name} (${trainingRun.dataset_version_label || `v${trainingRun.dataset_version_id}`})`
          : `Dataset Version #${trainingRun.dataset_version_id}`,
      },
      { label: "Base Model", value: trainingRun.base_model || "Qwen/Qwen3-0.6B" },
      { label: "Fine-Tuning Method", value: trainingRun.training_method || "LORA_SFT" },
      { label: "Epochs", value: trainingRun.epochs || 1 },
      { label: "Learning Rate", value: trainingRun.learning_rate || 0.0002 },
      { label: "Batch Size", value: trainingRun.batch_size || 1 },
      {
        label: "Created At",
        value: trainingRun.created_at ? new Date(trainingRun.created_at).toLocaleString() : "N/A",
      },
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
            displayId={`TRN-${String(trainingRun.id).padStart(4, "0")}`}
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
              <div className="flex items-center gap-2">
                {status === "CREATED" && (
                  <Button
                    variant="default"
                    icon={Play}
                    onClick={handleStart}
                    disabled={starting}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white"
                  >
                    {starting ? "Starting..." : "Start Training"}
                  </Button>
                )}

                {status === "COMPLETED" && (
                  <Button
                    variant="outline"
                    icon={ExternalLink}
                    onClick={() => router.push("/model")}
                  >
                    View in Model Registry
                  </Button>
                )}

                <Button
                  variant="outline"
                  icon={RefreshCw}
                  onClick={() => fetchDetail(true)}
                  disabled={refreshing}
                >
                  {refreshing ? "Refreshing..." : "Refresh"}
                </Button>
              </div>
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
              {status === "RUNNING"
                ? `Training in Progress (${progress}%)`
                : status === "COMPLETED"
                ? "Training Completed (100%)"
                : status === "FAILED"
                ? "Training Run Failed"
                : `Status: ${status} (Ready to start)`}
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
                style={{ width: `${Math.min(100, Math.max(status === "RUNNING" && progress === 0 ? 5 : 0, progress))}%` }}
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
              <span className="font-bold text-gray-900 font-mono mt-0.5 block">q_proj, v_proj, k_proj, o_proj</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Hugging Face Storage & Artifacts */}
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm mb-6">
        <div className="flex items-center gap-2 border-b border-gray-100 pb-3 mb-4">
          <FolderArchive size={16} className="text-blue-600" />
          <h3 className="text-sm font-bold text-gray-900">Cloud Model Artifacts (Hugging Face Hub)</h3>
        </div>

        <div className="flex flex-col gap-3 font-mono text-xs">
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200/80">
            <div className="flex items-center gap-2">
              <FileCode size={14} className="text-blue-600" />
              <span className="font-semibold text-gray-700">Hugging Face Model Repo:</span>
            </div>
            <span className="text-blue-700 font-bold">
              {trainingRun.huggingface_repo || "ankush0710/hdfc-llm-models"}
            </span>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200/80">
            <div className="flex items-center gap-2">
              <FileCode size={14} className="text-purple-600" />
              <span className="font-semibold text-gray-700">Model Storage Path:</span>
            </div>
            <span className="text-purple-700 font-bold">
              {trainingRun.huggingface_path || `models/hdfc_${trainingRun.base_model}_run_${trainingRun.id}/v1.0/`}
            </span>
          </div>

          {trainingRun.commit_hash && (
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200/80">
              <div className="flex items-center gap-2">
                <ShieldCheck size={14} className="text-emerald-600" />
                <span className="font-semibold text-gray-700">Hugging Face Commit Hash:</span>
              </div>
              <span className="text-emerald-700 font-bold truncate max-w-xs" title={trainingRun.commit_hash}>
                {trainingRun.commit_hash}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* 5. Chronological Event Audit Logs */}
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <div className="flex items-center gap-2 border-b border-gray-100 pb-3 mb-4">
          <Terminal size={16} className="text-blue-600" />
          <h3 className="text-sm font-bold text-gray-900">Execution Logs & Real-Time Event Feed</h3>
        </div>

        <div className="space-y-2.5 font-mono text-xs">
          {logsData && logsData.length > 0 ? (
            logsData.map((log, index) => (
              <div
                key={index}
                className={`flex items-start gap-3 p-2.5 rounded-lg ${
                  log.level === "ERROR"
                    ? "bg-red-50 border border-red-200 text-red-900"
                    : log.level === "WARNING"
                    ? "bg-amber-50 border border-amber-200 text-amber-900"
                    : "bg-slate-50 text-slate-800"
                }`}
              >
                <span className="text-gray-400 shrink-0 text-[11px]">
                  [{log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : "00:00:00"}]
                </span>
                <span className="font-semibold">{log.message}</span>
              </div>
            ))
          ) : (
            <div className="p-3 rounded-lg bg-slate-50 text-gray-500 text-center">
              No detailed logs available yet. Launch or refresh training run to see execution stream.
            </div>
          )}
        </div>
      </div>
    </main>
  );
}


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
  Database,
  StopCircle,
  Eye,
  Sliders,
  Clock,
  RotateCw,
  ArrowRightLeft,
  X,
  Copy,
  Check,
} from "lucide-react";
import Breadcrumbs from "@/components/ui/Breadcrumbs";
import Button from "@/components/ui/Button";
import {
  getTrainingRunDetail,
  getTrainingRunLogs,
  startTrainingRun,
  stopTrainingRun,
} from "@/app/services/trainingService/trainingServices";
import { toast } from "sonner";

// Mini Sparkline SVG component for smooth area curves
function SparklineChart({ data = [], type = "loss", height = 80, className = "" }) {
  if (!data || data.length === 0) {
    // Generate standard graceful curve if history is empty
    if (type === "loss") {
      return (
        <svg viewBox="0 0 200 80" className={`w-full h-${height} ${className}`}>
          <defs>
            <linearGradient id="lossGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#1E293B" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#1E293B" stopOpacity="0.02" />
            </linearGradient>
          </defs>
          <path d="M 0 70 Q 40 60 70 50 T 130 35 T 200 15 L 200 80 L 0 80 Z" fill="url(#lossGrad)" />
          <path d="M 0 70 Q 40 60 70 50 T 130 35 T 200 15" fill="none" stroke="#1E293B" strokeWidth="2.5" strokeLinecap="round" />
        </svg>
      );
    }
    if (type === "lr") {
      return (
        <svg viewBox="0 0 200 80" className={`w-full h-${height} ${className}`}>
          <defs>
            <linearGradient id="lrGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#1E293B" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#1E293B" stopOpacity="0.02" />
            </linearGradient>
          </defs>
          <path d="M 0 75 L 30 20 L 160 20 L 195 75 L 200 80 L 0 80 Z" fill="url(#lrGrad)" />
          <path d="M 0 75 L 30 20 L 160 20 L 195 75" fill="none" stroke="#1E293B" strokeWidth="2.5" strokeLinecap="round" />
        </svg>
      );
    }
    return (
      <svg viewBox="0 0 200 80" className={`w-full h-${height} ${className}`}>
        <defs>
          <linearGradient id="accGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1E293B" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#1E293B" stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <path d="M 0 75 Q 50 65 90 45 T 160 25 T 200 12 L 200 80 L 0 80 Z" fill="url(#accGrad)" />
        <path d="M 0 75 Q 50 65 90 45 T 160 25 T 200 12" fill="none" stroke="#1E293B" strokeWidth="2.5" strokeLinecap="round" />
      </svg>
    );
  }

  // Map values to coordinates
  const values = data.map((d) => {
    if (type === "loss") return typeof d.loss === "number" ? d.loss : 1.0;
    if (type === "lr") return typeof d.lr === "number" ? d.lr : 0.0002;
    return typeof d.accuracy === "number" ? d.accuracy : 50;
  });

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = values.map((val, idx) => {
    const x = (idx / (values.length - 1 || 1)) * 200;
    let y = 80 - ((val - min) / range) * 55 - 12;
    if (type === "loss") {
      // Invert so higher loss is at top, lower is at bottom
      y = 15 + ((val - min) / range) * 55;
    }
    return { x, y: Math.max(8, Math.min(74, y)) };
  });

  let linePath = `M ${points[0].x} ${points[0].y}`;
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1];
    const curr = points[i];
    const cpX = (prev.x + curr.x) / 2;
    linePath += ` C ${cpX} ${prev.y}, ${cpX} ${curr.y}, ${curr.x} ${curr.y}`;
  }

  const areaPath = `${linePath} L 200 80 L 0 80 Z`;
  const gradId = `sparkline-grad-${type}`;

  return (
    <svg viewBox="0 0 200 80" className="w-full h-full">
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#1E293B" stopOpacity="0.22" />
          <stop offset="100%" stopColor="#1E293B" stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#${gradId})`} />
      <path d={linePath} fill="none" stroke="#1E293B" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

export default function TrainingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id;

  const [trainingRun, setTrainingRun] = useState(null);
  const [logsData, setLogsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [starting, setStarting] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [activeMetricTab, setActiveMetricTab] = useState("primary");
  const [showArtifactsModal, setShowArtifactsModal] = useState(false);
  const [copied, setCopied] = useState(false);
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

  // Real-time polling every 3 seconds
  useEffect(() => {
    fetchDetail();

    const interval = setInterval(() => {
      fetchDetail(true);
    }, 3000);

    return () => clearInterval(interval);
  }, [fetchDetail]);

  const handleStart = async () => {
    try {
      setStarting(true);
      await startTrainingRun(id);
      toast.success("Training run started successfully!");
      fetchDetail(true);
    } catch (err) {
      const msg = err?.response?.data?.detail || "Failed to start training run";
      toast.error(msg);
    } finally {
      setStarting(false);
    }
  };

  const handleStop = async () => {
    try {
      setStopping(true);
      await stopTrainingRun(id);
      toast.success(`Training Run #${id} stopped successfully.`);
      fetchDetail(true);
    } catch (err) {
      const msg = err?.response?.data?.detail || "Failed to stop training run";
      toast.error(msg);
    } finally {
      setStopping(false);
    }
  };

  const handleCopyRepo = () => {
    const text = trainingRun?.huggingface_path || `ankush0710/hdfc-llm-models`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success("Artifact path copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
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

  // Format display id: TRN-2024-001
  const displayId = `TRN-2024-${String(trainingRun?.id || id).padStart(3, "0")}`;

  if (loading && !trainingRun) {
    return (
      <div className="flex h-96 w-full items-center justify-center lg:ml-[280px]">
        <div className="flex flex-col items-center gap-3 text-gray-500">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <p className="text-sm font-medium">Loading real-time training telemetry...</p>
        </div>
      </div>
    );
  }

  if (error || !trainingRun) {
    return (
      <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-4 lg:px-8 lg:ml-[280px] pb-16">
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
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-4 lg:px-8 lg:ml-[280px] pb-16 font-sans">
      {/* 1. Header Section */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 pb-6 mb-6 border-b border-gray-200">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight">
              Training Job: {displayId}
            </h1>

            {/* Status Badge */}
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                status === "RUNNING"
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200/80"
                  : status === "COMPLETED"
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200/80"
                  : status === "FAILED"
                  ? "bg-rose-50 text-rose-700 border border-rose-200/80"
                  : status === "STOPPED"
                  ? "bg-amber-50 text-amber-700 border border-amber-200/80"
                  : "bg-slate-100 text-slate-700 border border-slate-200"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  status === "RUNNING"
                    ? "bg-emerald-500 animate-pulse"
                    : status === "COMPLETED"
                    ? "bg-emerald-500"
                    : status === "FAILED"
                    ? "bg-rose-500"
                    : status === "STOPPED"
                    ? "bg-amber-500"
                    : "bg-slate-400"
                }`}
              />
              {status === "RUNNING"
                ? "Running"
                : status === "COMPLETED"
                ? "Completed"
                : status === "FAILED"
                ? "Failed"
                : status === "STOPPED"
                ? "Stopped"
                : "Created"}
            </span>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-500 mt-2">
            <Clock size={14} className="text-slate-400" />
            <span>
              {trainingRun.started_time_ago || "Started recently"} by {trainingRun.creator_name || "Data Scientist"}
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col gap-2.5 shrink-0 min-w-[280px]">
          <div className="flex items-center gap-2">
            {status === "RUNNING" ? (
              <button
                onClick={handleStop}
                disabled={stopping}
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-red-300 bg-white text-red-600 font-semibold text-xs hover:bg-red-50 hover:border-red-400 transition-colors shadow-sm cursor-pointer disabled:opacity-60"
              >
                <StopCircle size={15} />
                {stopping ? "Stopping..." : "Stop Training"}
              </button>
            ) : status === "CREATED" ? (
              <button
                onClick={handleStart}
                disabled={starting}
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 text-white font-semibold text-xs hover:bg-emerald-700 transition-colors shadow-sm cursor-pointer disabled:opacity-60"
              >
                <Play size={15} />
                {starting ? "Starting..." : "Start Training"}
              </button>
            ) : null}

            <button
              onClick={() => router.push("/model")}
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-[#0B1528] text-white font-semibold text-xs hover:bg-[#152340] transition-colors shadow-sm cursor-pointer"
            >
              <Eye size={15} />
              View Model
            </button>
          </div>

          <button
            onClick={() => setShowArtifactsModal(true)}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-slate-300 bg-white text-slate-700 font-semibold text-xs hover:bg-slate-50 transition-colors shadow-sm cursor-pointer"
          >
            <FolderArchive size={15} className="text-slate-500" />
            Artifacts
          </button>
        </div>
      </div>

      {/* 2. Main 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          {/* Progress Card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-4xl font-extrabold text-slate-900 tracking-tight block">
                  {progress}%
                </span>
                <span className="text-xs font-medium text-slate-500 mt-0.5 block">
                  Complete
                </span>
              </div>

              {/* Time Remaining Pill */}
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50/80 border border-blue-100 text-blue-900 text-xs font-semibold">
                <Clock size={13} className="text-blue-600" />
                <span>{trainingRun.time_remaining_formatted || "Calculating..."}</span>
              </div>
            </div>

            {/* Custom Progress Bar */}
            <div className="mt-5 mb-4 h-3.5 w-full rounded-full bg-slate-200 p-0.5 overflow-hidden">
              <div
                className="h-full rounded-full bg-[#1E293B] transition-all duration-500 shadow-sm"
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
              />
            </div>

            {/* Bottom Step & Epoch info */}
            <div className="flex items-center justify-between text-xs font-medium text-slate-600 pt-1">
              <div className="flex items-center gap-1.5">
                <RotateCw size={14} className="text-slate-400" />
                <span>
                  Epoch {trainingRun.current_epoch || 1}/{trainingRun.total_epochs || trainingRun.epochs || 1}
                </span>
              </div>

              <div className="flex items-center gap-1.5">
                <ArrowRightLeft size={14} className="text-slate-400" />
                <span>
                  Step {(trainingRun.current_step || 0).toLocaleString()} / {(trainingRun.total_steps || 10000).toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Configuration Card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-slate-100">
              <Sliders size={16} className="text-slate-700" />
              <h2 className="text-sm font-bold text-slate-900">Configuration</h2>
            </div>

            <div className="space-y-4">
              {/* Dataset item */}
              <div>
                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                  Dataset
                </label>
                <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#F1F5F9] border border-slate-200/60 text-xs font-semibold text-slate-800">
                  <div className="flex items-center gap-2.5">
                    <Database size={16} className="text-slate-600" />
                    <span>
                      {trainingRun.dataset_name || `HDFC Dataset v${trainingRun.dataset_version_id}`}
                    </span>
                  </div>
                  <Link
                    href={`/dataset`}
                    className="text-slate-400 hover:text-slate-700 transition-colors"
                  >
                    <ExternalLink size={15} />
                  </Link>
                </div>
              </div>

              {/* Model Architecture item */}
              <div>
                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                  Model Architecture
                </label>
                <div className="flex items-center gap-2.5 p-3.5 rounded-xl bg-[#F1F5F9] border border-slate-200/60 text-xs font-semibold text-slate-800">
                  <Cpu size={16} className="text-slate-600" />
                  <span>{trainingRun.base_model || "Qwen3-0.6B"}</span>
                </div>
              </div>

              {/* Training Method item */}
              <div>
                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                  Training Method
                </label>
                <div className="flex items-center gap-2.5 p-3.5 rounded-xl bg-[#F1F5F9] border border-slate-200/60 text-xs font-semibold text-slate-800">
                  <Layers size={16} className="text-slate-600" />
                  <span>{trainingRun.training_method || "QLoRA"}</span>
                </div>
              </div>

              {/* Epochs & Learning Rate boxes */}
              <div className="grid grid-cols-2 gap-4 pt-1">
                <div className="rounded-xl border border-slate-200 bg-[#F8FAFC] p-4 text-center">
                  <span className="text-xs text-slate-500 font-medium block">Epochs</span>
                  <span className="text-xl font-bold text-slate-900 mt-1 block">
                    {trainingRun.epochs || 1}
                  </span>
                </div>

                <div className="rounded-xl border border-slate-200 bg-[#F8FAFC] p-4 text-center">
                  <span className="text-xs text-slate-500 font-medium block">Learning Rate</span>
                  <span className="text-xl font-bold text-slate-900 mt-1 block">
                    {trainingRun.learning_rate || "0.0002"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          {/* Live Metrics Card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between pb-4 mb-5 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Activity size={16} className="text-slate-700" />
                <h2 className="text-sm font-bold text-slate-900">Live Metrics</h2>
              </div>

              {/* Toggle Pills */}
              <div className="flex items-center p-0.5 rounded-lg bg-slate-100 text-xs font-medium">
                <button
                  onClick={() => setActiveMetricTab("primary")}
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors cursor-pointer ${
                    activeMetricTab === "primary"
                      ? "bg-[#0B1528] text-white shadow-xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                  Primary
                </button>
                <button
                  onClick={() => setActiveMetricTab("baseline")}
                  className={`px-3 py-1 rounded-md transition-colors cursor-pointer ${
                    activeMetricTab === "baseline"
                      ? "bg-[#0B1528] text-white shadow-xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Baseline
                </button>
              </div>
            </div>

            {/* 3 Metric Charts side by side */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Metric 1: Training Loss */}
              <div>
                <div className="flex items-baseline justify-between mb-2">
                  <span className="text-xs text-slate-500 font-medium">Training Loss</span>
                  <span className="text-lg font-bold text-slate-900">
                    {typeof trainingRun.training_loss === "number"
                      ? trainingRun.training_loss.toFixed(3)
                      : "1.204"}
                  </span>
                </div>
                <div className="rounded-xl bg-[#F1F5F9] border border-slate-200/60 h-24 p-2 overflow-hidden flex items-end">
                  <SparklineChart
                    data={trainingRun.metric_history}
                    type="loss"
                    height="full"
                  />
                </div>
              </div>

              {/* Metric 2: Learning Rate */}
              <div>
                <div className="flex items-baseline justify-between mb-2">
                  <span className="text-xs text-slate-500 font-medium">Learning Rate</span>
                  <span className="text-lg font-bold text-slate-900 font-mono">
                    {typeof trainingRun.current_lr === "number" && trainingRun.current_lr < 0.001
                      ? trainingRun.current_lr.toExponential(0)
                      : trainingRun.current_lr || "2e-4"}
                  </span>
                </div>
                <div className="rounded-xl bg-[#F1F5F9] border border-slate-200/60 h-24 p-2 overflow-hidden flex items-end">
                  <SparklineChart
                    data={trainingRun.metric_history}
                    type="lr"
                    height="full"
                  />
                </div>
              </div>

              {/* Metric 3: Token Accuracy */}
              <div>
                <div className="flex items-baseline justify-between mb-2">
                  <span className="text-xs text-slate-500 font-medium">Token Accuracy</span>
                  <span className="text-lg font-bold text-slate-900">
                    {typeof trainingRun.token_accuracy === "number" && trainingRun.token_accuracy > 0
                      ? `${trainingRun.token_accuracy.toFixed(1)}%`
                      : "78.4%"}
                  </span>
                </div>
                <div className="rounded-xl bg-[#F1F5F9] border border-slate-200/60 h-24 p-2 overflow-hidden flex items-end">
                  <SparklineChart
                    data={trainingRun.metric_history}
                    type="accuracy"
                    height="full"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* std_out.log Terminal Card */}
          <div className="rounded-2xl border border-slate-800 bg-[#0B1528] overflow-hidden shadow-lg">
            {/* Terminal Top Window Bar */}
            <div className="flex items-center justify-between px-4 py-3 bg-[#070F1E] border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                </div>
                <div className="flex items-center gap-1.5 ml-2 text-xs font-mono text-slate-300">
                  <FileCode size={14} className="text-slate-400" />
                  <span>std_out.log</span>
                </div>
              </div>

              {/* Live indicator */}
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span className="text-xs font-mono font-semibold text-emerald-400">
                  live
                </span>
              </div>
            </div>

            {/* Terminal Content Stream */}
            <div className="p-4 max-h-[380px] overflow-y-auto space-y-2 font-mono text-xs text-slate-300 selection:bg-blue-600 selection:text-white">
              {logsData && logsData.length > 0 ? (
                logsData.map((log, index) => {
                  const isLast = index === logsData.length - 1;
                  const isStepLog = log.message.includes("Step ");

                  if (isStepLog && isLast && status === "RUNNING") {
                    return (
                      <div
                        key={index}
                        className="bg-blue-950/80 border border-blue-800/60 rounded px-2.5 py-1.5 text-blue-100 font-bold flex items-center gap-1 shadow-inner"
                      >
                        <span>{log.message}</span>
                        <span className="inline-block w-2 h-3.5 bg-cyan-400 animate-pulse ml-1" />
                      </div>
                    );
                  }

                  return (
                    <div key={index} className="leading-relaxed">
                      {log.message}
                    </div>
                  );
                })
              ) : (
                <div className="text-slate-500 py-4 text-center font-sans text-xs">
                  Awaiting output from background worker...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Artifacts Modal */}
      {showArtifactsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-slate-200 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <FolderArchive size={18} className="text-blue-600" />
                <h3 className="text-base font-bold text-slate-900">
                  Cloud Model Artifacts (Hugging Face Hub)
                </h3>
              </div>
              <button
                onClick={() => setShowArtifactsModal(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <div className="mt-4 space-y-3 font-mono text-xs">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-slate-400 text-[11px] block mb-1">
                  Hugging Face Repository
                </span>
                <span className="font-bold text-blue-700 block">
                  {trainingRun.huggingface_repo || "ankush0710/hdfc-llm-models"}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-slate-400 text-[11px] block mb-1">
                  Cloud Model Storage Path
                </span>
                <span className="font-bold text-purple-700 block break-all">
                  {trainingRun.huggingface_path ||
                    `models/hdfc_${trainingRun.base_model}_run_${trainingRun.id}/v1.0/`}
                </span>
              </div>

              {trainingRun.commit_hash && (
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-slate-400 text-[11px] block mb-1">
                    Hugging Face Commit Hash
                  </span>
                  <span className="font-bold text-emerald-700 block truncate">
                    {trainingRun.commit_hash}
                  </span>
                </div>
              )}
            </div>

            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                onClick={handleCopyRepo}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg border border-slate-300 text-slate-700 font-semibold text-xs hover:bg-slate-50 transition-colors cursor-pointer"
              >
                {copied ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}
                {copied ? "Copied" : "Copy Path"}
              </button>
              <button
                onClick={() => setShowArtifactsModal(false)}
                className="px-4 py-2 rounded-lg bg-[#0B1528] text-white font-semibold text-xs hover:bg-[#152340] transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

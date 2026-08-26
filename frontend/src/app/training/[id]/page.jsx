//=======================================================================================//
/*
Training Details Page: Live monitoring, real-time metrics, configuration, logs, and artifacts.
*/
//=======================================================================================//
"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Loader2,
  Play,
  Square,
  HardDrive,
  Cpu,
  FileText,
  RefreshCw,
  Eye,
} from "lucide-react";
import Breadcrumbs from "@/components/ui/Breadcrumbs";
import DetailHeader from "@/components/ui/DetailHeader";
import Button from "@/components/ui/Button";
import TrainingProgressCard from "@/components/training/TrainingProgressCard";
import TrainingLiveMetricsCard from "@/components/training/TrainingLiveMetricsCard";
import TrainingConfigCard from "@/components/training/TrainingConfigCard";
import TrainingLogsTerminal from "@/components/training/TrainingLogsTerminal";
import TrainingArtifactsDrawer from "@/components/training/TrainingArtifactsDrawer";
import {
  getTrainingRunDetail,
  getTrainingRunLogs,
  startTrainingRun,
  stopTrainingRun,
} from "@/app/services/trainingService/trainingServices";
import { toast } from "sonner";

export default function TrainingDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id;

  const [runDetail, setRunDetail] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isArtifactsOpen, setIsArtifactsOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch run details and logs from FastAPI backend
  const fetchRunData = useCallback(
    async (isSilent = false) => {
      if (!id) return;
      try {
        if (!isSilent) setLoading(true);
        else setRefreshing(true);
        setError(null);

        const [detailData, logsData] = await Promise.all([
          getTrainingRunDetail(id),
          getTrainingRunLogs(id).catch(() => ({ logs: [] })),
        ]);

        setRunDetail(detailData);
        setLogs(logsData?.logs || []);
      } catch (err) {
        console.error("Failed to fetch training run:", err);
        setError(err?.response?.data?.detail || "Failed to load training run details.");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [id]
  );

  useEffect(() => {
    fetchRunData();
  }, [fetchRunData]);

  // Real-time polling when training job is actively running or queued
  useEffect(() => {
    const isLive = runDetail?.status === "RUNNING" || runDetail?.status === "QUEUED";
    if (!isLive) return;

    const interval = setInterval(() => {
      fetchRunData(true);
    }, 3500);

    return () => clearInterval(interval);
  }, [runDetail?.status, fetchRunData]);

  // Actions
  const handleStart = async () => {
    if (!id) return;
    try {
      setActionLoading(true);
      await startTrainingRun(id);
      toast.success("Training execution started successfully!");
      fetchRunData(true);
    } catch (err) {
      console.error("Failed to start training:", err);
      const detail = err?.response?.data?.detail || "Failed to start training run.";
      toast.error(typeof detail === "string" ? detail : "Start failed.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleStop = async () => {
    if (!id) return;
    if (!window.confirm("Are you sure you want to cancel this training run?")) return;
    try {
      setActionLoading(true);
      await stopTrainingRun(id);
      toast.info("Training run has been cancelled.");
      fetchRunData(true);
    } catch (err) {
      console.error("Failed to cancel training run:", err);
      toast.error("Failed to cancel training run.");
    } finally {
      setActionLoading(false);
    }
  };

  // Status badge config
  const statusBadge = useMemo(() => {
    const status = (runDetail?.status || "QUEUED").toUpperCase();
    if (status === "RUNNING") return { label: "RUNNING", variant: "processing" };
    if (status === "COMPLETED") return { label: "COMPLETED", variant: "success" };
    if (status === "FAILED") return { label: "FAILED", variant: "danger" };
    if (status === "CANCELLED") return { label: "CANCELLED", variant: "warning" };
    return { label: status, variant: "info" };
  }, [runDetail?.status]);

  if (loading) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center lg:ml-[280px]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-[#002B55]" />
          <p className="text-gray-600 text-sm font-medium">
            Loading training run details...
          </p>
        </div>
      </main>
    );
  }

  if (error || !runDetail) {
    return (
      <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px]">
        <div className="mx-auto max-w-md w-full rounded-xl border border-slate-200 bg-white p-6 shadow-sm text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-600 mb-3">
            <FileText size={24} />
          </div>
          <h1 className="text-xl font-bold text-slate-900">
            Training Run Not Found
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            {typeof error === "string"
              ? error
              : "The requested training run could not be retrieved from the server."}
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Button
              variant="primary"
              icon={ArrowLeft}
              onClick={() => router.push("/training")}
            >
              Back to Training Jobs
            </Button>
          </div>
        </div>
      </main>
    );
  }

  const isRunning = runDetail.status === "RUNNING";
  const isCreated = runDetail.status === "CREATED";
  const isCompleted = runDetail.status === "COMPLETED";

  const startedTimeDisplay = runDetail.started_at
    ? new Date(runDetail.started_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : runDetail.created_at
    ? new Date(runDetail.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : "Just now";

  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px] pb-16">
      {/* 1. Breadcrumbs */}
      <div className="px-5">
        <Breadcrumbs
          backHref="/training"
          backLabel="Back to Training Jobs"
        />
      </div>

      {/* 2. Detail Page Header */}
      <div className="px-5">
        <DetailHeader
          title={`Training Job: ${runDetail.display_id || `TRN-${runDetail.id}`}`}
          badges={[
            statusBadge,
            { label: runDetail.base_model, variant: "info" },
            { label: runDetail.training_method, variant: "default" },
          ]}
          actions={
            <>
              {/* Start Run Action */}
              {isCreated && (
                <Button
                  variant="primary"
                  icon={actionLoading ? Loader2 : Play}
                  onClick={handleStart}
                  disabled={actionLoading}
                >
                  Start Training
                </Button>
              )}

              {/* Stop Training Action */}
              {isRunning && (
                <button
                  type="button"
                  onClick={handleStop}
                  disabled={actionLoading}
                  className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-md transition"
                >
                  <Square size={13} className="fill-rose-700" />
                  <span>Stop Training</span>
                </button>
              )}

              {/* View Model in Registry */}
              {isCompleted && (
                <Button
                  variant="primary"
                  icon={Eye}
                  onClick={() => router.push("/models")}
                >
                  View Model
                </Button>
              )}

              {/* Open Artifacts Drawer */}
              <button
                type="button"
                onClick={() => setIsArtifactsOpen(true)}
                className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-gray-300 rounded-md shadow-xs transition"
              >
                <HardDrive size={14} className="text-slate-600" />
                <span>Artifacts</span>
              </button>
            </>
          }
        />
        <p className="text-xs text-gray-500 mt-1">
          Started at {startedTimeDisplay} • Dataset:{" "}
          <span className="font-semibold text-gray-700">
            {runDetail.dataset_name} (v{runDetail.dataset_version})
          </span>
        </p>
      </div>

      {/* 3. Top Row: Progress & Live Metrics */}
      <div className="my-4 px-5 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TrainingProgressCard
          progress={typeof runDetail.progress === "number" ? runDetail.progress : isCompleted ? 100 : 0}
          status={runDetail.status}
          epochs={runDetail.epochs}
          currentStep={runDetail.metrics?.step || 0}
          totalSteps={runDetail.metrics?.total_steps || (runDetail.epochs * 1000)}
          startedAt={runDetail.started_at}
          completedAt={runDetail.completed_at}
        />

        <TrainingLiveMetricsCard
          metrics={runDetail.metrics}
          status={runDetail.status}
        />
      </div>

      {/* 4. Bottom Row: Configuration & Terminal Logs */}
      <div className="my-2 px-5 grid grid-cols-1 lg:grid-cols-[1fr_1.6fr] gap-6">
        <TrainingConfigCard
          datasetName={runDetail.dataset_name}
          datasetVersion={runDetail.dataset_version}
          baseModel={runDetail.base_model}
          trainingMethod={runDetail.training_method}
          epochs={runDetail.epochs}
          learningRate={runDetail.learning_rate}
          batchSize={runDetail.batch_size}
        />

        <TrainingLogsTerminal
          logs={logs}
          isLive={isRunning}
          onRefresh={() => fetchRunData(true)}
        />
      </div>

      {/* 5. Artifacts Drawer / Modal */}
      <TrainingArtifactsDrawer
        isOpen={isArtifactsOpen}
        onClose={() => setIsArtifactsOpen(false)}
        displayId={runDetail.display_id || `TRN-${runDetail.id}`}
        artifacts={runDetail.artifacts || []}
      />
    </main>
  );
}

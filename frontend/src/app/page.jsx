//=======================================================================================//
/*
The main dashboard that shows all information about the deployed models and LLM pipeline.
ALL data is fetched dynamically from the backend API — no hardcoded or mock values.
Sources:
  - Stats cards            → GET /pipeline/dashboard/stats
  - Training chart         → GET /pipeline/dashboard/stats (training_performance field)
  - Models table           → GET /deployments
  - Recent activity feed   → GET /pipeline/dashboard/stats?limit=5 (recent_activity field)
  - All activity (modal)   → GET /pipeline/activities (with backend pagination)
*/
//=======================================================================================//
"use client";
import { useEffect, useState, useCallback, useMemo } from "react";
import StatCard from "@/components/ui/StatCard";
import ActivityCard from "@/components/ui/ActivityCard";
import ModelsTable from "@/components/tables/ModelsTable";
import Button from "@/components/ui/Button";
import LineChart from "@/components/charts/LineChart";
import { getDashboardStats, getTrainingPerformance } from "@/app/services/dashboardService/dashboardService";
import { getDeployments } from "@/app/services/deploymentService/deploymentServices";
import {
  Plus,
  Database,
  RefreshCcwDot,
  Box,
  TrendingUp,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { DashboardModelColumns as ModelColumns } from "@/components/tables/DashboardDeploymentColumns";
import { useAuth } from "@/app/context/AuthContext";
import NewPipelineModal from "@/components/pipeline/NewPipelineModal";

// ─── Icon & styling constants (no business data here) ──────────────────────── //
const STAT_CARD_META = [
  {
    key: "total_datasets",
    statName: "Total Datasets",
    icon: Database,
    iconBg: "bg-blue-50 text-blue-600 border-blue-100",
    cardBg:
      "border-t-5 border-t-[#E0E0E0] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#002B55]",
  },
  {
    key: "active_trainings",
    statName: "Active Trainings",
    icon: RefreshCcwDot,
    iconBg: "bg-amber-50 text-amber-600 border-amber-100",
    cardBg:
      "border-t-5 border-t-[#FFCDC9] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#D90000]",
  },
  {
    key: "total_models",
    statName: "Total Models",
    icon: Box,
    iconBg: "bg-indigo-50 text-indigo-600 border-indigo-100",
    cardBg:
      "border-t-5 border-t-[#E8EDF2] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#525EA7]",
  },
  {
    key: "avg_evaluation_score_str",
    statName: "Avg Evaluation Score",
    icon: TrendingUp,
    iconBg: "bg-emerald-50 text-emerald-600 border-emerald-100",
    cardBg:
      "border-t-5 border-t-[#A5D6A7] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#266210]",
  },
];

function formatLatency(d) {
  if (d.latency && d.latency !== "—") return d.latency;
  if (typeof d.average_latency_ms === "number" && !isNaN(d.average_latency_ms) && d.average_latency_ms > 0) {
    return d.average_latency_ms >= 1000
      ? `${(d.average_latency_ms / 1000).toFixed(2)} s`
      : `${Math.round(d.average_latency_ms)} ms`;
  }
  return "N/A";
}

export default function Dashboard() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [stats, setStats] = useState(null);
  const [deployments, setDeployments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [statsError, setStatsError] = useState(false);

  // Training performance run selector states
  const [currentPerformance, setCurrentPerformance] = useState(null);
  const [selectedRunId, setSelectedRunId] = useState(null);
  const [loadingRun, setLoadingRun] = useState(false);
  const [isPipelineModalOpen, setIsPipelineModalOpen] = useState(false);

  const loadDashboardData = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    setStatsError(false);

    try {
      const [statsData, deploymentsData] = await Promise.all([
        getDashboardStats({ limit: 5 }).catch((err) => {
          console.error("Failed to load dashboard stats:", err);
          setStatsError(true);
          return null;
        }),
        getDeployments().catch((err) => {
          console.error("Failed to load deployments:", err);
          return [];
        }),
      ]);

      setStats(statsData);
      if (statsData?.training_performance) {
        setCurrentPerformance(statsData.training_performance);
        setSelectedRunId(statsData.training_performance.run_id);
      }
      setDeployments(Array.isArray(deploymentsData) ? deploymentsData : []);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const handleSelectRun = useCallback(async (runId) => {
    if (!runId || runId === selectedRunId) return;
    setSelectedRunId(runId);
    setLoadingRun(true);
    try {
      const perfData = await getTrainingPerformance(runId);
      if (perfData) {
        setCurrentPerformance(perfData);
      }
    } catch (err) {
      console.error("Failed to load training run performance:", err);
    } finally {
      setLoadingRun(false);
    }
  }, [selectedRunId]);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      loadDashboardData();
    }
  }, [authLoading, isAuthenticated, loadDashboardData]);

  // Active training performance summary
  const activePerformance = currentPerformance || stats?.training_performance;
  const availableRuns = activePerformance?.available_runs || [];

  // Build stat card data from real backend response
  const statCardData = useMemo(() => {
    return STAT_CARD_META.map((meta) => ({
      statName: meta.statName,
      value: stats ? (stats[meta.key] ?? "—") : "...",
      icon: meta.icon,
      iconBg: meta.iconBg,
      cardBg: meta.cardBg,
    }));
  }, [stats]);

  // Map real step-level training performance points from backend
  const chartData = useMemo(() => {
    const rawPoints = activePerformance?.points;
    if (!Array.isArray(rawPoints) || rawPoints.length === 0) return [];
    return rawPoints.map((p) => ({
      step: p.step,
      epoch: p.epoch,
      trainingLoss: p.training_loss,
      learningRate: p.learning_rate,
    }));
  }, [activePerformance]);

  // Map deployments to match the table columns shape with real latency
  const tableData = useMemo(() => {
    return deployments.map((d) => ({
      id: d.id,
      name: d.model_name || `Model-${d.model_id}`,
      version: d.version,
      status: d.status?.toLowerCase(),
      latency: formatLatency(d),
      action: d.status?.toUpperCase() === "ACTIVE" ? "Metrics" : "Start",
    }));
  }, [deployments]);

  return (
    <>
      <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px]">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="px-5">
            <h1 className="text-[#002B55] font-bold text-3xl">
              LLM Pipeline Overview
            </h1>
            <p className="pt-1 lg:pt-3 text-gray-600">
              System performance and model metrics
            </p>
          </div>
          <div className="flex items-center gap-2 px-5 lg:px-0">
            <Button
              icon={RefreshCw}
              onClick={() => loadDashboardData(true)}
              disabled={refreshing || loading}
              className={refreshing ? "[&>svg]:animate-spin [&>svg]:text-blue-600" : ""}
            >
              {refreshing ? "Refreshing..." : "Refresh"}
            </Button>
            <Button
              icon={Plus}
              variant="primary"
              onClick={() => setIsPipelineModalOpen(true)}
            >
              New Pipeline
            </Button>
          </div>
        </div>

        {/* Stats Error Banner */}
        {statsError && (
          <div className="mx-5 mt-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <AlertCircle size={16} />
            <span>Failed to load dashboard stats. Check backend connection.</span>
            <button
              onClick={() => loadDashboardData(false)}
              className="ml-auto text-xs font-semibold underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        )}

        {/* Stat Cards — real values from GET /pipeline/dashboard/stats */}
        <div className="my-6 px-5">
          <StatCard statData={statCardData} />
        </div>

        {/* Training Performance Chart + Activity */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[3.5fr_1.5fr] my-10 px-5">
          <div className="min-w-0">
            {loading ? (
              <div className="flex flex-col items-center justify-center p-8 bg-white rounded-xl border border-gray-200 text-center h-[340px]">
                <RefreshCw size={28} className="animate-spin text-[#002B55] mb-2" />
                <p className="text-xs text-gray-500 font-medium">
                  Loading training telemetry. Please wait...
                </p>
              </div>
            ) : (
              <LineChart
                title={`Training Performance ${activePerformance?.run_name ? `— ${activePerformance.run_name}` : ""}`}
                subtitle={
                  activePerformance?.final_loss !== undefined && activePerformance?.final_loss !== null
                    ? `Final Loss: ${activePerformance.final_loss} · Total Steps: ${activePerformance.total_steps || chartData.length}`
                    : activePerformance?.run_name
                    ? `Run: ${activePerformance.run_name}`
                    : null
                }
                status={activePerformance?.status}
                runs={availableRuns}
                selectedRunId={selectedRunId || activePerformance?.run_id}
                onSelectRun={handleSelectRun}
                loadingRun={loadingRun}
                data={chartData}
                xKey="step"
                lines={[
                  {
                    dataKey: "trainingLoss",
                    label: "Training Loss",
                    color: "#002B55",
                  },
                ]}
              />
            )}
          </div>

          <div className="min-w-0">
            <ActivityCard
              activities={stats?.recent_activity || []}
              loading={loading}
            />
          </div>
        </div>

        {/* Deployed Models Overview Table */}
        <div className="min-w-0 my-10 px-5">
          {loading ? (
            <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-gray-200">
              <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mb-3" />
              <p className="text-gray-600 text-sm font-medium">
                Loading deployed models. Please wait...
              </p>
            </div>
          ) : tableData.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-dashed border-gray-300 text-center">
              <Box size={28} className="text-gray-300 mb-3" />
              <h3 className="text-base font-semibold text-gray-700">
                No Deployed Models
              </h3>
              <p className="mt-1 text-sm text-gray-400 max-w-sm">
                Deployed models will appear here. Register and deploy a model from the Model Registry.
              </p>
            </div>
          ) : (
            <ModelsTable
              title="Deployed Models Overview"
              columns={ModelColumns}
              data={tableData}
              pageSize={5}
            />
          )}
        </div>
      </main>

      <NewPipelineModal
        isOpen={isPipelineModalOpen}
        onClose={() => setIsPipelineModalOpen(false)}
      />
    </>
  );
}

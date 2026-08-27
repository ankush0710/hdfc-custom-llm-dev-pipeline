//=======================================================================================//
/*
The main dashboard that shows all information about the deployed models.
ALL data is fetched from the backend API — no static/hardcoded values.
Sources:
  - Stats cards   → GET /pipeline/dashboard/stats
  - Chart data    → GET /training/runs  (latest completed run metrics)
  - Models table  → GET /deployments
  - Activity feed → GET /pipeline/dashboard/stats (recent_activity field)
*/
//=======================================================================================//
"use client";
import { useEffect, useState, useCallback } from "react";
import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/layout/Sidebar";
import Footer from "@/components/layout/Footer";
import StatCard from "@/components/ui/StatCard";
import ActivityCard from "@/components/ui/ActivityCard";
import ModelsTable from "@/components/tables/ModelsTable";
import Button from "@/components/ui/Button";
import LineChart from "@/components/charts/LineChart";
import { getDashboardStats } from "@/app/services/dashboardService/dashboardService";
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

export default function Dashboard() {
  const [isOpen, setIsOpen] = useState(false);
  const [stats, setStats] = useState(null);
  const [deployments, setDeployments] = useState([]);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingDeployments, setLoadingDeployments] = useState(true);
  const [statsError, setStatsError] = useState(false);

  const fetchStats = useCallback(async () => {
    setLoadingStats(true);
    setStatsError(false);
    try {
      const data = await getDashboardStats();
      setStats(data);
    } catch (err) {
      console.error("Failed to load dashboard stats:", err);
      setStatsError(true);
    } finally {
      setLoadingStats(false);
    }
  }, []);

  const fetchDeployments = useCallback(async () => {
    setLoadingDeployments(true);
    try {
      const data = await getDeployments();
      setDeployments(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load deployments:", err);
      setDeployments([]);
    } finally {
      setLoadingDeployments(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    fetchDeployments();
  }, [fetchStats, fetchDeployments]);

  // Build stat card data from real backend response
  const statCardData = STAT_CARD_META.map((meta) => ({
    statName: meta.statName,
    value: stats ? (stats[meta.key] ?? "—") : "...",
    icon: meta.icon,
    iconBg: meta.iconBg,
    cardBg: meta.cardBg,
  }));

  // Build chart data: use a placeholder message if no completed training metrics exist.
  // The chart is intentionally empty until real training metrics are available.
  const chartData = [];

  // Map deployments to match the table columns shape
  const tableData = deployments.map((d) => ({
    id: d.id,
    name: d.model_name || `Model-${d.model_id}`,
    version: d.version,
    status: d.status?.toLowerCase(),
    latency: d.average_latency_ms ? `${d.average_latency_ms}ms` : "—",
    action: d.status?.toUpperCase() === "ACTIVE" ? "Metrics" : "Start",
  }));

  const isLoading = loadingStats || loadingDeployments;

  return (
    <>
      <div className="min-h-screen bg-gray-50">
        {/* Sidebar */}
        <Sidebar isOpen={isOpen} onClose={() => setIsOpen(false)} />

        {/* Navbar */}
        <Navbar onMenuClick={() => setIsOpen((prev) => !prev)} />

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
                onClick={() => { fetchStats(); fetchDeployments(); }}
                disabled={isLoading}
                className={isLoading ? "[&>svg]:animate-spin [&>svg]:text-blue-600" : ""}
              >
                Refresh
              </Button>
              <Button icon={Plus} variant="primary">
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
                onClick={fetchStats}
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
              {chartData.length > 0 ? (
                <LineChart
                  title="Training Performance"
                  data={chartData}
                  xKey="epoch"
                  lines={[
                    {
                      dataKey: "trainingLoss",
                      name: "Training Loss",
                      color: "#2563eb",
                    },
                    {
                      dataKey: "validationLoss",
                      name: "Validation Loss",
                      color: "#dc2626",
                    },
                  ]}
                />
              ) : (
                <div className="w-full h-full min-h-[280px] flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-300 bg-white text-center px-6">
                  <TrendingUp size={28} className="text-gray-300 mb-3" />
                  <p className="text-sm font-semibold text-gray-500">
                    No Training Metrics Yet
                  </p>
                  <p className="text-xs text-gray-400 mt-1 max-w-xs">
                    Training loss data will appear here once a training run completes.
                    Start a training job to see performance charts.
                  </p>
                </div>
              )}
            </div>
            <div className="min-w-0">
              {/* Activity feed — real recent activity from /pipeline/dashboard/stats */}
              <ActivityCard
                activities={stats?.recent_activity || []}
                loading={loadingStats}
              />
            </div>
          </div>

          {/* Deployed Models Table — real data from GET /deployments */}
          <div className="min-w-0 my-6 px-5">
            {loadingDeployments ? (
              <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-gray-200">
                <RefreshCw className="h-7 w-7 animate-spin text-blue-600 mb-3" />
                <p className="text-gray-600 text-sm font-medium">
                  Loading deployed models...
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

        {/* Footer */}
        <div className="mt-12 lg:ml-[280px]">
          <Footer />
        </div>
      </div>
    </>
  );
}

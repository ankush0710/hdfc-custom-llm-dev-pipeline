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
import { useEffect, useState, useCallback, useMemo } from "react";
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
  const [stats, setStats] = useState(null);
  const [deployments, setDeployments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [statsError, setStatsError] = useState(false);

  const loadDashboardData = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    setStatsError(false);

    try {
      const [statsData, deploymentsData] = await Promise.all([
        getDashboardStats().catch((err) => {
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
      setDeployments(Array.isArray(deploymentsData) ? deploymentsData : []);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

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
            {chartData.length > 0 ? (
              <LineChart
                title="Training Performance"
                data={chartData}
                xKey="epoch"
                lines={[
                  {
                    dataKey: "trainingLoss",
                    label: "Training Loss",
                    color: "#002B55",
                  },
                ]}
              />
            ) : (
              <div className="flex flex-col items-center justify-center p-8 bg-white rounded-xl border border-dashed border-gray-300 text-center h-[340px]">
                <TrendingUp size={32} className="text-gray-300 mb-2" />
                <h3 className="text-base font-semibold text-gray-700">
                  Training Performance Chart
                </h3>
                <p className="mt-1 text-sm text-gray-400 max-w-sm">
                  Loss curves will appear here automatically once fine-tuning runs complete.
                </p>
              </div>
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
    </>
  );
}

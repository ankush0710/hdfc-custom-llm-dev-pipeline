//=======================================================================================//
/*
Model Evaluation History Page: Review and manage past evaluation runs across enterprise models.
*/
//=======================================================================================//
"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { Plus, RefreshCw, Activity, Target, CheckCircle2, TrendingUp } from "lucide-react";
import Button from "@/components/ui/Button";
import ModelsTable from "@/components/tables/ModelsTable";
import NewEvaluationModal from "@/components/evaluation/NewEvaluationModal";
import { createEvaluationColumns } from "@/components/tables/EvaluationTableColumns/EvaluationColumns";
import { getEvaluations, getEvaluationStats } from "@/app/services/evaluationService/evaluationServices";
import { toast } from "sonner";

export default function EvaluationPage() {
  const [evaluations, setEvaluations] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState("ALL");

  // Fetch evaluations and aggregate stats from FastAPI
  const fetchData = useCallback(async (isSilent = false) => {
    try {
      if (!isSilent) setLoading(true);
      else setRefreshing(true);

      const [evalList, evalStats] = await Promise.all([
        getEvaluations().catch(() => []),
        getEvaluationStats().catch(() => null),
      ]);

      setEvaluations(Array.isArray(evalList) ? evalList : []);
      setStats(evalStats);
    } catch (err) {
      console.error("Failed to fetch evaluation data:", err);
      toast.error("Failed to load evaluation records");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Filter options for ModelsTable dropdown
  const filterOptions = useMemo(
    () => [
      { label: "All Statuses", value: "ALL" },
      { label: "Passed", value: "PASSED" },
      { label: "Running", value: "RUNNING" },
      { label: "Queued", value: "QUEUED" },
      { label: "Failed", value: "FAILED" },
    ],
    []
  );

  // Filtered dataset
  const filteredEvaluations = useMemo(() => {
    if (statusFilter === "ALL") return evaluations;

    return evaluations.filter((item) => {
      const itemStatus = (item.evaluation_status || "").toUpperCase();
      if (statusFilter === "PASSED") {
        return itemStatus === "PASSED" || itemStatus === "COMPLETED";
      }
      return itemStatus === statusFilter;
    });
  }, [evaluations, statusFilter]);

  const columns = useMemo(
    () =>
      createEvaluationColumns({
        onStartEval: () => fetchData(true),
      }),
    [fetchData]
  );

  // Use real backend stats — show '—' when not available, never fabricate
  const totalEvalsDisplay = stats?.total_evaluations ?? evaluations.length;
  const avgScoreDisplay = stats?.avg_score_str ?? (stats?.avg_score != null ? `${stats.avg_score}%` : "N/A");
  const successRateDisplay = stats?.success_rate ?? "N/A";

  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px] pb-16">
      {/* 1. Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 px-3 lg:px-0">
        <div>
          <h1 className="text-2xl lg:text-3xl font-extrabold text-gray-900 tracking-tight">
            Model Evaluation History
          </h1>
          <p className="text-xs lg:text-sm text-gray-500 mt-1 font-medium">
            Review and manage past evaluation runs across all deployed models.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="default"
            icon={RefreshCw}
            onClick={() => fetchData(true)}
            disabled={refreshing}
          >
            {refreshing ? "Refreshing..." : "Refresh"}
          </Button>

          <Button
            variant="primary"
            icon={Plus}
            onClick={() => setIsModalOpen(true)}
          >
            New Evaluation
          </Button>
        </div>
      </div>

      {/* 2. Top 3 Stat Cards matching Screenshot 1 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 px-3 lg:px-0">
        {/* Card 1: Total Evaluations */}
        <div className="bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-gray-400">
            <span>Total Evaluations</span>
            <Activity size={16} className="text-blue-600" />
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <span className="font-mono text-3xl font-extrabold text-gray-900 tracking-tight">
              {loading ? "..." : totalEvalsDisplay.toLocaleString()}
            </span>
            <span className="text-xs font-mono font-semibold text-emerald-600">
              {stats?.evaluations_trend ?? "—"}
            </span>
          </div>
        </div>

        {/* Card 2: Avg. Score */}
        <div className="bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-gray-400">
            <span>Avg. Score</span>
            <Target size={16} className="text-indigo-600" />
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <span className="font-mono text-3xl font-extrabold text-gray-900 tracking-tight">
              {loading ? "..." : avgScoreDisplay}
            </span>
            <span className="text-xs font-medium text-gray-400">
              Across top models
            </span>
          </div>
        </div>

        {/* Card 3: Success Rate */}
        <div className="bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-gray-400">
            <span>Success Rate</span>
            <CheckCircle2 size={16} className="text-emerald-600" />
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <span className="font-mono text-3xl font-extrabold text-gray-900 tracking-tight">
              {loading ? "..." : successRateDisplay}
            </span>
            <span className="text-xs font-mono font-semibold text-emerald-600 flex items-center gap-0.5">
              <TrendingUp size={13} />
              <span>{stats?.success_trend ?? "—"}</span>
            </span>
          </div>
        </div>
      </div>

      {/* 3. Recent Evaluations Table with Filter */}
      <div className="min-w-0">
        <ModelsTable
          title="Recent Evaluations"
          columns={columns}
          data={filteredEvaluations}
          pageSize={10}
          showFilter={true}
          filterOptions={filterOptions}
          selectedFilter={statusFilter}
          onFilterChange={(val) => setStatusFilter(val)}
        />
      </div>

      {/* 4. New Evaluation Modal */}
      <NewEvaluationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onEvaluationCreated={() => fetchData(true)}
      />
    </main>
  );
}

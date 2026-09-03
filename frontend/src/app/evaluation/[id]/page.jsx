//=======================================================================================//
/*
Evaluation Details Page: Granular benchmark analysis, overall scores, and task breakdowns.
*/
//=======================================================================================//
"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Loader2,
  Download,
  Boxes,
  FileSpreadsheet,
  CheckCircle2,
  RotateCcw,
} from "lucide-react";
import Breadcrumbs from "@/components/ui/Breadcrumbs";
import DetailHeader from "@/components/ui/DetailHeader";
import Button from "@/components/ui/Button";
import EvaluationOverallScoreCard from "@/components/evaluation/EvaluationOverallScoreCard";
import EvaluationMetricsGrid from "@/components/evaluation/EvaluationMetricsGrid";
import EvaluationBenchmarkBreakdownCard from "@/components/evaluation/EvaluationBenchmarkBreakdownCard";
import { getEvaluationDetail } from "@/app/services/evaluationService/evaluationServices";
import { toast } from "sonner";

export default function EvaluationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id;

  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch real-time evaluation details
  const fetchDetail = useCallback(async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const data = await getEvaluationDetail(id);
      setEvaluation(data);
    } catch (err) {
      console.error("Failed to fetch evaluation details:", err);
      setError(err?.response?.data?.detail || "Failed to load evaluation details");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  // Export report as JSON file
  const handleExportReport = () => {
    if (!evaluation) return;
    const jsonStr = JSON.stringify(evaluation, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `evaluation_${evaluation.display_id || evaluation.evaluation_id}.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success("Evaluation report exported successfully!");
  };

  const handleRegisterModel = () => {
    router.push("/model");
  };

  if (loading) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center lg:ml-[280px]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-[#002B55]" />
          <p className="text-gray-600 text-sm font-medium">
            Loading evaluation details. Please wait...
          </p>
        </div>
      </main>
    );
  }

  if (error || !evaluation) {
    return (
      <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px]">
        <div className="mx-auto max-w-md w-full rounded-2xl border border-slate-200 bg-white p-6 shadow-sm text-center">
          <h1 className="text-xl font-bold text-slate-900">
            Evaluation Not Found
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            {typeof error === "string" ? error : "The requested evaluation could not be found."}
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Button
              variant="primary"
              icon={ArrowLeft}
              onClick={() => router.push("/evaluation")}
            >
              Back to Evaluations
            </Button>
          </div>
        </div>
      </main>
    );
  }

  const rawStatus = (evaluation.status || "QUEUED").toLowerCase();
  const isCompleted = rawStatus === "completed" || rawStatus === "passed";
  const isFailed = rawStatus === "failed";
  const isRunning = rawStatus === "running";

  const badges = [
    {
      label: isCompleted ? "completed" : isFailed ? "failed" : rawStatus,
      variant: isCompleted ? "success" : isFailed ? "failed" : isRunning ? "running" : "default",
    },
  ];

  if (isCompleted && evaluation.target_met !== undefined && evaluation.target_met !== null) {
    badges.push({
      label: evaluation.target_met ? "target met" : "below target",
      variant: evaluation.target_met ? "success" : "warning",
    });
  }

  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px] pb-16">
      {/* 1. Breadcrumbs */}
      <div className="px-3 lg:px-0">
        <Breadcrumbs
          backHref="/evaluation"
          backLabel="Evaluation History"
        />
      </div>

      {/* 2. Detail Header matching Screenshot 2 */}
      <div className="px-3 lg:px-0 mb-6">
        <DetailHeader
          title={`Evaluation Details: ${evaluation.display_id || `EV-${evaluation.evaluation_id}`}`}
          badges={badges}
          actions={
            <>
              <Button
                variant="default"
                icon={Download}
                onClick={handleExportReport}
              >
                Export Report
              </Button>

              {isCompleted && (
                <Button
                  variant="primary"
                  icon={Boxes}
                  onClick={handleRegisterModel}
                >
                  Register Model
                </Button>
              )}
            </>
          }
        />

        {/* Model, Dataset, and Date Subtitle */}
        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 font-medium mt-1.5">
          <span>
            Model: <strong className="text-gray-900 font-semibold">{evaluation.model_name}</strong>
          </span>
          <span className="text-gray-300">•</span>
          <span>
            Dataset: <strong className="text-gray-900 font-semibold">{evaluation.dataset_name} ({evaluation.dataset_version})</strong>
          </span>
          <span className="text-gray-300">•</span>
          <span>
            Date: <strong className="text-gray-700 font-mono">{evaluation.date_formatted}</strong>
          </span>
        </div>
      </div>

      {/* 3. Upper Dashboard Grid: Overall Score & 4 Metric Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.3fr] gap-6 mb-6">
        {/* Left: Radial Progress Overall Score */}
        <EvaluationOverallScoreCard
          score={evaluation.overall_score}
          status={isCompleted ? "completed" : isFailed ? "failed" : rawStatus}
          targetMet={evaluation.target_met}
          threshold={evaluation.threshold}
        />

        {/* Right: Accuracy, Precision, Recall, F1 */}
        <EvaluationMetricsGrid
          accuracy={evaluation.accuracy}
          accuracyTrend={evaluation.accuracy_trend}
          precision={evaluation.precision}
          recall={evaluation.recall}
          recallTrend={evaluation.recall_trend}
          f1Score={evaluation.f1_score}
          f1Trend={evaluation.f1_trend}
        />
      </div>

      {/* 4. Bottom Section: Benchmark Results Breakdown */}
      <div className="min-w-0">
        <EvaluationBenchmarkBreakdownCard
          tasks={evaluation.benchmark_breakdown || []}
        />
      </div>
    </main>
  );
}

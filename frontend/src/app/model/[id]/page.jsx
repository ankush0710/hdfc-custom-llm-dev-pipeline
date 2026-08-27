//=======================================================================================//
/*
Model Details Page: Deep dive into model overview, deployment, metrics, and version history.
*/
//=======================================================================================//
"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Loader2,
  FileText,
  Rocket,
  MoreVertical,
  Check,
  RotateCcw,
} from "lucide-react";
import Breadcrumbs from "@/components/ui/Breadcrumbs";
import DetailHeader from "@/components/ui/DetailHeader";
import Button from "@/components/ui/Button";
import ModelsTable from "@/components/tables/ModelsTable";
import ModelOverviewCard from "@/components/model/ModelOverviewCard";
import ModelDeploymentInfoCard from "@/components/model/ModelDeploymentInfoCard";
import ModelPerformanceMetricsCard from "@/components/model/ModelPerformanceMetricsCard";
import ModelLogsModal from "@/components/model/ModelLogsModal";
import { getModelDetail, updateModelStatus } from "@/app/services/modelService/modelServices";
import { toast } from "sonner";

export default function ModelDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id;

  const [modelDetail, setModelDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isLogsOpen, setIsLogsOpen] = useState(false);
  const [deploying, setDeploying] = useState(false);

  // Fetch real model details from FastAPI
  const fetchDetail = useCallback(async (isSilent = false) => {
    if (!id) return;
    try {
      if (!isSilent) setLoading(true);
      setError(null);

      const data = await getModelDetail(id);
      setModelDetail(data);
    } catch (err) {
      console.error("Failed to fetch model details:", err);
      setError(err?.response?.data?.detail || "Failed to load model details");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  // Deployment action
  const handleDeploy = async () => {
    try {
      setDeploying(true);
      await updateModelStatus(id, "ACTIVE");
      toast.success("Model deployment triggered successfully!", {
        description: "Active serving endpoint provisioned on enterprise cluster.",
      });
      fetchDetail(true);
    } catch (err) {
      console.error("Failed to deploy model:", err);
      toast.error("Failed to deploy model.");
    } finally {
      setDeploying(false);
    }
  };

  // Version history table columns
  const versionColumns = useMemo(
    () => [
      {
        key: "version",
        label: "VERSION",
        render: (row) => (
          <span className="font-bold text-xs text-gray-900 font-mono">
            {row.version}
          </span>
        ),
      },
      {
        key: "status",
        label: "STATUS",
        render: (row) => {
          const isAct = (row.status || "").toUpperCase() === "ACTIVE" || (row.status || "").toUpperCase() === "READY";
          return (
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                isAct
                  ? "bg-emerald-50 border border-emerald-200 text-emerald-700"
                  : "bg-slate-100 border border-slate-200 text-slate-600"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  isAct ? "bg-emerald-500" : "bg-slate-400"
                }`}
              />
              <span>{isAct ? "Active" : "Archived"}</span>
            </span>
          );
        },
      },
      {
        key: "deployed_date",
        label: "DEPLOYED DATE",
        render: (row) => (
          <span className="text-xs text-gray-600 font-medium">
            {row.deployed_date}
          </span>
        ),
      },
      {
        key: "accuracy",
        label: "ACCURACY",
        render: (row) => (
          <span className="text-xs font-mono font-bold text-gray-800">
            {row.accuracy}
          </span>
        ),
      },
      {
        key: "changes",
        label: "CHANGES",
        render: (row) => (
          <span className="text-xs text-gray-600 line-clamp-1 max-w-md block" title={row.changes}>
            {row.changes}
          </span>
        ),
      },
      {
        key: "action",
        label: "ACTION",
        align: "right",
        render: () => (
          <button
            type="button"
            className="p-1 rounded text-gray-400 hover:text-gray-700 transition cursor-pointer"
            title="Options"
          >
            <MoreVertical size={15} />
          </button>
        ),
      },
    ],
    []
  );

  if (loading) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center lg:ml-[280px]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-[#002B55]" />
          <p className="text-gray-600 text-sm font-medium">
            Loading model details...
          </p>
        </div>
      </main>
    );
  }

  if (error || !modelDetail) {
    return (
      <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px]">
        <div className="mx-auto max-w-md w-full rounded-2xl border border-slate-200 bg-white p-6 shadow-sm text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-600 mb-3">
            <FileText size={24} />
          </div>
          <h1 className="text-xl font-bold text-slate-900">
            Model Not Found
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            {typeof error === "string" ? error : "The requested model could not be retrieved."}
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Button
              variant="primary"
              icon={ArrowLeft}
              onClick={() => router.push("/model")}
            >
              Back to Model Registry
            </Button>
          </div>
        </div>
      </main>
    );
  }

  const rawStatus = (modelDetail.status || "READY").toUpperCase();
  const isActive = rawStatus === "ACTIVE" || rawStatus === "READY" || rawStatus === "DEPLOYED";

  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px] pb-16">
      {/* 1. Breadcrumbs */}
      <div className="px-3 lg:px-0">
        <Breadcrumbs
          backHref="/model"
          backLabel="Back to Model Registry"
        />
      </div>

      {/* 2. Detail Header */}
      <div className="px-3 lg:px-0 mb-6">
        <DetailHeader
          title={`${modelDetail.model_name}-${modelDetail.version}`}
          badges={[
            {
              label: isActive ? "Active" : modelDetail.status,
              variant: isActive ? "success" : "warning",
            },
          ]}
          actions={
            <>
              <Button
                variant="default"
                icon={FileText}
                onClick={() => setIsLogsOpen(true)}
              >
                View Logs
              </Button>

              <Button
                variant="primary"
                icon={deploying ? Loader2 : Rocket}
                onClick={handleDeploy}
                disabled={deploying}
              >
                {deploying ? "Deploying..." : "Deploy Model"}
              </Button>
            </>
          }
        />
        <p className="text-xs text-gray-500 mt-1 font-medium">
          {modelDetail.description}
        </p>
      </div>

      {/* 3. Top Row: Model Overview & Deployment Info */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.5fr_1fr] gap-6 mb-6">
        <ModelOverviewCard
          baseModel={modelDetail.overview?.base_model}
          totalParameters={modelDetail.overview?.total_parameters}
          datasetName={modelDetail.overview?.dataset_name}
          trainingDate={modelDetail.overview?.training_date}
        />

        <ModelDeploymentInfoCard
          environment={modelDetail.deployment_info?.environment}
          instanceType={modelDetail.deployment_info?.instance_type}
          endpointUrl={modelDetail.deployment_info?.endpoint_url}
          status={modelDetail.status}
        />
      </div>

      {/* 4. Middle Section: Performance Metrics */}
      <div className="mb-6">
        <ModelPerformanceMetricsCard
          accuracy={modelDetail.performance_metrics?.accuracy}
          accuracyTrend={modelDetail.performance_metrics?.accuracy_trend}
          f1Score={modelDetail.performance_metrics?.f1_score}
          f1Trend={modelDetail.performance_metrics?.f1_trend}
          latency={modelDetail.performance_metrics?.latency_ms}
          throughput={modelDetail.performance_metrics?.throughput_req_s}
          lastEvaluated={modelDetail.performance_metrics?.last_evaluated}
        />
      </div>

      {/* 5. Bottom Section: Version History Table */}
      <div className="min-w-0">
        <ModelsTable
          title="Version History"
          columns={versionColumns}
          data={modelDetail.version_history || []}
          pageSize={5}
          showFilter={false}
        />
      </div>

      {/* Logs Modal */}
      <ModelLogsModal
        isOpen={isLogsOpen}
        onClose={() => setIsLogsOpen(false)}
        modelName={`${modelDetail.model_name} (${modelDetail.version})`}
        logs={modelDetail.logs || []}
      />
    </main>
  );
}

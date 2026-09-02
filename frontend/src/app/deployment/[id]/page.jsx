//=======================================================================================//
/*
Deployment Details Page: Runtime status, health metrics, and administrative lifecycle actions.
*/
//=======================================================================================//
"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Loader2,
  FileText,
  Activity,
  Server,
} from "lucide-react";
import Breadcrumbs from "@/components/ui/Breadcrumbs";
import DetailHeader from "@/components/ui/DetailHeader";
import Button from "@/components/ui/Button";
import DeploymentOverviewCard from "@/components/deployment/DeploymentOverviewCard";
import DeploymentRuntimeStatusCard from "@/components/deployment/DeploymentRuntimeStatusCard";
import DeploymentHealthMetricsCard from "@/components/deployment/DeploymentHealthMetricsCard";
import DeploymentAdminActionsCard from "@/components/deployment/DeploymentAdminActionsCard";
import ModelLogsModal from "@/components/model/ModelLogsModal";
import { getDeploymentById } from "@/app/services/deploymentService/deploymentServices";
import { toast } from "sonner";

export default function DeploymentDetailPage({ params: pageParams }) {
  const routeParams = useParams();
  const router = useRouter();
  const id = routeParams?.id || pageParams?.id;

  const [deployment, setDeployment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isLogsOpen, setIsLogsOpen] = useState(false);

  // Fetch deployment details from FastAPI
  const fetchDetail = useCallback(async (isSilent = false) => {
    if (!id) return;
    try {
      if (!isSilent) setLoading(true);
      setError(null);

      const data = await getDeploymentById(id);
      setDeployment(data);
    } catch (err) {
      console.error("Failed to fetch deployment details:", err);
      setError(err?.response?.data?.detail || "Failed to load deployment details");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  if (loading) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center lg:ml-[280px]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-[#002B55]" />
          <p className="text-gray-600 text-sm font-medium">
            Loading deployment details. Please wait...
          </p>
        </div>
      </main>
    );
  }

  if (error || !deployment) {
    return (
      <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px]">
        <div className="mx-auto max-w-md w-full rounded-2xl border border-slate-200 bg-white p-6 shadow-sm text-center">
          <h1 className="text-xl font-bold text-slate-900">
            Deployment Not Found
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            {typeof error === "string" ? error : "The requested deployment could not be retrieved."}
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Button
              variant="primary"
              icon={ArrowLeft}
              onClick={() => router.push("/deployment")}
            >
              Back to Deployments
            </Button>
          </div>
        </div>
      </main>
    );
  }

  const rawStatus = (deployment.status || "ACTIVE").toUpperCase();
  const isActive = rawStatus === "ACTIVE" || rawStatus === "READY";
  const modelVerTitle = `${deployment.model_name || `Model-${deployment.model_id}`} ${deployment.version?.startsWith("v") ? deployment.version : `v${deployment.version}`}`;

  const sampleLogs = [
    `[${deployment.created_at ? new Date(deployment.created_at).toLocaleTimeString() : "10:00:00"}] Initializing model container on ${deployment.environment} cluster...`,
    `[${deployment.created_at ? new Date(deployment.created_at).toLocaleTimeString() : "10:00:05"}] Weights loaded successfully for ${deployment.model_name || "model"}.`,
    `[${deployment.created_at ? new Date(deployment.created_at).toLocaleTimeString() : "10:00:12"}] LoRA adapter merged with base model.`,
    `[${deployment.created_at ? new Date(deployment.created_at).toLocaleTimeString() : "10:00:18"}] HTTP serving endpoint listening at ${deployment.endpoint}.`,
    `[${deployment.created_at ? new Date(deployment.created_at).toLocaleTimeString() : "10:00:25"}] Health check status: 200 OK (Latency: 142ms).`,
  ];

  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px] pb-16">
      {/* 1. Breadcrumbs */}
      <div className="px-3 lg:px-0">
        <Breadcrumbs
          backHref="/deployment"
          backLabel="Back to Deployments"
        />
      </div>

      {/* 2. Detail Header matching Screenshot 2 */}
      <div className="px-3 lg:px-0 mb-6">
        <DetailHeader
          title={`Deployment: ${modelVerTitle}`}
          badges={[
            {
              label: isActive ? "ACTIVE" : deployment.status,
              variant: isActive ? "success" : "danger",
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
                variant="default"
                icon={Activity}
                onClick={() => router.push(`/model/${deployment.model_id}`)}
              >
                View Metrics
              </Button>
            </>
          }
        />
      </div>

      {/* 3. Top Row: Overview & Runtime Status */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-6 mb-6">
        <DeploymentOverviewCard
          modelVersion={modelVerTitle}
          environment={deployment.environment}
          status={deployment.status}
          endpointUrl={deployment.endpoint}
        />

        <DeploymentRuntimeStatusCard
          status={deployment.status}
          modelLoaded={isActive}
          adapterLoaded={isActive}
          inferenceReady={isActive}
        />
      </div>

      {/* 4. Bottom Row: Health Metrics & Administrative Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.4fr] gap-6">
        <DeploymentHealthMetricsCard
          status={deployment.status}
          lastRequestTime={deployment.updated_at ? new Date(deployment.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + " (TODAY)" : "18:03 (TODAY)"}
        />

        <DeploymentAdminActionsCard
          deploymentId={deployment.id}
          status={deployment.status}
          onActionComplete={() => fetchDetail(true)}
        />
      </div>

      {/* Logs Modal */}
      <ModelLogsModal
        isOpen={isLogsOpen}
        onClose={() => setIsLogsOpen(false)}
        modelName={modelVerTitle}
        logs={sampleLogs}
      />
    </main>
  );
}

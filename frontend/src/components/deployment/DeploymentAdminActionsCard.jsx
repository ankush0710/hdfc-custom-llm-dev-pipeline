"use client";

import { useState } from "react";
import { AlertTriangle, Power, RotateCw, RefreshCcw, Loader2 } from "lucide-react";
import Button from "@/components/ui/Button";
import {
  unloadModel,
  reloadModel,
  restartDeployment,
  startDeployment,
} from "@/app/services/deploymentService/deploymentServices";
import { toast } from "sonner";

export default function DeploymentAdminActionsCard({
  deploymentId,
  status = "ACTIVE",
  onActionComplete,
}) {
  const [loadingAction, setLoadingAction] = useState(null);

  const isStopped = String(status).toUpperCase() === "STOPPED";

  const handleUnloadToggle = async () => {
    try {
      setLoadingAction(isStopped ? "start" : "unload");
      if (isStopped) {
        await startDeployment(deploymentId);
        toast.success("Model deployment started successfully");
      } else {
        await unloadModel(deploymentId);
        toast.success("Model unloaded successfully");
      }
      if (onActionComplete) onActionComplete();
    } catch (err) {
      console.error("Action failed:", err);
      toast.error(err?.response?.data?.detail || "Action failed");
    } finally {
      setLoadingAction(null);
    }
  };

  const handleReload = async () => {
    try {
      setLoadingAction("reload");
      await reloadModel(deploymentId);
      toast.success("Model weights reloaded in memory");
      if (onActionComplete) onActionComplete();
    } catch (err) {
      console.error("Reload failed:", err);
      toast.error(err?.response?.data?.detail || "Reload failed");
    } finally {
      setLoadingAction(null);
    }
  };

  const handleRestart = async () => {
    try {
      setLoadingAction("restart");
      await restartDeployment(deploymentId);
      toast.success("Inference container restarted");
      if (onActionComplete) onActionComplete();
    } catch (err) {
      console.error("Restart failed:", err);
      toast.error(err?.response?.data?.detail || "Restart failed");
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="h-full bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm flex flex-col justify-between">
      {/* Title */}
      <div>
        <div className="flex items-center gap-2 mb-1.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
            <AlertTriangle size={16} />
          </div>
          <h3 className="text-base font-bold text-gray-900">
            Administrative Actions
          </h3>
        </div>
        <p className="text-xs text-gray-400 font-medium">
          These actions directly affect the production deployment. Use with caution.
        </p>
      </div>

      {/* 3 Action Buttons matching Screenshot */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
        {/* Button 1: Unload / Start */}
        <button
          type="button"
          onClick={handleUnloadToggle}
          disabled={!!loadingAction}
          className="flex items-center justify-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-xs font-bold text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition cursor-pointer disabled:opacity-50"
        >
          {loadingAction === "unload" || loadingAction === "start" ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Power size={14} />
          )}
          <span>{isStopped ? "Start Model" : "Unload Model"}</span>
        </button>

        {/* Button 2: Reload */}
        <button
          type="button"
          onClick={handleReload}
          disabled={!!loadingAction}
          className="flex items-center justify-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-xs font-bold text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition cursor-pointer disabled:opacity-50"
        >
          {loadingAction === "reload" ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <RotateCw size={14} />
          )}
          <span>Reload Model</span>
        </button>

        {/* Button 3: Restart Service */}
        <button
          type="button"
          onClick={handleRestart}
          disabled={!!loadingAction}
          className="flex items-center justify-center gap-1.5 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-xs font-bold text-rose-700 hover:bg-rose-100 transition cursor-pointer disabled:opacity-50"
        >
          {loadingAction === "restart" ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <RefreshCcw size={14} />
          )}
          <span>Restart Service</span>
        </button>
      </div>
    </div>
  );
}

//=======================================================================================//
/*
Training Jobs Dashboard: Monitor and manage foundation model fine-tuning pipelines.
*/
//=======================================================================================//
"use client";

import { useEffect, useState, useMemo, useCallback, useRef } from "react";
import StatCard from "@/components/ui/StatCard";
import ModelsTable from "@/components/tables/ModelsTable";
import Button from "@/components/ui/Button";
import NewTrainingModal from "@/components/training/NewTrainingModal";
import { createTrainingColumns } from "@/components/tables/TrainingTableColumns/TrainingColumns";
import {
  getTrainingRuns,
  startTrainingRun,
  stopTrainingRun,
} from "@/app/services/trainingService/trainingServices";

import {
  Plus,
  RefreshCw,
  Sparkles,
  CircleCheck,
  RefreshCcwDot,
  CircleAlert,
  Layers,
} from "lucide-react";
import { toast } from "sonner";

import { useAuth } from "@/app/context/AuthContext";

export default function Training() {
  const { hasRole, isAuthenticated, loading: authLoading } = useAuth();
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState("ALL");

  const canManageTraining = hasRole("ADMIN", "DS");

  const isFetchingRef = useRef(false);
  const latestReqIdRef = useRef(0);

  // Load real training runs from backend API
  const loadRuns = useCallback(async (isSilent = false) => {
    // Avoid overlapping background polling requests
    if (isFetchingRef.current && isSilent) {
      return;
    }

    const reqId = ++latestReqIdRef.current;
    isFetchingRef.current = true;

    if (!isSilent) setLoading(true);
    else setRefreshing(true);

    try {
      const data = await getTrainingRuns();
      // Ensure only the newest response updates state to avoid race condition overwrites
      if (reqId === latestReqIdRef.current && Array.isArray(data)) {
        setRuns((prevRuns) => {
          const prevMap = new Map(prevRuns.map((r) => [r.id, r]));
          return data.map((newRun) => {
            const prevRun = prevMap.get(newRun.id);
            if (
              prevRun &&
              (newRun.status || "").toUpperCase() === "RUNNING" &&
              (prevRun.status || "").toUpperCase() === "RUNNING"
            ) {
              const prevProg =
                typeof prevRun.progress === "number"
                  ? prevRun.progress
                  : prevRun.job_progress || 0;
              const newProg =
                typeof newRun.progress === "number"
                  ? newRun.progress
                  : newRun.job_progress || 0;
              // Guarantee monotonic progress display while running
              if (newProg < prevProg) {
                return { ...newRun, progress: prevProg, job_progress: prevProg };
              }
            }
            return newRun;
          });
        });
      }
    } catch (err) {
      console.error("Failed to load training runs:", err);
      if (!isSilent) {
        toast.error("Failed to fetch training runs from server.");
      }
    } finally {
      isFetchingRef.current = false;
      if (reqId === latestReqIdRef.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, []);

  // Initial load
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      loadRuns();
    }
  }, [authLoading, isAuthenticated, loadRuns]);

  // Check if any training run is actively running or queued
  const hasActiveRuns = useMemo(() => {
    return runs.some((r) => {
      const status = (r.status || "").toUpperCase();
      return status === "RUNNING" || status === "QUEUED";
    });
  }, [runs]);

  // Clean polling every 2.5 seconds while active runs exist
  useEffect(() => {
    if (!hasActiveRuns) return;

    const intervalId = setInterval(() => {
      loadRuns(true);
    }, 2500);

    return () => clearInterval(intervalId);
  }, [hasActiveRuns, loadRuns]);

  // Action handlers
  const handleStartRun = async (run) => {
    try {
      await startTrainingRun(run.id);
      toast.success(`Training Run #${run.id} started successfully!`);
      loadRuns(true);
    } catch (err) {
      console.error("Failed to start training run:", err);
      const detail = err?.response?.data?.detail || "Failed to start training run.";
      toast.error(typeof detail === "string" ? detail : "Start failed.");
    }
  };

  const handleStopRun = async (run) => {
    try {
      await stopTrainingRun(run.id);
      toast.success(`Training Run #${run.id} stopped successfully.`);
      loadRuns(true);
    } catch (err) {
      console.error("Failed to stop training run:", err);
      const detail = err?.response?.data?.detail || "Failed to stop training run.";
      toast.error(typeof detail === "string" ? detail : "Stop failed.");
    }
  };

  const handleViewMetrics = (run) => {
    toast.success(`Opening metrics for Training Run #${run.id}`);
  };

  const handleViewLogs = (run) => {
    toast.error(`Viewing error logs for Training Run #${run.id}: ${run.error_message || "No specific error logs recorded."}`);
  };

  const handleCancelRun = async (run) => {
    try {
      await stopTrainingRun(run.id);
      toast.success(`Training Run #${run.id} cancelled successfully.`);
      loadRuns(true);
    } catch (err) {
      console.error("Failed to cancel training run:", err);
      const detail = err?.response?.data?.detail || "Failed to cancel training run.";
      toast.error(typeof detail === "string" ? detail : "Cancel failed.");
    }
  };


  // Build table columns
  const columns = useMemo(
    () =>
      createTrainingColumns({
        onStartRun: canManageTraining ? handleStartRun : undefined,
        onStopRun: canManageTraining ? handleStopRun : undefined,
        onViewMetrics: handleViewMetrics,
        onViewLogs: handleViewLogs,
        onCancelRun: canManageTraining ? handleCancelRun : undefined,
      }),
    [canManageTraining]
  );

  // Compute stat cards dynamically from real backend training run records
  const statCards = useMemo(() => {
    const total = runs.length;
    let completed = 0;
    let running = 0;
    let failed = 0;

    runs.forEach((r) => {
      const status = (r.status || "").toUpperCase();
      if (status === "COMPLETED") {
        completed++;
      } else if (status === "RUNNING" || status === "QUEUED" || status === "CREATED") {
        running++;
      } else if (status === "FAILED") {
        failed++;
      }
    });

    return [
      {
        statName: "Total Runs",
        value: total,
        icon: Layers,
        iconBg: "bg-blue-50 text-blue-600 border-blue-100",
        cardBg:
          "border-t-5 border-t-[#E0E0E0] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#002B55]",
        valueColor: "text-[#002B55]",
      },
      {
        statName: "Completed",
        value: completed,
        icon: CircleCheck,
        iconBg: "bg-emerald-50 text-emerald-600 border-emerald-100",
        cardBg:
          "border-t-5 border-t-[#A5D6A7] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#266210]",
        valueColor: "text-[#002B55]",
      },
      {
        statName: "In Progress",
        value: running,
        icon: RefreshCcwDot,
        iconBg: "bg-amber-50 text-amber-600 border-amber-100",
        cardBg:
          "border-t-5 border-t-[#FFE082] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#FFA000]",
        valueColor: "text-[#002B55]",
      },
      {
        statName: "Failed",
        value: failed,
        icon: CircleAlert,
        iconBg: "bg-red-50 text-red-600 border-red-100",
        cardBg:
          "border-t-5 border-t-[#FFCDC9] px-6 py-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 group hover:border-t-[#D90000]",
        valueColor: "text-[#D90000]",
      },
    ];
  }, [runs]);

  // Filter options for the ModelsTable filter dropdown
  const filterOptions = useMemo(() => {
    return [
      { label: "All Runs", value: "ALL", count: runs.length },
      {
        label: "Running",
        value: "RUNNING",
        count: runs.filter((r) => (r.status || "").toUpperCase() === "RUNNING").length,
      },
      {
        label: "Completed",
        value: "COMPLETED",
        count: runs.filter((r) => (r.status || "").toUpperCase() === "COMPLETED").length,
      },
      {
        label: "Failed",
        value: "FAILED",
        count: runs.filter((r) => (r.status || "").toUpperCase() === "FAILED").length,
      },
      {
        label: "Queued",
        value: "QUEUED",
        count: runs.filter((r) => (r.status || "").toUpperCase() === "QUEUED").length,
      },
      {
        label: "Created",
        value: "CREATED",
        count: runs.filter((r) => (r.status || "").toUpperCase() === "CREATED").length,
      },
    ];
  }, [runs]);

  // Filtered runs passed into ModelsTable
  const filteredRuns = useMemo(() => {
    if (statusFilter === "ALL") return runs;
    return runs.filter((r) => (r.status || "").toUpperCase() === statusFilter);
  }, [runs, statusFilter]);

  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px]">
      {/* Header row containing title and actions section */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="px-5">
          <h1 className="text-[#002B55] font-bold text-3xl">
            Training Jobs
          </h1>
          <p className="pt-1 lg:pt-3 text-gray-600 text-sm">
            Monitor and manage foundation model fine-tuning pipelines.
          </p>
        </div>

        <div className="flex items-center gap-3 px-5 lg:px-0">
          <Button
            onClick={() => loadRuns(true)}
            disabled={refreshing || loading}
            icon={RefreshCw}
            className={refreshing ? "[&>svg]:animate-spin [&>svg]:text-blue-600" : ""}
          >
            Refresh
          </Button>

          {canManageTraining && (
            <Button
              onClick={() => setIsModalOpen(true)}
              icon={Plus}
              variant="primary"
            >
              New Training
            </Button>
          )}
        </div>
      </div>

      {/* Stat cards for displaying training pipeline metrics */}
      <div className="my-6 px-5">
        <StatCard statData={statCards} />
      </div>

      {/* Training runs table section using ModelsTable component */}
      <div className="min-w-0 my-6 px-5">
        {loading ? (
          <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-gray-200">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mb-3" />
            <p className="text-gray-600 text-sm font-medium">
              Loading training runs from server...
            </p>
          </div>
        ) : runs.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-dashed border-gray-300 text-center">
            <div className="h-12 w-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
              <Sparkles size={24} />
            </div>
            <h3 className="text-base font-semibold text-gray-900">
              No training runs configured yet
            </h3>
            <p className="mt-1 text-sm text-gray-500 max-w-sm">
              Initiate a fine-tuning run on an existing dataset version to start training your custom LLM.
            </p>
            {canManageTraining && (
              <div className="mt-6">
                <Button
                  onClick={() => setIsModalOpen(true)}
                  icon={Plus}
                  variant="primary"
                >
                  Create First Training Job
                </Button>
              </div>
            )}
          </div>
        ) : (
          <ModelsTable
            title="Recent Training Runs"
            columns={columns}
            data={filteredRuns}
            pageSize={5}
            showFilter={true}
            filterOptions={filterOptions}
            selectedFilter={statusFilter}
            onFilterChange={setStatusFilter}
          />
        )}
      </div>

      {/* New Training Configuration Modal */}
      <NewTrainingModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onRunCreated={() => loadRuns(true)}
      />
    </main>
  );
}

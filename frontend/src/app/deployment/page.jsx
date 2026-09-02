//=======================================================================================//
/*
Model Deployment Page: Manage and provision active enterprise language models across environments.
*/
//=======================================================================================//
"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { Plus, RefreshCw, Server } from "lucide-react";
import Button from "@/components/ui/Button";
import ModelsTable from "@/components/tables/ModelsTable";
import DeployNewModelModal from "@/components/deployment/DeployNewModelModal";
import { createDeploymentColumns } from "@/components/tables/DeploymentTableColumns/DeploymentColumns";
import { getDeployments } from "@/app/services/deploymentService/deploymentServices";
import { useAuth } from "@/app/context/AuthContext";
import { toast } from "sonner";

export default function DeploymentPage() {
  const { hasRole, isAuthenticated, loading: authLoading } = useAuth();
  const [deployments, setDeployments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState("ALL");

  const canDeploy = hasRole("ADMIN");

  // Fetch active deployments from FastAPI
  const fetchDeployments = useCallback(async (isSilent = false) => {
    try {
      if (!isSilent) setLoading(true);
      else setRefreshing(true);

      const data = await getDeployments();
      if (Array.isArray(data)) {
        setDeployments(data);
      } else {
        setDeployments([]);
      }
    } catch (err) {
      console.error("Failed to fetch deployments:", err);
      toast.error("Failed to load deployments from server");
      setDeployments([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      fetchDeployments();
    }
  }, [authLoading, isAuthenticated, fetchDeployments]);


  // Filter options for ModelsTable dropdown
  const filterOptions = useMemo(
    () => [
      { label: "All Statuses", value: "ALL" },
      { label: "Active", value: "ACTIVE" },
      { label: "Stopped", value: "STOPPED" },
    ],
    []
  );

  // Filtered dataset
  const filteredDeployments = useMemo(() => {
    if (statusFilter === "ALL") return deployments;

    return deployments.filter((item) => {
      const itemStatus = (item.status || "").toUpperCase();
      return itemStatus === statusFilter;
    });
  }, [deployments, statusFilter]);

  const columns = useMemo(() => createDeploymentColumns(), []);

  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px] pb-16">
      {/* Header Section matching Screenshot 1 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 px-3 lg:px-0">
        <div>
          <h1 className="text-2xl lg:text-3xl font-extrabold text-gray-900 tracking-tight">
            Model Deployment
          </h1>
          <p className="text-xs lg:text-sm text-gray-500 mt-1 font-medium">
            Manage active language model deployments across environments.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="default"
            icon={RefreshCw}
            onClick={() => fetchDeployments(true)}
            disabled={refreshing}
          >
            {refreshing ? "Refreshing..." : "Refresh"}
          </Button>

          {canDeploy && (
            <Button
              variant="primary"
              icon={Plus}
              onClick={() => setIsModalOpen(true)}
            >
              Deploy New Model
            </Button>
          )}
        </div>
      </div>

      {/* Deployments Table with built-in Status Filter */}
      <div className="min-w-0">
        {loading ? (
          <div className="flex min-h-[280px] items-center justify-center rounded-2xl border border-gray-200/80 bg-white shadow-sm">
            <div className="flex flex-col items-center gap-3 text-gray-500">
              <RefreshCw size={24} className="animate-spin text-[#002B55]" />
              <span className="text-sm font-medium">
                Loading deployment records...
              </span>
            </div>
          </div>
        ) : (
          <ModelsTable
            title="Active Deployments"
            columns={columns}
            data={filteredDeployments}
            pageSize={10}
            showFilter={true}
            filterOptions={filterOptions}
            selectedFilter={statusFilter}
            onFilterChange={(val) => setStatusFilter(val)}
          />
        )}
      </div>

      {/* Deploy New Model Modal */}
      <DeployNewModelModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onModelDeployed={() => fetchDeployments(true)}
      />
    </main>
  );
}

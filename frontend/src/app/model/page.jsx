//=======================================================================================//
/*
Model Registry Page: Manage, deploy, and track all language models across the enterprise.
*/
//=======================================================================================//
"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import ModelsTable from "@/components/tables/ModelsTable";
import Button from "@/components/ui/Button";
import NewModelModal from "@/components/model/NewModelModal";
import ModelDetailsDrawer from "@/components/model/ModelDetailsDrawer";
import { createModelColumns } from "@/components/tables/ModelTableColumns/ModelColumns";
import { getModels } from "@/app/services/modelService/modelServices";
import { useAuth } from "@/app/context/AuthContext";
import { Plus, RefreshCw } from "lucide-react";
import { toast } from "sonner";

export default function ModelRegistryPage() {
    const { hasRole, isAuthenticated, loading: authLoading } = useAuth();
    const [models, setModels] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedModel, setSelectedModel] = useState(null);
    const [statusFilter, setStatusFilter] = useState("ALL");

    const canRegisterModel = hasRole("ADMIN", "DS");

    // Fetch models from FastAPI backend
    const fetchModels = useCallback(async (isSilent = false) => {
        try {
            if (!isSilent) setLoading(true);
            else setRefreshing(true);
            setError(null);

            const data = await getModels();
            if (Array.isArray(data)) {
                setModels(data);
            } else {
                setModels([]);
            }
        } catch (err) {
            console.error("Failed to fetch models:", err);
            const msg = err?.response?.data?.detail || "Failed to fetch models from Model Registry.";
            setError(typeof msg === "string" ? msg : "Failed to load models.");
            toast.error("Failed to fetch models from Model Registry.");
            setModels([]);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, []);

    useEffect(() => {
        if (!authLoading && isAuthenticated) {
            fetchModels();
        }
    }, [authLoading, isAuthenticated, fetchModels]);


    // Filter options for ModelsTable filter dropdown
    const filterOptions = useMemo(
        () => [
            { label: "All Statuses", value: "ALL" },
            { label: "Active", value: "ACTIVE" },
            { label: "Training", value: "TRAINING" },
            { label: "Archived", value: "ARCHIVED" },
            { label: "Created", value: "CREATED" },
        ],
        []
    );

    // Filtered dataset
    const filteredModels = useMemo(() => {
        if (statusFilter === "ALL") return models;

        return models.filter((item) => {
            const itemStatus = (item.status || "").toUpperCase();
            if (statusFilter === "ACTIVE") {
                return ["ACTIVE", "APPROVED", "READY", "DEPLOYED"].includes(itemStatus);
            }
            if (statusFilter === "TRAINING") {
                return ["TRAINING", "EVALUATING"].includes(itemStatus);
            }
            if (statusFilter === "ARCHIVED") {
                return ["ARCHIVED", "DEPRECATED", "REJECTED"].includes(itemStatus);
            }
            if (statusFilter === "CREATED") {
                return itemStatus === "CREATED";
            }
            return true;
        });
    }, [models, statusFilter]);

    const columns = useMemo(
        () =>
            createModelColumns({
                onViewDetails: (model) => setSelectedModel(model),
            }),
        []
    );

    return (
        <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px] pb-16">
            {/* Header Section */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 px-3 lg:px-0">
                <div>
                    <h1 className="text-2xl lg:text-3xl font-extrabold text-gray-900 tracking-tight">
                        Model Registry
                    </h1>
                    <p className="text-xs lg:text-sm text-gray-500 mt-1 font-medium">
                        Manage, deploy, and track all language models across the enterprise.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <Button
                        variant="default"
                        icon={RefreshCw}
                        onClick={() => fetchModels(true)}
                        disabled={refreshing}
                    >
                        {refreshing ? "Refreshing..." : "Refresh"}
                    </Button>

                    {canRegisterModel && (
                        <Button
                            variant="primary"
                            icon={Plus}
                            onClick={() => setIsModalOpen(true)}
                        >
                            Register New Model
                        </Button>
                    )}
                </div>
            </div>

            {/* Models Table with built-in Status Filter */}
            <div className="min-w-0">
                <ModelsTable
                    title="Registered Enterprise Models"
                    columns={columns}
                    data={filteredModels}
                    pageSize={10}
                    showFilter={true}
                    filterOptions={filterOptions}
                    selectedFilter={statusFilter}
                    onFilterChange={(val) => setStatusFilter(val)}
                    loading={loading}
                    error={error}
                    onRetry={() => fetchModels()}
                    emptyMessage="No models registered in the Model Registry yet. Create and train a model or register one using the button above."
                />
            </div>

            {/* Register New Model Modal */}
            <NewModelModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onModelCreated={() => fetchModels(true)}
            />

            {/* Model Details Drawer / Dialog */}
            <ModelDetailsDrawer
                isOpen={!!selectedModel}
                onClose={() => setSelectedModel(null)}
                model={selectedModel}
                onStatusUpdated={() => fetchModels(true)}
            />
        </main>
    );
}
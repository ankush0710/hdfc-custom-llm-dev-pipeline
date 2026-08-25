//=======================================================================================//
/*
The main dashboard that shows all information about datasets
*/
//=======================================================================================//
"use client";
import { useRouter } from "next/navigation";
import StatCard from "@/components/ui/StatCard";
import ModelsTable from "@/components/tables/ModelsTable";
import Button from "@/components/ui/Button";
import { DatasetStatData } from "@/sampleData/Dataset/DatasetStatData";
import { createDatasetColumns } from "@/components/tables/DatasetTableColumns/DatasetColumns";
import { getDataset, deleteDataset } from "../services/datasetService/datasetServices";
import { useEffect, useState, useMemo, useCallback } from "react";
import { Upload, RefreshCw, Database } from "lucide-react";
import { toast } from "sonner";

export default function Dataset() {
  const router = useRouter();
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const loadDatasets = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);

    try {
      const data = await getDataset();
      setDatasets(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load datasets:", err);
      toast.error("Failed to fetch datasets from server.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadDatasets();
  }, [loadDatasets]);

  const handleDelete = async (dataset) => {
    if (
      !window.confirm(
        `Are you sure you want to delete dataset "${dataset.dataset_name}"? This action cannot be undone.`
      )
    ) {
      return;
    }

    try {
      setDeletingId(dataset.id);
      await deleteDataset(dataset.id);
      toast.success(`Dataset "${dataset.dataset_name}" deleted successfully.`);
      setDatasets((prev) => prev.filter((d) => d.id !== dataset.id));
    } catch (err) {
      console.error("Failed to delete dataset:", err);
      const detail = err?.response?.data?.detail || "Failed to delete dataset.";
      toast.error(typeof detail === "string" ? detail : "Delete failed.");
    } finally {
      setDeletingId(null);
    }
  };

  const columns = useMemo(
    () => createDatasetColumns({ onDelete: handleDelete }),
    []
  );

  // Use the stat card configuration created in DatasetStatData and update only values
  const statCards = useMemo(() => {
    const total = datasets.length;
    let validated = 0;
    let processing = 0;
    let failed = 0;

    datasets.forEach((d) => {
      const versions = d.versions || [];
      const latest = versions[versions.length - 1];
      const status = (latest?.status || d.status || "").toLowerCase();

      if (status === "validated" || status === "processed" || status === "uploaded") {
        validated++;
      } else if (status === "processing") {
        processing++;
      } else if (status === "failed") {
        failed++;
      } else {
        validated++;
      }
    });

    return DatasetStatData.map((card) => {
      let value = card.value;
      if (card.statName === "Total Datasets") {
        value = total;
      } else if (card.statName === "Validated") {
        value = validated;
      } else if (card.statName === "Processing") {
        value = processing;
      } else if (card.statName === "Failed") {
        value = failed;
      }

      return {
        ...card,
        value,
      };
    });
  }, [datasets]);

  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px]">
      {/* Header row containing title and actions section */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="px-5">
          <h1 className="text-[#002B55] font-bold text-3xl">
            Dataset Inventory
          </h1>
          <p className="pt-1 lg:pt-3 text-gray-600 text-sm">
            Manage, review, and ingest training and evaluation datasets.
          </p>
        </div>
        <div className="flex items-center gap-3 px-5 lg:px-0">
          <button
            type="button"
            onClick={() => loadDatasets(true)}
            disabled={refreshing || loading}
            title="Refresh datasets"
            className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-slate-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw
              size={16}
              className={refreshing ? "animate-spin text-blue-600" : ""}
            />
            <span>Refresh</span>
          </button>

          <Button
            onClick={() => router.push("/dataset/uploadDataset")}
            icon={Upload}
            variant="primary"
          >
            Upload Dataset
          </Button>
        </div>
      </div>

      {/* stat cards for displaying all info about dataset inventory */}
      <div className="my-6 px-5">
        <StatCard statData={statCards} />
      </div>

      {/* dataset table section */}
      <div className="min-w-0 my-6 px-5">
        {loading ? (
          <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-gray-200">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mb-3" />
            <p className="text-gray-600 text-sm font-medium">Loading datasets from server...</p>
          </div>
        ) : datasets.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-dashed border-gray-300 text-center">
            <div className="h-12 w-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
              <Database size={24} />
            </div>
            <h3 className="text-base font-semibold text-gray-900">No datasets uploaded yet</h3>
            <p className="mt-1 text-sm text-gray-500 max-w-sm">
              Ingest your first CSV, XLSX, JSON, or JSONL dataset to start training or processing.
            </p>
            <div className="mt-6">
              <Button
                onClick={() => router.push("/dataset/uploadDataset")}
                icon={Upload}
                variant="primary"
              >
                Upload First Dataset
              </Button>
            </div>
          </div>
        ) : (
          <ModelsTable
            title="Recent Datasets"
            columns={columns}
            data={datasets}
            pageSize={5}
          />
        )}
      </div>
    </main>
  );
}

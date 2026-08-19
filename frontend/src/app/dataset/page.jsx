//=======================================================================================//
/*
The dataset page that shows the all information aout the datasets
*/
//=======================================================================================//
//=======================================================================================//
/*
The main dashboard that shows the all information aout the deployed models
*/
//=======================================================================================//
"use client";
import { useRouter } from "next/navigation";
import StatCard from "@/components/ui/StatCard";
import ModelsTable from "@/components/tables/ModelsTable";
import Button from "@/components/ui/Button";
import { DatasetStatData } from "@/sampleData/Dataset/DatasetStatData";
import { DatasetColumns } from "@/components/tables/DatasetTableColumns/DatasetColumns";
import { getDataset } from "../services/datasetServices";
import { useEffect, useState } from "react";
import { Upload } from "lucide-react";
import { toast } from "sonner";

export default function Dataset() {
  const router = useRouter();
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDatasets = async () => {
      try {
        const data = await getDataset();
        setDatasets(data);
      } catch {
        toast.error("Failed to upload data");
      } finally {
        setLoading(false);
      }
    };

    loadDatasets();
  }, []);

  return (
    <>
      <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px]">
        {/* Header row containing title and actions section */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="px-5">
            <h1 className="text-[#002B55] font-bold text-3xl">
              Dataset Inventory
            </h1>
            <p className="pt-1 lg:pt-3 text-gray-600">
              Manage and monitor your training and evaluation datasets.
            </p>
          </div>
          <div className="flex items-center gap-2 px-5 lg:px-0">
            <Button
              onClick={() => router.push("/dataset/uploadDataset")}
              icon={Upload}
              variant="primary"
            >
              Upload Dataset
            </Button>
          </div>
        </div>

        {/* stat cards for displaying all info about trained model section */}
        <div className="my-6 px-5">
          <StatCard statData={DatasetStatData} />
        </div>

        {/* model table section will show the all the information relates to the registered models  */}
        <div className="min-w-0 my-6 px-5">
          {loading ? (
            <div>Loading datasets...</div>
          ) : datasets.length === 0 ? (
            <div>No datasets found.</div>
          ) : (
            <ModelsTable
              title="Recent Datasets"
              columns={DatasetColumns}
              data={datasets}
              pageSize={5}
            />
          )}
        </div>
      </main>
    </>
  );
}

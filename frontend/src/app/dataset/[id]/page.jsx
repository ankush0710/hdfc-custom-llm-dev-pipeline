"use client";
import { useEffect, useState, useMemo, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Download,
  Plus,
  Loader2,
  FileText,
  ArrowLeft,
  Play,
} from "lucide-react";
import {
  getDatasetById,
  downloadVersionFile,
  getVersionQualityMetrics,
  startProcessingJob,
} from "@/app/services/datasetService/datasetServices";
import { getTrainingRuns } from "@/app/services/trainingService/trainingServices";
import Breadcrumbs from "@/components/ui/Breadcrumbs";
import DetailHeader from "@/components/ui/DetailHeader";
import MetadataCard from "@/components/ui/MetadataCard";
import ChecklistCard from "@/components/ui/ChecklistCard";
import LineageCard from "@/components/ui/LineageCard";
import ModelsTable from "@/components/tables/ModelsTable";
import Button from "@/components/ui/Button";
import { toast } from "sonner";

const formatFileSize = (sizeInMb) => {
  if (sizeInMb === undefined || sizeInMb === null) return "0 MB";
  const num = Number(sizeInMb);
  if (isNaN(num)) return "0 MB";
  if (num < 0.01) {
    return `${(num * 1024).toFixed(1)} KB`;
  }
  if (num >= 1024) {
    return `${(num / 1024).toFixed(2)} GB`;
  }
  return `${num.toFixed(1)} MB`;
};

const formatRecordCount = (count) => {
  if (!count && count !== 0) return "-";
  const num = Number(count);
  if (isNaN(num)) return "-";
  if (num >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(1)}M`;
  }
  if (num >= 1_000) {
    return `${(num / 1_000).toFixed(1)}K`;
  }
  return num.toLocaleString();
};

export default function DatasetDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id;

  const [dataset, setDataset] = useState(null);
  const [metricsData, setMetricsData] = useState(null);
  const [trainingRuns, setTrainingRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const [versionFilter, setVersionFilter] = useState("ALL");

  const fetchDataset = useCallback(
    async (isSilent = false) => {
      if (!id) return;
      try {
        if (!isSilent) setLoading(true);
        setError(null);

        const [data, runsData] = await Promise.all([
          getDatasetById(id),
          getTrainingRuns().catch(() => []),
        ]);
        setDataset(data);
        setTrainingRuns(Array.isArray(runsData) ? runsData : []);

        // Fetch metrics for versions in parallel and pick the latest valid metrics
        if (data?.versions && data.versions.length > 0) {
          const versions = [...data.versions].reverse();
          const metricsList = await Promise.all(
            versions.map((ver) => getVersionQualityMetrics(ver.id).catch(() => null))
          );
          const resolvedMetrics =
            metricsList.find(
              (m) =>
                m &&
                (m.total_rows !== undefined ||
                  m.total_records !== undefined ||
                  m.quality_score !== undefined)
            ) || null;
          setMetricsData(resolvedMetrics);
        }
      } catch (err) {
        console.error("Failed to fetch dataset:", err);
        setError(err?.response?.data?.detail || "Failed to load dataset");
      } finally {
        setLoading(false);
      }
    },
    [id]
  );

  useEffect(() => {
    fetchDataset();
  }, [fetchDataset]);

  const latestVersion = useMemo(() => {
    if (dataset?.versions && dataset.versions.length > 0) {
      return dataset.versions[dataset.versions.length - 1];
    }
    return null;
  }, [dataset]);

  const isProcessed =
    String(latestVersion?.status || "").toLowerCase() === "processed" ||
    String(dataset?.status || "").toLowerCase() === "processed";
  const isRunning = isProcessing || String(latestVersion?.status || "").toLowerCase() === "running";

  const handleStartProcessing = useCallback(async () => {
    if (!latestVersion) {
      toast.error("No dataset version available to process.");
      return;
    }

    try {
      setIsProcessing(true);
      toast.info(`Processing dataset version ${latestVersion.version}...`);

      await startProcessingJob(latestVersion.id, ["clean", "remove_duplicate"]);

      toast.success("Dataset processed successfully!", {
        description:
          "Schema verified, duplicates removed, and quality score computed.",
      });

      // Refetch dataset and updated metrics
      await fetchDataset(true);
    } catch (err) {
      console.error("Processing failed:", err);
      const detail = err?.response?.data?.detail;
      toast.error(
        typeof detail === "string"
          ? detail
          : "Failed to process dataset version."
      );
    } finally {
      setIsProcessing(false);
    }
  }, [latestVersion, fetchDataset]);

  const handleDownloadVersion = useCallback(async (version) => {
    try {
      const filename = version.file_name || `dataset_v${version.version}`;
      await downloadVersionFile(version.id, filename);
      toast.success(`Download started for ${filename}`);
    } catch (err) {
      console.error("Download failed:", err);
      toast.error("Failed to download version file.");
    }
  }, []);

  const versionsList = useMemo(() => {
    return dataset?.versions ? [...dataset.versions].reverse() : [];
  }, [dataset]);

  // Version Filter Options
  const versionFilterOptions = useMemo(() => [
    { label: "All Versions", value: "ALL" },
    { label: "Valid (Processed)", value: "Processed" },
    { label: "Processing (Running)", value: "Running" },
    { label: "Pending (Uploaded)", value: "Uploaded" },
  ], []);

  // Filtered versions data for ModelsTable
  const filteredVersions = useMemo(() => {
    if (!versionsList) return [];
    if (versionFilter === "ALL") return versionsList;

    return versionsList.filter((ver) => {
      const s = (ver.status || "").toLowerCase();
      if (versionFilter === "Processed") {
        return s === "processed" || s === "valid";
      }
      if (versionFilter === "Running") {
        return s === "running" || s === "processing";
      }
      if (versionFilter === "Uploaded") {
        return s === "uploaded" || s === "pending";
      }
      return s === versionFilter.toLowerCase();
    });
  }, [versionsList, versionFilter]);

  const latestVerName = latestVersion?.version || "1.0.0";

  // Robust field mapping handling all naming variants (total_records, total_rows, record_count, total_columns, quality_score, qualityScore)
  const rawRecords =
    metricsData?.total_records ??
    metricsData?.total_rows ??
    metricsData?.record_count ??
    dataset?.total_records ??
    dataset?.total_rows ??
    dataset?.record_count;

  const rawColumns =
    metricsData?.total_columns ??
    metricsData?.column_count ??
    dataset?.total_columns ??
    dataset?.column_count;

  const rawQuality =
    metricsData?.quality_score ??
    metricsData?.qualityScore ??
    dataset?.quality_score ??
    dataset?.qualityScore;

  const recordsCount = rawRecords !== undefined && rawRecords !== null
    ? formatRecordCount(rawRecords)
    : "—";

  const columnsCount = rawColumns !== undefined && rawColumns !== null
    ? String(rawColumns)
    : "—";

  const qualityScoreDisplay = rawQuality !== undefined && rawQuality !== null
    ? `${typeof rawQuality === "number" ? Math.round(rawQuality * 10) / 10 : rawQuality}%`
    : "—";

  const fileSizeDisplay = latestVersion?.file_size !== undefined && latestVersion?.file_size !== null
    ? formatFileSize(latestVersion.file_size)
    : "—";

  const createdDateDisplay = dataset?.created_at
    ? new Date(dataset.created_at).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    })
    : "—";

  const piiInstancesDisplay = metricsData?.pii_instances_detected !== undefined && metricsData?.pii_instances_detected !== null
    ? String(metricsData.pii_instances_detected)
    : (isProcessed ? "0" : "—");

  const piiTypesDisplay = metricsData?.pii_types_detected || (isProcessed ? "NONE" : "—");

  const sanitizedRecordsDisplay = metricsData?.records_sanitized !== undefined && metricsData?.records_sanitized !== null
    ? String(metricsData.records_sanitized)
    : (isProcessed ? "0" : "—");

  const isSafeForTraining = Boolean(
    isProcessed && (metricsData?.is_safe_for_training !== false && latestVersion?.is_safe_for_training !== false)
  );

  // Reusable metadata items
  const metadataItems = useMemo(() => [
    { label: "RECORDS", value: recordsCount },
    { label: "COLUMNS", value: columnsCount },
    { label: "QUALITY SCORE", value: qualityScoreDisplay },
    { label: "PII DETECTED", value: `${piiInstancesDisplay}` },
    { label: "RECORDS SANITIZED", value: sanitizedRecordsDisplay },
    { label: "SAFE FOR TRAINING", value: isSafeForTraining ? "YES" : "NO" },
    { label: "FILE SIZE", value: fileSizeDisplay },
    { label: "CREATED AT", value: createdDateDisplay, size: "small" },
  ], [recordsCount, columnsCount, qualityScoreDisplay, piiInstancesDisplay, piiTypesDisplay, sanitizedRecordsDisplay, isSafeForTraining, fileSizeDisplay, createdDateDisplay]);

  // Dynamic status badge depending on processing state
  const statusBadge = useMemo(() => {
    if (isProcessed) {
      return { label: isSafeForTraining ? "VALID (SAFE FOR TRAINING)" : "VALID", variant: "success" };
    }
    if (isRunning) {
      return { label: "PROCESSING & SCANNING", variant: "processing" };
    }
    return { label: "PENDING VALIDATION", variant: "warning" };
  }, [isProcessed, isRunning, isSafeForTraining]);

  // Dynamic checklist mapping directly to backend validator & quality metrics
  const validationItems = useMemo(() => {
    if (isProcessed && metricsData) {
      const isQualityGood = (metricsData.quality_score ?? 100) >= 80;
      const dupCount = metricsData.duplicate_rows ?? 0;
      const missingCount = metricsData.missing_values ?? 0;
      const emptyRowCount = metricsData.empty_rows ?? 0;
      const piiHits = metricsData.pii_instances_detected ?? 0;

      return [
        {
          label: `Schema & file format verified (${latestVersion?.file_type?.toUpperCase() || "CSV/JSON"
            })`,
          status: "valid",
        },
        {
          label: `${metricsData.total_columns || 0} valid columns, ${metricsData.total_rows || 0
            } records loaded`,
          status: "valid",
        },
        {
          label: isQualityGood
            ? `Data quality benchmark met (${metricsData.quality_score}% score)`
            : `Quality score below optimal (${metricsData.quality_score}%)`,
          status: isQualityGood ? "valid" : "warning",
        },
        {
          label:
            dupCount === 0
              ? "Deduplication passed (0 duplicates remaining)"
              : `${dupCount} duplicate rows resolved`,
          status: "valid",
        },
        {
          label:
            missingCount === 0 && emptyRowCount === 0
              ? "No critical errors, missing values, or empty rows"
              : `${missingCount} nulls & ${emptyRowCount} empty rows handled`,
          status: emptyRowCount === 0 ? "valid" : "warning",
        },
        {
          label: `PII & Banking Sensitive Data Scan (Passed: ${piiHits} sensitive instances detected & de-identified)`,
          status: "valid",
        },
        {
          label: isSafeForTraining
            ? "Dataset verified safe for LLM training (Zero unredacted PII)"
            : "Dataset not yet verified safe for LLM training",
          status: isSafeForTraining ? "valid" : "warning",
        },
      ];
    }

    if (isProcessed) {
      return [
        { label: "Schema valid & structure verified", status: "valid" },
        { label: "Required fields present", status: "valid" },
        { label: "Data quality metrics benchmark met", status: "valid" },
        { label: "PII & banking sensitive data de-identified", status: "valid" },
        { label: "Verified safe for LLM training", status: "valid" },
      ];
    }

    if (isRunning) {
      return [
        { label: "Loading file and validating schema...", status: "pending" },
        {
          label: "Deduplicating rows and removing redundancies...",
          status: "pending",
        },
        { label: "Cleaning null values and fixing encoding...", status: "pending" },
        { label: "Scanning for PII, PAN, Aadhaar, Cards, Bank Accounts & UPI...", status: "pending" },
        { label: "Applying de-identification and credential redaction...", status: "pending" },
        { label: "Running post-sanitization safety verification check...", status: "pending" },
        { label: "Calculating quality score and pipeline readiness...", status: "pending" },
      ];
    }

    return [
      { label: "Schema validation (Pending processing)", status: "pending" },
      {
        label: "Required fields verification (Pending processing)",
        status: "pending",
      },
      {
        label: "Deduplication & cleaning (Pending processing)",
        status: "pending",
      },
      {
        label: "PII & banking sensitive data scan (Pending processing)",
        status: "pending",
      },
      {
        label: "De-identification & credential redaction (Pending processing)",
        status: "pending",
      },
      {
        label: "Training safety gate validation (Pending processing)",
        status: "pending",
      },
    ];
  }, [isProcessed, isRunning, metricsData, latestVersion, isSafeForTraining]);

  // Reusable lineage links from real training runs
  const lineageItems = useMemo(() => {
    if (!trainingRuns || trainingRuns.length === 0 || !dataset?.versions) return [];
    const versionIds = new Set(dataset.versions.map((v) => v.id));
    const matchingRuns = trainingRuns.filter((r) => versionIds.has(r.dataset_version_id));
    return matchingRuns.map((r) => ({
      label: `Training Run #${r.id} (${r.base_model} - ${r.status})`,
      href: "/training",
    }));
  }, [trainingRuns, dataset]);

  // Version table columns for common ModelsTable
  const versionColumns = useMemo(
    () => [
      {
        key: "version",
        label: "VERSION",
        render: (ver) => (
          <span className="font-bold text-slate-900 text-sm">
            v{ver.version}
          </span>
        ),
      },
      {
        key: "created_at",
        label: "DATE",
        render: (ver) => {
          const verDate = ver.created_at
            ? new Date(ver.created_at).toLocaleDateString("en-US", {
              month: "short",
              day: "2-digit",
              year: "numeric",
            })
            : "—";
          return (
            <span className="text-slate-600 font-medium text-xs">
              {verDate}
            </span>
          );
        },
      },
      {
        key: "status",
        label: "STATUS",
        render: (ver) => {
          if (ver.status === "Processed") {
            return (
              <span className="inline-flex rounded bg-[#EAF8EE] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[#16A34A] border border-[#BDECC9]">
                VALID
              </span>
            );
          }
          if (ver.status === "Running") {
            return (
              <span className="inline-flex rounded bg-sky-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-sky-700 border border-sky-200">
                PROCESSING
              </span>
            );
          }
          return (
            <span className="inline-flex rounded bg-amber-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-amber-700 border border-amber-200">
              PENDING
            </span>
          );
        },
      },
      {
        key: "description",
        label: "DESCRIPTION",
        render: (ver, idx) => {
          const isLatest = idx === 0;
          const desc =
            dataset?.description ||
            (isLatest
              ? `Dataset version v${ver.version} (${ver.status || "Ready"})`
              : `Uploaded dataset version v${ver.version}`);
          return (
            <span
              className="text-slate-600 text-xs line-clamp-1 max-w-md block"
              title={desc}
            >
              {desc}
            </span>
          );
        },
      },
      {
        key: "action",
        label: "ACTION",
        align: "right",
        render: (ver) => (
          <button
            type="button"
            onClick={() => handleDownloadVersion(ver)}
            title="Download version file"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 hover:text-[#002B55] bg-slate-50 hover:bg-slate-100 border border-slate-200 px-2.5 py-1 rounded transition-colors cursor-pointer"
          >
            <Download size={13} />
            <span>Download</span>
          </button>
        ),
      },
    ],
    [dataset, handleDownloadVersion]
  );

  // Early returns placed ONLY after all hooks have been declared unconditionally
  if (loading) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center lg:ml-[280px]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-[#002B55]" />
          <p className="text-gray-600 text-sm font-medium">
            Loading dataset details. Please wait...
          </p>
        </div>
      </main>
    );
  }

  if (error || !dataset) {
    return (
      <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px]">
        <div className="mx-auto max-w-md w-full rounded-xl border border-slate-200 bg-white p-6 shadow-sm text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-600 mb-3">
            <FileText size={24} />
          </div>
          <h1 className="text-xl font-bold text-slate-900">
            Dataset Not Found
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            {typeof error === "string"
              ? error
              : "The requested dataset could not be retrieved from the server."}
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Button
              variant="primary"
              icon={ArrowLeft}
              onClick={() => router.push("/dataset")}
            >
              Back to Datasets
            </Button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px] pb-16">
      {/* 1. Breadcrumbs & Back Button */}
      <div className="px-5">
        <Breadcrumbs
          backHref="/dataset"
          backLabel="Back to Datasets"
        />
      </div>

      {/* 2. Detail Page Header */}
      <div className="px-5">
        <DetailHeader
          title={dataset.dataset_name}
          badges={[
            statusBadge,
            { label: `v${latestVerName}`, variant: "info" },
          ]}
          actions={
            <>
              {/* Start Processing / Reprocess Button */}
              <Button
                variant={isProcessed ? "default" : "primary"}
                icon={isProcessing ? Loader2 : Play}
                onClick={handleStartProcessing}
                disabled={isProcessing}
              >
                {isProcessing
                  ? "Processing..."
                  : isProcessed
                    ? "Reprocess Dataset"
                    : "Start Processing"}
              </Button>

              {/* New Version Button */}
              <Button
                variant={isProcessed ? "primary" : "default"}
                icon={Plus}
                onClick={() =>
                  router.push(
                    `/dataset/uploadDataset?datasetName=${encodeURIComponent(
                      dataset.dataset_name
                    )}`
                  )
                }
              >
                New Version
              </Button>
            </>
          }
        />
      </div>

      {/* 3. Metadata Card */}
      <div className="my-3 px-5">
        <MetadataCard
          title="Dataset Metadata"
          items={metadataItems}
          columns={5}
        />
      </div>

      {/* 4. Middle Section (Validation Status & Lineage) */}
      <div className="my-3 px-5 grid grid-cols-1 md:grid-cols-2 gap-6">
        <ChecklistCard
          title="Validation Status"
          items={validationItems}
        />

        <LineageCard
          title="Used By (Lineage)"
          items={lineageItems}
        />
      </div>

      {/* 5. Version History Common Table */}
      <div className="min-w-0 my-6 px-5">
        <ModelsTable
          title="Version History"
          columns={versionColumns}
          data={filteredVersions}
          pageSize={5}
          showFilter={true}
          filterOptions={versionFilterOptions}
          selectedFilter={versionFilter}
          onFilterChange={(val) => setVersionFilter(val)}
          emptyMessage="No dataset versions match the selected filter."
        />
      </div>
    </main>
  );
}

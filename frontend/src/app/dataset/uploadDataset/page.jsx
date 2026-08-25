//=======================================================================================//
/*
The dataset page that allows uploading and ingesting new datasets
*/
//=======================================================================================//

"use client";
import Button from "@/components/ui/Button";
import FormField from "@/components/form/FormField";
import SelectField from "@/components/form/SelectField";
import TextAreaField from "@/components/form/TextAreaField";
import FileUpload from "@/components/form/FileUpload";
import Breadcrumbs from "@/components/ui/Breadcrumbs";
import { useState, useEffect, Suspense } from "react";
import { Upload, Loader2 } from "lucide-react";
import { uploadDataset } from "../../services/datasetService/datasetServices";
import { toast } from "sonner";
import { useRouter, useSearchParams } from "next/navigation";

const categoryOptions = [
  {
    value: "fine-tuning",
    label: "Fine-tuning",
  },
  {
    value: "evaluation",
    label: "Evaluation",
  },
  {
    value: "validation",
    label: "Validation",
  },
  {
    value: "faq_data",
    label: "FAQ / Q&A",
  },
  {
    value: "banking",
    label: "Banking Domain",
  },
  {
    value: "rag_corpus",
    label: "RAG Knowledge Corpus",
  },
];

function UploadDatasetContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialName = searchParams?.get("datasetName") || "";

  const [formData, setFormData] = useState({
    datasetName: initialName,
    category: "fine-tuning",
    version: "1.0.0",
    source: "",
    description: "",
    file: null,
  });

  useEffect(() => {
    if (initialName) {
      setFormData((prev) => ({
        ...prev,
        datasetName: initialName,
      }));
    }
  }, [initialName]);

  const [isUploading, setIsUploading] = useState(false);

  const getUploadErrorMessage = (error) => {
    const detail = error?.response?.data?.detail;

    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          const location = item.loc
            ?.filter((part) => part !== "body")
            .join(".");
          return location ? `${location}: ${item.msg}` : item.msg;
        })
        .filter(Boolean)
        .join("; ");
    }

    if (typeof detail === "string") return detail;
    return (
      error?.message ||
      "Failed to upload dataset. Please check the form and try again."
    );
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleFileSelect = (selectedFile) => {
    setFormData((prev) => ({
      ...prev,
      file: selectedFile,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const requiredFields = [
      ["datasetName", "dataset name"],
      ["category", "category"],
      ["version", "version"],
      ["source", "source"],
    ];

    const missingField = requiredFields.find(
      ([field]) => !String(formData[field] ?? "").trim()
    );

    if (missingField) {
      toast.error(`Please enter the ${missingField[1]}.`);
      return;
    }

    if (!formData.file) {
      toast.error("Please select a dataset file to upload.");
      return;
    }

    try {
      setIsUploading(true);
      const uploadFormData = new FormData();
      uploadFormData.append("datasetName", formData.datasetName.trim());
      uploadFormData.append("category", formData.category.trim());
      uploadFormData.append("version", formData.version.trim());
      uploadFormData.append("source", formData.source.trim());
      uploadFormData.append("description", formData.description?.trim() || "");
      uploadFormData.append("file", formData.file);

      await uploadDataset(uploadFormData);

      toast.success("Dataset uploaded successfully!", {
        description: `"${formData.datasetName}" version ${formData.version} has been registered and added to Recent Datasets.`,
      });

      router.push("/dataset");
    } catch (err) {
      console.error("Upload failed:", err);
      toast.error(getUploadErrorMessage(err));
    } finally {
      setIsUploading(false);
    }
  };

  const handleCancel = () => {
    router.push("/dataset");
  };

  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px] pb-16">
      {/* 1. Back to Datasets Button - on the left */}
      <div className="px-5">
        <Breadcrumbs
          backHref="/dataset"
          backLabel="Back to Datasets"
        />
      </div>

      {/* 2. Page Header - on the left, same as dataset details page */}
      <div className="px-5 mb-6">
        <h1 className="text-2xl lg:text-3xl font-bold text-[#002B5C]">
          Upload Dataset
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Configure metadata and ingest new training, evaluation, or fine-tuning
          data into the FastAPI pipeline.
        </p>
      </div>

      {/* 3. Form Card - centered in the middle */}
      <div className="px-5 flex justify-center">
        <form
          onSubmit={handleSubmit}
          className="w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
        >
          {/* Card Header */}
          <div className="border-b border-slate-200 bg-[#FAFBFE] px-6 py-4">
            <h2 className="text-base font-semibold text-[#002B5C]">
              Dataset Configuration & Ingestion
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Supported formats: CSV, XLSX, JSONL, JSON
            </p>
          </div>

          {/* Form Content */}
          <div className="space-y-6 p-6">
            {/* Name + Category */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <FormField
                label="Dataset Name"
                name="datasetName"
                placeholder="e.g. HDFC Customer Support FAQ"
                value={formData.datasetName}
                onChange={handleChange}
                required
              />

              <SelectField
                label="Category"
                name="category"
                value={formData.category}
                onChange={handleChange}
                options={categoryOptions}
                required
              />

              <FormField
                label="Dataset Version"
                name="version"
                placeholder="e.g. 1.0.0"
                value={formData.version}
                onChange={handleChange}
                required
              />

              <FormField
                label="Dataset Source"
                name="source"
                placeholder="e.g. Core Banking Logs, CRM Export"
                value={formData.source}
                onChange={handleChange}
                required
              />
            </div>

            {/* Description */}
            <TextAreaField
              label="Description (Optional)"
              name="description"
              placeholder="Provide context regarding data source, schema structure, and intended downstream use case..."
              value={formData.description}
              onChange={handleChange}
              rows={3}
            />

            {/* File Upload */}
            <FileUpload onFileSelect={handleFileSelect} />
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 border-t border-slate-200 bg-[#FAFBFE] px-6 py-4">
            <Button
              type="button"
              variant="default"
              onClick={handleCancel}
              disabled={isUploading}
            >
              Cancel
            </Button>

            <Button
              type="submit"
              icon={isUploading ? Loader2 : Upload}
              variant="primary"
              disabled={isUploading}
            >
              {isUploading ? "Uploading Dataset..." : "Upload Dataset"}
            </Button>
          </div>
        </form>
      </div>
    </main>
  );
}

export default function UploadDataset() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center lg:ml-[280px]">
          <Loader2 className="h-8 w-8 animate-spin text-[#002B55]" />
        </div>
      }
    >
      <UploadDatasetContent />
    </Suspense>
  );
}

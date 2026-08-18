"use client";

import { CheckCircle2, Download, ShieldCheck } from "lucide-react";

import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import MetadataGrid from "@/components/metaGrid/MetadataGrid";
import QualityMetric from "@/components/qualityMetrics/QualityMetrics";

const dataset = {
  name: "Q3_Financial_Transcripts_Cleaned",
  status: "Validated",

  description:
    "This dataset contains thoroughly cleaned and anonymized financial earnings call transcripts from Q3 2023. It has been specifically curated for fine-tuning language models on financial sentiment analysis and summarization tasks. All Personal Identifiable Information (PII) has been scrubbed via the automated compliance pipeline.",

  metadata: [
    {
      label: "Total Records",
      value: "1,240,500",
    },
    {
      label: "Format",
      value: "JSONL",
    },
    {
      label: "Version",
      value: "v1.2.0",
      badge: true,
    },
    {
      label: "Created Date",
      value: "Oct 24, 2023",
    },
    {
      label: "Source",
      value: "Internal CRM",
    },
    {
      label: "Category",
      value: "Fine-tuning",
    },
  ],

  quality: [
    {
      label: "Completeness",
      value: 96,
    },
    {
      label: "Accuracy",
      value: 94,
    },
    {
      label: "Consistency",
      value: 91,
    },
    {
      label: "Validity",
      value: 98,
      variant: "success",
    },
  ],
};

export default function DatasetDetailsPage() {
  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px]">
      {/* Header row containing title and actions section */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="px-5">
          <div className="flex flex-col lg:flex-row lg:items-center gap-3">
            <h1 className="text-xl text-[#002B55] font-bold lg:text-3xl">
              {dataset.name}
            </h1>
            <Badge variant="success">
              <CheckCircle2 size={13} className="mr-1" />
              {dataset.status}
            </Badge>
          </div>
          <p className="pt-1 lg:pt-3 text-gray-600">
            Manage and review dataset metadata and quality metrics before
            training.
          </p>
        </div>
        <div className="flex items-center gap-2 px-5 lg:px-0">
          <Button icon={Download}>Download</Button>
        </div>
      </div>
      {/* Main Grid */}
      <div className="my-6 grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_390px]">
        {/* Left Column */}
        <div className="space-y-5">
          {/* Description */}
          <div className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
            <h2 className="mb-5 text-base font-semibold text-slate-900">
              Description
            </h2>

            <p className="text-sm leading-6 text-slate-600">
              {dataset.description}
            </p>
          </div>

          {/* Metadata */}
          <div className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
            <h2 className="mb-5 text-base font-semibold text-slate-900">
              Key Metadata
            </h2>

            <MetadataGrid columns={3} items={dataset.metadata} />
          </div>
        </div>

        {/* Right Column */}
        <div className="h-fit rounded-lg border border-slate-300 bg-white p-5 shadow-sm">
          <div className="mb-6 flex items-center gap-2">
            <div className="text-red-500">
              <CheckCircle2 size={18} />
            </div>

            <h2 className="text-base font-semibold text-slate-900">
              Quality Metrics
            </h2>
          </div>

          <QualityMetric metrics={dataset.quality} />

          {/* PII Scan */}
          <div className="mt-6 rounded-lg border border-green-200 bg-green-50 p-4">
            <div className="flex items-start gap-3">
              <ShieldCheck
                size={19}
                className="mt-0.5 shrink-0 text-green-600"
              />

              <div>
                <p className="text-sm font-semibold text-green-800">
                  PII Scan Clean
                </p>

                <p className="mt-1 text-xs leading-5 text-green-700">
                  0 instances detected. Dataset is safe for unclassified
                  environments.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

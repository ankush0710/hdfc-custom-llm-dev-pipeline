"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Database,
  BrainCircuit,
  ChartColumn,
  Rocket,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  Layers,
  ArrowLeft,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Breadcrumbs from "@/components/ui/Breadcrumbs";

export default function PipelinePage() {
  const router = useRouter();

  const stages = [
    {
      step: "01",
      title: "Dataset Ingestion & Sanitization",
      description:
        "Upload raw CSV/JSON banking datasets. Automatically detects and redacts customer PII (PAN, Aadhaar, Cards, UPI, Account Numbers) before any training occurs.",
      actionLabel: "Upload Dataset",
      href: "/dataset/uploadDataset",
      icon: Database,
      badge: "Stage 1",
      status: "Ready",
    },
    {
      step: "02",
      title: "LoRA Fine-Tuning Execution",
      description:
        "Train parameter-efficient LoRA adapters on domain data using Qwen or SmolLM base models. Streams live loss and step telemetry to PostgreSQL.",
      actionLabel: "Configure Training",
      href: "/training",
      icon: BrainCircuit,
      badge: "Stage 2",
      status: "Ready",
    },
    {
      step: "03",
      title: "Benchmark & Safety Quality Gate",
      description:
        "Run evaluation benchmark scoring intent JSON structure, factual accuracy, policy flags, and safety compliance before deployment approval.",
      actionLabel: "View Evaluations",
      href: "/evaluation",
      icon: ChartColumn,
      badge: "Stage 3",
      status: "Ready",
    },
    {
      step: "04",
      title: "Model Registry & Deployment",
      description:
        "Publish approved models to the enterprise model registry and activate real-time low-latency inference endpoints with latency tracking.",
      actionLabel: "Deploy Model",
      href: "/deployment",
      icon: Rocket,
      badge: "Stage 4",
      status: "Ready",
    },
  ];

  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px] pb-16">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 px-5 mb-6">
        <div>
          <h1 className="text-[#002B55] font-bold text-3xl">
            Custom LLM Development Pipeline
          </h1>
          <p className="pt-1 lg:pt-2 text-gray-600 text-sm">
            End-to-end enterprise lifecycle: ingest data, fine-tune models, evaluate safety gates, and deploy serving endpoints.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            icon={ArrowLeft}
            onClick={() => router.push("/")}
          >
            Dashboard
          </Button>
        </div>
      </div>

      {/* Pipeline Lifecycle Stages Grid */}
      <div className="px-5 grid grid-cols-1 md:grid-cols-2 gap-6">
        {stages.map((stg) => {
          const Icon = stg.icon;
          return (
            <div
              key={stg.step}
              className="flex flex-col justify-between bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md hover:border-[#002B55] transition-all group"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-mono font-bold text-slate-400">
                    STEP {stg.step}
                  </span>
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                    {stg.badge}
                  </span>
                </div>

                <div className="flex items-center gap-3 mb-3">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-700 group-hover:bg-[#002B55] group-hover:text-white transition-colors">
                    <Icon size={22} />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900 group-hover:text-[#002B55] transition-colors">
                      {stg.title}
                    </h2>
                    <span className="text-[11px] text-emerald-600 font-semibold flex items-center gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                      {stg.status}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed mb-6">
                  {stg.description}
                </p>
              </div>

              <div className="pt-4 border-t border-slate-100">
                <Button
                  variant="primary"
                  className="w-full justify-between"
                  onClick={() => router.push(stg.href)}
                >
                  <span>{stg.actionLabel}</span>
                  <ArrowRight size={16} />
                </Button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Governance Banner */}
      <div className="mx-5 mt-8 p-4 bg-white rounded-xl border border-slate-200 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center shrink-0">
            <ShieldCheck size={20} />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900">
              Enterprise Banking Guardrails Active
            </h3>
            <p className="text-[11px] text-slate-500">
              All pipeline workflows enforce automated PII scrubbing, LoRA adapter isolation, and threshold-based model quality gates.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}

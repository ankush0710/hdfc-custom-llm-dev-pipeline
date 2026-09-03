"use client";

import { useRouter } from "next/navigation";
import {
  X,
  Plus,
  Database,
  BrainCircuit,
  ChartColumn,
  Rocket,
  ArrowRight,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

export default function NewPipelineModal({ isOpen, onClose }) {
  const router = useRouter();

  if (!isOpen) return null;

  const pipelineSteps = [
    {
      step: "01",
      title: "Upload & Clean Dataset",
      description:
        "Ingest CSV or JSON banking dataset with automatic schema validation, deduplication, and PII de-identification.",
      icon: Database,
      badge: "Data Ingestion",
      href: "/dataset/uploadDataset",
      color: "from-blue-600 to-indigo-600",
      accentBg: "bg-blue-50 text-blue-700 border-blue-200",
    },
    {
      step: "02",
      title: "Start LoRA Fine-Tuning",
      description:
        "Train parameter-efficient LoRA adapters (Qwen / SmolLM) on validated enterprise banking datasets.",
      icon: BrainCircuit,
      badge: "Model Training",
      href: "/training",
      color: "from-purple-600 to-indigo-700",
      accentBg: "bg-purple-50 text-purple-700 border-purple-200",
    },
    {
      step: "03",
      title: "Run Benchmark Evaluation",
      description:
        "Execute automated quality gates scoring intent accuracy, policy alignment, and compliance benchmarks.",
      icon: ChartColumn,
      badge: "Quality Gate",
      href: "/evaluation",
      color: "from-emerald-600 to-teal-700",
      accentBg: "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
      step: "04",
      title: "Deploy Serving Endpoint",
      description:
        "Promote approved model weights to active inference servers with real-time token generation.",
      icon: Rocket,
      badge: "Production Serving",
      href: "/deployment",
      color: "from-amber-600 to-orange-600",
      accentBg: "bg-amber-50 text-amber-700 border-amber-200",
    },
  ];

  const handleSelect = (href) => {
    onClose();
    router.push(href);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-fadeIn">
      <div className="relative w-full max-w-3xl rounded-2xl bg-white shadow-2xl border border-slate-200 overflow-hidden">
        {/* Modal Header */}
        <div className="bg-[#002B55] px-6 py-5 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 text-white border border-white/20">
              <Sparkles size={20} />
            </div>
            <div>
              <h2 className="text-lg font-bold">Start New LLM Pipeline</h2>
              <p className="text-xs text-blue-200">
                Choose a workflow stage to begin or advance your enterprise custom LLM pipeline.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-blue-200 hover:text-white hover:bg-white/10 transition"
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body: Pipeline Stage Cards */}
        <div className="p-6 bg-slate-50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pipelineSteps.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.step}
                  type="button"
                  onClick={() => handleSelect(item.href)}
                  className="group relative flex flex-col justify-between p-5 bg-white rounded-xl border border-slate-200 hover:border-[#002B55] hover:shadow-md transition-all duration-200 text-left cursor-pointer"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-[11px] font-mono font-bold text-slate-400">
                        STAGE {item.step}
                      </span>
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${item.accentBg}`}
                      >
                        {item.badge}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 mb-2">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-700 group-hover:bg-[#002B55] group-hover:text-white transition-colors">
                        <Icon size={18} />
                      </div>
                      <h3 className="text-sm font-bold text-slate-900 group-hover:text-[#002B55] transition-colors">
                        {item.title}
                      </h3>
                    </div>

                    <p className="text-xs text-slate-500 leading-relaxed">
                      {item.description}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-blue-600 group-hover:text-[#002B55]">
                    <span>Launch Stage</span>
                    <ArrowRight
                      size={14}
                      className="group-hover:translate-x-1 transition-transform"
                    />
                  </div>
                </button>
              );
            })}
          </div>

          <div className="mt-5 flex items-center justify-between p-3.5 bg-blue-50/80 rounded-xl border border-blue-100 text-xs text-blue-900">
            <div className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-blue-700 shrink-0" />
              <span>
                Standard HDFC Governance Pipeline: Data Ingestion &rarr; LoRA Training &rarr; Benchmark Gate &rarr; Production Serving.
              </span>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="text-xs font-bold text-blue-700 hover:underline shrink-0"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

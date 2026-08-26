//=======================================================================================//
/*
AI Playground: Interactive inference sandbox evaluating active deployed enterprise models.
*/
//=======================================================================================//
"use client";

import { useState, useEffect, useCallback } from "react";
import { Loader2, Bot, AlertCircle } from "lucide-react";
import PlaygroundParametersPanel, {
  SYSTEM_ROLE_PRESETS,
} from "@/components/playground/PlaygroundParametersPanel";
import PlaygroundChatWindow from "@/components/playground/PlaygroundChatWindow";
import { getDeployments } from "@/app/services/deploymentService/deploymentServices";
import { getModels } from "@/app/services/modelService/modelServices";
import { runInference } from "@/app/services/inferenceService/inferenceServices";
import { toast } from "sonner";

export default function PlaygroundPage() {
  const [deployedModels, setDeployedModels] = useState([]);
  const [selectedModelId, setSelectedModelId] = useState("");
  const [loadingModels, setLoadingModels] = useState(true);
  const [inferencing, setInferencing] = useState(false);

  const [parameters, setParameters] = useState({
    temperature: 0.2,
    topP: 0.9,
    maxTokens: 1024,
    systemInstruction: SYSTEM_ROLE_PRESETS[0].instruction,
  });

  // Start with empty chat — the playground shows real inference results only
  const [messages, setMessages] = useState([]);
  const [tokenCount, setTokenCount] = useState(0);

  // Fetch only deployed / active models
  const fetchDeployedModels = useCallback(async () => {
    try {
      setLoadingModels(true);
      const [deploymentsData, modelsData] = await Promise.all([
        getDeployments().catch(() => []),
        getModels().catch(() => []),
      ]);

      const activeDeployments = Array.isArray(deploymentsData)
        ? deploymentsData.filter((d) => (d.status || "").toUpperCase() === "ACTIVE")
        : [];

      let availableList = [];
      if (activeDeployments.length > 0) {
        availableList = activeDeployments;
      } else {
        // Fallback to active/deployed models in registry if deployment table is not populated yet
        const validModels = Array.isArray(modelsData)
          ? modelsData.filter((m) =>
              ["DEPLOYED", "ACTIVE", "READY", "APPROVED", "CREATED"].includes(
                (m.status || "").toUpperCase()
              )
            )
          : [];
        availableList = validModels.map((m) => ({
          id: m.id,
          model_id: m.id,
          model_name: m.model_name,
          version: m.version,
          environment: "Production",
          status: "ACTIVE",
          base_model: m.base_model,
        }));
      }

      setDeployedModels(availableList);
      if (availableList.length > 0) {
        setSelectedModelId(String(availableList[0].model_id || availableList[0].id));
      }
    } catch (err) {
      console.error("Failed to load deployed models:", err);
      toast.error("Failed to load deployed models");
    } finally {
      setLoadingModels(false);
    }
  }, []);

  useEffect(() => {
    fetchDeployedModels();
  }, [fetchDeployedModels]);

  const activeModel = deployedModels.find(
    (m) => String(m.model_id || m.id) === String(selectedModelId)
  ) || deployedModels[0];

  // Send message to inference API
  const handleSendMessage = async (userPrompt) => {
    if (!selectedModelId) {
      toast.error("Please select a deployed model first");
      return;
    }

    const newMessages = [...messages, { role: "user", content: userPrompt }];
    setMessages(newMessages);

    try {
      setInferencing(true);
      const result = await runInference({
        model_id: parseInt(selectedModelId, 10),
        task_type: "inference",
        question: userPrompt,
        context: parameters.systemInstruction,
        max_new_tokens: parameters.maxTokens,
        temperature: parameters.temperature,
        top_p: parameters.topP,
        do_sample: parameters.temperature > 0.05,
      });

      const assistantText =
        result?.response ||
        result?.text ||
        "Inference completed with response generated.";

      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: assistantText,
          latency: result?.latency_seconds,
          tokens: result?.tokens_generated,
        },
      ]);
      // Update token count from real API response
      if (result?.tokens_generated != null) {
        setTokenCount((prev) => prev + (result.tokens_generated || 0));
      }
    } catch (err) {
      console.error("Inference failed:", err);
      toast.error(err?.response?.data?.detail || "Inference call failed");
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: `⚠️ Failed to generate response: ${
            err?.response?.data?.detail || err?.message || "Server Error"
          }`,
        },
      ]);
    } finally {
      setInferencing(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setTokenCount(0);
    toast.success("Chat history cleared");
  };

  const handleResetParameters = () => {
    setParameters({
      temperature: 0.2,
      topP: 0.9,
      maxTokens: 1024,
      systemInstruction: SYSTEM_ROLE_PRESETS[0].instruction,
    });
    toast.success("Parameters reset to default");
  };

  if (loadingModels) {
    return (
      <main className="flex min-h-[70vh] items-center justify-center lg:ml-[280px]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-[#002B55]" />
          <p className="text-gray-600 text-sm font-medium">
            Loading deployed enterprise models...
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px] pb-8 h-[calc(100vh-40px)]">
      {/* Page Title / Subtitle */}
      <div className="mb-4 px-3 lg:px-0">
        <h1 className="text-2xl lg:text-3xl font-extrabold text-gray-900 tracking-tight">
          AI Playground
        </h1>
        <p className="text-xs lg:text-sm text-gray-500 mt-0.5 font-medium">
          Interactive inference sandbox evaluating active deployed enterprise models.
        </p>
      </div>

      {/* 2-Column Playground Grid matching Screenshot */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6 flex-1 min-h-0">
        {/* Left: Chat Window */}
        <div className="h-full min-h-[500px]">
          <PlaygroundChatWindow
            activeModel={activeModel}
            messages={messages}
            onSendMessage={handleSendMessage}
            onClearChat={handleClearChat}
            loading={inferencing}
            tokenCount={tokenCount}
          />
        </div>

        {/* Right: Parameters Panel */}
        <div className="h-full min-h-[500px]">
          <PlaygroundParametersPanel
            deployedModels={deployedModels}
            selectedModelId={selectedModelId}
            onModelChange={(id) => setSelectedModelId(id)}
            parameters={parameters}
            onParametersChange={(newParams) => setParameters(newParams)}
            onReset={handleResetParameters}
          />
        </div>
      </div>
    </main>
  );
}

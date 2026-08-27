"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Trash2,
  Copy,
  Check,
  ThumbsUp,
  ThumbsDown,
  Cpu,
  Bot,
  User,
  Sparkles,
  Loader2,
  Layers,
} from "lucide-react";
import { toast } from "sonner";

export default function PlaygroundChatWindow({
  activeModel,
  messages = [],
  onSendMessage,
  onClearChat,
  loading = false,
  tokenCount = 0,
}) {
  const [inputPrompt, setInputPrompt] = useState("");
  const [copiedIndex, setCopiedIndex] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputPrompt.trim() || loading) return;
    onSendMessage(inputPrompt);
    setInputPrompt("");
  };

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    toast.success("Message copied to clipboard");
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const modelDisplayName = activeModel?.model_name || "HDFC-Banking-v1.2";

  return (
    <div className="h-full bg-white rounded-2xl border border-gray-200/80 shadow-sm flex flex-col justify-between overflow-hidden">
      {/* 1. Header */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b border-gray-100 bg-[#FAFBFE]">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-50 text-[#002B55]">
            <Cpu size={15} />
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm text-gray-900">
              {modelDisplayName}
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[10px] font-bold text-emerald-700 uppercase tracking-wider">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              DEPLOYED
            </span>
          </div>
        </div>

        <button
          type="button"
          onClick={onClearChat}
          className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition cursor-pointer"
        >
          <Trash2 size={13} />
          <span>Clear Chat</span>
        </button>
      </div>

      {/* 2. Messages Thread */}
      <div className="flex-1 p-6 overflow-y-auto space-y-6">
        {/* System Instruction Banner */}
        <div className="flex justify-center">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 border border-slate-200/70 px-3.5 py-1 text-[11px] font-semibold text-slate-600 shadow-2xs">
            <Sparkles size={12} className="text-amber-500" />
            <span>System Instruction Injected</span>
          </span>
        </div>

        {messages.length === 0 ? (
          <div className="h-48 flex flex-col items-center justify-center text-center text-gray-400">
            <Bot size={32} className="text-gray-300 mb-2" />
            <p className="text-xs font-medium">
              Start evaluating {modelDisplayName} by entering a prompt below.
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => {
            const isUser = msg.role === "user";
            return (
              <div
                key={idx}
                className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
              >
                {!isUser && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-[#002B55] border border-blue-100 shadow-2xs">
                    <Bot size={16} />
                  </div>
                )}

                <div
                  className={`max-w-2xl rounded-2xl p-4 text-xs leading-relaxed ${
                    isUser
                      ? "bg-[#002B55] text-white rounded-tr-none shadow-sm"
                      : "bg-[#F8FAFC] border border-slate-200/80 text-gray-800 rounded-tl-none"
                  }`}
                >
                  {/* Model Header */}
                  {!isUser && (
                    <span className="font-bold text-[11px] text-gray-900 block mb-1">
                      {modelDisplayName}
                    </span>
                  )}

                  {/* Message Content */}
                  <div className="whitespace-pre-wrap font-sans space-y-2">
                    {msg.content}
                  </div>

                  {/* Latency & Actions for Assistant */}
                  {!isUser && (
                    <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-200/60 text-[11px] text-gray-400">
                      {msg.latency && (
                        <span>
                          Latency: {(msg.latency * 1000).toFixed(0)}ms
                        </span>
                      )}

                      <div className="flex items-center gap-1 ml-auto">
                        <button
                          type="button"
                          onClick={() => handleCopy(msg.content, idx)}
                          className="p-1 rounded text-gray-400 hover:text-gray-700 transition"
                          title="Copy response"
                        >
                          {copiedIndex === idx ? (
                            <Check size={13} className="text-emerald-600" />
                          ) : (
                            <Copy size={13} />
                          )}
                        </button>
                        <button
                          type="button"
                          className="p-1 rounded text-gray-400 hover:text-gray-700 transition"
                          title="Thumbs up"
                        >
                          <ThumbsUp size={13} />
                        </button>
                        <button
                          type="button"
                          className="p-1 rounded text-gray-400 hover:text-gray-700 transition"
                          title="Thumbs down"
                        >
                          <ThumbsDown size={13} />
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-200 text-slate-700">
                    <User size={16} />
                  </div>
                )}
              </div>
            );
          })
        )}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-[#002B55]">
              <Bot size={16} />
            </div>
            <div className="rounded-2xl rounded-tl-none bg-[#F8FAFC] border border-slate-200 p-4 text-xs flex items-center gap-2 text-gray-500">
              <Loader2 size={15} className="animate-spin text-[#002B55]" />
              <span>Generating inference response...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 3. Bottom Prompt Input Bar matching Screenshot */}
      <div className="p-4 border-t border-gray-100 bg-[#FAFBFE]">
        <div className="flex items-center justify-between text-[11px] font-semibold text-gray-400 mb-2 px-1">
          <span>Tokens: {tokenCount} / 4,096</span>
          <span className="font-mono">Context Window: 4k</span>
        </div>

        <form onSubmit={handleSubmit} className="relative flex items-center">
          <input
            type="text"
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            placeholder="Enter prompt to evaluate model behavior..."
            disabled={loading}
            className="w-full rounded-xl border border-gray-200 bg-white pl-4 pr-12 py-3 text-xs text-gray-900 placeholder:text-gray-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 shadow-2xs"
          />

          <button
            type="submit"
            disabled={!inputPrompt.trim() || loading}
            className="absolute right-2 flex h-8 w-8 items-center justify-center rounded-lg bg-[#002B55] text-white hover:bg-[#001D3D] transition cursor-pointer disabled:opacity-40"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          </button>
        </form>
      </div>
    </div>
  );
}

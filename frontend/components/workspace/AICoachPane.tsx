"use client";

import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Send,
  CheckCircle2,
  Lock,
  Unlock,
  ArrowRight,
  Zap,
  Code2,
  Settings,
  X,
  Key,
  Sparkles,
} from "lucide-react";
import { ChatEvaluation } from "@/types/problem";

interface AICoachPaneProps {
  questionId: string;
  questionTitle: string;
  language: string;
  isUnlocked: boolean;
  tokensUsed: number;
  onPushToEditor: (starterCode: string) => void;
  onTokenUpdate: (used: number) => void;
}

interface Message {
  id: string;
  sender: "coach" | "student";
  text: string;
  evaluation?: ChatEvaluation;
  starterCode?: string | null;
  isPushed?: boolean;
  promptTokens?: number;
  completionTokens?: number;
  turnTokens?: number;
  providerUsed?: string;
  modelUsed?: string;
}

export function AICoachPane({
  questionId,
  questionTitle,
  language,
  isUnlocked,
  tokensUsed,
  onPushToEditor,
  onTokenUpdate,
}: AICoachPaneProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial-msg",
      sender: "coach",
      text: `Before writing code, explain your algorithmic strategy:\n\n1. What do you understand about the problem?\n2. What data structure will you use?\n3. What algorithm or pattern will you apply?\n4. What is your expected time and space complexity?\n\nI retain memory across our conversation. Once approved, I will generate your starter template in **${language.toUpperCase()}** with a **Push to Code Editor & Unlock** button.`,
    },
  ]);
  const [prompt, setPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // BYOK (Bring Your Own Key) Settings State for Google Gemini
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [customApiKey, setCustomApiKey] = useState("");

  const TOKEN_LIMIT = 2000;
  const tokenPercentage = Math.min(100, Math.round((tokensUsed / TOKEN_LIMIT) * 100));

  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedKey = localStorage.getItem("dsa_gemini_api_key") || "";
      setCustomApiKey(savedKey);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    if (typeof window !== "undefined") {
      localStorage.setItem("dsa_gemini_api_key", customApiKey.trim());
    }
    setIsSettingsOpen(false);
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const textToSend = prompt.trim();
    if (!textToSend || isLoading) return;

    const userMsgId = `user-${Date.now()}`;
    const newMessages: Message[] = [
      ...messages,
      { id: userMsgId, sender: "student", text: textToSend },
    ];
    setMessages(newMessages);
    setPrompt("");
    setIsLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
      const res = await fetch(`${apiUrl}/api/v1/chat/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer dev_user_student42",
        },
        body: JSON.stringify({
          question_id: questionId,
          prompt: textToSend,
          language: language,
          custom_provider: "gemini",
          custom_api_key: customApiKey.trim() ? customApiKey.trim() : undefined,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server returned HTTP ${res.status}`);
      }

      const evalData: ChatEvaluation = await res.json();
      onTokenUpdate(evalData.tokens_used);

      setMessages([
        ...newMessages,
        {
          id: `coach-${Date.now()}`,
          sender: "coach",
          text: evalData.feedback,
          evaluation: evalData,
          starterCode: evalData.starter_code,
          isPushed: false,
          promptTokens: evalData.prompt_tokens,
          completionTokens: evalData.completion_tokens,
          turnTokens: evalData.turn_tokens,
          providerUsed: "gemini",
          modelUsed: evalData.model_used || "gemini-3.5-flash-lite",
        },
      ]);
    } catch (err: any) {
      setMessages([
        ...newMessages,
        {
          id: `err-${Date.now()}`,
          sender: "coach",
          text: `⚠️ Communication error: ${err.message}. Verify that FastAPI backend is running on port 8000.`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePush = (messageId: string, starterCode: string) => {
    onPushToEditor(starterCode);
    setMessages((prev) =>
      prev.map((msg) => (msg.id === messageId ? { ...msg, isPushed: true } : msg))
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0d1117] overflow-hidden relative">
      {/* Pane Header */}
      <div className="border-b border-zinc-800/80 px-3 py-2 bg-[#161b22]/70 shrink-0 space-y-1.5">
        {/* Row 1: Brand & Model + Settings */}
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 min-w-0">
            <span className="font-semibold text-zinc-100 tracking-tight shrink-0">AI Coach</span>
            <span className="inline-flex items-center gap-1.5 text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800/90 text-zinc-300 border border-zinc-700/70 whitespace-nowrap shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
              <span>Gemini 3.8 Flash</span>
            </span>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            {/* BYOK Settings Trigger */}
            <button
              type="button"
              onClick={() => setIsSettingsOpen(true)}
              title="Configure Google Gemini API Key"
              className="p-1 rounded text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400 cursor-pointer"
            >
              <Settings className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Row 2: Status & Input Token Budget */}
        <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400">
          <div className="flex items-center gap-1.5">
            {isUnlocked ? (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-emerald-950/40 text-emerald-400 border border-emerald-800/50">
                <Unlock className="w-2.5 h-2.5" aria-hidden="true" /> Unlocked
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-zinc-800/60 text-zinc-400 border border-zinc-700/60">
                <Lock className="w-2.5 h-2.5" aria-hidden="true" /> Locked
              </span>
            )}
          </div>

          <div className="tabular-nums text-right whitespace-nowrap">
            <span
              className={`font-semibold ${
                tokensUsed >= TOKEN_LIMIT
                  ? "text-rose-400"
                  : tokensUsed > 1400
                  ? "text-amber-400"
                  : "text-zinc-200"
              }`}
            >
              {tokensUsed}
            </span>
            <span className="text-zinc-500"> / {TOKEN_LIMIT} input tokens</span>
          </div>
        </div>

        {/* Minimal Token Meter Bar */}
        <div className="w-full bg-zinc-800/80 rounded-full h-1 overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              tokensUsed > 1800 ? "bg-rose-500" : tokensUsed > 1200 ? "bg-amber-400" : "bg-sky-400"
            }`}
            style={{ width: `${tokenPercentage}%` }}
          />
        </div>
      </div>

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3.5 text-xs leading-relaxed select-text">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.sender === "student" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`max-w-[94%] rounded-lg p-3 ${
                msg.sender === "student"
                  ? "bg-zinc-800 text-zinc-100 border border-zinc-700/80"
                  : "bg-[#161b22]/90 text-zinc-200 border border-zinc-800 space-y-2.5"
              }`}
            >
              {/* Message Body */}
              <div className="prose prose-invert max-w-none text-xs leading-relaxed">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                    strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
                    ul: ({ children }) => <ul className="list-disc pl-4 space-y-1 mb-2">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal pl-4 space-y-1 mb-2">{children}</ol>,
                    li: ({ children }) => <li className="text-zinc-300">{children}</li>,
                    code: ({ children }) => (
                      <code className="bg-zinc-900 text-zinc-200 font-mono px-1 py-0.5 rounded text-[11px] border border-zinc-700/50">
                        {children}
                      </code>
                    ),
                  }}
                >
                  {msg.text}
                </ReactMarkdown>
              </div>

              {/* Starter Code Block with Push Button */}
              {msg.starterCode && (
                <div className="mt-3 pt-3 border-t border-zinc-800/80 space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400">
                    <span className="flex items-center gap-1.5 text-zinc-300 font-medium">
                      <Code2 className="w-3.5 h-3.5 text-emerald-400" />
                      Starter Template ({language})
                    </span>
                  </div>

                  <pre className="p-2.5 rounded bg-[#0d1117] border border-zinc-800 text-zinc-200 font-mono text-[11px] overflow-x-auto whitespace-pre leading-relaxed max-h-48">
                    {msg.starterCode}
                  </pre>

                  <div className="pt-1">
                    <button
                      type="button"
                      onClick={() => handlePush(msg.id, msg.starterCode!)}
                      disabled={msg.isPushed}
                      className={`w-full flex items-center justify-center gap-2 py-2 px-3 rounded text-xs font-semibold transition-all shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400 cursor-pointer ${
                        msg.isPushed
                          ? "bg-zinc-800 text-emerald-400 border border-emerald-500/30 cursor-default"
                          : "bg-white hover:bg-zinc-200 text-zinc-950 hover:shadow"
                      }`}
                    >
                      {msg.isPushed ? (
                        <>
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          <span>Pushed to Code Editor ✓</span>
                        </>
                      ) : (
                        <>
                          <ArrowRight className="w-4 h-4" />
                          <span>Push to Code Editor & Unlock</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Transparent Token Breakdown */}
              {msg.promptTokens !== undefined && msg.promptTokens > 0 && (
                <div className="mt-2 pt-2 border-t border-zinc-800/60 flex items-center justify-between text-[10px] font-mono text-zinc-500">
                  <span className="flex items-center gap-1 text-zinc-400">
                    <Zap className="w-3 h-3 text-sky-400" />
                    Turn: {msg.promptTokens} input tokens (+ {msg.completionTokens} response)
                  </span>
                  <span className="text-zinc-500">{msg.modelUsed || "Gemini 3.5 Flash-Lite"}</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-start">
            <div className="bg-[#161b22] border border-zinc-800 p-3 rounded-lg text-xs text-zinc-400 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Analyzing multi-turn algorithmic strategy…</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSendMessage} className="p-2.5 border-t border-zinc-800/80 bg-[#161b22]/50">
        <div className="relative flex flex-col gap-1.5">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading || tokensUsed >= TOKEN_LIMIT}
            placeholder={
              tokensUsed >= TOKEN_LIMIT
                ? "Token budget limit reached (2,000 tokens)."
                : "Explain your approach: problem understanding, data structure, algorithm, and time/space complexity (Enter to send, Shift+Enter for newline)…"
            }
            rows={3}
            className="w-full bg-[#0d1117] border border-zinc-800 rounded-md p-2.5 text-xs text-zinc-100 placeholder-zinc-500 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400 resize-none disabled:opacity-50"
          />

          <div className="flex items-center justify-between px-1">
            <span className="text-[10px] font-mono text-zinc-500">
              Press Enter to send · Shift+Enter for new line
            </span>

            <button
              type="submit"
              disabled={!prompt.trim() || isLoading || tokensUsed >= TOKEN_LIMIT}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-white hover:bg-zinc-200 text-zinc-950 disabled:opacity-30 disabled:hover:bg-white transition-colors cursor-pointer disabled:cursor-not-allowed"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Send</span>
            </button>
          </div>
        </div>
      </form>

      {/* Google Gemini BYOK Settings Modal Overlay */}
      {isSettingsOpen && (
        <div className="absolute inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-sm bg-[#161b22] border border-zinc-800 rounded-lg p-4 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-white">
                <Sparkles className="w-4 h-4 text-sky-400" />
                <span>Google Gemini Configuration</span>
              </div>
              <button
                type="button"
                onClick={() => setIsSettingsOpen(false)}
                className="text-zinc-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveSettings} className="space-y-3.5 text-xs">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-zinc-400 font-medium flex items-center gap-1">
                    <Key className="w-3 h-3 text-sky-400" />
                    <span>Gemini API Key</span>
                  </label>
                  <span className="text-[10px] font-mono text-sky-400">Free Tier Supported</span>
                </div>
                <input
                  type="password"
                  value={customApiKey}
                  onChange={(e) => setCustomApiKey(e.target.value)}
                  placeholder="AIzaSy..."
                  className="w-full bg-[#0d1117] border border-zinc-700 rounded px-2.5 py-1.5 text-xs text-zinc-100 font-mono focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400"
                />
                <p className="text-[10px] text-zinc-500 mt-1.5 leading-relaxed">
                  Generate your free key from{" "}
                  <a
                    href="https://aistudio.google.com"
                    target="_blank"
                    rel="noreferrer"
                    className="text-sky-400 underline hover:text-sky-300"
                  >
                    Google AI Studio
                  </a>
                  . Stored locally in your browser.
                </p>
              </div>

              <div className="p-2.5 rounded bg-zinc-900/60 border border-zinc-800 text-[11px] text-zinc-400 space-y-1">
                <div className="font-medium text-zinc-300">Active Model Stack:</div>
                <div className="font-mono text-[10px] text-zinc-400">
                  • Primary: <span className="text-zinc-200">gemini-3.5-flash-lite</span>
                </div>
                <div className="font-mono text-[10px] text-zinc-400">
                  • High-Demand Fallback: <span className="text-zinc-200">gemini-3.1-flash-lite</span>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-zinc-800">
                <button
                  type="button"
                  onClick={() => setIsSettingsOpen(false)}
                  className="px-3 py-1 rounded text-zinc-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 rounded bg-white hover:bg-zinc-200 text-zinc-950 font-medium cursor-pointer"
                >
                  Save Key
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

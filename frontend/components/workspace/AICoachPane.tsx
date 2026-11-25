"use client";

import React, { useState } from "react";
import { Sparkles, Send, ShieldAlert, CheckCircle, AlertTriangle, Lightbulb, Lock, Unlock } from "lucide-react";
import { ChatEvaluation } from "@/types/problem";

interface AICoachPaneProps {
  questionId: string;
  questionTitle: string;
  isUnlocked: boolean;
  tokensUsed: number;
  onUnlock: (starterCode: string) => void;
  onTokenUpdate: (used: number) => void;
}

interface Message {
  sender: "coach" | "student";
  text: string;
  evaluation?: ChatEvaluation;
}

const QUICK_STARTERS = [
  "I will use a Hash Map to store complement values in O(N) time and O(N) space.",
  "I will use a Stack to track open brackets in O(N) time.",
  "Can I solve this using Two Pointers in O(N) time?",
];

export function AICoachPane({
  questionId,
  questionTitle,
  isUnlocked,
  tokensUsed,
  onUnlock,
  onTokenUpdate,
}: AICoachPaneProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "coach",
      text: `Welcome! The code editor is locked. Before writing code, explain your algorithmic strategy to me. State the data structure, algorithm/pattern, and expected time and space complexity to receive starter code and unlock the editor.`,
    },
  ]);
  const [prompt, setPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const TOKEN_LIMIT = 2000;
  const tokenPercentage = Math.min(100, Math.round((tokensUsed / TOKEN_LIMIT) * 100));

  // Determine token progress bar color
  const tokenBarColor =
    tokensUsed > 1800
      ? "bg-rose-500"
      : tokensUsed > 1200
      ? "bg-amber-500"
      : "bg-emerald-500";

  const handleSendMessage = async (userText: string) => {
    const textToSend = userText || prompt;
    if (!textToSend.trim() || isLoading) return;

    const newMessages: Message[] = [...messages, { sender: "student", text: textToSend }];
    setMessages(newMessages);
    setPrompt("");
    setIsLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/chat/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer dev_user_student42",
        },
        body: JSON.stringify({
          question_id: questionId,
          prompt: textToSend,
          language: "python",
        }),
      });

      if (!res.ok) {
        throw new Error(`AI Coach responded with ${res.status}`);
      }

      const evalData: ChatEvaluation = await res.json();
      onTokenUpdate(evalData.tokens_used);

      if (evalData.is_approved && evalData.starter_code) {
        onUnlock(evalData.starter_code);
      }

      setMessages([
        ...newMessages,
        {
          sender: "coach",
          text: evalData.feedback,
          evaluation: evalData,
        },
      ]);
    } catch (err: any) {
      setMessages([
        ...newMessages,
        {
          sender: "coach",
          text: `⚠️ Communication error with AI Coach: ${err.message}. Please check that your FastAPI backend is running on port 8000.`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
      {/* Pane Header & 2,000-Token Meter */}
      <div className="border-b border-zinc-800 p-3 bg-zinc-900">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 font-semibold text-xs text-white">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <span>AI Algorithmic Coach</span>
          </div>

          <div className="flex items-center gap-1.5 text-xs font-mono">
            <span className="text-zinc-400">Tokens:</span>
            <span className={tokensUsed > 1800 ? "text-rose-400 font-bold" : "text-white font-bold"}>
              {tokensUsed}
            </span>
            <span className="text-zinc-500">/ {TOKEN_LIMIT}</span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${tokenBarColor}`}
            style={{ width: `${tokenPercentage}%` }}
          />
        </div>

        {/* Status Indicator */}
        <div className="flex items-center justify-between mt-2 text-[11px]">
          <span className="text-zinc-500">Redis Guardrail Active</span>
          {isUnlocked ? (
            <span className="flex items-center gap-1 text-emerald-400 font-medium">
              <Unlock className="w-3 h-3" /> Editor Unlocked
            </span>
          ) : (
            <span className="flex items-center gap-1 text-amber-400 font-medium">
              <Lock className="w-3 h-3" /> Editor Locked
            </span>
          )}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex flex-col ${
              msg.sender === "student" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`max-w-[90%] p-3.5 rounded-xl leading-relaxed ${
                msg.sender === "student"
                  ? "bg-emerald-500/10 text-emerald-100 border border-emerald-500/30 rounded-tr-none"
                  : "bg-zinc-950 border border-zinc-800 text-zinc-300 rounded-tl-none shadow-sm"
              }`}
            >
              {msg.text}

              {/* Evaluation Detail Badges */}
              {msg.evaluation && (
                <div className="mt-3 pt-3 border-t border-zinc-800/80 space-y-2">
                  <div className="flex flex-wrap gap-1.5 text-[10px]">
                    {msg.evaluation.detected_data_structure && (
                      <span className="px-2 py-0.5 rounded bg-zinc-800 text-emerald-400 border border-zinc-700 font-mono">
                        DS: {msg.evaluation.detected_data_structure}
                      </span>
                    )}
                    {msg.evaluation.detected_algorithm && (
                      <span className="px-2 py-0.5 rounded bg-zinc-800 text-cyan-400 border border-zinc-700 font-mono">
                        Pattern: {msg.evaluation.detected_algorithm}
                      </span>
                    )}
                    {msg.evaluation.time_complexity && (
                      <span className="px-2 py-0.5 rounded bg-zinc-800 text-amber-400 border border-zinc-700 font-mono">
                        TC: {msg.evaluation.time_complexity}
                      </span>
                    )}
                    {msg.evaluation.space_complexity && (
                      <span className="px-2 py-0.5 rounded bg-zinc-800 text-purple-400 border border-zinc-700 font-mono">
                        SC: {msg.evaluation.space_complexity}
                      </span>
                    )}
                  </div>

                  {msg.evaluation.is_approved ? (
                    <div className="flex items-center gap-1.5 text-emerald-400 font-semibold text-xs pt-1">
                      <CheckCircle className="w-4 h-4" />
                      <span>Approach approved! Starter code released to editor.</span>
                    </div>
                  ) : msg.evaluation.missing_requirements?.length > 0 ? (
                    <div className="text-amber-400 text-[11px] space-y-1">
                      <span className="font-semibold block">Missing Requirements:</span>
                      <ul className="list-disc list-inside space-y-0.5 text-zinc-400">
                        {msg.evaluation.missing_requirements.map((req, idx) => (
                          <li key={idx}>{req}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center gap-2 text-zinc-500 text-xs italic">
            <Sparkles className="w-3.5 h-3.5 animate-spin text-emerald-400" />
            <span>AI Coach analyzing your algorithmic approach...</span>
          </div>
        )}
      </div>

      {/* Quick Prompts Footer */}
      {!isUnlocked && (
        <div className="p-2 border-t border-zinc-800/60 bg-zinc-950/40">
          <div className="flex items-center gap-1 text-[11px] text-zinc-500 mb-1.5">
            <Lightbulb className="w-3 h-3 text-amber-400" />
            <span>Suggested Explanations:</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {QUICK_STARTERS.map((s, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(s)}
                className="text-[10px] text-zinc-400 hover:text-white bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded px-2 py-1 transition-colors text-left truncate max-w-full"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage(prompt);
        }}
        className="p-3 border-t border-zinc-800 bg-zinc-900 flex gap-2"
      >
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={
            tokensUsed >= TOKEN_LIMIT
              ? "Token limit reached (2,000/2,000)"
              : "Explain your data structure, pattern, and complexity..."
          }
          disabled={isLoading || tokensUsed >= TOKEN_LIMIT}
          className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500"
        />
        <button
          type="submit"
          disabled={isLoading || !prompt.trim() || tokensUsed >= TOKEN_LIMIT}
          className="px-3 py-2 rounded-lg bg-emerald-500 text-zinc-950 font-semibold hover:bg-emerald-400 disabled:opacity-40 disabled:hover:bg-emerald-500 transition-colors flex items-center justify-center"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}

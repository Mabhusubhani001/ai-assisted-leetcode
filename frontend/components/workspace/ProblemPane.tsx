"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { QuestionDetail } from "@/types/problem";
import { FileText, CheckCircle2, Clock, Cpu, History } from "lucide-react";

interface ProblemPaneProps {
  problem: QuestionDetail;
}

export function ProblemPane({ problem }: ProblemPaneProps) {
  const [activeTab, setActiveTab] = useState<"description" | "cases">("description");

  const difficultyColors = {
    easy: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    medium: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    hard: "text-rose-400 bg-rose-500/10 border-rose-500/20",
  }[problem.difficulty.toLowerCase()] || "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";

  return (
    <div className="flex flex-col h-full bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
      {/* Pane Header Tabs */}
      <div className="flex items-center justify-between border-b border-zinc-800 px-4 bg-zinc-900">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("description")}
            className={`flex items-center gap-2 py-3 px-3 text-xs font-medium border-b-2 transition-colors ${
              activeTab === "description"
                ? "border-emerald-500 text-white"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Problem Statement</span>
          </button>
          <button
            onClick={() => setActiveTab("cases")}
            className={`flex items-center gap-2 py-3 px-3 text-xs font-medium border-b-2 transition-colors ${
              activeTab === "cases"
                ? "border-emerald-500 text-white"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Visible Cases ({problem.test_cases?.length || 0})</span>
          </button>
        </div>

        <div className="flex items-center gap-3">
          <span className={`text-xs px-2.5 py-0.5 rounded-full border font-semibold ${difficultyColors}`}>
            {problem.difficulty}
          </span>
          <span className="flex items-center gap-1 text-[11px] text-zinc-400 font-mono">
            <Clock className="w-3 h-3" />
            {problem.time_limit_sec}s
          </span>
          <span className="flex items-center gap-1 text-[11px] text-zinc-400 font-mono">
            <Cpu className="w-3 h-3" />
            {problem.memory_limit_mb}MB
          </span>
        </div>
      </div>

      {/* Pane Content */}
      <div className="flex-1 overflow-y-auto p-5 text-zinc-300">
        {activeTab === "description" ? (
          <div className="prose prose-invert prose-emerald max-w-none prose-headings:font-bold prose-headings:text-white prose-p:leading-relaxed prose-pre:bg-zinc-950 prose-pre:border prose-pre:border-zinc-800">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {problem.description}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-xs text-zinc-400 mb-2">
              These 3 public test cases will run during practice. An additional 7 confidential edge cases will be evaluated on final submission.
            </p>
            {problem.test_cases.map((tc, index) => (
              <div key={tc.id || index} className="p-3 rounded-lg border border-zinc-800 bg-zinc-950/80">
                <div className="text-xs font-semibold text-zinc-400 mb-2">
                  Case {index + 1}
                </div>
                <div className="space-y-2 text-xs font-mono">
                  <div>
                    <span className="text-zinc-500 block text-[11px] uppercase tracking-wider mb-1">Standard Input:</span>
                    <pre className="p-2 rounded bg-zinc-900 border border-zinc-800/80 text-emerald-400 overflow-x-auto whitespace-pre-wrap">
                      {tc.stdin}
                    </pre>
                  </div>
                  <div>
                    <span className="text-zinc-500 block text-[11px] uppercase tracking-wider mb-1">Expected Output:</span>
                    <pre className="p-2 rounded bg-zinc-900 border border-zinc-800/80 text-cyan-400 overflow-x-auto">
                      {tc.expected_stdout}
                    </pre>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
